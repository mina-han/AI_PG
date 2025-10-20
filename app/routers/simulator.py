import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from twilio.rest import Client
import json

from app.config import settings

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.api_route("/twiml/{incident_id}", methods=["GET", "POST"])
def get_twiml(incident_id: int, contact_name: Optional[str] = None) -> Response:
    """TwiML을 반환하는 endpoint (URL 방식 - GET/POST 모두 지원)"""
    twiml = create_twiml("", contact_name, incident_id)
    print(f"[TWIML ENDPOINT] Returning TwiML for incident {incident_id}")
    return Response(content=twiml, media_type="application/xml")


class SimulatorCallRequest(BaseModel):
    primary_name: str
    primary_phone: str
    secondary_name: Optional[str] = None
    secondary_phone: Optional[str] = None
    incident_summary: str
    tts_text: str


def create_twiml(message: str, contact_name: str = None, incident_id: int = None) -> str:
    """TwiML 생성 - 메시지 + Gather (XML 이스케이프)"""
    import html
    
    # DB에서 실제 메시지 가져오기
    from app.db import get_session, get_incident
    with get_session() as session:
        inc = get_incident(session, incident_id)
        full_message = inc.tts_text if inc else "긴급 상황입니다."
    
    # 담당자 이름 포함
    if contact_name:
        full_message = f"{contact_name} 담당자님, {full_message}"
    
    # XML 특수문자 이스케이프
    full_message = html.escape(full_message)
    
    # Action URL
    action_url = f"{settings.public_base_url}/twilio/transfer?incident_id={incident_id}"
    if contact_name:
        action_url += f"&contact_name={quote(contact_name)}"
    
    # Action URL도 이스케이프 (& 기호 때문)
    action_url = html.escape(action_url)
    
    # TwiML 생성 (메시지 + 안내를 2번 반복)
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response>'
    # 1차 반복
    twiml += f'<Say language="ko-KR">{full_message}</Say>'
    twiml += '<Pause length="1"/>'
    twiml += '<Say language="ko-KR">상황근무자 연결은 1번, 장애 문자 전송은 2번을 눌러주세요.</Say>'
    twiml += '<Pause length="1"/>'
    # 2차 반복 (Gather 포함)
    twiml += f'<Gather action="{action_url}" method="POST" numDigits="1" timeout="10">'
    twiml += f'<Say language="ko-KR">{full_message}</Say>'
    twiml += '<Pause length="1"/>'
    twiml += '<Say language="ko-KR">상황근무자 연결은 1번, 장애 문자 전송은 2번을 눌러주세요.</Say>'
    twiml += '</Gather>'
    twiml += '<Hangup/></Response>'
    
    print(f"[TWIML-ESCAPED] incident {incident_id}:")
    print(twiml[:300])
    
    return twiml


async def check_call_status(client: Client, call_sid: str, max_wait: int = 20) -> dict:
    """
    Twilio 통화 상태를 폴링하여 최종 결과 확인
    
    Returns:
        {"status": "answered" | "no-answer" | "busy" | "failed" | "canceled", "duration": int}
    """
    start_time = time.time()
    in_progress_detected = False  # in-progress 상태를 한번이라도 감지했는지
    in_progress_start_time = None  # in-progress 시작 시간
    check_count = 0  # 체크 횟수
    
    while time.time() - start_time < max_wait:
        try:
            call = client.calls(call_sid).fetch()
            status = call.status
            check_count += 1
            
            # 디버깅: 상태 변화 로깅
            if check_count <= 3 or status in ["completed", "busy", "failed", "canceled", "in-progress"]:
                print(f"Call {call_sid} status: {status} (check #{check_count})")
            
            # 통화 상태별 처리
            if status == "completed":
                # completed 상태를 처음 감지했을 때, duration이 업데이트될 때까지 빠르게 재조회
                duration = 0
                answered_by = None
                
                for retry in range(3):  # 3번 재시도 (0.4초 간격, 총 1.2초)
                    await asyncio.sleep(0.4)
                    call = client.calls(call_sid).fetch()
                    
                    try:
                        if call.duration:
                            duration = int(call.duration)
                    except (ValueError, TypeError):
                        duration = 0
                    
                    answered_by = getattr(call, 'answered_by', None)
                    
                    # duration이 업데이트되었거나 in_progress가 감지되었으면 즉시 종료
                    if duration > 0 or in_progress_detected:
                        break
                
                print(f"Call completed - duration: {duration}s, answered_by: {answered_by}, in_progress_detected: {in_progress_detected}")
                
                # 실제로 통화가 이루어졌는지 엄격하게 확인:
                # 1. duration이 최소 5초 이상 (전화 받고 메시지 듣기 시작하면 최소 5초)
                # 2. answered_by가 machine/fax가 아님 (사람이 받은 경우)
                if duration >= 5 and answered_by not in ['machine', 'fax']:
                    return {"status": "answered", "duration": duration}
                # duration은 있지만 너무 짧거나 자동응답기가 받은 경우
                elif duration > 0:
                    print(f"Call duration too short ({duration}s) or answered_by={answered_by} - marking as no-answer")
                    return {"status": "no-answer", "duration": duration}
                else:
                    # duration이 0이면 전화 거절 또는 즉시 끊김
                    return {"status": "no-answer", "duration": 0}
            
            elif status == "busy":
                return {"status": "busy", "duration": 0}
            
            elif status in ["failed", "canceled"]:
                return {"status": status, "duration": 0}
            
            # 아직 진행 중이면 대기 (초기엔 빠르게, 이후엔 0.5초마다 체크)
            elif status in ["queued", "ringing"]:
                # 초반 5번은 0.2초마다 빠르게 체크 (빠른 거절 감지)
                wait_time = 0.2 if check_count <= 5 else 0.4
                await asyncio.sleep(wait_time)
                continue
            
            elif status == "in-progress":
                # 전화가 연결되어 통화 중 상태 - completed 될 때까지 빠르게 체크
                if not in_progress_detected:
                    in_progress_detected = True
                    in_progress_start_time = time.time()
                    print(f"Call in progress detected at {in_progress_start_time - start_time:.1f}s")
                print(f"Call in progress - waiting for completion...")
                await asyncio.sleep(0.5)  # 통화 중 빠르게 체크하여 종료 즉시 감지
                continue
                
        except Exception as e:
            print(f"Error checking call status: {e}")
            # in-progress가 감지되었고 최소 5초 이상 통화했다면 성공으로 처리
            if in_progress_detected and in_progress_start_time:
                elapsed = time.time() - in_progress_start_time
                if elapsed >= 5:
                    print(f"Network error during call, but in-progress lasted {elapsed:.1f}s -> marking as answered")
                    return {"status": "answered", "duration": int(elapsed)}
                else:
                    print(f"Network error, in-progress only lasted {elapsed:.1f}s -> marking as no-answer")
                    return {"status": "no-answer", "duration": 0}
            # 네트워크 에러가 반복되면 재시도
            await asyncio.sleep(1)
            continue
    
    # 타임아웃 - in-progress가 감지되었고 최소 5초 이상이라면 성공으로 처리
    if in_progress_detected and in_progress_start_time:
        elapsed = time.time() - in_progress_start_time
        if elapsed >= 5:
            print(f"Timeout but in-progress lasted {elapsed:.1f}s -> marking as answered")
            return {"status": "answered", "duration": int(elapsed)}
        else:
            print(f"Timeout, in-progress only lasted {elapsed:.1f}s -> marking as no-answer")
            return {"status": "no-answer", "duration": 0}
    
    return {"status": "timeout", "duration": 0}


async def escalate_with_status(request: SimulatorCallRequest):
    """
    순차적 에스컬레이션 로직 with 실시간 상태 업데이트
    정 → 부 → 정 → 부 (최대 4회)
    한 명이라도 받으면 즉시 종료
    """
    def get_timestamp():
        """한국 시간 타임스탬프 생성"""
        return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    
    # Incident 생성 (SMS에서 사용할 수 있도록)
    from app.db import get_session, create_incident
    incident_id = None
    try:
        with get_session() as session:
            incident = create_incident(
                session=session,
                summary=request.incident_summary,
                tts_text=request.tts_text
            )
            incident_id = incident.id
            print(f"[SIMULATOR] Created incident {incident_id} for SMS")
    except Exception as e:
        print(f"[SIMULATOR] Failed to create incident: {e}")
    
    # 담당자 리스트 (정-부-정-부)
    contacts = [
        {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자"},
        {"name": request.secondary_name, "phone": request.secondary_phone, "role": "부담당자"},
        {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자(2차)"},
        {"name": request.secondary_name, "phone": request.secondary_phone, "role": "부담당자(2차)"},
    ]
    
    # 부담당자가 없으면 정담당자만 2회 시도
    if not request.secondary_name or not request.secondary_phone:
        contacts = [
            {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자"},
            {"name": request.primary_name, "phone": request.primary_phone, "role": "정담당자(2차)"},
        ]
    
    for idx, contact in enumerate(contacts, 1):
        # 발신 시작 이벤트
        yield f"data: {json.dumps({'type': 'call_start', 'attempt': idx, 'name': contact['name'], 'phone': contact['phone'], 'role': contact['role'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        try:
            # URL 방식으로 TwiML 제공 (inline 대신)
            twiml_url = f"{settings.public_base_url}/simulator/twiml/{incident_id}?contact_name={quote(contact['name'])}"
            
            print(f"[SIMULATOR] TwiML URL: {twiml_url}")
            
            # 전화 발신 (URL 방식)
            call = client.calls.create(
                to=contact['phone'],
                from_=settings.twilio_from_number,
                url=twiml_url,
                timeout=settings.call_timeout_seconds
            )
            
            call_sid = call.sid
            
            # 발신 완료 (통화 대기 중)
            yield f"data: {json.dumps({'type': 'call_initiated', 'attempt': idx, 'call_id': call_sid, 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.3)
            
            # 통화 상태 확인 (최대 20초 대기 - 빠른 실패 감지)
            result = await check_call_status(client, call_sid, max_wait=20)
            
            # DB에 통화 결과 저장 및 Incident 상태 업데이트
            if incident_id:
                try:
                    from app.db import log_call_attempt, get_incident
                    with get_session() as session:
                        call_result = "answered" if result['status'] == 'answered' else "no_answer"
                        log_call_attempt(
                            session=session,
                            incident_id=incident_id,
                            callee=contact['phone'],
                            provider="twilio",
                            result=call_result,
                            duration_sec=result.get('duration', 0)
                        )
                        print(f"[SIMULATOR] DB에 통화 기록 저장: {call_result}")
                        
                        # 전화를 받았으면 Incident 상태를 "answered"로 변경 (아직 대응은 안함)
                        if result['status'] == 'answered':
                            inc = get_incident(session, incident_id)
                            if inc and inc.status == "new":
                                inc.status = "answered"
                                session.add(inc)
                                session.commit()
                                print(f"[SIMULATOR] Incident #{incident_id} 상태를 'answered'로 변경 (미대응)")
                except Exception as e:
                    print(f"[SIMULATOR] DB 저장 실패: {e}")
            
            # 결과 전송
            if result['status'] == 'answered':
                yield f"data: {json.dumps({'type': 'call_answered', 'attempt': idx, 'name': contact['name'], 'duration': result['duration'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'escalation_complete', 'total_attempts': idx, 'answered_by': contact['name'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                return  # 성공 시 즉시 종료
            else:
                # 실패 (no-answer, busy, failed, timeout)
                yield f"data: {json.dumps({'type': 'call_failed', 'attempt': idx, 'name': contact['name'], 'reason': result['status'], 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
                # 실패 후 짧은 대기 후 다음 시도 (0.5초)
                await asyncio.sleep(0.5)
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'call_error', 'attempt': idx, 'name': contact['name'], 'error': str(e), 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(1)
    
    # 모든 시도 실패
    yield f"data: {json.dumps({'type': 'escalation_failed', 'total_attempts': len(contacts), 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"


@router.post("/call")
async def simulator_call(request: SimulatorCallRequest):
    """
    실시간 순차 에스컬레이션 with SSE (Server-Sent Events)
    
    정담당자 → 부담당자 → 정담당자(2차) → 부담당자(2차)
    한 명이라도 받으면 즉시 종료
    """
    async def event_generator():
        try:
            async for event in escalate_with_status(request):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx buffering 방지
        }
    )


@router.get("/transfer-log/{call_sid}")
def get_transfer_log(call_sid: str):
    """
    호전환 기록 조회
    """
    from app.providers.twilio_provider import transfer_logs
    
    if call_sid in transfer_logs:
        log = transfer_logs[call_sid]
        return {
            "found": True,
            "transferred": log.get("transferred", False),
            "to_number": log.get("to_number"),
            "timestamp": log.get("timestamp")
        }
    else:
        return {
            "found": False,
            "transferred": False
        }


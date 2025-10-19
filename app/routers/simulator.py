import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from twilio.rest import Client
import json

from app.config import settings

router = APIRouter(prefix="/simulator", tags=["simulator"])


class SimulatorCallRequest(BaseModel):
    primary_name: str
    primary_phone: str
    secondary_name: Optional[str] = None
    secondary_phone: Optional[str] = None
    incident_summary: str
    tts_text: str


def create_twiml(message: str, contact_name: str = None, incident_id: int = None) -> str:
    """TwiML 생성 - 각 문장을 별도 Say 태그로 분리하여 첫 글자 잘림 방지"""
    # 이름이 있으면 메시지 앞에 추가
    if contact_name:
        full_message = f"{contact_name} 담당자님, {message}"
    else:
        full_message = message
    
    # 각 문장을 분리
    sentences = [s.strip() for s in full_message.split('. ') if s.strip()]
    
    # 각 문장을 별도의 Say 태그로 생성
    say_tags = []
    for sentence in sentences:
        # 문장 시작 전 충분한 pause로 첫 글자 보호
        say_tags.append('<Pause length="0.5"/>')
        say_tags.append(f'<Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">{sentence}.</prosody></Say>')
        say_tags.append('<Pause length="0.8"/>')
    
    first_part = '\n  '.join(say_tags)
    
    # Gather 액션 URL 생성 - 절대 URL 사용 (Twilio는 절대 URL 필요)
    gather_action = f"{settings.public_base_url}/twilio/transfer"
    if incident_id:
        gather_action = f"{settings.public_base_url}/twilio/transfer?incident_id={incident_id}"
    
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  {first_part}
  <Pause length="1"/>
  <Gather action="{gather_action}" method="POST" numDigits="1" timeout="10">
    <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">상황근무자와의 통화연결을 원하시면 1번을 눌러주세요.</prosody></Say>
    <Pause length="2"/>
    <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">다시 한 번 말씀드립니다.</prosody></Say>
    <Pause length="2"/>
    {first_part}
    <Pause length="1"/>
    <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">상황근무자와의 통화연결을 원하시면 1번을 눌러주세요.</prosody></Say>
  </Gather>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""


async def check_call_status(client: Client, call_sid: str, max_wait: int = 20) -> dict:
    """
    Twilio 통화 상태를 폴링하여 최종 결과 확인
    
    Returns:
        {"status": "answered" | "no-answer" | "busy" | "failed" | "canceled", "duration": int}
    """
    start_time = time.time()
    in_progress_detected = False  # in-progress 상태를 한번이라도 감지했는지
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
                # completed 상태를 처음 감지했을 때, duration이 업데이트될 때까지 재조회 (최대 4초)
                duration = 0
                answered_by = None
                
                for retry in range(4):  # 4번 재시도 (0.8초 간격)
                    await asyncio.sleep(0.8)
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
                
                # in-progress 상태를 한번이라도 감지했으면 전화를 받은 것
                if in_progress_detected:
                    return {"status": "answered", "duration": duration if duration > 0 else 1}
                # duration이 조금이라도 있으면 전화를 받은 것으로 간주
                elif duration > 0:
                    return {"status": "answered", "duration": duration}
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
                # 전화가 연결되어 통화 중 상태 - completed 될 때까지 대기
                in_progress_detected = True
                print(f"Call in progress - waiting for completion...")
                await asyncio.sleep(1)  # 통화 중에는 천천히 체크
                continue
                
        except Exception as e:
            print(f"Error checking call status: {e}")
            # in-progress가 감지되었다면 네트워크 에러도 성공으로 처리 (전화 수신으로 인한 끊김)
            if in_progress_detected:
                print(f"Network error during call, but in-progress was detected -> marking as answered")
                return {"status": "answered", "duration": 1}
            # 네트워크 에러가 반복되면 재시도 (최대 3번)
            await asyncio.sleep(1)
            continue
    
    # 타임아웃 - in-progress가 감지되었다면 성공으로 처리
    if in_progress_detected:
        print(f"Timeout but in-progress was detected -> marking as answered")
        return {"status": "answered", "duration": 1}
    
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
            # 각 담당자 이름을 포함한 개인화된 TwiML 생성
            twiml = create_twiml(request.tts_text, contact['name'])
            
            # 전화 발신
            call = client.calls.create(
                to=contact['phone'],
                from_=settings.twilio_from_number,
                twiml=twiml,
                timeout=settings.call_timeout_seconds
            )
            
            call_sid = call.sid
            
            # 발신 완료 (통화 대기 중)
            yield f"data: {json.dumps({'type': 'call_initiated', 'attempt': idx, 'call_id': call_sid, 'timestamp': get_timestamp()}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.3)
            
            # 통화 상태 확인 (최대 20초 대기 - 빠른 실패 감지)
            result = await check_call_status(client, call_sid, max_wait=20)
            
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

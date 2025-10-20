from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Response, Form, Request, Query
from twilio.rest import Client

from app.config import settings
from app.providers.base import VoiceProvider
from app.db import get_session, get_incident

# 호전환 기록 저장 (메모리 기반)
transfer_logs = {}


class TwilioProvider(VoiceProvider):
    def __init__(self) -> None:
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        # TwiML URL for voice message
        twiml_url = f"{webhook_base}/twilio/voice?incident_id={incident_id}"
        call = self.client.calls.create(
            url=twiml_url,
            to=to_number,
            from_=settings.twilio_from_number,
            timeout=settings.call_timeout_seconds,
            status_callback=f"{webhook_base}/twilio/status?incident_id={incident_id}",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        return call.sid

    def send_sms(self, *, to_number: str, message: str) -> str:
        """Send SMS message using Twilio"""
        message_obj = self.client.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=to_number
        )
        return message_obj.sid

    def webhook_path(self) -> str:
        return "/twilio"


router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.get("/voice")
def twilio_voice(incident_id: int, text: Optional[str] = None) -> Response:
    # Twilio fetches TwiML; repeat message 2 times (no DTMF input required)
    if text:
        speak_text = text
    else:
        with get_session() as session:
            inc = get_incident(session, incident_id)
            speak_text = (
                inc.tts_text if inc else "긴급 알림입니다."
            )
    
    # Repeat message 2 times
    twiml = f"""
<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon">{speak_text}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">{speak_text}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">메시지 전달이 완료되었습니다. 감사합니다.</Say>
  <Hangup/>
</Response>
""".strip()
    return Response(content=twiml, media_type="application/xml")


@router.post("/gather")
def twilio_gather(incident_id: int, Digits: Optional[str] = Form(None)) -> Response:  # Twilio posts Digits
    from app.services.escalation import acknowledge_incident, retry_next
    
    if Digits == "1":
        acknowledge_incident(incident_id, dtmf="1")
        twiml = """
<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="en-US">Confirmation received. Thank you.</Say>
  <Hangup/>
</Response>
""".strip()
    else:
        with get_session() as session:
            inc = get_incident(session, incident_id)
            text = inc.tts_text if inc else "알림입니다."
        retry_next(incident_id, text)
        twiml = """
<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="en-US">Invalid input. Ending call.</Say>
  <Hangup/>
</Response>
""".strip()
    return Response(content=twiml, media_type="application/xml")


@router.post("/transfer")
async def twilio_transfer(
    request: Request,
    incident_id: Optional[int] = Query(None),
    contact_name: Optional[str] = Query(None),
    Digits: Optional[str] = Form(None)
) -> Response:
    """
    호전환 및 SMS 전송 처리
    1번: 상황근무자 연결
    2번: 장애 메시지 SMS 전송
    """
    # Twilio에서 전달하는 CallSid와 To(수신자 번호) 받기
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    caller_number = form.get("To", "")  # To가 실제 담당자 번호
    
    # incident_id가 Query로 안 오면 Form에서 가져오기
    if not incident_id:
        incident_id_str = form.get("incident_id")
        if incident_id_str:
            try:
                incident_id = int(incident_id_str)
            except:
                incident_id = None
    
    # 전체 폼 데이터 로그
    print(f"[TRANSFER] === FULL FORM DATA ===")
    for key, value in form.items():
        print(f"[TRANSFER] {key}: {value}")
    print(f"[TRANSFER] === END FORM DATA ===")
    print(f"[TRANSFER] Parsed - Digits: {Digits}, CallSid: {call_sid}, To: {caller_number}, incident_id: {incident_id}, contact_name: {contact_name}")
    
    # 상황근무자 번호 (010-8672-1718 -> +821086721718)
    situation_room_number = "+821086721718"
    
    if Digits == "1":
        print(f"[TRANSFER] Simulating transfer to {situation_room_number} (demo mode)")
        
        # 호전환 기록 저장 (메모리)
        transfer_logs[call_sid] = {
            "transferred": True,
            "to_number": situation_room_number,
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident_id,
            "action": "call_transfer"
        }
        print(f"[TRANSFER] Saved transfer log for CallSid: {call_sid}")
        
        # DB에 DTMF 입력 기록 저장 및 Incident 상태 업데이트
        if incident_id:
            try:
                with get_session() as session:
                    from app.db import log_call_attempt, get_incident
                    
                    # CallAttempt 기록
                    log_call_attempt(
                        session=session,
                        incident_id=incident_id,
                        callee=caller_number or "unknown",
                        provider="twilio",
                        result="ack",  # 호전환 요청 = 승인으로 처리
                        dtmf="1"
                    )
                    print(f"[TRANSFER] DB에 DTMF=1 기록 저장 완료")
                    
                    # Incident 상태를 "ack"로 변경
                    inc = get_incident(session, incident_id)
                    if inc and inc.status != "ack":
                        inc.status = "ack"
                        inc.acknowledged_at = datetime.utcnow()
                        session.add(inc)
                        session.commit()
                        print(f"[TRANSFER] Incident #{incident_id} 상태를 'ack'로 변경 완료")
            except Exception as e:
                print(f"[TRANSFER] DB 저장 실패: {e}")
        
        # 체험용: 실제 전화 없이 메시지만 재생
        twiml = f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">상황근무자에게 연결합니다.</prosody></Say>
  <Pause length="2"/>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">상황근무자와 연결이 완료되었습니다. 감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""
    
    elif Digits == "2":
        print(f"[SMS] ===== DIGIT 2 PRESSED =====")
        print(f"[SMS] CallSid: {call_sid}")
        
        sms_sent = False
        
        # CallSid로 원래 전화의 To 번호 조회
        try:
            print(f"[SMS] Fetching original call details for CallSid: {call_sid}")
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            call = client.calls(call_sid).fetch()
            original_to = call.to  # 원래 전화를 받은 담당자 번호
            caller_number = original_to
            print(f"[SMS] Original call To (담당자): {original_to}")
        except Exception as e:
            print(f"[SMS] ERROR fetching call details: {e}")
            caller_number = None
        
        print(f"[SMS] Final caller_number: {caller_number}")
        print(f"[SMS] incident_id: {incident_id}")
        
        # caller_number 검증
        if not caller_number:
            print(f"[SMS] ERROR: caller_number is EMPTY!")
            sms_sent = False
        elif not incident_id:
            print(f"[SMS] WARNING: incident_id is EMPTY! Trying to get latest incident...")
            # incident_id가 없으면 가장 최근 incident 가져오기
            try:
                with get_session() as session:
                    from app.db import Incident
                    latest_inc = session.query(Incident).order_by(Incident.id.desc()).first()
                    if latest_inc:
                        incident_id = latest_inc.id
                        print(f"[SMS] Found latest incident: {incident_id}")
                    else:
                        print(f"[SMS] ERROR: No incidents found in database!")
                        sms_sent = False
            except Exception as e:
                print(f"[SMS] ERROR fetching latest incident: {e}")
                sms_sent = False
        
        if caller_number:
            try:
                sms_message = None
                
                # incident_id가 있으면 실제 메시지 가져오기
                if incident_id:
                    print(f"[SMS] Fetching incident {incident_id}...")
                    with get_session() as session:
                        inc = get_incident(session, incident_id)
                        if inc:
                            print(f"[SMS] Incident found: {inc.tts_text[:30]}...")
                            name_prefix = f"{contact_name} 담당자님,\n\n" if contact_name else ""
                            # 한국 시간으로 변환 (DB는 UTC로 저장되므로 먼저 UTC로 지정 후 KST로 변환)
                            from zoneinfo import ZoneInfo
                            utc_time = inc.created_at.replace(tzinfo=ZoneInfo("UTC"))
                            kst_time = utc_time.astimezone(ZoneInfo("Asia/Seoul"))
                            sms_message = f"{name_prefix}[긴급 장애 알림]\n{inc.tts_text}\n\n발생시각: {kst_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n신속한 확인 부탁드립니다."
                
                # incident가 없으면 기본 메시지 사용
                if not sms_message:
                    print(f"[SMS] Using default message (no incident found)")
                    from zoneinfo import ZoneInfo
                    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
                    now_str = now_kst.strftime('%Y-%m-%d %H:%M:%S')
                    name_prefix = f"{contact_name} 담당자님,\n\n" if contact_name else ""
                    sms_message = f"{name_prefix}[긴급 장애 알림]\n단위DB 서버 다운 Critical 장애가 발생했습니다.\n\n발생시각: {now_str} (KST)\n담당자님의 신속한 확인 부탁드립니다."
                
                print(f"[SMS] Prepared message (length: {len(sms_message)})")
                
                # SMS 전송
                print(f"[SMS] Creating Twilio client...")
                sms_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
                
                print(f"[SMS] Sending SMS from {settings.twilio_from_number} to {caller_number}...")
                message = sms_client.messages.create(
                    body=sms_message,
                    from_=settings.twilio_from_number,
                    to=caller_number
                )
                
                sms_sent = True
                print(f"[SMS] ✅ SMS sent successfully! MessageSid: {message.sid}")
                
                # SMS 전송 기록 저장 (메모리)
                transfer_logs[call_sid] = {
                    "transferred": False,
                    "sms_sent": True,
                    "to_number": caller_number,
                    "message_sid": message.sid,
                    "timestamp": datetime.now().isoformat(),
                    "incident_id": incident_id,
                    "action": "sms_send"
                }
                print(f"[SMS] Log saved for CallSid: {call_sid}")
                
                # DB에 DTMF 입력 기록 저장 및 Incident 상태 업데이트
                if incident_id:
                    try:
                        with get_session() as session:
                            from app.db import log_call_attempt, get_incident
                            
                            # CallAttempt 기록
                            log_call_attempt(
                                session=session,
                                incident_id=incident_id,
                                callee=caller_number,
                                provider="twilio",
                                result="ack",  # SMS 전송 = 승인으로 처리
                                dtmf="2"
                            )
                            print(f"[SMS] DB에 DTMF=2 기록 저장 완료")
                            
                            # Incident 상태를 "ack"로 변경
                            inc = get_incident(session, incident_id)
                            if inc and inc.status != "ack":
                                inc.status = "ack"
                                inc.acknowledged_at = datetime.utcnow()
                                session.add(inc)
                                session.commit()
                                print(f"[SMS] Incident #{incident_id} 상태를 'ack'로 변경 완료")
                    except Exception as e:
                        print(f"[SMS] DB 저장 실패: {e}")
            except Exception as e:
                import traceback
                print(f"[SMS] ❌ Exception occurred: {e}")
                print(f"[SMS] Full traceback:")
                print(traceback.format_exc())
                sms_sent = False
        
        print(f"[SMS] Final sms_sent status: {sms_sent}")
        
        # TwiML 응답
        if sms_sent:
            twiml = """<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">장애 메시지가 문자로 전송되었습니다.</prosody></Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""
        else:
            twiml = """<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">문자 전송에 실패했습니다. 감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""
    
    else:
        print(f"[TRANSFER] No valid digit received, ending call")
        # 1번, 2번 외의 입력 또는 타임아웃
        twiml = """<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""
    
    print(f"[TRANSFER] Returning TwiML: {twiml[:100]}...")
    return Response(content=twiml.strip(), media_type="application/xml")


@router.post("/status")
async def twilio_status(request: Request, incident_id: int) -> dict:
    """Handle Twilio status callbacks for call events"""
    from app.services.escalation import acknowledge_incident, retry_next
    
    form = await request.form()
    call_status = form.get("CallStatus")
    call_sid = form.get("CallSid")
    
    # Log the call status for monitoring
    print(f"Twilio Status - Incident: {incident_id}, CallSid: {call_sid}, Status: {call_status}")
    
    # If call is answered, automatically acknowledge the incident
    if call_status == "answered":
        acknowledge_incident(incident_id, dtmf=None)
        print(f"Incident {incident_id} automatically acknowledged (call answered)")
    
    # If call completed but not answered, try next person
    elif call_status == "completed":
        with get_session() as session:
            incident = get_incident(session, incident_id)
            if incident and incident.status != "ack":
                print(f"Call completed but not answered - trying next person")
                tts_text = incident.tts_text
                retry_result = retry_next(incident_id, tts_text)
                print(f"Retry result: {retry_result}")
    
    # Store call status in database for audit trail
    with get_session() as session:
        from app.db import log_call_attempt
        log_call_attempt(
            session,
            incident_id=incident_id,
            callee="callback",
            provider=settings.voice_provider,
            result=call_status or "unknown",
        )
    
    return {"ok": True, "incident_id": incident_id, "call_status": call_status, "call_sid": call_sid}


@router.post("/sms")
async def send_sms(request: Request) -> dict:
    """Send SMS message for testing"""
    form = await request.form()
    to_number = form.get("to_number")
    message = form.get("message")
    
    provider = TwilioProvider()
    try:
        message_sid = provider.send_sms(to_number=to_number, message=message)
        return {
            "ok": True, 
            "message_sid": message_sid, 
            "to": to_number, 
            "message": message
        }
    except Exception as e:
        return {
            "ok": False, 
            "error": str(e), 
            "to": to_number, 
            "message": message
        }



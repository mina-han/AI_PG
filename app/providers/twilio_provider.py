from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Response, Form, Request
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
    Digits: Optional[str] = Form(None), 
    incident_id: Optional[int] = None
) -> Response:
    """
    호전환 처리 (콜드 방식)
    1번 누르면 상황근무자 번호로 바로 연결
    """
    # Twilio에서 전달하는 CallSid 받기
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    
    # 디버깅 로그
    print(f"[TRANSFER] Received Digits: {Digits}, CallSid: {call_sid}, incident_id: {incident_id}")
    
    # 상황근무자 번호 (010-8672-1718 -> +821086721718)
    situation_room_number = "+821086721718"
    
    if Digits == "1":
        print(f"[TRANSFER] Attempting to dial {situation_room_number}")
        
        # 호전환 기록 저장
        transfer_logs[call_sid] = {
            "transferred": True,
            "to_number": situation_room_number,
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident_id
        }
        print(f"[TRANSFER] Saved transfer log for CallSid: {call_sid}")
        
        # 콜드 방식 호전환: 바로 상황근무자에게 연결
        twiml = f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">상황근무자에게 연결합니다.</prosody></Say>
  <Dial timeout="30">
    <Number>{situation_room_number}</Number>
  </Dial>
  <Say language="ko-KR" voice="Polly.Seoyeon"><prosody rate="100%">연결이 종료되었습니다. 감사합니다.</prosody></Say>
  <Hangup/>
</Response>"""
    else:
        print(f"[TRANSFER] No valid digit received, ending call")
        # 1번 외의 입력 또는 타임아웃
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



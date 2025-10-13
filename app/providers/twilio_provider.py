from fastapi import APIRouter, Response, Form, Request
from twilio.rest import Client

from app.config import settings
from app.providers.base import VoiceProvider
from app.db import get_session, get_incident


class TwilioProvider(VoiceProvider):
    def __init__(self) -> None:
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        # TwiML URL for gather
        twiml_url = f"{webhook_base}/twilio/voice?incident_id={incident_id}"
        call = self.client.calls.create(
            url=twiml_url,
            to=to_number,
            from_=settings.twilio_from_number,
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
def twilio_voice(incident_id: int, text: str | None = None) -> Response:
    # Twilio fetches TwiML; send a Gather for DTMF '1'
    if text:
        speak_text = text
    else:
        with get_session() as session:
            inc = get_incident(session, incident_id)
            speak_text = (
                inc.tts_text if inc else "Emergency alert. Please press 1 to confirm."
            )
    twiml = f"""
<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Gather input="dtmf" numDigits="1" action="/twilio/gather?incident_id={incident_id}" method="POST" timeout="20">
    <Say language="en-US">{speak_text}</Say>
  </Gather>
  <Say language="en-US">No input received. Ending call.</Say>
  <Hangup/>
</Response>
""".strip()
    return Response(content=twiml, media_type="application/xml")


@router.post("/gather")
def twilio_gather(incident_id: int, Digits: str | None = Form(None)) -> Response:  # Twilio posts Digits
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


@router.post("/status")
async def twilio_status(request: Request, incident_id: int) -> dict:
    """Handle Twilio status callbacks for call events"""
    form = await request.form()
    call_status = form.get("CallStatus")
    call_sid = form.get("CallSid")
    
    # Log the call status for monitoring
    print(f"Twilio Status - Incident: {incident_id}, CallSid: {call_sid}, Status: {call_status}")
    
    # TODO: Store call status in database for audit trail
    # with get_session() as session:
    #     # Update CallAttempt record with status
    #     pass
    
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



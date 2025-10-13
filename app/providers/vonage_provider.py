from fastapi import APIRouter, Response, Request
import vonage

from app.config import settings
from app.providers.base import VoiceProvider


class VonageProvider(VoiceProvider):
    def __init__(self) -> None:
        self.client = vonage.Client(key=settings.vonage_api_key, secret=settings.vonage_api_secret)
        self.voice = vonage.Voice(self.client)

    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        ncco = [
            {"action": "talk", "text": tts_text, "language": "ko-KR"},
            {
                "action": "input",
                "type": ["dtmf"],
                "dtmf": {"timeOut": 5, "maxDigits": 1, "submitOnHash": False},
                "eventUrl": [f"{webhook_base}/vonage/gather?incident_id={incident_id}"],
            },
            {"action": "talk", "text": "입력이 없어 통화를 종료합니다.", "language": "ko-KR"},
        ]
        resp = self.voice.create_call(
            {
                "to": [{"type": "phone", "number": to_number}],
                "from": {"type": "phone", "number": settings.vonage_from_number},
                "ncco": ncco,
                "event_url": [f"{webhook_base}/vonage/status?incident_id={incident_id}"],
            }
        )
        return resp.get("uuid", "")

    def webhook_path(self) -> str:
        return "/vonage"


router = APIRouter(prefix="/vonage", tags=["vonage"])


@router.post("/gather")
async def vonage_gather(request: Request, incident_id: int):
    """Handle Vonage DTMF input callbacks"""
    from app.services.escalation import acknowledge_incident, retry_next
    
    body = await request.json()
    dtmf = None
    if isinstance(body, dict):
        dtmf = body.get("dtmf") or body.get("payload", {}).get("dtmf") if isinstance(body.get("payload"), dict) else body.get("dtmf")
    
    print(f"Vonage DTMF - Incident: {incident_id}, DTMF: {dtmf}")
    
    if dtmf == "1":
        acknowledge_incident(incident_id, dtmf="1")
        # Return NCCO to confirm acknowledgment
        return [
            {"action": "talk", "text": "승인 입력을 확인했습니다. 감사합니다.", "language": "ko-KR"}
        ]
    else:
        # Retry next callee
        from app.db import get_session, get_incident
        with get_session() as session:
            incident = get_incident(session, incident_id)
            text = incident.tts_text if incident else "알림입니다."
        retry_next(incident_id, text)
        return [
            {"action": "talk", "text": "유효하지 않은 입력입니다. 통화를 종료합니다.", "language": "ko-KR"}
        ]


@router.post("/status")
async def vonage_status(request: Request, incident_id: int) -> dict:
    """Handle Vonage status callbacks for call events"""
    body = await request.json()
    status = body.get("status") if isinstance(body, dict) else None
    uuid = body.get("uuid") if isinstance(body, dict) else None
    
    # Log the call status for monitoring
    print(f"Vonage Status - Incident: {incident_id}, UUID: {uuid}, Status: {status}")
    
    # TODO: Store call status in database for audit trail
    # with get_session() as session:
    #     # Update CallAttempt record with status
    #     pass
    
    return {"ok": True, "incident_id": incident_id, "call_status": status, "call_uuid": uuid}



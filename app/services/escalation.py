from typing import Tuple, Optional

from app.config import settings
from app.db import (
    get_session,
    create_incident,
    increment_attempt,
    log_call_attempt,
    mark_acknowledged,
    get_incident,
)
from app.providers.twilio_provider import TwilioProvider
from app.providers.vonage_provider import VonageProvider
from app.providers.solapi_provider import SolapiProvider


def _get_provider():
    from app.providers.base import VoiceProvider

    class MockProvider(VoiceProvider):
        def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
            print(f"모의 전화 발신 대상: {to_number}")
            print(f"TTS 메시지: {tts_text}")
            print(f"웹훅 URL: {webhook_base}/twilio/voice?incident_id={incident_id}")
            print(f"전화 발신 완료! (실제로는 Mock)")
            return f"mock_call_{incident_id}"

        def webhook_path(self) -> str:
            return "/mock"

    if settings.voice_provider == "mock":
        return MockProvider()
    elif settings.voice_provider == "twilio":
        try:
            return TwilioProvider()
        except Exception as e:
            print(f"Twilio initialization failed: {e}, using MockProvider")
            return MockProvider()
    elif settings.voice_provider == "solapi":
        try:
            return SolapiProvider()
        except Exception as e:
            print(f"SOLAPI initialization failed: {e}, using MockProvider")
            return MockProvider()
    else:
        try:
            return VonageProvider()
        except Exception as e:
            print(f"Vonage initialization failed: {e}, using MockProvider")
            return MockProvider()


def _next_callee(attempts: int) -> Tuple[str, str]:
    # Even attempts -> primary first call, odd -> secondary
    if attempts % 2 == 0:
        return settings.primary_contact, "primary"
    return settings.secondary_contact, "secondary"


def start_escalation(summary: str, tts_text: str) -> dict:
    with get_session() as session:
        incident = create_incident(session, summary, tts_text)
        provider = _get_provider()
        callee, role = _next_callee(incident.attempts)
        increment_attempt(session, incident.id)
        call_id = provider.place_call(
            to_number=callee,
            tts_text=tts_text,
            webhook_base=settings.public_base_url,
            incident_id=incident.id,
        )
        log_call_attempt(
            session,
            incident_id=incident.id,
            callee=callee,
            provider=settings.voice_provider,
            result="initiated",
        )
        return {"incident_id": incident.id, "call_id": call_id, "to": callee, "role": role}


def acknowledge_incident(incident_id: int, dtmf: Optional[str] = None) -> None:
    with get_session() as session:
        if get_incident(session, incident_id) is None:
            return
        mark_acknowledged(session, incident_id)
        log_call_attempt(
            session,
            incident_id=incident_id,
            callee="unknown",
            provider=settings.voice_provider,
            result="ack",
            dtmf=dtmf,
        )


def retry_next(incident_id: int, tts_text: str) -> dict:
    with get_session() as session:
        incident = get_incident(session, incident_id)
        if incident is None:
            return {"error": "incident_not_found"}
        if incident.attempts >= settings.max_attempts:
            return {"status": "max_attempts_reached"}
        provider = _get_provider()
        callee, role = _next_callee(incident.attempts)
        increment_attempt(session, incident.id)
        call_id = provider.place_call(
            to_number=callee,
            tts_text=tts_text,
            webhook_base=settings.public_base_url,
            incident_id=incident.id,
        )
        log_call_attempt(
            session,
            incident_id=incident.id,
            callee=callee,
            provider=settings.voice_provider,
            result="initiated",
        )
        return {"incident_id": incident.id, "call_id": call_id, "to": callee, "role": role}
from fastapi.testclient import TestClient

from app.main import app
from app.services import escalation


class DummyProvider:
    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        return "dummy-call-id"

    def webhook_path(self) -> str:
        return "/dummy"


client = TestClient(app)


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


def test_start_and_ack_flow(monkeypatch):
    monkeypatch.setattr(escalation, "_get_provider", lambda: DummyProvider())

    # Start escalation -> creates incident and logs attempt
    start = client.post(
        "/webhook/start",
        json={
            "incident_summary": "서버 A CPU 95%",
            "tts_text": "긴급 알림입니다. 확인 후 1번을 눌러 승인해주세요.",
        },
    )
    assert start.status_code == 200
    data = start.json()
    incident_id = data["incident_id"]
    assert incident_id > 0

    # Simulate Twilio DTMF '1' gather -> acknowledge
    ack = client.post(f"/twilio/gather?incident_id={incident_id}", data={"Digits": "1"})
    assert ack.status_code == 200
    assert "application/xml" in ack.headers.get("content-type", "")

    # Verify incident is acknowledged
    status = client.get(f"/webhook/incident/{incident_id}")
    assert status.status_code == 200
    assert status.json().get("status") == "ack"


def test_twilio_voice_returns_twiml(monkeypatch):
    monkeypatch.setattr(escalation, "_get_provider", lambda: DummyProvider())

    # Create an incident to reference
    start = client.post(
        "/webhook/start",
        json={
            "incident_summary": "서버 B 메모리 경고",
            "tts_text": "메모리 사용량 경고. 1번을 눌러 승인.",
        },
    )
    incident_id = start.json()["incident_id"]

    # Twilio will fetch TwiML; our endpoint is GET as per Twilio requirements
    twiml = client.get(f"/twilio/voice?incident_id={incident_id}")
    assert twiml.status_code == 200
    assert "application/xml" in twiml.headers.get("content-type", "")


from fastapi import APIRouter, HTTPException

from app.models import StartEscalationRequest
from app.services.escalation import start_escalation, acknowledge_incident, retry_next
from app.db import get_session, get_incident

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.post("/start")
def webhook_start(payload: StartEscalationRequest) -> dict:
    # 에스컬레이션 시작
    result = start_escalation(payload.incident_summary, payload.tts_text)
    return result

@router.post("/ack/{incident_id}")
def webhook_ack(incident_id: int) -> dict:
    acknowledge_incident(incident_id, dtmf="1")
    return {"ok": True}

@router.post("/retry/{incident_id}")
def webhook_retry(incident_id: int, payload: StartEscalationRequest) -> dict:
    return retry_next(incident_id, payload.tts_text)

@router.get("/incident/{incident_id}")
def webhook_incident(incident_id: int) -> dict:
    with get_session() as session:
        inc = get_incident(session, incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="not found")
        return {
            "id": inc.id,
            "summary": inc.summary,
            "tts_text": inc.tts_text,
            "status": inc.status,
            "attempts": inc.attempts,
            "acknowledged_at": str(inc.acknowledged_at) if inc.acknowledged_at else None,
        }
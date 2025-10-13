from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    summary: str
    tts_text: str
    status: str = Field(default="new")  # new|ack|closed
    attempts: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None


class CallAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int
    callee: str
    provider: str
    result: str  # initiated|answered|no_answer|failed|ack
    dtmf: Optional[str] = None
    duration_sec: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


engine = create_engine("sqlite:///./orchestrator.db")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)


def create_incident(session: Session, summary: str, tts_text: str) -> Incident:
    incident = Incident(summary=summary, tts_text=tts_text)
    session.add(incident)
    session.commit()
    session.refresh(incident)
    return incident


def get_incident(session: Session, incident_id: int) -> Optional[Incident]:
    return session.get(Incident, incident_id)


def increment_attempt(session: Session, incident_id: int) -> None:
    incident = session.get(Incident, incident_id)
    if incident is None:
        return
    incident.attempts += 1
    session.add(incident)
    session.commit()


def mark_acknowledged(session: Session, incident_id: int) -> None:
    incident = session.get(Incident, incident_id)
    if incident is None:
        return
    incident.status = "ack"
    incident.acknowledged_at = datetime.utcnow()
    session.add(incident)
    session.commit()


def log_call_attempt(
    session: Session,
    incident_id: int,
    callee: str,
    provider: str,
    result: str,
    dtmf: Optional[str] = None,
    duration_sec: Optional[int] = None,
) -> CallAttempt:
    entry = CallAttempt(
        incident_id=incident_id,
        callee=callee,
        provider=provider,
        result=result,
        dtmf=dtmf,
        duration_sec=duration_sec,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry



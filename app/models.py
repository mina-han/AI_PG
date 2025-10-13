from enum import Enum
from pydantic import BaseModel


class StartEscalationRequest(BaseModel):
    incident_summary: str
    tts_text: str


class Provider(str, Enum):
    twilio = "twilio"
    vonage = "vonage"



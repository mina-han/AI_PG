import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv


load_dotenv()


def getenv(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Invalid int for {name}: {value}") from exc


@dataclass
class Settings:
    app_host: str = getenv("APP_HOST", "0.0.0.0")
    app_port: int = getenv_int("APP_PORT", 8000)

    voice_provider: Literal["twilio", "vonage", "solapi", "mock"] = getenv("VOICE_PROVIDER", "mock")  # type: ignore[assignment]

    public_base_url: str = getenv("PUBLIC_BASE_URL", "http://localhost:8000")

    primary_contact: str = getenv("PRIMARY_CONTACT", "+821098942273")
    secondary_contact: str = getenv("SECONDARY_CONTACT", "+821098942273")

    call_timeout_seconds: int = getenv_int("CALL_TIMEOUT_SECONDS", 40)
    max_attempts: int = getenv_int("MAX_ATTEMPTS", 12)

    # Twilio
    twilio_account_sid: str = getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    twilio_auth_token: str = getenv("TWILIO_AUTH_TOKEN", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    twilio_from_number: str = getenv("TWILIO_FROM_NUMBER", "+821098942273")

    # Vonage
    vonage_api_key: str = getenv("VONAGE_API_KEY", "dummy")
    vonage_api_secret: str = getenv("VONAGE_API_SECRET", "dummy")
    vonage_from_number: str = getenv("VONAGE_FROM_NUMBER", "14155550100")

    # SOLAPI
    solapi_api_key: str = getenv("SOLAPI_API_KEY", "dummy")
    solapi_api_secret: str = getenv("SOLAPI_API_SECRET", "dummy")
    solapi_from_number: str = getenv("SOLAPI_FROM_NUMBER", "01098942273")  # SOLAPI에 등록된 발신번호


settings = Settings()




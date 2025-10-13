from fastapi import FastAPI

from app.config import settings
from app.db import init_db
from app.routers.health import router as health_router
from app.routers.webhook import router as webhook_router
from app.providers.twilio_provider import router as twilio_router
from app.providers.vonage_provider import router as vonage_router
from app.providers.solapi_provider import router as solapi_router


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="Call Orchestrator", version="0.1.0")
    app.include_router(health_router)
    app.include_router(webhook_router)
    app.include_router(twilio_router)
    app.include_router(vonage_router)
    app.include_router(solapi_router)
    return app


app = create_app()






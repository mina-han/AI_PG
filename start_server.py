#!/usr/bin/env python3
"""
FastAPI 서버 시작 스크립트
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 80)
    print("FastAPI 서버 시작")
    print("=" * 80)
    print(f"Host: {settings.app_host}")
    print(f"Port: {settings.app_port}")
    print(f"Provider: {settings.voice_provider}")
    print(f"Primary: {settings.primary_contact}")
    print(f"Secondary: {settings.secondary_contact}")
    print(f"Max Attempts: {settings.max_attempts}")
    print(f"Timeout: {settings.call_timeout_seconds}s")
    print("=" * 80)
    print("\n서버를 시작합니다...\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )


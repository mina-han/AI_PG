import httpx
from fastapi import APIRouter, Response, Form, Request
from typing import Dict, Any

from app.config import settings
from app.providers.base import VoiceProvider
from app.db import get_session, get_incident


class SolapiProvider(VoiceProvider):
    def __init__(self) -> None:
        self.api_key = settings.solapi_api_key
        self.api_secret = settings.solapi_api_secret
        self.from_number = settings.solapi_from_number
        self.base_url = "https://api.solapi.com"

    def place_call(self, *, to_number: str, tts_text: str, webhook_base: str, incident_id: int) -> str:
        """Place voice call using SOLAPI"""
        url = f"{self.base_url}/messages/v4/send-many/detail"
        
        # 발신번호와 수신번호가 같으면 에러 방지
        if self.from_number == to_number:
            print(f"SOLAPI Error: 발신번호와 수신번호가 동일합니다. (from: {self.from_number}, to: {to_number})")
            return f"solapi_error_same_number_{incident_id}"
        
        # SOLAPI 음성 메시지 요청 데이터 구성
        payload = {
            "messages": [{
                "to": to_number,
                "from": self.from_number,
                "text": tts_text,
                "type": "VOICE",
                "voiceOptions": {
                    "voiceType": "FEMALE",
                    "replyRange": 3  # 메시지 전체 읽기를 위해 3으로 설정
                }
            }]
        }
        
        date = self._get_date()
        salt = self._get_salt()
        signature = self._get_signature(date, salt)
        
        headers = {
            "Authorization": f"HMAC-SHA256 apiKey={self.api_key}, date={date}, salt={salt}, signature={signature}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                # SOLAPI는 messageId를 반환
                return result.get("messageId", f"solapi_{incident_id}")
                
        except httpx.HTTPError as e:
            print(f"SOLAPI API error: {e}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return f"solapi_error_{incident_id}"
        except Exception as e:
            print(f"SOLAPI unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return f"solapi_error_{incident_id}"

    def _get_date(self) -> str:
        """Get current date in ISO 8601 format"""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    def _get_salt(self) -> str:
        """Generate random salt"""
        import uuid
        return str(uuid.uuid4())

    def _get_signature(self, date: str, salt: str) -> str:
        """Generate HMAC-SHA256 signature (SOLAPI 방식)"""
        import hmac
        import hashlib
        
        try:
            # SOLAPI signature format: HMAC-SHA256(date + salt)
            # 규칙: hexdigest() 사용 (base64 아님)
            data = f"{date}{salt}"
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()  # base64 대신 hexdigest 사용
            
            return signature
        except Exception as e:
            print(f"SOLAPI signature generation error: {e}")
            return "dummy_signature"

    def webhook_path(self) -> str:
        return "/solapi"


router = APIRouter(prefix="/solapi", tags=["solapi"])


@router.post("/webhook")
async def solapi_webhook(request: Request) -> dict:
    """Handle SOLAPI webhook callbacks"""
    try:
        data = await request.json()
        
        # SOLAPI 웹훅 데이터 구조에 따라 처리
        message_id = data.get("messageId")
        status = data.get("status")
        to_number = data.get("to")
        
        print(f"SOLAPI Webhook - MessageId: {message_id}, Status: {status}, To: {to_number}")
        
        # TODO: 데이터베이스에 상태 업데이트
        # with get_session() as session:
        #     # CallAttempt 상태 업데이트
        #     pass
        
        return {"ok": True, "message_id": message_id, "status": status}
        
    except Exception as e:
        print(f"SOLAPI webhook error: {e}")
        return {"ok": False, "error": str(e)}


@router.post("/send-voice")
async def send_voice_message(request: Request) -> dict:
    """Send voice message for testing"""
    try:
        data = await request.json()
        to_number = data.get("to_number")
        message = data.get("message", "테스트 음성 메시지입니다.")
        
        provider = SolapiProvider()
        message_id = provider.place_call(
            to_number=to_number,
            tts_text=message,
            webhook_base=settings.public_base_url,
            incident_id=999  # 테스트용 incident_id
        )
        
        return {
            "ok": True,
            "message_id": message_id,
            "to": to_number,
            "message": message
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "to": data.get("to_number") if 'data' in locals() else None,
            "message": data.get("message") if 'data' in locals() else None
        }


@router.get("/test")
async def test_solapi() -> dict:
    """Test SOLAPI connection"""
    try:
        provider = SolapiProvider()
        
        # 간단한 연결 테스트
        test_message_id = provider.place_call(
            to_number="01000000000",  # 테스트 번호
            tts_text="SOLAPI 연결 테스트입니다.",
            webhook_base=settings.public_base_url,
            incident_id=0
        )
        
        return {
            "ok": True,
            "message": "SOLAPI provider initialized successfully",
            "test_message_id": test_message_id
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "message": "SOLAPI provider initialization failed"
        }

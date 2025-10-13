#!/usr/bin/env python3
"""
SOLAPI 음성 메시지 테스트 스크립트
"""

import os
import sys
import json
import requests
from datetime import datetime

# SOLAPI 설정 (실제 값으로 교체하세요)
SOLAPI_API_KEY = "NCS6P2VW8NH44ZNI"
SOLAPI_API_SECRET = "EMAMDFGPTPMH3SQI37ZIBTZVGQQLRBN3"
SOLAPI_FROM_NUMBER = "0200000000"  # SOLAPI에서 등록된 발신번호

# 테스트 대상 번호
TEST_TO_NUMBER = "01000000000"  # 실제 테스트할 번호로 교체

def get_auth_header():
    """SOLAPI 인증 헤더 생성"""
    import hmac
    import hashlib
    import base64
    import uuid
    from datetime import datetime
    
    # 현재 시간 (UTC) 가져오기
    date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 랜덤 salt 생성
    salt = str(uuid.uuid4())
    
    # 시그니처 생성 (SOLAPI 방식: HMAC-SHA256(apiSecret + date + salt))
    def make_signature(api_secret, date, salt):
        data = f"{api_secret}{date}{salt}"
        signature = hmac.new(api_secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    signature = make_signature(SOLAPI_API_SECRET, date, salt)
    
    return {
        "Authorization": f"HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}",
        "Content-Type": "application/json"
    }

def send_voice_message(to_number: str, message: str):
    """SOLAPI로 음성 메시지 발송"""
    url = "https://api.solapi.com/messages/v4/send-many/detail"
    
    payload = {
        "messages": [{
            "to": to_number,
            "from": SOLAPI_FROM_NUMBER,
            "text": message,
            "type": "VOICE",
            "voiceOptions": {
                "voiceType": "FEMALE",
                "headerMessage": "안녕하세요. 긴급 알림입니다.",
                "tailMessage": "감사합니다. 좋은 하루 되세요.",
                "replyRange": 1
            }
        }]
    }
    
    headers = get_auth_header()
    
    try:
        print(f"음성 메시지 발송 중...")
        print(f"대상: {to_number}")
        print(f"메시지: {message}")
        print(f"발신번호: {SOLAPI_FROM_NUMBER}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print(f"[SUCCESS] 발송 성공!")
        print(f"Message ID: {result.get('messageId')}")
        print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP 오류: {e}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        return None

def test_solapi_connection():
    """SOLAPI 연결 테스트"""
    print("=== SOLAPI 연결 테스트 ===")
    
    if SOLAPI_API_KEY == "your_solapi_api_key_here":
        print("[ERROR] SOLAPI_API_KEY를 실제 값으로 설정하세요")
        return False
    
    if SOLAPI_API_SECRET == "your_solapi_api_secret_here":
        print("[ERROR] SOLAPI_API_SECRET을 실제 값으로 설정하세요")
        return False
    
    print("[OK] API 키 설정 확인됨")
    return True

def main():
    """메인 함수"""
    print("SOLAPI 음성 메시지 테스트")
    print("=" * 50)
    
    # 연결 테스트
    if not test_solapi_connection():
        print("\n설정을 확인하고 다시 시도하세요.")
        return
    
    # 음성 메시지 발송 테스트
    test_message = "안녕하세요. SOLAPI 음성 메시지 테스트입니다. 1번을 누르시면 확인됩니다."
    
    print(f"\n=== 음성 메시지 발송 테스트 ===")
    result = send_voice_message(TEST_TO_NUMBER, test_message)
    
    if result:
        print(f"\n[SUCCESS] 테스트 완료!")
        print(f"전화가 곧 발신됩니다.")
    else:
        print(f"\n[ERROR] 테스트 실패")

if __name__ == "__main__":
    main()

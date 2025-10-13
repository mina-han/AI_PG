#!/usr/bin/env python3
"""
SOLAPI REST API 직접 호출 테스트
"""

import requests
import json
import hmac
import hashlib
import base64
import time

# SOLAPI 설정
API_KEY = 'NCS6P2VW8NH44ZNI'
API_SECRET = 'EMAMDFGPTPMH3SQI37ZIBTZVGQQLRBN3'

def create_auth_header():
    """SOLAPI 인증 헤더 생성"""
    from datetime import datetime
    
    # 현재 시간 (ISO 8601 형식)
    date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 고유 salt 생성
    salt = 'unique_salt_value'
    
    # 시그니처 생성: HMAC-SHA256(date + salt)
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        (date + salt).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "Authorization": f"HMAC-SHA256 apiKey={API_KEY}, date={date}, salt={salt}, signature={signature}",
        "Content-Type": "application/json"
    }

def send_voice_message():
    """SOLAPI REST API로 음성 메시지 발송"""
    
    url = "https://api.solapi.com/messages/v4/send-many/detail"
    
    # 음성 메시지 페이로드
    payload = {
        "messages": [{
            "to": "01086721718",  # 수신번호
            "from": "01098942273",  # 발신번호 (고정)
            "text": "안녕하세요. SOLAPI 음성 메시지 테스트입니다. 1번을 누르시면 확인됩니다.",
            "type": "VOICE",
            "voiceOptions": {
                "voiceType": "FEMALE",
                "replyRange": 3  # 메시지 전체 읽기를 위해 3으로 설정 (1은 너무 빨리 짤림)
            }
        }]
    }
    
    headers = create_auth_header()
    
    try:
        print("=== SOLAPI REST API 음성 메시지 발송 ===")
        print(f"발신번호: {payload['messages'][0]['from']}")
        print(f"수신번호: {payload['messages'][0]['to']}")
        print(f"메시지: {payload['messages'][0]['text']}")
        print("음성 메시지 발송 중...")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] 발송 성공!")
            print(f"Message ID: {result.get('messageId')}")
            return result
        else:
            print(f"[ERROR] 발송 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        return None

if __name__ == "__main__":
    send_voice_message()

#!/usr/bin/env python3
"""
SOLAPI 간단 테스트 스크립트
"""

import requests
import json

def test_solapi_endpoints():
    """SOLAPI 엔드포인트 테스트"""
    base_url = "http://localhost:8000"
    
    print("=== SOLAPI 엔드포인트 테스트 ===")
    
    # 1. SOLAPI 테스트 엔드포인트
    print("\n1. SOLAPI 테스트 엔드포인트:")
    try:
        response = requests.get(f"{base_url}/solapi/test")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. 음성 메시지 발송 테스트
    print("\n2. 음성 메시지 발송 테스트:")
    try:
        payload = {
            "to_number": "01000000000",
            "message": "SOLAPI 테스트 음성 메시지입니다."
        }
        response = requests.post(
            f"{base_url}/solapi/send-voice",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. 긴급 알림 시스템 테스트 (Mock 모드)
    print("\n3. 긴급 알림 시스템 테스트:")
    try:
        payload = {
            "incident_summary": "SOLAPI 테스트 알림",
            "tts_text": "안녕하세요. SOLAPI 테스트 음성 메시지입니다."
        }
        response = requests.post(
            f"{base_url}/webhook/start",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_solapi_endpoints()

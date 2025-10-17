#!/usr/bin/env python3
"""
Twilio 크리티컬 메시지 음성 전화 테스트
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# 환경 변수 로드
load_dotenv()

# Twilio 설정
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# 테스트 수신 번호
TO_NUMBER = '+821098942273'

# 크리티컬 메시지
CRITICAL_MESSAGE = "크리티컬 메시지가 발생되었습니다. danidb1p pmon down. 담당자 확인 부탁드립니다."

def send_critical_call():
    """크리티컬 메시지 음성 전화 발신"""
    
    try:
        print("=" * 80)
        print("Twilio 크리티컬 메시지 음성 전화 발신")
        print("=" * 80)
        print(f"발신번호: {FROM_NUMBER}")
        print(f"수신번호: {TO_NUMBER}")
        print(f"메시지: {CRITICAL_MESSAGE}")
        print("-" * 80)
        
        # Twilio 클라이언트 생성
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        
        # TwiML 음성 메시지 생성
        twiml_message = f"""
        <Response>
            <Say language="ko-KR" voice="Polly.Seoyeon">
                {CRITICAL_MESSAGE}
            </Say>
            <Pause length="1"/>
            <Say language="ko-KR" voice="Polly.Seoyeon">
                메시지를 확인하셨으면 1번을 눌러주세요.
                다시 듣기를 원하시면 9번을 눌러주세요.
            </Say>
            <Gather input="dtmf" numDigits="1" timeout="10" action="/webhook/dtmf">
                <Say language="ko-KR" voice="Polly.Seoyeon">
                    번호를 입력해주세요.
                </Say>
            </Gather>
            <Say language="ko-KR" voice="Polly.Seoyeon">
                입력이 없어 전화를 종료합니다. 다시 전화드리겠습니다.
            </Say>
        </Response>
        """
        
        print(f"음성 전화 발신 중...")
        
        # 전화 발신
        call = client.calls.create(
            to=TO_NUMBER,
            from_=FROM_NUMBER,
            twiml=twiml_message,
            status_callback=f"http://localhost:8000/webhook/twilio-callback",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        print(f"[SUCCESS] 크리티컬 전화 발신 성공!")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        print(f"Direction: {call.direction}")
        print(f"To: {call.to}")
        print(f"From: {FROM_NUMBER}")
        print("=" * 80)
        print(f"\n수신자 전화기를 확인하세요: {TO_NUMBER}")
        print("\n전화가 연결되면 다음 메시지가 재생됩니다:")
        print(f'"{CRITICAL_MESSAGE}"')
        print("=" * 80)
        
        return call
        
    except Exception as e:
        print(f"[ERROR] 전화 발신 실패: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return None

def main():
    """메인 함수"""
    
    print("\n크리티컬 메시지 음성 전화를 발신합니다...\n")
    
    result = send_critical_call()
    
    if result:
        print("\n[SUCCESS] 전화 발신 완료!")
        print("통화 내역은 Twilio 콘솔에서 확인 가능합니다:")
        print("https://console.twilio.com/us1/monitor/logs/calls")
    else:
        print("\n[ERROR] 전화 발신 실패!")

if __name__ == "__main__":
    main()


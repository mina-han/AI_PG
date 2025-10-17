#!/usr/bin/env python3
"""
Twilio 음성 전화 테스트 스크립트
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

# 테스트 수신 번호들
TEST_NUMBERS = [
    '+821098942273',
    '+821031289491', 
    '+821045741344'
]

def test_twilio_call(to_number: str):
    """Twilio 음성 전화 테스트"""
    
    try:
        print("=" * 60)
        print("Twilio 음성 전화 테스트")
        print("=" * 60)
        print(f"발신번호: {FROM_NUMBER}")
        print(f"수신번호: {to_number}")
        print(f"Account SID: {ACCOUNT_SID}")
        print("-" * 60)
        
        # Twilio 클라이언트 생성
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        
        # TwiML 음성 메시지 생성
        twiml_message = """
        <Response>
            <Say language="ko-KR" voice="Polly.Seoyeon">
                안녕하세요. 긴급 알림 시스템 테스트입니다. 
                이 메시지를 확인하셨으면 1번을 눌러주세요. 
                다시 듣기를 원하시면 9번을 눌러주세요.
            </Say>
            <Gather input="dtmf" numDigits="1" timeout="10">
                <Say language="ko-KR" voice="Polly.Seoyeon">
                    번호를 입력해주세요.
                </Say>
            </Gather>
            <Say language="ko-KR" voice="Polly.Seoyeon">
                입력이 없어 전화를 종료합니다.
            </Say>
        </Response>
        """
        
        # 공개 URL (ngrok 또는 서버 URL 필요)
        # 테스트를 위해 TwiML Bins 사용 가능
        public_url = os.getenv('PUBLIC_BASE_URL', 'http://localhost:8000')
        
        print(f"음성 전화 발신 중...")
        
        # 전화 발신
        call = client.calls.create(
            to=to_number,
            from_=FROM_NUMBER,
            twiml=twiml_message,
            status_callback=f"{public_url}/webhook/twilio-callback",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        print(f"[SUCCESS] 전화 발신 성공!")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        print(f"Direction: {call.direction}")
        print("=" * 60)
        
        return call
        
    except Exception as e:
        print(f"[ERROR] 전화 발신 실패: {e}")
        print("=" * 60)
        return None

def check_twilio_credentials():
    """Twilio 인증 정보 확인"""
    print("\n=== Twilio 인증 정보 확인 ===")
    print(f"Account SID: {ACCOUNT_SID}")
    print(f"Auth Token: {'*' * 20 if AUTH_TOKEN else 'None'}")
    print(f"From Number: {FROM_NUMBER}")
    print("=" * 60)
    
    if not all([ACCOUNT_SID, AUTH_TOKEN, FROM_NUMBER]):
        print("[ERROR] Twilio 인증 정보가 완전하지 않습니다!")
        return False
    
    return True

def main():
    """메인 테스트 함수"""
    
    # 인증 정보 확인
    if not check_twilio_credentials():
        return
    
    # 첫 번째 수신번호로 테스트
    test_number = TEST_NUMBERS[0]
    
    print(f"\n첫 번째 수신번호 ({test_number})로 테스트를 시작합니다.")
    print("테스트 전화를 발신합니다...\n")
    
    result = test_twilio_call(test_number)
    
    if result:
        print("\n[SUCCESS] Twilio 음성 전화 테스트 성공!")
        print(f"\n수신자 ({test_number})의 전화기를 확인하세요.")
        print("\n다른 번호들도 테스트하려면 아래 명령을 실행하세요:")
        for i, num in enumerate(TEST_NUMBERS[1:], start=2):
            print(f"  {i}. {num}")
    else:
        print("\n[ERROR] Twilio 음성 전화 테스트 실패!")

if __name__ == "__main__":
    main()


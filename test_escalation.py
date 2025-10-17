#!/usr/bin/env python3
"""
전체 에스컬레이션 로직 테스트 스크립트

요구사항:
1. 메시지 알람 내용 2번 반복
2. DTMF 입력(1번 누르기) 제거
3. 정담당자 -> 부담당자 -> 정담당자 -> 부담당자 순서 (총 4번)
4. 15초 타임아웃
5. 한 명이라도 받으면 종료
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

# 담당자 정보
PRIMARY_CONTACT = os.getenv('PRIMARY_CONTACT', '+821098942273')
SECONDARY_CONTACT = os.getenv('SECONDARY_CONTACT', '+821020149672')
MAX_ATTEMPTS = int(os.getenv('MAX_ATTEMPTS', '4'))
CALL_TIMEOUT = int(os.getenv('CALL_TIMEOUT_SECONDS', '15'))

# 크리티컬 메시지
CRITICAL_MESSAGE = "크리티컬 메시지가 발생되었습니다. danidb1p pmon down. 담당자 확인 부탁드립니다."


def create_twiml_for_message(message: str) -> str:
    """메시지를 2번 반복하는 TwiML 생성"""
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">메시지 전달이 완료되었습니다. 감사합니다.</Say>
  <Hangup/>
</Response>"""


def test_escalation_sequence():
    """에스컬레이션 시퀀스 테스트"""
    
    print("=" * 80)
    print("전체 에스컬레이션 로직 테스트")
    print("=" * 80)
    print(f"발신번호: {FROM_NUMBER}")
    print(f"정담당자: {PRIMARY_CONTACT}")
    print(f"부담당자: {SECONDARY_CONTACT}")
    print(f"최대 시도: {MAX_ATTEMPTS}번")
    print(f"타임아웃: {CALL_TIMEOUT}초")
    print(f"메시지: {CRITICAL_MESSAGE}")
    print("=" * 80)
    
    # 에스컬레이션 순서
    escalation_order = []
    for attempt in range(MAX_ATTEMPTS):
        if attempt % 2 == 0:
            escalation_order.append(("정담당자", PRIMARY_CONTACT))
        else:
            escalation_order.append(("부담당자", SECONDARY_CONTACT))
    
    print("\n[에스컬레이션 순서]")
    for i, (role, number) in enumerate(escalation_order, 1):
        print(f"  {i}. {role} ({number})")
    
    print("\n" + "=" * 80)
    print("실제 전화 발신을 시작하시겠습니까?")
    print("이 테스트는 실제로 전화를 발신합니다!")
    print("=" * 80)
    
    # Twilio 클라이언트 생성
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    # TwiML 생성
    twiml = create_twiml_for_message(CRITICAL_MESSAGE)
    
    print("\n[TwiML 미리보기]")
    print(twiml)
    print("=" * 80)
    
    # 첫 번째 담당자에게 전화 발신
    first_role, first_number = escalation_order[0]
    
    print(f"\n[1차 시도] {first_role} ({first_number})에게 전화 발신 중...")
    
    try:
        call = client.calls.create(
            to=first_number,
            from_=FROM_NUMBER,
            twiml=twiml,
            timeout=CALL_TIMEOUT,
            status_callback="http://localhost:8000/twilio/status?incident_id=test",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        
        print(f"[SUCCESS] 전화 발신 성공!")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        print(f"To: {call.to}")
        print(f"Timeout: {CALL_TIMEOUT}초")
        print("=" * 80)
        
        print("\n[통화 내용]")
        print(f"1. {CRITICAL_MESSAGE}")
        print(f"2. (1초 휴식)")
        print(f"3. {CRITICAL_MESSAGE}")
        print(f"4. (1초 휴식)")
        print(f"5. 메시지 전달이 완료되었습니다. 감사합니다.")
        print("=" * 80)
        
        print("\n[주의사항]")
        print("- 전화를 받으면 자동으로 incident가 완료됩니다")
        print("- 전화를 받지 않으면 다음 담당자에게 자동으로 전화됩니다")
        print("- 최대 4번까지 시도합니다 (정-부-정-부)")
        print("- 각 시도마다 15초 타임아웃이 적용됩니다")
        print("=" * 80)
        
        print("\n[Twilio 콘솔]")
        print(f"통화 내역 확인: https://console.twilio.com/us1/monitor/logs/calls/{call.sid}")
        print("=" * 80)
        
        return call
        
    except Exception as e:
        print(f"[ERROR] 전화 발신 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_api_integration():
    """FastAPI와 통합 테스트"""
    import requests
    
    print("\n" + "=" * 80)
    print("FastAPI 서버 통합 테스트")
    print("=" * 80)
    print("서버가 http://localhost:8000 에서 실행 중이어야 합니다.")
    print("=" * 80)
    
    # 서버 헬스체크
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] FastAPI 서버 실행 중")
        else:
            print(f"[WARNING] 서버 응답 이상: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] 서버에 연결할 수 없습니다: {e}")
        print("서버를 먼저 실행하세요: uvicorn app.main:app --reload")
        return
    
    # Incident 생성 및 에스컬레이션 시작
    try:
        print("\n[Incident 생성 및 에스컬레이션 시작]")
        response = requests.post(
            "http://localhost:8000/webhook/start",
            json={
                "incident_summary": "danidb1p pmon down",
                "tts_text": CRITICAL_MESSAGE
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Incident 생성 완료")
            print(f"Incident ID: {result.get('incident_id')}")
            print(f"Call ID: {result.get('call_id')}")
            print(f"To: {result.get('to')}")
            print(f"Role: {result.get('role')}")
            print("=" * 80)
            
            print("\n[자동 에스컬레이션]")
            print("- 전화를 받지 않으면 자동으로 다음 담당자에게 전화됩니다")
            print("- FastAPI 서버가 자동으로 에스컬레이션을 처리합니다")
            print("=" * 80)
        else:
            print(f"[ERROR] Incident 생성 실패: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[ERROR] API 호출 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    
    print("\n" + "=" * 80)
    print("Twilio 에스컬레이션 시스템 테스트")
    print("=" * 80)
    print("\n테스트 옵션:")
    print("1. 단일 전화 발신 테스트 (Twilio 직접 호출)")
    print("2. FastAPI 서버 통합 테스트 (자동 에스컬레이션)")
    print("=" * 80)
    
    # 옵션 1: 단일 전화 테스트
    print("\n[옵션 1] 단일 전화 발신 테스트를 실행합니다...")
    test_escalation_sequence()
    
    print("\n\n[옵션 2] FastAPI 서버 통합 테스트")
    print("FastAPI 서버 통합 테스트를 실행하시겠습니까? (y/n): ", end="")
    # 자동으로 실행하지 않음 (서버가 실행 중이어야 함)
    print("(서버 실행 필요)")
    # test_api_integration()


if __name__ == "__main__":
    main()


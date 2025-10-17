#!/usr/bin/env python3
"""
전체 에스컬레이션 시뮬레이션 테스트
FastAPI 서버 없이 에스컬레이션 로직 테스트
"""

import os
import time
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


def get_call_status(client: Client, call_sid: str) -> dict:
    """통화 상태 확인"""
    try:
        call = client.calls(call_sid).fetch()
        return {
            "sid": call.sid,
            "status": call.status,
            "to": call.to,
            "duration": call.duration
        }
    except Exception as e:
        return {"error": str(e)}


def place_call_to(client: Client, to_number: str, message: str, attempt: int) -> str:
    """전화 발신"""
    twiml = create_twiml_for_message(message)
    
    print(f"\n[{attempt}차 시도] {to_number}에게 전화 발신 중...")
    
    try:
        call = client.calls.create(
            to=to_number,
            from_=FROM_NUMBER,
            twiml=twiml,
            timeout=CALL_TIMEOUT,
        )
        
        print(f"[SUCCESS] 전화 발신 완료!")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        print(f"To: {call.to}")
        
        return call.sid
        
    except Exception as e:
        print(f"[ERROR] 전화 발신 실패: {e}")
        return None


def wait_for_call_completion(client: Client, call_sid: str, timeout: int = 20) -> str:
    """전화 완료 대기"""
    print(f"\n전화 상태 확인 중 (최대 {timeout}초)...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status_info = get_call_status(client, call_sid)
        current_status = status_info.get("status")
        
        if current_status != last_status:
            print(f"  - Status: {current_status}")
            last_status = current_status
        
        # 전화가 완료되었는지 확인
        if current_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
            print(f"\n[통화 종료] Status: {current_status}")
            if status_info.get("duration"):
                print(f"Duration: {status_info.get('duration')}초")
            return current_status
        
        time.sleep(2)  # 2초마다 체크
    
    print(f"\n[TIMEOUT] {timeout}초 경과")
    return "timeout"


def test_full_escalation():
    """전체 에스컬레이션 시뮬레이션"""
    
    print("=" * 80)
    print("전체 에스컬레이션 시뮬레이션 테스트")
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
    print("실제 전화 발신을 시작합니다!")
    print("전화를 받으면 즉시 종료됩니다.")
    print("=" * 80)
    
    # Twilio 클라이언트
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    # 에스컬레이션 시작
    for attempt in range(MAX_ATTEMPTS):
        role, number = escalation_order[attempt]
        
        print(f"\n\n{'=' * 80}")
        print(f"[{attempt + 1}/{MAX_ATTEMPTS}차 시도] {role} ({number})")
        print("=" * 80)
        
        # 전화 발신
        call_sid = place_call_to(client, number, CRITICAL_MESSAGE, attempt + 1)
        
        if not call_sid:
            print("[ERROR] 전화 발신 실패, 다음 시도로 진행...")
            continue
        
        # 전화 완료 대기
        final_status = wait_for_call_completion(client, call_sid, timeout=CALL_TIMEOUT + 10)
        
        # 전화를 받았는지 확인
        # Twilio status: busy, no-answer는 안받은 것, completed는 받았을 수도 있음
        if final_status == "completed":
            # duration을 확인해서 실제로 통화가 이루어졌는지 확인
            status_info = get_call_status(client, call_sid)
            duration = status_info.get("duration")
            
            if duration and int(duration) > 0:
                print(f"\n[SUCCESS] {role}가 전화를 받았습니다! (통화시간: {duration}초)")
                print("에스컬레이션을 종료합니다.")
                print("=" * 80)
                return True
        
        # 전화를 안받았으면 다음 담당자로
        print(f"\n{role}가 전화를 받지 않았습니다.")
        
        if attempt < MAX_ATTEMPTS - 1:
            next_role, next_number = escalation_order[attempt + 1]
            print(f"다음: {next_role} ({next_number})로 전화를 시도합니다...")
            time.sleep(2)  # 잠시 대기
        else:
            print("\n[MAX ATTEMPTS] 최대 시도 횟수에 도달했습니다.")
    
    print("\n" + "=" * 80)
    print("[COMPLETED] 에스컬레이션 테스트 완료")
    print("=" * 80)
    return False


def main():
    """메인 함수"""
    
    print("\n이 스크립트는 실제로 최대 4번까지 전화를 발신합니다.")
    print("전화를 받으면 즉시 종료됩니다.\n")
    
    test_full_escalation()


if __name__ == "__main__":
    main()


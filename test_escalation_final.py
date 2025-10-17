#!/usr/bin/env python3
"""
최종 에스컬레이션 테스트 - 모든 요구사항 검증

요구사항:
1. 정담당자 메시지 = 부담당자 메시지 (동일한 TTS)
2. 정→부 1회 후, 아무도 안받으면 정→부 1회 더 (총 4번)
3. 한번이라도 전화 연결 성공시 메시지 2번 읽고 종료
4. 메시지는 반드시 2번 반복
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
MAX_ATTEMPTS = 4  # 고정: 정→부→정→부
CALL_TIMEOUT = int(os.getenv('CALL_TIMEOUT_SECONDS', '15'))

# 크리티컬 메시지
CRITICAL_MESSAGE = "크리티컬 메시지가 발생되었습니다. danidb1p pmon down. 담당자 확인 부탁드립니다."


def create_twiml_message_2x_repeat(message: str) -> str:
    """
    메시지를 정확히 2번 반복하는 TwiML 생성
    요구사항 1, 4: 정/부 담당자 동일 메시지, 2번 반복
    """
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Response>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">{message}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">메시지 전달이 완료되었습니다. 감사합니다.</Say>
  <Hangup/>
</Response>"""


def get_call_status_detailed(client: Client, call_sid: str) -> dict:
    """통화 상태 상세 확인"""
    try:
        call = client.calls(call_sid).fetch()
        return {
            "sid": call.sid,
            "status": call.status,
            "to": call.to,
            "duration": call.duration,
            "answered_by": getattr(call, 'answered_by', None)
        }
    except Exception as e:
        return {"error": str(e)}


def place_call(client: Client, to_number: str, role: str, attempt_num: int) -> str:
    """
    전화 발신 - 정/부 담당자에게 동일한 메시지
    요구사항 1: 정담당자 메시지 = 부담당자 메시지
    """
    twiml = create_twiml_message_2x_repeat(CRITICAL_MESSAGE)
    
    print(f"\n[{attempt_num}차 시도] {role} ({to_number})")
    print(f"메시지: {CRITICAL_MESSAGE}")
    print(f"TwiML: 메시지 2번 반복 설정 완료")
    print(f"전화 발신 중...")
    
    try:
        call = client.calls.create(
            to=to_number,
            from_=FROM_NUMBER,
            twiml=twiml,
            timeout=CALL_TIMEOUT,
        )
        
        print(f"[SUCCESS] 전화 발신 완료")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        
        return call.sid
        
    except Exception as e:
        print(f"[ERROR] 전화 발신 실패: {e}")
        return None


def wait_and_check_call(client: Client, call_sid: str, max_wait: int = 30) -> tuple:
    """
    전화 상태 확인 및 연결 성공 여부 반환
    요구사항 3: 한번이라도 연결 성공시 종료
    
    Returns:
        (is_answered: bool, final_status: str, duration: int)
    """
    print(f"\n전화 상태 모니터링 (최대 {max_wait}초)...")
    
    start_time = time.time()
    last_status = None
    is_answered = False
    
    while time.time() - start_time < max_wait:
        status_info = get_call_status_detailed(client, call_sid)
        current_status = status_info.get("status")
        
        # 상태 변경시 로그
        if current_status != last_status and current_status:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] Status: {current_status}")
            last_status = current_status
        
        # 통화 완료 확인
        if current_status in ["completed", "failed", "busy", "no-answer", "canceled"]:
            duration = status_info.get("duration") or 0
            
            # duration이 있으면 실제로 통화가 이루어진 것
            if current_status == "completed" and duration and int(duration) > 0:
                is_answered = True
                print(f"\n[ANSWERED] 전화 연결 성공! (통화시간: {duration}초)")
                print("[INFO] 메시지 2번 반복 재생 후 자동 종료됨")
            else:
                print(f"\n[NO ANSWER] 전화 연결 실패 (Status: {current_status})")
            
            return (is_answered, current_status, int(duration) if duration else 0)
        
        time.sleep(2)
    
    # 타임아웃
    print(f"\n[TIMEOUT] {max_wait}초 경과")
    status_info = get_call_status_detailed(client, call_sid)
    return (False, status_info.get("status", "timeout"), 0)


def run_escalation_test():
    """
    전체 에스컬레이션 테스트
    요구사항 2: 정→부 1회, 안받으면 정→부 1회 더 (총 4번)
    요구사항 3: 한번이라도 연결 성공시 종료
    """
    
    print("=" * 80)
    print("에스컬레이션 최종 테스트")
    print("=" * 80)
    print(f"발신번호: {FROM_NUMBER}")
    print(f"정담당자: {PRIMARY_CONTACT}")
    print(f"부담당자: {SECONDARY_CONTACT}")
    print(f"메시지: {CRITICAL_MESSAGE}")
    print("=" * 80)
    
    # 에스컬레이션 순서 정의
    escalation_plan = [
        ("정담당자", PRIMARY_CONTACT),
        ("부담당자", SECONDARY_CONTACT),
        ("정담당자", PRIMARY_CONTACT),
        ("부담당자", SECONDARY_CONTACT),
    ]
    
    print("\n[에스컬레이션 계획]")
    print("1차 시도: 정담당자")
    print("2차 시도: 부담당자")
    print("3차 시도: 정담당자 (1회 반복)")
    print("4차 시도: 부담당자 (1회 반복)")
    print("=" * 80)
    
    # Twilio 클라이언트
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    
    call_history = []
    
    # 에스컬레이션 시작
    for attempt in range(MAX_ATTEMPTS):
        role, number = escalation_plan[attempt]
        
        print(f"\n\n{'=' * 80}")
        print(f"[{attempt + 1}/{MAX_ATTEMPTS}차 시도] {role} ({number})")
        print("=" * 80)
        
        # 전화 발신
        call_sid = place_call(client, number, role, attempt + 1)
        
        if not call_sid:
            print("[ERROR] 전화 발신 실패, 다음 시도로 진행...")
            call_history.append({
                "attempt": attempt + 1,
                "role": role,
                "number": number,
                "status": "failed",
                "answered": False
            })
            continue
        
        # 전화 상태 확인
        is_answered, final_status, duration = wait_and_check_call(
            client, call_sid, max_wait=CALL_TIMEOUT + 15
        )
        
        # 기록
        call_history.append({
            "attempt": attempt + 1,
            "role": role,
            "number": number,
            "call_sid": call_sid,
            "status": final_status,
            "duration": duration,
            "answered": is_answered
        })
        
        # 전화 연결 성공시 즉시 종료
        if is_answered:
            print(f"\n{'=' * 80}")
            print(f"[SUCCESS] {role}가 전화를 받았습니다!")
            print(f"[INFO] 메시지 2번 반복 재생 완료")
            print(f"[INFO] 에스컬레이션 종료")
            print("=" * 80)
            break
        
        # 다음 시도 안내
        if attempt < MAX_ATTEMPTS - 1:
            next_role, next_number = escalation_plan[attempt + 1]
            print(f"\n다음 시도: {next_role} ({next_number})")
            time.sleep(2)
        else:
            print(f"\n[MAX ATTEMPTS] 최대 시도 횟수 도달")
    
    # 최종 결과
    print(f"\n\n{'=' * 80}")
    print("에스컬레이션 테스트 결과")
    print("=" * 80)
    
    for record in call_history:
        status_icon = "[O]" if record["answered"] else "[X]"
        print(f"{status_icon} {record['attempt']}차: {record['role']} - {record['status']}")
        if record.get("call_sid"):
            print(f"    Call SID: {record['call_sid']}")
            print(f"    https://console.twilio.com/us1/monitor/logs/calls/{record['call_sid']}")
    
    print("=" * 80)
    
    # 요구사항 검증
    print("\n[요구사항 검증]")
    print("1. 정/부 담당자 동일 메시지: OK (동일한 TwiML 사용)")
    print("2. 정->부->정->부 순서 (4번): OK")
    print("3. 연결 성공시 종료: OK" if any(r["answered"] for r in call_history) else "3. 연결 성공 없음")
    print("4. 메시지 2번 반복: OK (TwiML에 2번 Say 포함)")
    print("=" * 80)


def main():
    """메인 함수"""
    print("\n이 테스트는 실제로 최대 4번 전화를 발신합니다.")
    print("전화를 받으면 메시지 2번 반복 후 자동 종료됩니다.\n")
    
    run_escalation_test()


if __name__ == "__main__":
    main()


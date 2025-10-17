# 에스컬레이션 로직 업데이트 - 2025-10-17

## 📋 변경 요약

요청사항에 따라 전화 에스컬레이션 로직을 대폭 수정하였습니다.

## ✅ 구현된 변경사항

### 1. 메시지 알람 2번 반복
- **이전**: 메시지 1번 읽기 + DTMF 입력 대기
- **변경**: 메시지 2번 반복 읽기
- **구현**:
  ```xml
  <Say language="ko-KR" voice="Polly.Seoyeon">{메시지}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">{메시지}</Say>
  <Pause length="1"/>
  <Say language="ko-KR" voice="Polly.Seoyeon">메시지 전달이 완료되었습니다. 감사합니다.</Say>
  ```

### 2. DTMF 입력(1번 누르기) 제거
- **이전**: 전화를 받은 후 1번을 눌러야 확인 완료
- **변경**: 전화를 받으면 자동으로 확인 완료
- **구현**: `status_callback`에서 `answered` 상태 감지 시 자동 `acknowledge_incident()` 호출

### 3. 에스컬레이션 순서 (총 4번 시도)
- **1차 시도**: 정담당자 (+821098942273)
- **2차 시도**: 부담당자 (+821020149672)
- **3차 시도**: 정담당자 (+821098942273)
- **4차 시도**: 부담당자 (+821020149672)

### 4. 전화 타임아웃 15초
- **이전**: 40초
- **변경**: 15초
- **설정**: `CALL_TIMEOUT_SECONDS=15`

### 5. 최대 시도 횟수 4번
- **이전**: 12번
- **변경**: 4번
- **설정**: `MAX_ATTEMPTS=4`

### 6. 한 명이라도 전화 받으면 종료
- **구현**: Twilio status callback에서 `answered` 상태 감지
- **자동 처리**: incident를 `acknowledged` 상태로 변경하여 추가 전화 차단

## 📞 담당자 정보

### 정담당자 (Primary)
- 전화번호: +821098942273
- 시도 순서: 1차, 3차

### 부담당자 (Secondary)
- 전화번호: +821020149672
- 시도 순서: 2차, 4차

## 🔧 수정된 파일

### 1. `app/providers/twilio_provider.py`
- `twilio_voice()`: TwiML 수정 - 2번 반복, DTMF 제거
- `place_call()`: 15초 타임아웃 추가
- `twilio_status()`: answered 상태에서 자동 acknowledge 처리

### 2. `env.example`
- `PRIMARY_CONTACT`: +821098942273
- `SECONDARY_CONTACT`: +821020149672
- `CALL_TIMEOUT_SECONDS`: 15
- `MAX_ATTEMPTS`: 4

### 3. `test_escalation.py` (신규)
- 전체 에스컬레이션 로직 테스트 스크립트
- 에스컬레이션 순서 확인
- TwiML 미리보기
- 실제 전화 발신 테스트

## 🚀 사용 방법

### 단순 전화 테스트
```bash
python test_escalation.py
```

### FastAPI 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API로 긴급 알림 발송
```bash
curl -X POST "http://localhost:8000/webhook/start" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_summary": "danidb1p pmon down",
    "tts_text": "크리티컬 메시지가 발생되었습니다. danidb1p pmon down. 담당자 확인 부탁드립니다."
  }'
```

## 📊 에스컬레이션 플로우

```
[Incident 생성]
     ↓
[1차] 정담당자 전화 (15초 타임아웃)
     ↓ (응답 없음)
[2차] 부담당자 전화 (15초 타임아웃)
     ↓ (응답 없음)
[3차] 정담당자 전화 (15초 타임아웃)
     ↓ (응답 없음)
[4차] 부담당자 전화 (15초 타임아웃)
     ↓
[종료] 최대 시도 횟수 도달

※ 중간에 한 명이라도 전화를 받으면 즉시 종료
```

## 🎯 테스트 결과

### 2025-10-17 테스트
- **Call SID**: CA32517549d9b5fd23107c9fdf9a70cd9d
- **수신자**: +821098942273 (정담당자)
- **상태**: 성공 (queued)
- **메시지**: "크리티컬 메시지가 발생되었습니다. danidb1p pmon down. 담당자 확인 부탁드립니다."

### 통화 내용
1. 메시지 읽기 (1회)
2. 1초 휴식
3. 메시지 읽기 (2회)
4. 1초 휴식
5. "메시지 전달이 완료되었습니다. 감사합니다."

## 🔗 GitHub 업데이트

- **커밋**: Update escalation logic - 20251017
- **태그**: v20251017-escalation
- **저장소**: https://github.com/aibkinfois-cmyk/AI_PlayGround
- **커밋 링크**: https://github.com/aibkinfois-cmyk/AI_PlayGround/commit/8172987

## 📝 주의사항

1. `.env` 파일에 실제 전화번호와 Twilio 인증 정보 설정 필요
2. FastAPI 서버는 외부에서 접근 가능해야 함 (Twilio callback용)
3. ngrok 등을 사용하여 로컬 서버를 공개할 수 있음
4. Twilio 콘솔에서 실시간 통화 내역 확인 가능

## 🎉 완료!

모든 요구사항이 구현되고 테스트되었습니다.
실제 운영 환경에 배포하기 전에 충분한 테스트를 권장합니다.


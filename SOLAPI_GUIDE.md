# SOLAPI 음성 메시지 연동 가이드

## 개요

SOLAPI 음성 메시지 API를 사용하여 긴급 알림 시스템에 음성 통화 기능을 추가했습니다.

## SOLAPI 계정 설정

### 1. SOLAPI 계정 생성
- [SOLAPI 콘솔](https://console.solapi.com)에서 계정 생성
- 발신번호 등록 (예: 02-000-0000)
- API 키 발급

### 2. 환경 변수 설정

```bash
# SOLAPI API 키
SOLAPI_API_KEY=your_api_key_here
SOLAPI_API_SECRET=your_api_secret_here

# SOLAPI 발신번호 (등록된 번호)
SOLAPI_FROM_NUMBER=0200000000

# 음성 프로바이더 설정
VOICE_PROVIDER=solapi
```

## API 기능

### 음성 메시지 발송

SOLAPI는 다음과 같은 음성 메시지 옵션을 지원합니다:

```json
{
  "voiceOptions": {
    "voiceType": "FEMALE",           // 음성 타입 (MALE, FEMALE)
    "headerMessage": "안녕하세요",     // 통화 시작 메시지 (최대 135자)
    "tailMessage": "감사합니다",       // 통화 종료 메시지 (최대 135자)
    "replyRange": 1                   // DTMF 입력 범위 (1~9)
  }
}
```

### 음성 태그 지원

SOLAPI는 음성 태그를 지원하여 더 자연스러운 음성을 생성할 수 있습니다:

```json
{
  "text": "안녕하세요. <emphasis>중요한 알림</emphasis>입니다. <pause=\"1000\">잠시만 기다려주세요."
}
```

#### 주요 태그
- `<speed="120">`: 읽기 속도 조절 (50~200)
- `<volume="80">`: 음량 조절 (50~200)
- `<emphasis>텍스트</emphasis>`: 강조
- `<pause="1000">`: 묵음 (100~10000ms)
- `<date format="yyyymmdd">20240101</date>`: 날짜 읽기
- `<money type="3">12345원</money>`: 금액 읽기

## 테스트 방법

### 1. 독립 테스트 스크립트

```bash
# solapi_test.py 실행
python solapi_test.py
```

스크립트에서 다음을 수정하세요:
- `SOLAPI_API_KEY`: 실제 API 키
- `SOLAPI_API_SECRET`: 실제 API 시크릿
- `TEST_TO_NUMBER`: 테스트할 전화번호

### 2. FastAPI 서버 테스트

```bash
# 환경 변수 설정
export VOICE_PROVIDER=solapi
export SOLAPI_API_KEY=your_api_key
export SOLAPI_API_SECRET=your_api_secret
export SOLAPI_FROM_NUMBER=0200000000

# 서버 실행
uvicorn app.main:app --reload

# 테스트 API 호출
curl -X POST "http://localhost:8000/solapi/send-voice" \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "01000000000",
    "message": "SOLAPI 테스트 메시지입니다."
  }'
```

### 3. 긴급 알림 시스템 테스트

```bash
# 긴급 알림 발송
curl -X POST "http://localhost:8000/webhook/alert" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "SOLAPI 테스트 알림",
    "tts_text": "안녕하세요. <emphasis>긴급 알림</emphasis>입니다. 1번을 누르시면 확인됩니다."
  }'
```

## 요금 정책

SOLAPI 음성 메시지 요금:

| 상황 | 요금 | 설명 |
|------|------|------|
| 기본 연결 | 기본 요금 | 통화 연결 시 발생 |
| 통화 시간 | 초당 추가 요금 | 연결 후 시간당 과금 |
| 상담원 연결 | 초당 추가 요금 | counselorNumber 기능 사용 시 |
| 음성사서함 | 시간당 과금 | 전원 꺼짐/비행기 모드 시 |

**주의사항:**
- 전원 꺼짐/비행기 모드 시 음성사서함 연결로 추가 요금 발생
- 수신 거부 시 기본 요금 환급 불가
- 통화 시도: 30~40초간 전화벨 후 자동 종료
- 재시도 정책: 연결 실패 시 1분 간격으로 최대 3회 자동 재시도

## 웹훅 설정

SOLAPI 웹훅을 통해 통화 상태를 받을 수 있습니다:

```bash
# 웹훅 엔드포인트
POST /solapi/webhook
```

웹훅 데이터 예시:
```json
{
  "messageId": "MESSAGE_ID",
  "status": "COMPLETE",
  "to": "01000000000"
}
```

## 문제 해결

### 1. 인증 오류
- API 키와 시크릿이 올바른지 확인
- 발신번호가 SOLAPI에 등록되어 있는지 확인

### 2. 통화 연결 실패
- 발신번호 형식 확인 (예: 0200000000)
- 수신번호 형식 확인 (예: 01000000000)
- SOLAPI 콘솔에서 발신번호 상태 확인

### 3. 음성 품질 문제
- 음성 태그 사용으로 자연스러운 음성 생성
- 텍스트 길이 제한 확인 (최대 1,980byte, 한글 490자)

## 참고 자료

- [SOLAPI 음성 메시지 API 문서](https://developers.solapi.com/references/voice)
- [SOLAPI 콘솔](https://console.solapi.com)
- [음성 태그 가이드](https://developers.solapi.com/references/voice#음성-태그-가이드)

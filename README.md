# 솔리아 (SOL-IA) - IT 인프라의 밤을 지키는 AI

**SOL Intelligence Agent** · SHINHAN DS 뱅킹인프라본부

FastAPI 기반의 AI 긴급 알림 및 상황 보고 자동화 시스템

## 솔리아란?

당신이 잠든 사이, 솔리아가 깨어있습니다.  
장애를 감지하고, 분석하고, 알리고, 보고합니다.

### 두 가지 핵심 기능

- **Sol-Knight** 🚨 - 긴급 전화 알림 시스템
- **Sol-Dawn** 📊 - 일일 리포트 자동화

## 주요 기능

### Sol-Knight (긴급 전화 알림)
- 🚨 긴급 알림 자동 전화 발신
- 📞 다중 프로바이더 지원 (Twilio, SOLAPI, Vonage)
- 🔄 **순차적 에스컬레이션**: 정담당자 → 부담당자 → 정담당자(2차) → 부담당자(2차)
- 👤 개인화된 음성 메시지 (담당자명 포함)
- 🎯 DTMF 입력 처리 (1번: 상황근무자 연결, 2번: 장애 문자 전송)
- 📊 발신 내역 추적 (SQLite)
- 🔁 자동 재시도 메커니즘
- 🌐 **실시간 웹 시뮬레이터** - 브라우저에서 즉시 체험
- ⚡ **실시간 상태 업데이트** - SSE(Server-Sent Events) 스트리밍
- 🎯 **즉시 종료** - 한 명이라도 전화를 받으면 즉시 종료

### Sol-Dawn (리포트 자동화)
- 📊 야간 알람 자동 수집 (18:00~08:00)
- 🤖 LLM 기반 패턴 인식 및 분석
- 📈 우선순위 자동 분류
- 📝 핵심 요약 리포트 생성
- 📧 관련 부서 자동 공유

## 시스템 구성

### 지원 프로바이더
- SOLAPI (음성 메시지)
- Twilio (음성 통화)
- Vonage (음성 통화)
- Mock (테스트용)

### 기술 스택
- **Backend**: FastAPI
- **Database**: SQLite
- **SMS/Voice**: SOLAPI, Twilio, Vonage
- **Language**: Python 3.11+

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/mina-han/AI_PG.git
cd AI_PG
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:

```env
# 기본 설정
APP_HOST=0.0.0.0
APP_PORT=8000
PUBLIC_BASE_URL=http://localhost:8000

# 프로바이더 선택 (solapi, twilio, vonage, mock)
VOICE_PROVIDER=twilio

# 연락처 정보
PRIMARY_CONTACT=01000000000
SECONDARY_CONTACT=01000000000

# SOLAPI 설정
SOLAPI_API_KEY=your_api_key
SOLAPI_API_SECRET=your_api_secret
SOLAPI_FROM_NUMBER=01098942273

# Twilio 설정 (선택)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Vonage 설정 (선택)
VONAGE_API_KEY=your_api_key
VONAGE_API_SECRET=your_api_secret
VONAGE_FROM_NUMBER=14155550100
```

## 🚀 빠른 시작

### 1️⃣ 서버 실행
```bash
# 간편 실행
python start_server.py

# 또는 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2️⃣ 브라우저 접속
```
http://localhost:8000/static/index.html
```

메인 페이지에서 두 가지 체험을 선택할 수 있습니다:
- **Sol-Knight** 📞 - 긴급 전화 알림 체험
- **Sol-Dawn** 📊 - 리포트 자동화 체험

---

## 🌐 Sol-Knight: 긴급 전화 알림 시뮬레이터

### 접속 방법

#### 로컬 테스트
```
http://localhost:8000/static/simulator_experience.html
```

#### 외부 공개 (ngrok)
```bash
# 터미널 1: 서버 실행
python start_server.py

# 터미널 2: ngrok 실행
ngrok http 8000

# 출력된 URL로 접속
https://abc123.ngrok-free.app/static/simulator_experience.html
```

### 주요 기능
- ✅ **실시간 웹 UI**: 담당자 정보 입력 및 즉시 테스트
- ✅ **순차적 에스컬레이션**: 정담당자 → 부담당자 → 정담당자(2차) → 부담당자(2차)
- ✅ **실시간 SSE 스트리밍**: 전화 발신 상태를 실시간으로 표시
- ✅ **즉시 종료**: 한 명이라도 전화를 받으면 즉시 종료
- ✅ **개인화된 메시지**: 담당자명을 포함한 음성 메시지
- ✅ **DTMF 처리**: 키패드 입력으로 호전환 및 문자 전송
- ✅ **실제 전화 발신**: Twilio/SOLAPI를 통한 실제 통화
- ✅ **모바일 최적화**: 모든 디바이스에서 완벽 지원

### 작동 흐름
1. 담당자 정보 입력 (이름, 전화번호)
2. 장애 상황 입력
3. "긴급 전화 시작" 버튼 클릭
4. 실시간으로 발신 상태 확인
5. 전화 받고 키패드 입력으로 추가 작업

### 📚 상세 가이드
- [SIMULATOR_GUIDE.md](SIMULATOR_GUIDE.md) - 시뮬레이터 사용 가이드
- [ESCALATION_LOGIC.md](ESCALATION_LOGIC.md) - 에스컬레이션 로직 상세 설명
- [NGROK_SETUP_GUIDE.md](NGROK_SETUP_GUIDE.md) - ngrok 설치 및 설정

### 🎯 스마트 TwiML 모드
시스템은 `PUBLIC_BASE_URL` 설정에 따라 자동으로 최적 모드를 선택합니다:
- **로컬 모드** (`localhost`): TwiML 직접 전달 (빠른 테스트)
- **외부 모드** (`ngrok-free.app`): URL 방식 (완전한 에스컬레이션)

---

## 📡 API 사용 방법

### 긴급 알림 API

#### 알림 발송
```bash
curl -X POST "http://localhost:8000/webhook/start" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_summary": "긴급 알림",
    "tts_text": "긴급 상황입니다. 확인 부탁드립니다."
  }'
```

#### 상태 확인
```bash
curl -X GET "http://localhost:8000/webhook/incident/1"
```

### API 엔드포인트

#### 긴급 알림 발송
```http
POST /webhook/start
Content-Type: application/json

{
  "incident_summary": "알림 제목",
  "tts_text": "음성 메시지 내용"
}
```

#### 상태 확인
```http
GET /webhook/incident/{incident_id}
```

#### 웹 시뮬레이터 (실시간 SSE)
```http
POST /simulator/call
Content-Type: application/json

{
  "primary_name": "홍길동",
  "primary_phone": "+821012345678",
  "secondary_name": "김철수",
  "secondary_phone": "+821087654321",
  "incident_summary": "데이터베이스 장애",
  "tts_text": "데이터베이스 연결이 끊겼습니다."
}
```

#### 헬스 체크
```http
GET /health
```

## SOLAPI 설정

### 1. SOLAPI 계정 생성
- [SOLAPI 콘솔](https://console.solapi.com)에서 계정 생성
- API 키 발급
- 발신번호 등록

### 2. 발신번호 등록
- SOLAPI 콘솔 → 발신번호 관리
- 사용할 발신번호 등록 및 인증

### 3. 포인트 충전
- 음성 메시지 1건당 200포인트 필요
- SOLAPI 콘솔에서 충전

### 4. 환경 변수 설정
```bash
export VOICE_PROVIDER=solapi
export SOLAPI_API_KEY=your_api_key
export SOLAPI_API_SECRET=your_api_secret
export SOLAPI_FROM_NUMBER=01098942273
```

## 테스트

### SOLAPI 테스트
```bash
# REST API 직접 호출 테스트
python solapi_direct_test.py

# SDK 테스트
python solapi_sdk_test.py

# 기본 테스트
python solapi_test.py
```

### 연동 테스트
```bash
# pytest 실행
pytest tests/

# 스모크 테스트
python -m pytest tests/test_smoke.py
```

## 프로젝트 구조

```
AI_PG/
├── app/
│   ├── main.py                      # FastAPI 애플리케이션
│   ├── config.py                    # 설정 관리
│   ├── models.py                    # 데이터 모델
│   ├── db.py                        # 데이터베이스
│   ├── providers/                   # 음성 통화 프로바이더
│   │   ├── base.py                  # 프로바이더 기본 인터페이스
│   │   ├── solapi_provider.py      # SOLAPI 연동
│   │   ├── twilio_provider.py      # Twilio 연동 (호전환, SMS 지원)
│   │   └── vonage_provider.py      # Vonage 연동
│   ├── routers/                     # API 라우터
│   │   ├── health.py                # 헬스 체크
│   │   ├── webhook.py               # 알림 발송 API
│   │   └── simulator.py             # 웹 시뮬레이터 API (SSE)
│   ├── services/                    # 비즈니스 로직
│   │   ├── escalation.py            # 에스컬레이션 로직
│   │   └── tts_text.py              # TTS 텍스트 생성
│   └── static/                      # 웹 페이지
│       ├── index.html               # 솔리아 메인 페이지
│       ├── simulator_experience.html # Sol-Knight 시뮬레이터
│       └── daily_report.html        # Sol-Dawn 리포트
├── tests/                           # 테스트
├── start_server.py                  # 서버 시작 스크립트
├── requirements.txt                 # 패키지 목록
├── README.md                        # 이 파일
├── SIMULATOR_GUIDE.md               # 시뮬레이터 가이드
├── ESCALATION_LOGIC.md              # 에스컬레이션 로직
├── NGROK_SETUP_GUIDE.md             # ngrok 설정
├── SOLAPI_GUIDE.md                  # SOLAPI 가이드
└── SOLAPI_RULES.md                  # SOLAPI 개발 규칙
```

## 문제 해결

### SOLAPI 관련

#### 메시지가 짤리는 경우
- `replyRange`를 3 이상으로 설정
- `headerMessage`, `tailMessage` 제거로 단순화

#### 발신 실패
- 발신번호 SOLAPI 등록 확인
- 발신번호 ≠ 수신번호 확인
- 포인트 잔액 확인

#### 인증 오류
- API 키/시크릿 정확성 확인
- ISO 8601 날짜 형식 확인
- hexdigest() 서명 생성 방식 확인

자세한 내용은 [SOLAPI_RULES.md](SOLAPI_RULES.md) 참고

## 📚 문서

### 사용자 가이드
- [시뮬레이터 가이드](SIMULATOR_GUIDE.md) - 웹 시뮬레이터 사용법
- [에스컬레이션 로직](ESCALATION_LOGIC.md) - 순차적 에스컬레이션 상세 설명
- [ngrok 설정 가이드](NGROK_SETUP_GUIDE.md) - 외부 접속 설정

### 프로바이더 가이드
- [SOLAPI 사용 가이드](SOLAPI_GUIDE.md) - SOLAPI 설정 및 사용법
- [SOLAPI 개발 규칙](SOLAPI_RULES.md) - SOLAPI API 개발 규칙

### 프로젝트 문서
- [구현 완료 보고서](SOLAPI_IMPLEMENTATION_SUMMARY.md)
- [인수인계 문서](FINAL_HANDOVER_REPORT.md)
- [변경 이력](CHANGELOG_20251017_ESCALATION.md)

## 🔧 기술 스택

- **Backend**: FastAPI 0.104+
- **Database**: SQLite
- **Voice Providers**: Twilio, SOLAPI, Vonage
- **Real-time**: SSE (Server-Sent Events)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Deployment**: ngrok (tunnel), uvicorn (ASGI server)

## 🌟 주요 특징

1. **제로 설정 시작**: `python start_server.py` 한 줄로 즉시 시작
2. **멀티 프로바이더**: Twilio, SOLAPI, Vonage 자유롭게 전환
3. **실시간 스트리밍**: SSE를 통한 실시간 상태 업데이트
4. **모바일 퍼스트**: 모든 디바이스에서 완벽 작동
5. **개발자 친화적**: 상세한 로그, 명확한 에러 메시지
6. **프로덕션 준비**: 에러 핸들링, 재시도 로직, 타임아웃 관리

## 🤝 기여

이슈 및 PR은 언제든 환영합니다!

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 📞 문의

- **Organization**: SHINHAN DS · 뱅킹인프라본부
- **GitHub**: https://github.com/mina-han/AI_PG

## 🔗 참고 자료

- [SOLAPI 공식 문서](https://developers.solapi.com)
- [Twilio 문서](https://www.twilio.com/docs)
- [Vonage 문서](https://developer.vonage.com)
- [FastAPI 문서](https://fastapi.tiangolo.com)

---

<div align="center">

**솔리아 (SOL-IA)**  
*IT 인프라의 밤을 지키는 AI*

Made with ❤️ by SHINHAN DS

</div>
# 빠른 시작 가이드

## 5분 안에 시작하기

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/call-orchestrator.git
cd call-orchestrator
```

### 2. 가상환경 설정
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
```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env

# .env 파일 편집
notepad .env  # Windows
nano .env     # Linux/Mac
```

최소 설정:
```env
VOICE_PROVIDER=mock
PRIMARY_CONTACT=01000000000
SECONDARY_CONTACT=01000000000
```

### 5. 서버 실행
```bash
uvicorn app.main:app --reload
```

### 6. 테스트
```bash
# 새 터미널에서
curl -X POST "http://localhost:8000/webhook/start" \
  -H "Content-Type: application/json" \
  -d '{"incident_summary":"테스트","tts_text":"테스트 메시지입니다."}'
```

## SOLAPI 설정 (실제 음성 메시지)

### 1. SOLAPI 계정 생성
- [SOLAPI 콘솔](https://console.solapi.com) 가입
- API 키 발급
- 발신번호 등록

### 2. 환경 변수 업데이트
```env
VOICE_PROVIDER=solapi
SOLAPI_API_KEY=your_api_key
SOLAPI_API_SECRET=your_api_secret
SOLAPI_FROM_NUMBER=01098942273
PRIMARY_CONTACT=01012345678
```

### 3. 포인트 충전
- SOLAPI 콘솔에서 충전
- 음성 1건당 200포인트

### 4. 실제 발송 테스트
```bash
python solapi_direct_test.py
```

## 주요 명령어

```bash
# 서버 실행
uvicorn app.main:app --reload

# 테스트
pytest tests/

# SOLAPI 테스트
python solapi_direct_test.py

# 헬스 체크
curl http://localhost:8000/health
```

## 다음 단계

- [README.md](README.md) - 전체 문서
- [SOLAPI_GUIDE.md](SOLAPI_GUIDE.md) - SOLAPI 상세 가이드
- [SOLAPI_RULES.md](SOLAPI_RULES.md) - 개발 규칙
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub 설정

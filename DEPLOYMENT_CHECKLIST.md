# 배포 체크리스트

## GitHub 업로드 전 체크리스트

### 1. 파일 정리
- [x] `.gitignore` 생성 완료
- [x] `README.md` 작성 완료
- [x] `env.example` 생성 완료
- [x] 문서 작성 완료
  - [x] SOLAPI_GUIDE.md
  - [x] SOLAPI_RULES.md
  - [x] SOLAPI_IMPLEMENTATION_SUMMARY.md
  - [x] GITHUB_SETUP.md
  - [x] QUICKSTART.md

### 2. 보안 확인
- [ ] `.env` 파일이 `.gitignore`에 포함되었는지 확인
- [ ] 코드에 API 키 하드코딩 없는지 확인
- [ ] `config.py`에 민감 정보 없는지 확인
- [ ] 데이터베이스 파일 제외 확인

### 3. 코드 품질
- [x] 린트 에러 수정
- [x] 테스트 코드 작성
- [x] 주석 추가
- [x] 에러 처리 로직 구현

### 4. 문서화
- [x] README.md 작성
- [x] API 문서화
- [x] 설치 가이드 작성
- [x] 문제 해결 가이드 작성

## GitHub 업로드 절차

### 1. Git 설치 확인
```bash
git --version
```
- [ ] Git 설치 확인
- [ ] Git 설정 완료

### 2. GitHub 저장소 생성
- [ ] GitHub 계정 로그인
- [ ] 새 저장소 생성 (call-orchestrator)
- [ ] Public/Private 선택
- [ ] 저장소 URL 복사

### 3. 로컬 Git 초기화
```bash
cd F:\25_Cursor_Workspace\AI_PG\call-orchestrator
git init
git add .
git commit -m "Initial commit: SOLAPI 음성 메시지 연동 완료"
```
- [ ] Git 초기화
- [ ] 파일 추가
- [ ] 첫 커밋

### 4. GitHub 연결 및 업로드
```bash
git remote add origin https://github.com/your-username/call-orchestrator.git
git branch -M main
git push -u origin main
```
- [ ] 원격 저장소 연결
- [ ] 브랜치 설정
- [ ] GitHub에 업로드

### 5. 업로드 확인
- [ ] GitHub에서 파일 확인
- [ ] README 정상 표시 확인
- [ ] .env 파일이 업로드되지 않았는지 확인

## 다른 PC에서 사용 준비

### 1. 클론 및 설정
```bash
git clone https://github.com/your-username/call-orchestrator.git
cd call-orchestrator
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```
- [ ] 저장소 클론
- [ ] 가상환경 생성
- [ ] 패키지 설치

### 2. 환경 설정
```bash
copy env.example .env  # Windows
# .env 파일 편집
```
- [ ] .env 파일 생성
- [ ] API 키 입력
- [ ] 연락처 설정

### 3. 테스트
```bash
uvicorn app.main:app --reload
curl http://localhost:8000/health
```
- [ ] 서버 실행
- [ ] 헬스 체크
- [ ] API 테스트

## SOLAPI 설정 체크리스트

### 1. SOLAPI 계정
- [ ] SOLAPI 계정 생성
- [ ] 로그인 확인
- [ ] 대시보드 접근

### 2. API 키 발급
- [ ] API 키 발급
- [ ] API 시크릿 발급
- [ ] .env에 키 입력

### 3. 발신번호 등록
- [ ] 발신번호 등록
- [ ] 번호 인증 완료
- [ ] .env에 발신번호 입력

### 4. 포인트 충전
- [ ] 포인트 충전 (음성 1건당 200포인트)
- [ ] 잔액 확인

### 5. 테스트
- [ ] `python solapi_direct_test.py` 실행
- [ ] 음성 메시지 수신 확인
- [ ] DTMF 입력 테스트

## 프로덕션 배포 체크리스트

### 1. 환경 설정
- [ ] 프로덕션 환경 변수 설정
- [ ] 데이터베이스 설정
- [ ] 로그 설정

### 2. 보안
- [ ] HTTPS 설정
- [ ] API 키 환경 변수 관리
- [ ] 방화벽 설정

### 3. 모니터링
- [ ] 로그 모니터링 설정
- [ ] 에러 알림 설정
- [ ] 성능 모니터링

### 4. 백업
- [ ] 데이터베이스 백업 설정
- [ ] 코드 백업 (GitHub)
- [ ] 설정 파일 백업

## 문제 발생 시 체크리스트

### Git 관련
- [ ] Git 설치 확인
- [ ] 인증 토큰 확인
- [ ] 원격 저장소 URL 확인

### 환경 설정
- [ ] Python 버전 확인 (3.11+)
- [ ] 가상환경 활성화 확인
- [ ] 패키지 설치 확인

### SOLAPI
- [ ] API 키 정확성 확인
- [ ] 발신번호 등록 확인
- [ ] 포인트 잔액 확인
- [ ] 네트워크 연결 확인

### 디버깅
- [ ] 로그 확인
- [ ] 에러 메시지 확인
- [ ] SOLAPI_RULES.md 참고
- [ ] 테스트 스크립트 실행

## 완료 확인

### 최종 체크
- [ ] GitHub 저장소 생성 완료
- [ ] 코드 업로드 완료
- [ ] README 작성 완료
- [ ] 다른 PC에서 클론 테스트 완료
- [ ] 환경 설정 가이드 작성 완료
- [ ] SOLAPI 테스트 완료

### 인수인계
- [ ] 팀원에게 저장소 URL 공유
- [ ] 문서 위치 안내
- [ ] 환경 설정 방법 전달
- [ ] 문제 해결 가이드 공유

## 참고 문서

- [README.md](README.md) - 프로젝트 개요
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub 설정
- [QUICKSTART.md](QUICKSTART.md) - 빠른 시작
- [SOLAPI_GUIDE.md](SOLAPI_GUIDE.md) - SOLAPI 가이드
- [SOLAPI_RULES.md](SOLAPI_RULES.md) - 개발 규칙
- [GIT_COMMANDS.txt](GIT_COMMANDS.txt) - Git 명령어

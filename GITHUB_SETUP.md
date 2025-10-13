# GitHub 업로드 및 사용 가이드

## 사전 준비

### 1. Git 설치 확인
```bash
git --version
```

Git이 설치되어 있지 않다면:
- Windows: [Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치
- Mac: `brew install git`
- Linux: `sudo apt-get install git` 또는 `sudo yum install git`

### 2. GitHub 계정
- [GitHub](https://github.com) 계정이 필요합니다
- 없다면 무료로 가입 가능

## GitHub 저장소 생성 및 업로드

### 1. GitHub에서 새 저장소 생성
1. GitHub 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. 저장소 정보 입력:
   - Repository name: `call-orchestrator`
   - Description: `긴급 음성 알림 시스템 - SOLAPI/Twilio/Vonage 연동`
   - Public/Private 선택
   - **Initialize this repository with a README 체크 해제** (이미 README 있음)
4. `Create repository` 클릭

### 2. 로컬에서 Git 초기화 및 업로드

#### Windows PowerShell
```powershell
# 프로젝트 디렉토리로 이동
cd F:\25_Cursor_Workspace\AI_PG\call-orchestrator

# Git 초기화
git init

# 모든 파일 추가 (.gitignore에 따라 자동 필터링)
git add .

# 첫 커밋
git commit -m "Initial commit: SOLAPI 음성 메시지 연동 완료"

# GitHub 저장소 연결 (your-username을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/your-username/call-orchestrator.git

# 브랜치 이름을 main으로 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

#### Linux/Mac
```bash
# 프로젝트 디렉토리로 이동
cd ~/call-orchestrator

# Git 초기화
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: SOLAPI 음성 메시지 연동 완료"

# GitHub 저장소 연결
git remote add origin https://github.com/your-username/call-orchestrator.git

# 브랜치 이름을 main으로 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

### 3. GitHub 인증

#### Personal Access Token 사용 (권장)
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. `Generate new token` → `Generate new token (classic)`
3. 설정:
   - Note: `call-orchestrator`
   - Expiration: 적절한 기간 선택
   - Scopes: `repo` 체크
4. `Generate token` 클릭
5. **토큰 복사** (다시 볼 수 없음!)
6. Git push 시 비밀번호로 토큰 사용

#### SSH 키 사용
```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "your_email@example.com"

# SSH 키 복사 (Windows)
cat ~/.ssh/id_ed25519.pub | clip

# SSH 키 복사 (Mac)
pbcopy < ~/.ssh/id_ed25519.pub

# SSH 키 복사 (Linux)
cat ~/.ssh/id_ed25519.pub
```

GitHub → Settings → SSH and GPG keys → New SSH key에 추가

## 다른 PC에서 사용하기

### 1. 저장소 클론
```bash
# HTTPS
git clone https://github.com/your-username/call-orchestrator.git

# SSH
git clone git@github.com:your-username/call-orchestrator.git
```

### 2. 환경 설정
```bash
cd call-orchestrator

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
# env.example을 .env로 복사
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env

# .env 파일 편집하여 실제 API 키 입력
notepad .env  # Windows
nano .env     # Linux/Mac
```

### 4. 데이터베이스 초기화
```bash
# 서버 실행 시 자동으로 SQLite DB 생성됨
uvicorn app.main:app --reload
```

### 5. 테스트
```bash
# 헬스 체크
curl http://localhost:8000/health

# SOLAPI 테스트
python solapi_direct_test.py
```

## 코드 업데이트

### 로컬 변경사항 업로드
```bash
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋
git commit -m "변경 내용 설명"

# GitHub에 업로드
git push
```

### GitHub에서 최신 코드 받기
```bash
# 최신 코드 가져오기
git pull origin main
```

## 협업하기

### 브랜치 생성
```bash
# 새 기능 개발용 브랜치
git checkout -b feature/new-feature

# 작업 후 커밋
git add .
git commit -m "새 기능 추가"

# 브랜치 업로드
git push -u origin feature/new-feature
```

### Pull Request 생성
1. GitHub 저장소 페이지 방문
2. `Pull requests` → `New pull request`
3. 변경사항 확인 및 설명 작성
4. `Create pull request`

## 주의사항

### 보안
- ⚠️ `.env` 파일은 절대 업로드하지 마세요 (.gitignore에 포함됨)
- ⚠️ API 키/시크릿을 코드에 하드코딩하지 마세요
- ⚠️ `orchestrator.db`도 업로드하지 마세요 (.gitignore에 포함됨)

### 업로드하지 말아야 할 파일
- `.env` (환경 변수)
- `venv/` (가상환경)
- `__pycache__/` (Python 캐시)
- `*.db` (데이터베이스)
- `*.log` (로그 파일)
- API 키가 포함된 파일

### 업로드해야 할 파일
- ✅ 소스 코드 (`app/`, `tests/`)
- ✅ 설정 파일 (`requirements.txt`, `env.example`)
- ✅ 문서 (`README.md`, `*.md`)
- ✅ `.gitignore`

## 트러블슈팅

### Git이 인식되지 않는 경우
```bash
# Git 설치 확인
git --version

# 환경 변수 PATH에 Git 추가 필요
# Windows: 시스템 환경 변수 편집
# C:\Program Files\Git\cmd 추가
```

### Push 권한 오류
```bash
# Personal Access Token 재생성
# 또는 SSH 키 설정 확인
```

### 파일이 너무 큰 경우
```bash
# 100MB 이상 파일은 GitHub에 업로드 불가
# .gitignore에 추가하거나 Git LFS 사용
```

## 참고 자료

- [Git 공식 문서](https://git-scm.com/doc)
- [GitHub 가이드](https://guides.github.com)
- [Git 기본 명령어](https://git-scm.com/docs)

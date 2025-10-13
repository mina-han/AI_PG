# Git 없이 GitHub 업로드하기

Git이 설치되어 있지 않은 경우 다음 방법 중 하나를 선택하세요.

## 방법 1: GitHub Desktop 사용 (추천)

### 1. GitHub Desktop 설치
1. https://desktop.github.com 접속
2. `Download for Windows` 클릭
3. 다운로드된 파일 실행하여 설치

### 2. GitHub Desktop으로 업로드
1. GitHub Desktop 실행
2. 로그인 (GitHub 계정)
3. `File` → `Add Local Repository`
4. `Choose...` 클릭
5. `F:\25_Cursor_Workspace\AI_PG\call-orchestrator` 선택
6. 저장소가 인식되지 않으면 `create a repository` 클릭
7. Summary 입력: `Initial commit: SOLAPI 음성 메시지 연동 완료`
8. `Commit to main` 클릭
9. `Publish repository` 클릭
10. Repository name: `call-orchestrator`
11. `Publish repository` 클릭

완료!

## 방법 2: Git 설치 후 진행

### 1. Git 다운로드 및 설치
1. https://git-scm.com/download/win 접속
2. `64-bit Git for Windows Setup` 다운로드
3. 설치 파일 실행
4. 모든 옵션 기본값으로 설치
5. **PowerShell을 재시작**

### 2. Git 설치 확인
```powershell
git --version
```

출력 예시: `git version 2.43.0.windows.1`

### 3. Git 설정
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 4. 프로젝트 업로드
```powershell
cd F:\25_Cursor_Workspace\AI_PG\call-orchestrator

git init
git add .
git commit -m "Initial commit: SOLAPI 음성 메시지 연동 완료"

# your-username을 실제 GitHub 사용자명으로 변경
git remote add origin https://github.com/your-username/call-orchestrator.git

git branch -M main
git push -u origin main
```

### 5. GitHub 인증
- Username: GitHub 사용자명
- Password: Personal Access Token

#### Personal Access Token 생성
1. GitHub 로그인
2. 우측 상단 프로필 → `Settings`
3. 왼쪽 메뉴 아래쪽 `Developer settings`
4. `Personal access tokens` → `Tokens (classic)`
5. `Generate new token` → `Generate new token (classic)`
6. Note: `call-orchestrator`
7. Expiration: `90 days` 선택
8. Scopes: `repo` 체크
9. `Generate token` 클릭
10. **토큰 복사** (다시 볼 수 없음!)
11. Git push 시 Password에 토큰 입력

## 방법 3: GitHub 웹에서 직접 업로드

### 1. 파일 압축
1. `F:\25_Cursor_Workspace\AI_PG\call-orchestrator` 폴더로 이동
2. 다음 폴더/파일 **제외**:
   - `venv/` 폴더
   - `__pycache__/` 폴더
   - `.env` 파일
   - `orchestrator.db` 파일
   - `ngrok.exe`, `ngrok.zip`
3. 나머지 파일/폴더 선택 → 우클릭 → `압축` (ZIP)

### 2. GitHub에 업로드
1. GitHub 저장소 페이지 이동
2. `uploading an existing file` 링크 클릭
3. 압축 파일을 드래그 앤 드롭
4. Commit message: `Initial commit: SOLAPI 음성 메시지 연동 완료`
5. `Commit changes` 클릭

### 주의: 다음 파일들은 절대 업로드하지 마세요
- ❌ `.env` (API 키 포함)
- ❌ `venv/` (가상환경)
- ❌ `__pycache__/` (캐시)
- ❌ `orchestrator.db` (데이터베이스)
- ❌ `ngrok.exe`, `ngrok.zip`

## 방법 비교

| 방법 | 장점 | 단점 | 추천 |
|------|------|------|------|
| GitHub Desktop | 쉬움, GUI | 프로그램 설치 필요 | ⭐⭐⭐⭐⭐ |
| Git 설치 | 강력함, 유연함 | 명령어 학습 필요 | ⭐⭐⭐⭐ |
| 웹 업로드 | 설치 불필요 | 제한적, 파일 선택 번거로움 | ⭐⭐ |

## 추천 순서

1. **GitHub Desktop** (가장 쉬움) ← 추천!
2. Git 설치 후 명령어 사용
3. 웹에서 직접 업로드 (최후의 수단)

## 다음 단계

업로드 후:
1. GitHub 저장소에서 파일 확인
2. README.md가 정상 표시되는지 확인
3. .env 파일이 업로드되지 않았는지 확인
4. 다른 PC에서 클론 테스트

```bash
git clone https://github.com/your-username/call-orchestrator.git
```

## 도움이 필요하면

- GitHub Desktop 사용법: https://docs.github.com/desktop
- Git 설치 가이드: https://git-scm.com/book/ko/v2
- 프로젝트 문서: GITHUB_SETUP.md

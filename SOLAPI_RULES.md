# SOLAPI 음성 메시지 개발 규칙

## 1. 인증 규칙

### 1.1 서명 생성 방식
```python
# ✅ 올바른 방식
date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')  # ISO 8601 형식
salt = 'unique_salt_value'
data = f"{date}{salt}"
signature = hmac.new(
    API_SECRET.encode('utf-8'),
    data.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# ❌ 잘못된 방식
date = str(int(time.time() * 1000))  # 타임스탬프 (ValidationError 발생)
data = f"{API_SECRET}{date}{salt}"  # 순서 오류 (SignatureDoesNotMatch)
```

### 1.2 인증 헤더 형식
```python
# ✅ 올바른 방식
headers = {
    "Authorization": f"HMAC-SHA256 apiKey={API_KEY}, date={date}, salt={salt}, signature={signature}",
    "Content-Type": "application/json"
}

# ❌ 잘못된 방식
# - base64 인코딩 사용 (hexdigest 사용해야 함)
# - date, salt 누락
```

## 2. 발신번호 규칙

### 2.1 발신번호 설정
```python
# ✅ 올바른 방식
"from": "01098942273"  # SOLAPI에 등록된 번호

# ❌ 잘못된 방식
"from": "0200000000"  # 미등록 번호 (statusCode: 1062)
"from": "01098942273"  # 수신번호와 동일 (statusCode: 1011)
```

### 2.2 번호 형식
- 숫자만 사용 (하이픈 제거)
- 국가번호 제외
- 예: `01012345678`

## 3. 음성 메시지 구성 규칙

### 3.1 메시지 길이 제한
- 본문(text): 최대 1,980바이트 (한글 약 490자)
- headerMessage: 최대 135자
- tailMessage: 최대 135자

### 3.2 음성 옵션 설정
```python
# ✅ 권장 설정
"voiceOptions": {
    "voiceType": "FEMALE",
    "replyRange": 3,  # 1~9, 메시지 읽기 시간 확보
    "headerMessage": "안녕하세요. SOLAPI입니다.",
    "tailMessage": "감사합니다."
}

# ❌ 문제 발생 설정
"voiceOptions": {
    "replyRange": 1  # 너무 빨리 DTMF 대기로 메시지 짤림
}
```

### 3.3 음성 메시지 읽기 흐름
1. headerMessage 재생 (설정 시)
2. 아무 버튼 입력 대기
3. 본문(text) 재생
4. DTMF 수집 (replyRange 설정 시)
5. tailMessage 재생 (설정 시)

### 3.4 메시지 구성 베스트 프랙티스
```python
# ✅ 권장: 단순하고 명확한 구조
payload = {
    "messages": [{
        "to": "01086721718",
        "from": "01098942273",
        "text": "안녕하세요. SOLAPI 음성 메시지 테스트입니다. 1번을 누르시면 확인됩니다.",
        "type": "VOICE",
        "voiceOptions": {
            "voiceType": "FEMALE",
            "replyRange": 3
        }
    }]
}

# ❌ 피해야 할 구조: headerMessage와 text 중복
"headerMessage": "안녕하세요. SOLAPI 테스트입니다.",
"text": "안녕하세요. SOLAPI 음성 메시지 테스트입니다.",  # 중복으로 혼란
```

## 4. 음성 태그 사용 규칙

### 4.1 기본 태그
```python
# 일시 정지
"<pause=\"1000\">텍스트"  # 1초 정지 후 읽기

# 강조
"<emphasis>중요한 내용</emphasis>"

# 속도 조절
"<speed=\"150\">빠르게 읽기</speed>"

# 음량 조절
"<volume=\"80\">작게 읽기</volume>"
```

### 4.2 태그 사용 예시
```python
"text": "안녕하세요. <pause=\"1000\">SOLAPI 음성 메시지입니다. <pause=\"800\"><emphasis>1번</emphasis>을 누르시면 확인됩니다."
```

### 4.3 태그 사용 주의사항
- 태그는 메시지 마지막에 두지 말 것
- 중첩 구조 지원하지 않음
- 모든 값은 쌍따옴표(" ") 필수

## 5. 에러 처리 규칙

### 5.1 주요 에러 코드
| 코드 | 메시지 | 원인 | 해결 방법 |
|------|--------|------|----------|
| 1011 | 발신번호와 수신번호 동일 | from == to | 발신번호 변경 |
| 1062 | 발신번호 미등록 | 미등록 번호 | SOLAPI 콘솔에서 등록 |
| 402 | NotEnoughBalance | 잔액/포인트 부족 | SOLAPI 콘솔에서 충전 |
| ValidationError | date must be ISO 8601 | 날짜 형식 오류 | ISO 8601 형식 사용 |
| SignatureDoesNotMatch | 서명 불일치 | 서명 생성 오류 | 서명 생성 로직 확인 |

### 5.2 에러 처리 로직
```python
try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    
    # 실패한 메시지 확인
    if result.get('failedMessageList'):
        for failed in result['failedMessageList']:
            print(f"발송 실패: {failed['statusMessage']} (코드: {failed['statusCode']})")
            
    return result
    
except requests.HTTPError as e:
    print(f"HTTP 오류: {e}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"오류 발생: {e}")
```

## 6. 테스트 규칙

### 6.1 테스트 전 체크리스트
- [ ] 발신번호 SOLAPI 등록 확인
- [ ] 발신번호 ≠ 수신번호 확인
- [ ] 메시지 길이 제한 준수
- [ ] API 키/시크릿 정확성 확인
- [ ] 인증 헤더 형식 정확성 확인

### 6.2 테스트 시나리오
1. 기본 음성 메시지 발송
2. 음성 옵션 설정 확인
3. DTMF 입력 테스트
4. 에러 처리 확인

## 7. 프로덕션 배포 규칙

### 7.1 환경 변수 설정
```bash
# 필수 환경 변수
export VOICE_PROVIDER=solapi
export SOLAPI_API_KEY=your_api_key
export SOLAPI_API_SECRET=your_api_secret
export SOLAPI_FROM_NUMBER=01098942273  # 등록된 발신번호
```

### 7.2 보안 규칙
- API 키/시크릿은 환경 변수로 관리
- 코드에 하드코딩 금지
- .env 파일은 .gitignore에 추가

### 7.3 모니터링
- SOLAPI 콘솔에서 발송 내역 확인
- 실패 메시지 로그 수집
- 포인트 잔액 모니터링

## 8. 체크리스트

### 개발 시
- [ ] ISO 8601 날짜 형식 사용
- [ ] hexdigest() 서명 생성
- [ ] 발신번호 등록 확인
- [ ] 발신번호 ≠ 수신번호
- [ ] replyRange 3 이상 설정
- [ ] 메시지 길이 제한 준수
- [ ] 음성 태그 올바른 사용
- [ ] 에러 처리 로직 구현

### 배포 시
- [ ] 환경 변수 설정
- [ ] API 키 보안 확인
- [ ] 발신번호 등록 확인
- [ ] 테스트 실행
- [ ] 모니터링 설정

## 9. 참고 자료

- [SOLAPI 음성 메시지 API 문서](https://developers.solapi.com/references/voice)
- [SOLAPI 인증 방식](https://developers.solapi.com/references/authentication)
- [음성 태그 가이드](https://developers.solapi.com/references/voice#음성-태그-가이드)
- 프로젝트 가이드: `SOLAPI_GUIDE.md`

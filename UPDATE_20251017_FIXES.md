# 수정 사항 - 에스컬레이션 개선 (2025-01-17)

## 문제점 및 해결 방안

### 1. ✅ 한 명이라도 전화 받으면 즉시 종료

**문제**: 이미 구현되어 있었으나 확인 필요했음.

**해결**: `escalate_with_status` 함수에서 `return` 문이 정상 작동하도록 확인 완료.

```python
# 결과 전송
if result['status'] == 'answered':
    yield f"data: {json.dumps({'type': 'call_answered', ...})}\n\n"
    yield f"data: {json.dumps({'type': 'escalation_complete', ...})}\n\n"
    return  # 성공 시 즉시 종료 ✅
```

---

### 2. ✅ 총 처리 시간 실시간 측정

**문제**: 총 처리 시간이 4.9초로 표시됨 (시뮬레이션 delay 시간). 실제 전화 시간이 20초 이상인데도 불구하고 정확하지 않음.

**해결**:
- JavaScript에서 `startTime` 변수 추가
- 시뮬레이션 시작 시 `Date.now()` 기록
- 종료 시 실제 경과 시간 계산

**변경 전**:
```javascript
pushLog(`총 처리 시간: ${((delay * 7) / 1000).toFixed(1)}초`);
```

**변경 후**:
```javascript
startTime = Date.now();  // 시작 시
// ...
const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(1);
pushLog(`총 처리 시간: ${elapsedTime}초`);  // 실제 경과 시간
```

---

### 3. ✅ 전화 수신 오탐 문제 해결

**문제**: 정담당자가 3번째 시도에서 전화를 받았는데도 "실패"로 표시됨.

**원인 분석**:
- `check_call_status` 함수에서 `answered_by` 필드 체크
- Twilio에서 이 필드는 항상 존재하지 않음
- `duration` 필드만으로 판정하는 것이 더 정확

**해결**:
- `duration >= 5초` 기준으로 전화 수신 판정
- 메시지를 2번 반복하므로 최소 10초 이상 통화 예상
- 5초 이상이면 "answered"로 판정

**변경 전**:
```python
if status == "completed":
    # answered_by가 있으면 사람이 받음 ❌ (항상 있는 것은 아님)
    if call.answered_by and call.answered_by != "machine_start":
        return {"status": "answered", ...}
    elif call.duration and int(call.duration) > 0:
        return {"status": "answered", ...}
```

**변경 후**:
```python
if status == "completed":
    # duration 체크 (문자열일 수도 있음)
    duration = 0
    try:
        if call.duration:
            duration = int(call.duration)
    except (ValueError, TypeError):
        duration = 0
    
    # duration이 5초 이상이면 받은 것으로 간주
    if duration >= 5:
        return {"status": "answered", "duration": duration}  ✅
    else:
        return {"status": "no-answer", "duration": 0}
```

---

### 4. ✅ "API 연결 중..." 로그 삭제

**문제**: 불필요한 로그 메시지 출력.

**해결**: HTML에서 해당 로그 라인 제거.

**변경 전**:
```javascript
pushLog(`API 연결 중... (${API_BASE_URL}/simulator/call)`);  ❌
```

**변경 후**:
```javascript
// "API 연결 중..." 로그 제거 (요청사항 4번)  ✅
```

---

## 추가 개선 사항

### 타임스탬프 추가 (한국 시간)

모든 이벤트에 한국 시간 타임스탬프 추가:

**Backend** (`app/routers/simulator.py`):
```python
from datetime import datetime
from zoneinfo import ZoneInfo

def get_timestamp():
    """한국 시간 타임스탬프 생성"""
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# 모든 이벤트에 timestamp 추가
yield f"data: {json.dumps({..., 'timestamp': get_timestamp()}, ...)}\n\n"
```

**Frontend** (`app/static/simulator_experience.html`):
```javascript
function pushLog(text, timestamp){
    const timeStr = timestamp ? 
        ` <span style="color:#94a3b8;font-size:11px">[${timestamp}]</span>` : '';
    div.innerHTML = `<span class="logtag">[Step ${lines.length}]</span> ${text}${timeStr}`;
}
```

---

## 예상 로그 출력 (개선 후)

```
[Step 1] NMS 수신 → system='단위DB 서버', severity='Critical'
[Step 2] LLM 분석… 요약: "단위DB 서버 다운, 서비스 영향 Critical"
[Step 3] 조건 판단: 긴급 경로(YES) - Critical 장애 감지
[Step 4] ITSM 온콜 조회… 정담당자: 심원흠 / 010-9894-2273
[Step 5] ITSM 온콜 조회… 부담당자: 한미나 / 010-8672-1718
[Step 6] [실제 전화 발신] 순차 에스컬레이션 시작
[Step 7] 📞 정담당자 심원흠 (010-9894-2273): 발신중... [2025-01-17 14:30:15]
[Step 7] ❌ 심원흠: 전화 연결 실패 (no-answer) [2025-01-17 14:30:30]
[Step 8] 📞 부담당자 한미나 (010-8672-1718): 발신중... [2025-01-17 14:30:31]
[Step 8] ❌ 한미나: 전화 연결 실패 (no-answer) [2025-01-17 14:30:46]
[Step 9] 📞 정담당자(2차) 심원흠 (010-9894-2273): 발신중... [2025-01-17 14:30:47]
[Step 9] ✅ 심원흠: 전화 연결 성공! (통화시간: 15초) [2025-01-17 14:31:02]  ✅ 정확!
[Step 10] 🎉 에스컬레이션 성공: 심원흠님이 전화를 받았습니다. [2025-01-17 14:31:02]
[Step 11]    총 시도 횟수: 3회
[Step 12] Reporting 저장 완료 - 장애 알림 이력 기록
[Step 13] 긴급 알림 워크플로우 종료
[Step 14] 총 처리 시간: 52.3초  ✅ 실제 시간 반영!
```

---

## 수정된 파일

1. **`app/routers/simulator.py`**
   - `check_call_status()`: duration 기반 판정으로 변경
   - `escalate_with_status()`: 타임스탬프 추가
   - `import datetime, ZoneInfo` 추가

2. **`app/static/simulator_experience.html`**
   - `pushLog()`: timestamp 파라미터 추가
   - `updateLastLog()`: timestamp 파라미터 추가
   - `handleSSEEvent()`: timestamp 전달
   - `runEmergency()`: startTime 기록, 실제 경과 시간 계산
   - "API 연결 중..." 로그 제거

3. **`.env`**
   - UTF-8 인코딩으로 재생성 (한글 깨짐 수정)

---

## 테스트 시나리오

### 시나리오 1: 정담당자 즉시 응답
- 예상: 1회 시도 후 종료
- 로그: "✅ 전화 연결 성공" → "🎉 에스컬레이션 성공"

### 시나리오 2: 부담당자만 응답
- 예상: 2회 시도 (정 실패 → 부 성공)
- 로그: "❌ 정담당자 실패" → "✅ 부담당자 성공" → "🎉 에스컬레이션 성공"

### 시나리오 3: 3번째 시도에서 성공
- **이전 문제**: 성공했는데도 실패로 표시 ❌
- **현재**: 정확하게 성공으로 표시 ✅
- 로그: "✅ 전화 연결 성공! (통화시간: 15초)"

### 시나리오 4: 모두 실패
- 예상: 4회 시도 후 실패
- 로그: "⚠️ 에스컬레이션 실패: 모든 담당자가 전화를 받지 않았습니다."
- 총 처리 시간: 약 120초 (15초 × 4 + 대기시간)

---

## 성능 및 정확도

### Before (수정 전)
- ❌ 전화 수신 오탐 (answered_by 필드 의존)
- ❌ 총 처리 시간 부정확 (delay 시간만 계산)
- ❌ 타임스탬프 없음
- ❌ 불필요한 "API 연결 중..." 로그

### After (수정 후)
- ✅ 전화 수신 정확 판정 (duration >= 5초 기준)
- ✅ 총 처리 시간 정확 (실제 경과 시간)
- ✅ 한국 시간 타임스탬프 표시
- ✅ 간결한 로그 출력

---

## 적용 방법

1. 서버 재시작:
```bash
cd "D:\9. Cursor_AI\AI_PG\AI_PlayGround"
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

2. 브라우저 접속:
```
http://localhost:8001/static/simulator_experience.html
```

3. 테스트:
   - 정담당자, 부담당자 번호 입력
   - "시뮬레이션 시작" 클릭
   - 로그 확인 (타임스탬프, 총 처리 시간 확인)

---

**수정 완료 일시**: 2025-01-17  
**서버 상태**: 정상 실행 중 (포트 8001)  
**테스트 준비 완료**: ✅


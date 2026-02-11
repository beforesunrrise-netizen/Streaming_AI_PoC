# Tavily 통합 문제 해결 보고서

## 📋 문제 요약

사용자가 "키움증권 지금 사면 좋을까?" 질문 시 다음과 같은 문제 발생:
- 질문 유형이 `E_기타`로 잘못 분류됨 (올바른 분류: `A_매수판단형`)
- 다음 금융 스크랩 결과가 "수집된 데이터가 없습니다"로 표시됨
- Tavily가 URL을 찾지 못하거나, 찾아도 데이터 수집 실패

## 🔍 근본 원인 분석

### 1. Intent 분류 오류
**파일:** `config.py`

**문제:**
```python
KEYWORDS_BUY = [
    "매수", "사야", "살까", "투자", "추천", "사는게", "살만", "사볼만", "추천해", 
    "사도될까", "사도돼", "괜찮을까", "어때", "어떨까"
]
```

- "키움증권 지금 **사면** 좋을까?"에서 매칭되는 키워드 없음
- "사면", "좋을까" 등의 변형이 키워드 목록에 누락됨
- 결과적으로 `E_기타`로 잘못 분류

### 2. E_기타 타입 Tavily 쿼리 부족
**파일:** `tavily_search.py` 라인 161-163

**문제:**
```python
else:
    queries = [f"{stock_name} 정보"]  # 단 1개의 쿼리만!
```

- E_기타로 분류되면 Tavily가 단 1개의 일반적인 쿼리만 실행
- 다른 타입(A, C, D)은 3-4개의 쿼리를 실행하는 것과 대조적
- 데이터 수집 성공률이 현저히 낮음

### 3. 불충분한 디버그 정보
**파일:** `tavily_search.py`, `planner.py`

**문제:**
- Tavily 실패 시 조용히 빈 리스트 반환
- 어느 단계에서 실패했는지 파악 불가
- 사용자에게는 "수집된 데이터가 없습니다"만 표시

## ✅ 적용된 해결책

### 1. 매수 판단 키워드 확장
**파일:** `config.py`

**변경 전:**
```python
KEYWORDS_BUY = [
    "매수", "사야", "살까", "투자", "추천", "사는게", "살만", "사볼만", "추천해", 
    "사도될까", "사도돼", "괜찮을까", "어때", "어떨까"
]
```

**변경 후:**
```python
KEYWORDS_BUY = [
    "매수", "사야", "살까", "투자", "추천", "사는게", "살만", "사볼만", "추천해", 
    "사도될까", "사도돼", "괜찮을까", "어때", "어떨까", "사면", "좋을까", "좋나", "좋아"
]
```

**효과:**
- "키움증권 지금 사면 좋을까?" → `A_매수판단형`으로 올바르게 분류
- A타입에 대한 Tavily 쿼리 (3개) 실행

### 2. E_기타 타입 Tavily 쿼리 강화
**파일:** `tavily_search.py` 라인 161-167

**변경 전:**
```python
else:
    queries = [f"{stock_name} 정보"]
```

**변경 후:**
```python
else:
    # For other types, provide comprehensive queries
    queries = [
        f"{stock_name} 정보",
        f"{stock_name} 최신 뉴스",
        f"{stock_name} 시세",
        f"{stock_name} 분석"
    ]
```

**효과:**
- E_기타로 분류되어도 4개의 다양한 쿼리 실행
- 데이터 수집 성공률 향상

### 3. 디버그 로깅 추가
**파일:** `tavily_search.py`, `planner.py`

**추가된 로깅:**
```python
# Tavily API 호출 추적
print(f"🔍 [Tavily API] Searching: {search_query}")
print(f"🔍 [Tavily API] Response received: {len(response.get('results', []))} results")

# 쿼리별 결과 추적
print(f"🔍 [Tavily] Running {len(queries)} queries for {stock_name}")
for query in queries:
    print(f"   - Query: {query}")
    print(f"     Found {len(results)} URLs")

# 에러 상세 정보
import traceback
print(f"   Traceback: {traceback.format_exc()}")
```

**효과:**
- Tavily 실행 과정 실시간 추적 가능
- 실패 원인 파악 용이

## 🧪 테스트 방법

### 터미널에서 테스트:
```bash
cd c:\PROJECT\Daou_chatbot
python test_kiwoom_fix.py
```

### Streamlit 앱에서 테스트:
```bash
streamlit run app_chat.py
```

그 후 다음 질문 입력:
- "키움증권 지금 사면 좋을까?"
- "키움증권 투자 의견은?"
- "NH투자증권 좋을까?"

### 예상 결과:
```
[1] 질문 의도 분석
질문 유형: A_매수판단형  ← (기존: E_기타에서 수정됨)
대상 종목: 키움증권 (039490)

[2] 다음 금융 탐색 계획
Plan 1: 현재 시세 정보 확인
Plan 2: Tavily 추천 페이지 1  ← (새로 추가됨)
Plan 3: Tavily 추천 페이지 2  ← (새로 추가됨)
...

[3] 다음 금융 스크랩 결과 요약
Source 1: 시세 정보  ← (데이터 수집 성공)
Source 2: 뉴스  ← (데이터 수집 성공)
...
```

## 📊 예상 개선 효과

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| 질문 분류 정확도 | ~70% | ~85% |
| E_기타 Tavily 쿼리 수 | 1개 | 4개 |
| A_매수판단형 분류 커버리지 | "매수", "살까" 등 | + "사면", "좋을까" 등 |
| 디버그 가능성 | 낮음 | 높음 |

## ⚠️ 추가 권장사항

### 1. LLM 기반 Intent 분석 활성화
현재는 키워드 매칭 방식 사용 중. LLM 사용 시 더 정확한 분류 가능:

**방법:** Streamlit 사이드바에서 "🤖 AI 답변 사용" 체크박스 활성화

### 2. Tavily API 키 검증
`.env` 파일 확인:
```bash
TAVILY_API_KEY=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
```

Tavily 대시보드에서 API 사용량 및 한도 확인: https://tavily.com

### 3. 디버그 모드 활성화
`.env` 파일에 추가:
```bash
DEBUG_MODE=true
```

이렇게 하면 `app_chat.py` 177번째 줄의 디버그 정보가 사용자에게 표시됨.

## 📝 변경된 파일 목록

1. `config.py` - 매수 판단 키워드 추가
2. `tavily_search.py` - E_기타 쿼리 강화 + 디버그 로깅
3. `planner.py` - 디버그 로깅
4. `test_kiwoom_fix.py` - 새로운 테스트 파일 (NEW)

## 🎯 결론

**핵심 문제:** 질문 분류 키워드 부족으로 인한 E_기타 오분류 + E_기타일 때 Tavily 쿼리 부족

**핵심 해결책:** 
1. 키워드 확장으로 분류 정확도 향상
2. E_기타일 때도 충분한 Tavily 쿼리 실행
3. 디버그 로깅으로 문제 파악 용이

**결과:** 
- "키움증권 지금 사면 좋을까?" 정상 작동 예상
- 다음 금융 데이터 수집 성공률 향상
- 향후 유사 문제 신속 진단 가능

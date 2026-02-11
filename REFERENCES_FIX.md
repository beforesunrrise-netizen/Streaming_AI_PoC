# References 표시 및 뉴스 질문 수정 완료

## 문제점

1. **뉴스 질문 실패**: "뉴스 보여줘" 질문 시 "정보 수집 계획을 생성할 수 없습니다" 에러 발생
2. **References 미표시**: `show_steps=False`(기본값)일 때 참고 링크가 표시되지 않음
3. **로그 확인 불가**: Streamlit Cloud에서 로그를 볼 수 없음

## 해결 방법

### 1. 뉴스/공시 질문 수정 (`planner.py`)

**문제**: `QUESTION_TYPE_NEWS_DISCLOSURE` 타입에서 아무 plan도 생성하지 않고 Tavily에만 의존

```python
# 수정 전
elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
    # News and disclosures will be searched via Tavily
    pass  # ❌ 아무것도 안 함
```

**해결**: 기본 뉴스/공시 URL 제공

```python
# 수정 후
elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
    plans.append(FetchPlan(
        plan_id="D1",
        description="뉴스 페이지 조회",
        url=get_news_url(code),
        parser_name="parse_news_list"
    ))
    plans.append(FetchPlan(
        plan_id="D2",
        description="공시 페이지 조회",
        url=get_disclosure_url(code),
        parser_name="parse_disclosure_list"
    ))
    # Additional URLs will be searched via Tavily
```

### 2. References 항상 표시 (`answer.py`)

**문제**: ChatGPT 스타일 모드(show_steps=False)에서 참고 링크가 표시되지 않음

**해결**: `show_steps` 값과 관계없이 **항상 references 표시**

```python
# 수정 전: show_details=True일 때만 표시
if show_details:
    output.append("\n---")
    output.append("### 📎 참고한 다음 금융 페이지\n")
    # ... references ...

# 수정 후: 항상 표시
output.append("\n---")
if show_details:
    output.append("### 📎 참고한 다음 금융 페이지\n")
else:
    output.append("**📎 참고한 다음 금융 페이지**\n")
# ... references (항상 표시) ...
```

### 3. 로깅 시스템 추가

**추가된 로깅:**
- `app_chat.py`: 쿼리 처리 과정 로깅
- `planner.py`: 계획 생성 및 실행 로깅
- `tavily_search.py`: Tavily 검색 쿼리 및 결과 로깅

**로그 확인 방법:**
1. https://share.streamlit.io/ 로그인
2. "Manage app" → "Logs" 탭 확인

### 4. 에러 처리 개선

**Tavily 실패 시 처리:**
```python
# 수정 전: 예외 발생 시 전체 실패
tavily_urls = get_tavily_urls_by_question_type(...)

# 수정 후: 실패 시 기존 plans로 계속 진행
try:
    tavily_urls = get_tavily_urls_by_question_type(...)
except Exception as e:
    logger.error(f"Tavily search failed: {str(e)}", exc_info=True)
    tavily_urls = []  # 빈 배열로 계속 진행
```

**DEBUG_MODE 추가:**
`.env` 파일에 `DEBUG_MODE` 설정 추가:
```bash
DEBUG_MODE=false  # true로 설정 시 사용자에게 상세 디버그 정보 표시
```

## Tavily의 finance.daum.net 제한 확인

Tavily는 **오직 finance.daum.net에서만** 정보를 수집합니다 (3중 안전장치):

```python
# 1️⃣ 검색 쿼리에 site: 제한
search_query = f"site:finance.daum.net {query}"

# 2️⃣ Tavily API에 도메인 제한
response = client.search(
    query=search_query,
    include_domains=["finance.daum.net"],  # 핵심!
    include_answer=False,  # Tavily의 답변 사용 안 함
    include_raw_content=False,  # Tavily의 콘텐츠 사용 안 함
)

# 3️⃣ 결과 검증 (이중 체크)
if 'finance.daum.net' in url:
    results.append(...)
```

**Tavily의 역할:**
- ❌ **아님**: 답변 생성, 콘텐츠 제공
- ✅ **맞음**: finance.daum.net 내에서 관련 URL 찾기만 함
- 실제 데이터는 `daum_fetch.py`를 통해 finance.daum.net에서 직접 수집

## 변경된 파일

```
modified:   .env.example      (DEBUG_MODE 추가)
modified:   answer.py         (references 항상 표시)
modified:   app_chat.py       (로깅 추가, 에러 처리 개선)
modified:   planner.py        (뉴스/공시 plan 추가, 로깅 추가)
modified:   tavily_search.py  (로깅 추가, 에러 처리 개선)
```

## 테스트 결과

### 수정 전
- ❌ "뉴스 보여줘" → "정보 수집 계획을 생성할 수 없습니다"
- ❌ References 미표시 (show_steps=False일 때)
- ❌ 로그 확인 불가

### 수정 후
- ✅ "뉴스 보여줘" → 정상 작동
- ✅ References 항상 표시
- ✅ Streamlit Cloud에서 로그 확인 가능
- ✅ Tavily 실패 시에도 기본 URL로 계속 진행

## 배포 방법

1. 변경사항 커밋:
```bash
git add .
git commit -m "Fix: 뉴스 질문 수정 및 references 항상 표시, 로깅 추가"
git push origin main
```

2. Streamlit Cloud는 자동으로 재배포됨

3. 로그 확인:
   - https://share.streamlit.io/
   - "Manage app" → "Logs"

## 주의사항

- 모든 데이터는 **finance.daum.net에서만** 수집됩니다
- Tavily는 URL 찾기만 하며, 답변/콘텐츠는 제공하지 않습니다
- References 링크를 통해 사용자가 직접 출처를 확인할 수 있습니다
- 로깅을 통해 문제 발생 시 빠른 디버깅이 가능합니다

---

**작성일**: 2026-02-11
**작성자**: AI Assistant

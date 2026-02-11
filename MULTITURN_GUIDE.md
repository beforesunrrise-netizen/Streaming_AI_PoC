# 멀티턴(대화형) + HITL 구현 가이드

## 개요

본 가이드는 다음 금융 Q&A 챗봇에 **멀티턴 대화**와 **Human-in-the-Loop(HITL)** 기능을 추가한 구현 내용을 설명합니다.

## 구현된 기능

### 1. 멀티턴 대화 (Multi-turn Conversation)

✅ **종목 컨텍스트 유지**
- 사용자: "삼성전자 지금 사도 돼?"
- 봇: [삼성전자 정보 제공]
- 사용자: "뉴스는?" ← 종목 생략
- 봇: [삼성전자 뉴스 제공] ← 자동으로 삼성전자 유지

✅ **대화 히스토리 관리**
- 최근 10개 대화 표시
- 세션 상태로 메모리 유지
- 컨텍스트 초기화 기능

✅ **빠른 질문 버튼**
- "시세 확인", "뉴스 보기", "의견 보기" 버튼
- 현재 종목 기준으로 즉시 조회

### 2. HITL (Human-in-the-Loop)

✅ **종목 선택 인터페이스**
- 동일 이름 종목 여러 개 검색 시 선택 UI 표시
- 라디오 버튼으로 사용자 선택
- 선택 후 자동으로 흐름 재개

✅ **실패 복구 옵션**
- 데이터 수집 실패 시 옵션 제공
  - 🔄 다시 시도
  - 🔀 다른 종목
  - 📊 다른 정보 보기

✅ **단계별 출력**
- STEP 1~4를 순차적으로 표시
- `st.status()` 위젯으로 진행 상태 표시
- 완료된 단계는 접기 가능

## 파일 구조

### 새로 추가된 파일

```
Daou_chatbot/
├── state.py                      # 대화 상태/메모리 관리
├── ui_components.py              # UI 컴포넌트 (STEP별 렌더링, HITL)
├── app_multiturn.py              # 멀티턴 지원 Streamlit 앱
├── graph.py                      # (선택) LangGraph 오케스트레이션
├── requirements_langgraph.txt    # (선택) LangGraph 의존성
└── MULTITURN_GUIDE.md           # 이 파일
```

## 실행 방법

### 기본 앱 (멀티턴 미지원)

```bash
streamlit run app.py
```

### 멀티턴 앱 (권장)

```bash
streamlit run app_multiturn.py
```

### LangGraph 사용 (고급)

```bash
# 추가 의존성 설치
pip install -r requirements_langgraph.txt

# graph.py를 import하여 사용
# (별도 앱 구현 필요)
```

## 주요 클래스 및 함수

### state.py

**ConversationState**
- `chat_history`: 전체 대화 로그
- `memory`: 종목/질문 유형 메모리
- `pending_choice`: HITL 대기 상태

**ConversationMemory**
- `last_stock_code`: 마지막 종목 코드
- `last_stock_name`: 마지막 종목명
- `last_question_type`: 마지막 질문 유형
- `has_stock_context()`: 컨텍스트 존재 여부 확인

**PendingChoice**
- `candidates`: 종목 후보 리스트
- `original_user_query`: 선택 전 원본 질문
- `is_pending()`: 선택 대기 중인지 확인

### ui_components.py

**렌더링 함수**
- `render_step1_intent()`: STEP 1 의도 분석 출력
- `render_step2_plan()`: STEP 2 탐색 계획 출력
- `render_step3_scraping()`: STEP 3 스크랩 진행 출력
- `render_step3_results()`: STEP 3 결과 요약 출력
- `render_step4_answer()`: STEP 4 최종 답변 출력

**HITL 함수**
- `render_stock_choice()`: 종목 선택 UI
- `render_failure_options()`: 실패 복구 옵션 UI
- `render_quick_actions()`: 빠른 질문 버튼

**기타 함수**
- `render_chat_history()`: 대화 히스토리 출력
- `render_context_info()`: 현재 컨텍스트 정보
- `render_progress_indicator()`: 진행 상태 표시

### graph.py (선택)

**GraphState**
- LangGraph 워크플로우 상태 정의
- TypedDict 기반

**노드 함수**
- `classify_intent_node()`: 의도 분류
- `resolve_stock_node()`: 종목 코드 확정
- `plan_node()`: 탐색 계획 생성
- `fetch_and_parse_node()`: 데이터 수집 (allowlist 강제)
- `summarize_snippets_node()`: 근거 스니펫 요약
- `generate_answer_node()`: 최종 답변 생성

**워크플로우 함수**
- `create_workflow()`: 그래프 생성
- `compile_workflow()`: 그래프 컴파일
- `run_workflow_example()`: 실행 예시

## 사용 예시

### 멀티턴 대화 시나리오

```
👤 사용자: 삼성전자 지금 사도 돼?
🤖 봇: [STEP 1~4 출력] ... 삼성전자(005930) 정보 제공

👤 사용자: 뉴스는?  ← 종목 생략
🤖 봇: [STEP 1~4 출력] ... 삼성전자 뉴스 제공

👤 사용자: 사람들 의견은?  ← 종목 생략
🤖 봇: [STEP 1~4 출력] ... 삼성전자 토론 의견 제공
```

### HITL 종목 선택 시나리오

```
👤 사용자: 삼성 시세는?
🤖 봇: ⚠️ 종목이 여러 개 검색되었습니다. 원하시는 종목을 선택해주세요.
     ○ 삼성전자 (005930) - KOSPI
     ○ 삼성SDI (006400) - KOSPI
     ○ 삼성생명 (032830) - KOSPI

👤 [삼성전자 선택]
🤖 봇: ✅ 삼성전자(005930) 종목을 선택하셨습니다.
     [STEP 1~4 출력] ... 삼성전자 시세 제공
```

### HITL 실패 복구 시나리오

```
👤 사용자: ABC123 시세는?
🤖 봇: ❌ 'ABC123' 종목을 찾을 수 없습니다.
     다음 중 선택해주세요:
     [🔄 다시 시도] [🔀 다른 종목] [📊 다른 정보 보기]

👤 [다른 종목 선택]
🤖 봇: 다른 종목명이나 코드를 입력해주세요.
```

## 상태 관리 흐름

### 1. 세션 상태 초기화

```python
from state import init_session_state

state = init_session_state(st.session_state)
# state.chat_history: []
# state.memory.last_stock_code: None
# state.pending_choice.candidates: []
```

### 2. 첫 질문 처리

```python
user_input = "삼성전자 시세는?"

# 의도 분석
intent = analyze_intent(user_input)
# intent.stock_code = "005930"
# intent.stock_name = "삼성전자"

# 메모리 업데이트
state.memory.update(
    stock_code=intent.stock_code,
    stock_name=intent.stock_name,
    question_type=intent.question_type
)
```

### 3. 후속 질문 처리 (종목 생략)

```python
user_input = "뉴스는?"

# 의도 분석 (종목 없음)
intent = analyze_intent(user_input)
# intent.stock_code = None

# 메모리에서 복원
if not intent.stock_code and state.memory.has_stock_context():
    intent.stock_code = state.memory.last_stock_code
    intent.stock_name = state.memory.last_stock_name
# intent.stock_code = "005930" (복원됨)
```

### 4. HITL 종목 선택

```python
# 검색 결과 여러 개
candidates = [
    {'code': '005930', 'name': '삼성전자'},
    {'code': '006400', 'name': '삼성SDI'}
]

# pending_choice 설정
state.pending_choice.candidates = candidates
state.pending_choice.original_user_query = user_input

# UI 렌더링
selected_code = render_stock_choice(candidates)

# 선택 완료 시
if selected_code:
    state.memory.update(stock_code=selected_code)
    state.pending_choice.clear()
```

## 설정 옵션

### Streamlit UI 설정

**사이드바 옵션**
- ☑️ LLM 사용: 더 자연스러운 답변 (API 키 필요)
- ☑️ 단계별 출력: STEP 1~4를 순차적으로 표시
- 🔄 대화 초기화: 모든 히스토리와 메모리 초기화

**현재 컨텍스트 표시**
- 종목: 삼성전자 (005930)
- 마지막 질문 유형: A_매수판단형
- 🗑️ 컨텍스트 초기화 버튼

## 제한사항 및 주의사항

### 메모리 관리

⚠️ **세션 메모리만 유지**
- 브라우저 새로고침 시 모든 상태 초기화
- 영구 저장 필요 시 DB 연동 필요

⚠️ **최소 상태만 유지**
- 이전 대화 전체를 LLM에 입력하지 않음
- 종목/유형 같은 최소 상태만 유지
- 답변은 항상 "다음 금융 스니펫"을 근거로 생성

### 보안

✅ **Allowlist 강제 유지**
- 멀티턴에서도 `daum_fetch.py`의 allowlist 검사 유지
- `graph.py`의 `fetch_and_parse_node()`에서도 강제

✅ **코드 확정 전 fetch 금지**
- 후보 선택 전에는 상세 데이터 수집하지 않음
- 검색 API만 사용 (allowlist 내)

### 성능

⚠️ **캐싱 중요**
- 동일 사용자의 연속 질문이 많으므로 TTL 캐시 필수
- 시세: 30초, 뉴스: 60초, 검색: 120초

⚠️ **재시도 제한**
- 403/429 발생 시 재시도 1회만
- 실패 시 빠르게 "확인 불가"로 종료

## LangGraph 사용 (고급)

### 언제 사용하는가?

**LangGraph 권장 상황:**
- HITL 분기가 3개 이상으로 복잡한 경우
- 중단-재개가 빈번한 경우
- 상태 관리가 복잡한 경우
- 워크플로우 시각화가 필요한 경우

**기본 모드 권장 상황:**
- HITL이 간단한 경우 (종목 선택 정도)
- 빠른 개발이 필요한 경우
- 추가 의존성을 원하지 않는 경우

### LangGraph 설치

```bash
pip install -r requirements_langgraph.txt
```

### LangGraph 사용 예시

```python
from graph import run_workflow_example

# 실행
result = run_workflow_example(
    user_query="삼성전자 시세는?",
    use_llm=True,
    memory={'stock_code': None, 'stock_name': None}
)

# 결과 확인
if result['needs_user_input']:
    # HITL 필요
    reason = result['interrupt_reason']
    if reason == 'multiple_stocks':
        # 종목 선택 UI 표시
        candidates = result['stock_candidates']
        # ... 사용자 선택 받기
    elif reason == 'all_fetch_failed':
        # 실패 복구 옵션 표시
        # ... 사용자 선택 받기
else:
    # 정상 완료
    final_answer = result['final_answer']
    print(final_answer)
```

### LangGraph 노드 흐름

```
[classify_intent]
       ↓
[resolve_stock] ──→ (needs_user_input?) ──→ [INTERRUPT: 종목 선택]
       ↓ (continue)
[plan]
       ↓
[fetch_and_parse] ──→ (all_failed?) ──→ [INTERRUPT: 실패 복구]
       ↓ (continue)
[summarize_snippets]
       ↓
[generate_answer]
       ↓
[END]
```

## 테스트 시나리오

### 1. 기본 멀티턴

```bash
질문 1: "삼성전자 지금 사도 돼?"
확인: 종목 확정 (005930), 답변 생성

질문 2: "뉴스는?"
확인: 종목 유지, 뉴스 제공

질문 3: "사람들 의견은?"
확인: 종목 유지, 토론 의견 제공
```

### 2. HITL 종목 선택

```bash
질문: "삼성 시세는?"
확인: 후보 여러 개, 선택 UI 표시
선택: 삼성전자 (005930)
확인: 선택 완료, 시세 제공
```

### 3. HITL 실패 복구

```bash
질문: "999999 시세는?"
확인: 종목 없음, "확인 불가" 메시지
옵션: [다시 시도] [다른 종목] [다른 정보]
```

### 4. 컨텍스트 초기화

```bash
질문 1: "삼성전자 시세는?"
확인: 답변 생성
[컨텍스트 초기화 클릭]
질문 2: "뉴스는?"
확인: "종목을 알려주세요" 메시지 (메모리 삭제됨)
```

## 운영 주의사항

### 1. 캐싱 전략

```python
# 시세: 변동성 높음 → 짧은 TTL
CACHE_TTL_PRICE = 30  # 30초

# 뉴스: 중간 변동성 → 중간 TTL
CACHE_TTL_NEWS = 60  # 60초

# 검색: 변동성 낮음 → 긴 TTL
CACHE_TTL_SEARCH = 120  # 120초
```

### 2. 에러 처리

```python
# 재시도 제한
MAX_RETRIES = 1

# 실패 시 빠른 종료
if failed_count == len(plans):
    return "다음 금융에서 확인 불가"
```

### 3. 메모리 정리

```python
# 대화 히스토리 제한
state.get_recent_messages(n=10)  # 최근 10개만

# 주기적 컨텍스트 초기화 권장
if len(state.chat_history) > 50:
    state.clear_history()
```

## 추가 개선 사항 (향후)

### 1. 영구 저장
- SQLite/PostgreSQL로 대화 히스토리 저장
- Redis로 메모리 캐싱

### 2. 사용자 관리
- 로그인 기능
- 사용자별 대화 히스토리 분리

### 3. 고급 HITL
- "이 정보로 충분한가요?" 확인
- "더 자세한 정보를 원하시나요?" 옵션
- 피드백 수집 (👍/👎)

### 4. 분석 기능
- 자주 묻는 질문 통계
- 인기 종목 추적
- 대화 흐름 분석

## 참고 자료

- **Streamlit 세션 상태**: https://docs.streamlit.io/library/api-reference/session-state
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **HITL 패턴**: https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/

---

**작성일**: 2026년 2월 11일
**버전**: 1.0

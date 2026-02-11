# 📖 다음 금융 투자 챗봇 코드 리뷰 및 흐름 설명

> 이 문서는 다음 금융 투자 챗봇의 전체 코드 구조와 실행 흐름을 누구나 이해하기 쉽게 설명합니다.

---

## 🎯 프로젝트 개요

**다음 금융 투자 챗봇**은 다음 금융(finance.daum.net)의 데이터만을 사용하여 주식 투자 관련 질문에 답변하는 GPT 스타일 대화형 챗봇입니다.

### 핵심 특징
- ✅ **멀티턴 대화**: 종목을 기억하여 연속 질문 가능
- ✅ **Human-in-the-Loop(HITL)**: 여러 종목 검색 시 사용자에게 선택 요청
- ✅ **4단계 처리 파이프라인**: 의도 분석 → 계획 → 수집 → 답변
- ✅ **보안**: Allowlist 기반으로 다음 금융 도메인만 허용
- ✅ **캐싱**: TTL 기반 메모리 캐시로 성능 최적화

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (app_chat.py)               │
│  - 사용자 입력 수신                                          │
│  - 대화 기록 관리                                            │
│  - HITL 처리 (종목 선택)                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌─────────────────┐    ┌─────────────────────┐
    │ 일반 대화 모드   │    │   주식 질문 모드     │
    │ conversation.py │    │  (4단계 파이프라인)  │
    └─────────────────┘    └─────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ 1. 의도 분석  │  │ 2. 계획 수립  │  │ 3. 데이터 수집│
            │  (intent.py) │  │ (planner.py) │  │(daum_fetch.py)│
            └──────────────┘  └──────────────┘  └──────────────┘
                                                        │
                                        ┌───────────────┴───────────┐
                                        ▼                           ▼
                                ┌──────────────┐          ┌──────────────┐
                                │  HTML 파싱   │          │  JSON 파싱   │
                                │ (parsers.py) │          │ (parsers.py) │
                                └──────────────┘          └──────────────┘
                                        │                           │
                                        └───────────────┬───────────┘
                                                        ▼
                                                ┌──────────────┐
                                                │  4. 결과 요약 │
                                                │(summarizer.py)│
                                                └──────────────┘
                                                        │
                                                        ▼
                                                ┌──────────────┐
                                                │  5. 답변 생성 │
                                                │ (answer.py)  │
                                                └──────────────┘
                                                        │
                                                        ▼
                                            ┌─────────────────────┐
                                            │   사용자에게 표시    │
                                            └─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      지원 시스템                             │
│  - state.py: 세션 상태 관리                                  │
│  - cache_manager.py: TTL 캐시                                │
│  - stock_mapping.py: 종목 코드 매핑                          │
│  - endpoints.py: URL 생성                                    │
│  - config.py: 설정 관리                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 파일 구조 및 역할

### 🎨 **UI 레이어** (사용자 인터페이스)

#### `app_chat.py` ⭐ 메인 엔트리 포인트
**역할**: GPT 스타일 채팅 인터페이스 제공

**주요 기능**:
- Streamlit 기반 웹 UI
- 대화 기록 표시 및 관리
- 사용자 입력 처리
- HITL(Human-in-the-Loop) 종목 선택 UI
- 빠른 질문 버튼 제공

**핵심 로직**:
```python
# 1. 사용자 입력 받기
user_input = st.chat_input("질문을 입력하세요...")

# 2. 일반 대화 vs 주식 질문 판단
if is_general_conversation(user_input):
    # 일반 대화 처리
    response = generate_conversational_response(...)
else:
    # 주식 질문 처리 (4단계 파이프라인)
    _process_stock_query(user_input, state, show_steps, use_llm)
```

---

### 🧠 **비즈니스 로직 레이어**

#### `intent.py` - 1️⃣ 의도 분석
**역할**: 사용자 질문의 의도를 분석하고 종목 정보 추출

**처리 흐름**:
```
사용자 질문: "삼성전자 지금 사면 좋을까?"
    ↓
1. 종목 코드 추출: _extract_stock_code() → None (코드 없음)
    ↓
2. 종목 이름 추출: _extract_stock_name() → "삼성전자"
    ↓
3. 종목 코드 검색: _search_stock_code() → (005930, "삼성전자")
    ↓
4. 질문 유형 분류: _classify_question_basic()
   - 키워드 매칭: "사면", "좋을까" → A_매수판단형
    ↓
5. IntentResult 반환:
   - question_type: "A_매수판단형"
   - stock_code: "005930"
   - stock_name: "삼성전자"
```

**주요 함수**:
- `analyze_intent(question, use_llm)`: 메인 함수
- `_extract_stock_code()`: 6자리 코드 추출
- `_extract_stock_name()`: 한글 종목명 추출
- `_classify_question_basic()`: 키워드 기반 분류
- `_classify_question_llm()`: LLM 기반 분류 (선택)

---

#### `planner.py` - 2️⃣ 탐색 계획 수립
**역할**: 질문 유형에 따라 어떤 데이터를 수집할지 계획

**질문 유형별 계획**:

| 질문 유형 | 수집 데이터 | URL |
|---------|-----------|-----|
| A_매수판단형 | 1. 현재 시세<br>2. 최근 뉴스<br>3. 차트 데이터 | `/quotes/{code}`<br>`/quotes/{code}/news`<br>`/api/charts/{code}/days` |
| B_시세상태형 | 1. 차트 API (최신 시세)<br>2. 실시간 API (백업)<br>3. HTML 페이지 (최종) | `/api/charts/{code}/days`<br>`/api/quotes/{code}`<br>`/quotes/{code}` |
| C_여론요약형 | 1. 토론/의견<br>2. 현재 시세 (참고) | `/quotes/{code}/talks`<br>`/quotes/{code}` |
| D_뉴스공시형 | 1. 최근 뉴스<br>2. 최근 공시 | `/quotes/{code}/news`<br>`/quotes/{code}/disclosures` |
| E_기타 | 1. 기본 종목 정보<br>2. 상세 정보 | `/quotes/{code}`<br>`/quotes/{code}/company` |

**예시**:
```python
# 매수판단형 질문의 경우
plans = [
    FetchPlan(
        plan_id="A1",
        description="현재 시세 정보 확인",
        url="https://finance.daum.net/quotes/A005930",
        parser_name="parse_price_page"
    ),
    FetchPlan(
        plan_id="A2",
        description="최근 뉴스 확인",
        url="https://finance.daum.net/quotes/A005930/news",
        parser_name="parse_news_list"
    ),
    # ...
]
```

---

#### `daum_fetch.py` - 3️⃣ 데이터 수집
**역할**: 보안이 강화된 HTTP 요청 및 캐싱

**핵심 보안 기능**:
```python
# Allowlist 검증 (중요!)
ALLOWED_DOMAINS = [
    "finance.daum.net",
    "m.finance.daum.net",
    "ssl.daumcdn.net"
]

def _is_allowed_domain(url: str) -> bool:
    """허용된 도메인만 통과"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return domain in ALLOWED_DOMAINS

# 차단 예시
fetch("https://evil.com/data")  # ❌ 차단됨
fetch("https://finance.daum.net/quotes/A005930")  # ✅ 허용됨
```

**캐싱 전략**:
```python
# 데이터 유형별 TTL 설정
CACHE_TTL_PRICE = 60      # 시세: 1분
CACHE_TTL_NEWS = 300      # 뉴스: 5분
CACHE_TTL_SEARCH = 120    # 검색: 2분
```

**재시도 로직**:
- 403/429 에러 시 자동 재시도
- 최대 3회 재시도 (MAX_RETRIES = 2)
- 재시도 간격 1초

---

#### `parsers.py` - 4️⃣ 데이터 파싱
**역할**: HTML/JSON 데이터를 구조화된 데이터로 변환

**파서 종류**:

1. **`parse_search_results(html)`** - 검색 결과
```python
# 입력: 검색 페이지 HTML
# 출력: [{'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'}, ...]
```

2. **`parse_price_page(html)`** - 시세 페이지
```python
# 출력: {
#   'current_price': 72500,
#   'change': '+1500',
#   'change_rate': '+2.11%',
#   'volume': '15,234,567',
#   'open_price': 71000,
#   'high_price': 73000,
#   'low_price': 70500
# }
```

3. **`parse_chart_for_price(json)`** - 차트 API → 시세 변환
```python
# 차트 데이터에서 최신 캔들을 추출하여 시세 형식으로 변환
# 전일 대비 등락률도 자동 계산
```

4. **`parse_news_list(html)`** - 뉴스 목록
5. **`parse_disclosure_list(html)`** - 공시 목록
6. **`parse_talks_list(html)`** - 토론/의견

---

#### `summarizer.py` - 5️⃣ 결과 요약
**역할**: 파싱된 데이터를 사람이 읽기 쉬운 텍스트로 요약

**요약 예시**:
```python
# 시세 데이터 요약
_summarize_price_data({
    'current_price': 72500,
    'change': '+1500',
    'change_rate': '+2.11%',
    'volume': 15234567
})
# → "현재가 72,500원, 전일비 +1500 (+2.11%), 거래량 15,234,567"

# 뉴스 데이터 요약
_summarize_news_data([
    {'title': '삼성전자, 신제품 출시', 'date': '2024-01-15'},
    {'title': '2분기 실적 발표', 'date': '2024-01-14'}
])
# → "1. 삼성전자, 신제품 출시 (2024-01-15)
#     2. 2분기 실적 발표 (2024-01-14)"
```

---

#### `answer.py` - 6️⃣ 최종 답변 생성
**역할**: 4단계 구조화된 답변 생성

**답변 구조**:
```markdown
### [1] 질문 의도 분석
- **질문 유형:** A_매수판단형
- **대상 종목:** 삼성전자 (005930)
- **사용자가 원하는 것:** 매수/투자 판단에 대한 정보를 원하시는 것으로 보입니다

### [2] 다음 금융 탐색 계획
- **Plan 1:** 현재 시세 정보 확인
  - URL: `https://finance.daum.net/quotes/A005930`
- **Plan 2:** 최근 뉴스 확인
  - URL: `https://finance.daum.net/quotes/A005930/news`

### [3] 다음 금융 스크랩 결과 요약
**Source 1: 시세 정보**
- 근거 스니펫:
```
현재가 72,500원, 전일비 +1,500원 (+2.11%), 거래량 15,234,567
```

### [4] 최종 답변 (초보자 친화)
**[다음 금융 데이터 기반 분석]**

**현재 상태:**
현재가 72,500원, 전일비 +1,500원 (+2.11%)...

**체크포인트:**
- 위 정보는 다음 금융에서 수집한 현재 시점 데이터입니다
- 투자 결정은 본인의 투자 성향과 재무 상황을 고려하여 신중히 결정하세요
```

**LLM 모드** (선택):
- OpenAI/Anthropic API 사용
- 더 자연스러운 답변 생성
- 근거 스니펫만 사용하도록 제한

---

#### `conversation.py` - 대화 모드 처리
**역할**: 일반 대화 vs 주식 질문 구분 및 처리

**주요 함수**:
```python
def is_general_conversation(user_input: str) -> bool:
    """
    일반 대화인지 판단

    주식 키워드: 종목, 주가, 시세, 매수, 뉴스...
    일반 키워드: 안녕, 고마워, 도움말...

    반환:
        True: 일반 대화 (conversational_response 필요)
        False: 주식 질문 (stock_query 처리 필요)
    """
```

**대화 흐름**:
```
사용자: "안녕하세요"
    ↓
is_general_conversation() → True
    ↓
generate_conversational_response()
    ↓
답변: "안녕하세요! 다음 금융 투자 챗봇입니다..."

---

사용자: "삼성전자 주가는?"
    ↓
is_general_conversation() → False
    ↓
_process_stock_query() (4단계 파이프라인)
```

---

### 🗄️ **데이터 관리 레이어**

#### `state.py` - 세션 상태 관리
**역할**: 멀티턴 대화를 위한 상태 관리

**핵심 클래스**:

1. **`ConversationMemory`** - 대화 기억
```python
class ConversationMemory:
    last_stock_code: str      # "005930"
    last_stock_name: str      # "삼성전자"
    last_question_type: str   # "A_매수판단형"
    last_sources: List[Dict]  # 이전 데이터 소스
```

**사용 예시**:
```
사용자: "삼성전자 주가는?"
    → memory.update(stock_code="005930", stock_name="삼성전자")

사용자: "뉴스 보여줘"  (종목 생략!)
    → memory.has_stock_context() → True
    → 자동으로 삼성전자 뉴스 조회
```

2. **`PendingChoice`** - HITL 상태
```python
class PendingChoice:
    candidates: List[Dict]      # [{'code': '005930', 'name': '삼성전자'}, ...]
    original_user_query: str    # "삼성 주가는?"
    next_action: str            # "B_시세상태형"
```

**HITL 흐름**:
```
사용자: "삼성 주가는?"
    ↓
검색 결과: [삼성전자, 삼성물산, 삼성SDI, ...]
    ↓
pending_choice.candidates = [...]  # 후보 저장
    ↓
UI에 선택 버튼 표시:
[삼성전자 (005930)] [삼성물산 (028260)] [삼성SDI (006400)]
    ↓
사용자 클릭: 삼성전자 선택
    ↓
memory.update(stock_code="005930", stock_name="삼성전자")
pending_choice.clear()
```

3. **`ChatMessage`** - 채팅 메시지
```python
class ChatMessage:
    role: str           # 'user' or 'assistant'
    content: str        # 메시지 내용
    timestamp: datetime # 시간
```

---

#### `cache_manager.py` - TTL 캐시
**역할**: 메모리 기반 캐시로 성능 최적화

**캐시 구조**:
```python
# {cache_key: (value, expire_time)}
cache = {
    "md5_hash_of_url": ("<html>...</html>", 1642345678.9),
    # ...
}
```

**캐시 키 생성**:
```python
def _make_key(url, params):
    key_data = url + json.dumps(params, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()

# 예시:
# URL: "https://finance.daum.net/quotes/A005930"
# params: None
# → cache_key: "a1b2c3d4e5f6..."
```

**TTL 확인**:
```python
def get(url, params):
    key = _make_key(url, params)
    value, expire_time = cache[key]

    if time.time() > expire_time:
        # 만료됨 → 삭제 후 None 반환
        del cache[key]
        return None

    return value  # 캐시 히트!
```

---

#### `stock_mapping.py` - 종목 코드 매핑
**역할**: 빠른 종목 코드 조회를 위한 정적 매핑

**매핑 테이블**:
```python
STOCK_MAPPING = {
    "삼성전자": "005930",
    "삼성": "005930",      # 별칭
    "SK하이닉스": "000660",
    "하이닉스": "000660",  # 별칭
    # ... 약 200여 개 종목
}
```

**조회 우선순위**:
```
1. stock_mapping.get_stock_code() → 빠름 (0.01ms)
    ↓ (실패 시)
2. Daum Finance 검색 API → 느림 (100-500ms)
```

---

#### `endpoints.py` - URL 생성
**역할**: 다음 금융 URL을 생성하는 헬퍼 함수

**주요 함수**:
```python
get_search_url("삼성전자")
→ "https://finance.daum.net/search/search?q=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90"

get_price_url("005930")
→ "https://finance.daum.net/quotes/A005930"

get_chart_api_url("005930", period="days")
→ "https://finance.daum.net/api/charts/A005930/days"

get_news_url("005930", page=1)
→ "https://finance.daum.net/quotes/A005930/news?page=1"
```

---

#### `config.py` - 설정 관리
**역할**: 상수 및 환경 변수 관리

**주요 설정**:
```python
# 보안
ALLOWED_DOMAINS = ["finance.daum.net", "m.finance.daum.net", "ssl.daumcdn.net"]

# 캐시 TTL
CACHE_TTL_PRICE = 60      # 시세: 1분
CACHE_TTL_NEWS = 300      # 뉴스: 5분
CACHE_TTL_SEARCH = 120    # 검색: 2분

# HTTP 설정
DEFAULT_TIMEOUT = 10      # 요청 타임아웃
MAX_RETRIES = 2           # 최대 재시도

# 질문 유형
QUESTION_TYPE_BUY_RECOMMENDATION = "A_매수판단형"
QUESTION_TYPE_PRICE_STATUS = "B_시세상태형"
# ...
```

---

## 🔄 전체 실행 흐름 (End-to-End)

### 시나리오 1: 초기 질문 (종목 지정)

```
┌──────────────────────────────────────────────────────────────┐
│ 사용자: "삼성전자 지금 사면 좋을까?"                          │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [app_chat.py] 입력 수신                                       │
│ - is_general_conversation() → False (주식 질문)              │
│ - _process_stock_query() 호출                                │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 1] 의도 분석 (intent.py)                               │
│                                                              │
│ 1. _extract_stock_name("삼성전자 지금 사면 좋을까?")          │
│    → "삼성전자"                                              │
│                                                              │
│ 2. stock_mapping.get_stock_code("삼성전자")                  │
│    → ("005930", "삼성전자")                                  │
│                                                              │
│ 3. _classify_question_basic()                                │
│    키워드: "사면", "좋을까" → "A_매수판단형"                  │
│                                                              │
│ 4. IntentResult 반환:                                        │
│    - question_type: "A_매수판단형"                           │
│    - stock_code: "005930"                                    │
│    - stock_name: "삼성전자"                                  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [메모리 업데이트] state.memory.update()                       │
│ - last_stock_code = "005930"                                 │
│ - last_stock_name = "삼성전자"                               │
│ - last_question_type = "A_매수판단형"                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 2] 계획 수립 (planner.py)                              │
│                                                              │
│ create_plan(intent) → 매수판단형 계획:                        │
│   Plan A1: 현재 시세 확인                                     │
│     URL: finance.daum.net/quotes/A005930                     │
│   Plan A2: 최근 뉴스 확인                                     │
│     URL: finance.daum.net/quotes/A005930/news                │
│   Plan A3: 차트 데이터 확인                                   │
│     URL: finance.daum.net/api/charts/A005930/days            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 3] 데이터 수집 (daum_fetch.py)                         │
│                                                              │
│ Plan A1 실행:                                                │
│   1. 캐시 확인: cache.get(url) → None (캐시 미스)             │
│   2. Allowlist 검증: ✅ finance.daum.net 허용됨              │
│   3. HTTP GET 요청 → 200 OK                                  │
│   4. 캐시 저장: cache.set(url, html, ttl=60)                 │
│   5. FetchResult 반환: success=True, content="<html>..."     │
│                                                              │
│ Plan A2 실행: (뉴스)                                         │
│   캐시 히트! → 즉시 반환                                      │
│                                                              │
│ Plan A3 실행: (차트 JSON)                                    │
│   새로운 요청 → JSON 파싱                                     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 4] 파싱 및 요약 (parsers.py + summarizer.py)           │
│                                                              │
│ Source 1: 시세 정보                                           │
│   parse_price_page(html) → {current_price: 72500, ...}      │
│   _summarize_price_data() →                                  │
│     "현재가 72,500원, 전일비 +1,500원 (+2.11%), 거래량 15M"  │
│                                                              │
│ Source 2: 뉴스                                               │
│   parse_news_list(html) → [{'title': '...', 'date': '...'}, ...]│
│   _summarize_news_data() →                                   │
│     "1. 삼성전자 신제품 출시 (2024-01-15)"                   │
│     "2. 2분기 실적 발표 (2024-01-14)"                        │
│                                                              │
│ Source 3: 차트                                               │
│   parse_chart_json(json) → [{date, open, high, low, close}, ...]│
│   _summarize_chart_data() →                                  │
│     "최근 5일간 상승 추세 (+3.45%)"                          │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 5] 최종 답변 생성 (answer.py)                          │
│                                                              │
│ generate_answer(intent, plans, summaries, use_llm=False)     │
│                                                              │
│ 4단계 구조화된 답변 생성:                                     │
│ ### [1] 질문 의도 분석                                       │
│ ### [2] 다음 금융 탐색 계획                                  │
│ ### [3] 다음 금융 스크랩 결과 요약                            │
│ ### [4] 최종 답변 (초보자 친화)                              │
│                                                              │
│ (선택) LLM 모드:                                             │
│   - OpenAI/Anthropic API 호출                                │
│   - 프롬프트: "근거 스니펫만 사용하여 답변 생성"              │
│   - 더 자연스러운 답변                                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [app_chat.py] 답변 표시                                      │
│ - st.markdown(answer_text)                                   │
│ - state.add_assistant_message(answer_text)                   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 사용자에게 표시:                                             │
│                                                              │
│ ### [1] 질문 의도 분석                                       │
│ - 질문 유형: A_매수판단형                                    │
│ - 대상 종목: 삼성전자 (005930)                               │
│                                                              │
│ ### [2] 다음 금융 탐색 계획                                  │
│ - Plan 1: 현재 시세 정보 확인                                │
│ - Plan 2: 최근 뉴스 확인                                     │
│ - Plan 3: 차트 데이터 확인                                   │
│                                                              │
│ ### [3] 다음 금융 스크랩 결과 요약                            │
│ **Source 1: 시세 정보**                                      │
│ 현재가 72,500원, 전일비 +1,500원 (+2.11%)...                 │
│                                                              │
│ ### [4] 최종 답변                                            │
│ **[다음 금융 데이터 기반 분석]**                             │
│ 현재 삼성전자는 상승세를 보이고 있습니다...                   │
└──────────────────────────────────────────────────────────────┘
```

---

### 시나리오 2: 후속 질문 (종목 생략)

```
┌──────────────────────────────────────────────────────────────┐
│ [이전 대화] 메모리에 저장됨:                                  │
│ - last_stock_code = "005930"                                 │
│ - last_stock_name = "삼성전자"                               │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 사용자: "뉴스 보여줘"  (종목 생략!)                           │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 1] 의도 분석                                           │
│                                                              │
│ 1. analyze_intent("뉴스 보여줘")                             │
│    - _extract_stock_name() → None (종목 없음)                │
│    - _classify_question_basic() → "D_뉴스공시형"             │
│    - IntentResult:                                           │
│        question_type: "D_뉴스공시형"                         │
│        stock_code: None                                      │
│        stock_name: None                                      │
│                                                              │
│ 2. [app_chat.py] 메모리 확인:                                │
│    if not intent.stock_code and state.memory.has_stock_context():│
│        intent.stock_code = state.memory.last_stock_code      │
│        intent.stock_name = state.memory.last_stock_name      │
│                                                              │
│ 3. IntentResult 업데이트:                                    │
│        question_type: "D_뉴스공시형"                         │
│        stock_code: "005930"  ← 메모리에서 복원!              │
│        stock_name: "삼성전자" ← 메모리에서 복원!             │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 2-5] 정상 처리                                         │
│ - 뉴스공시형 계획 수립                                        │
│ - 삼성전자 뉴스 및 공시 조회                                  │
│ - 답변 생성 및 표시                                          │
└──────────────────────────────────────────────────────────────┘
```

---

### 시나리오 3: HITL (여러 종목 발견)

```
┌──────────────────────────────────────────────────────────────┐
│ 사용자: "삼성 주가는?"  (모호한 종목명)                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [STEP 1] 의도 분석                                           │
│                                                              │
│ 1. _extract_stock_name("삼성 주가는?") → "삼성"              │
│ 2. stock_mapping.get_stock_code("삼성")                      │
│    → ("005930", "삼성전자")  # "삼성"은 "삼성전자" 별칭       │
│                                                              │
│ → 일단 삼성전자로 확정                                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [만약 stock_mapping에 없었다면...]                            │
│                                                              │
│ 1. Daum Finance 검색:                                        │
│    fetch("https://finance.daum.net/search/search?q=삼성")    │
│                                                              │
│ 2. parse_search_results(html) → 여러 결과 발견:              │
│    [                                                         │
│      {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'},│
│      {'code': '028260', 'name': '삼성물산', 'market': 'KOSPI'},│
│      {'code': '006400', 'name': '삼성SDI', 'market': 'KOSPI'},│
│      {'code': '032830', 'name': '삼성생명', 'market': 'KOSPI'}│
│    ]                                                         │
│                                                              │
│ 3. len(candidates) > 1 → HITL 활성화!                        │
│    state.pending_choice.candidates = candidates              │
│    state.pending_choice.original_user_query = "삼성 주가는?"  │
│    state.pending_choice.next_action = "B_시세상태형"         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [app_chat.py] HITL UI 표시                                   │
│                                                              │
│ if state.pending_choice.is_pending():                        │
│     st.markdown("여러 종목이 검색되었습니다. 선택해주세요:")   │
│                                                              │
│     [삼성전자 (005930) KOSPI]  ← 버튼                        │
│     [삼성물산 (028260) KOSPI]  ← 버튼                        │
│     [삼성SDI (006400) KOSPI]   ← 버튼                        │
│     [삼성생명 (032830) KOSPI]  ← 버튼                        │
│     [❌ 취소]                  ← 버튼                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 사용자 클릭: "삼성전자 (005930)" 버튼                         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [app_chat.py] 선택 처리                                      │
│                                                              │
│ 1. 메모리 업데이트:                                          │
│    state.memory.update(                                      │
│        stock_code="005930",                                  │
│        stock_name="삼성전자"                                 │
│    )                                                         │
│                                                              │
│ 2. 확인 메시지 추가:                                         │
│    state.add_assistant_message(                              │
│        "✅ 삼성전자 (005930) 종목을 선택하셨습니다."          │
│    )                                                         │
│                                                              │
│ 3. pending_choice 초기화:                                    │
│    state.pending_choice.clear()                              │
│                                                              │
│ 4. 페이지 새로고침:                                          │
│    st.rerun()                                                │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ [다음 턴] 사용자가 다시 질문하면                              │
│ → 메모리에 "삼성전자" 저장되어 있음                           │
│ → 바로 시세 조회 진행                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔒 보안 및 안정성

### 1. Allowlist 기반 도메인 검증
```python
# daum_fetch.py
ALLOWED_DOMAINS = [
    "finance.daum.net",
    "m.finance.daum.net",
    "ssl.daumcdn.net"
]

def fetch(url, ...):
    # 맨 처음에 검증!
    if not _is_allowed_domain(url):
        return FetchResult(
            success=False,
            error_message=f"도메인 허용 목록에 없음: {url}"
        )
    # ... 이후 처리
```

**효과**:
- ✅ SSRF(Server-Side Request Forgery) 방지
- ✅ 외부 악의적인 URL 차단
- ✅ 다음 금융 데이터만 사용 보장

---

### 2. 재시도 및 에러 처리
```python
# 재시도 전략
MAX_RETRIES = 2
RETRY_DELAY = 1  # 초

# 재시도 대상 에러
- 403 Forbidden (접근 거부)
- 429 Too Many Requests (요청 제한)
- Timeout

# 재시도하지 않는 에러
- 404 Not Found
- 500 Internal Server Error
- 기타 HTTP 에러
```

---

### 3. 캐싱을 통한 부하 분산
```python
# 캐시 TTL 설정으로 다음 금융 서버 부하 감소
CACHE_TTL_PRICE = 60      # 시세: 1분
CACHE_TTL_NEWS = 300      # 뉴스: 5분
CACHE_TTL_SEARCH = 120    # 검색: 2분

# 효과:
# - 동일 종목 반복 조회 시 캐시에서 즉시 반환
# - 다음 금융 서버 요청 최소화
# - 응답 속도 향상 (100-500ms → 1ms)
```

---

### 4. 세션 격리
```python
# Streamlit session_state로 사용자별 독립 세션
# 각 브라우저 탭마다 별도의 ConversationState 인스턴스

# 사용자 A의 세션
session_A = {
    'conversation_state': ConversationState(
        memory={'last_stock_code': '005930'},  # 삼성전자
        chat_history=[...]
    )
}

# 사용자 B의 세션
session_B = {
    'conversation_state': ConversationState(
        memory={'last_stock_code': '035420'},  # 네이버
        chat_history=[...]
    )
}

# → 서로 영향 없음!
```

---

## ⚡ 성능 최적화

### 1. 캐시 히트율 향상
```python
# 전략:
# 1. 시세 데이터: 짧은 TTL (1분) → 최신성 유지
# 2. 뉴스 데이터: 긴 TTL (5분) → 변경 빈도 낮음
# 3. 검색 결과: 중간 TTL (2분) → 종목 코드 고정

# 예상 히트율:
# - 시세: 30-50% (동일 종목 반복 조회)
# - 뉴스: 70-90% (뉴스는 자주 변경되지 않음)
```

---

### 2. 파싱 최적화
```python
# BeautifulSoup: lxml 파서 사용 (html.parser보다 2-3배 빠름)
soup = BeautifulSoup(html, 'lxml')

# CSS 선택자: 구체적으로 지정하여 탐색 범위 최소화
items = soup.select('.searchStockList .item_stock')  # ✅ 빠름
items = soup.find_all('div')  # ❌ 느림
```

---

### 3. 병렬 요청 (향후 개선 가능)
```python
# 현재: 순차 처리
for plan in plans:
    result = fetch(plan.url)

# 개선안: asyncio + aiohttp로 병렬 처리
async def fetch_all(plans):
    tasks = [fetch_async(plan.url) for plan in plans]
    results = await asyncio.gather(*tasks)
    return results

# 예상 속도 향상:
# - 3개 요청 × 200ms = 600ms (순차)
# - max(200ms, 200ms, 200ms) = 200ms (병렬)
# → 3배 빠름!
```

---

## 🐛 일반적인 문제 해결

### 문제 1: "종목을 찾을 수 없습니다"
**원인**:
- stock_mapping에 없는 종목
- 다음 금융 검색 실패
- 오타 또는 비상장 종목

**해결**:
```python
# 1. stock_mapping.py에 종목 추가
STOCK_MAPPING = {
    "새로운종목": "123456",
    # ...
}

# 2. 정확한 종목명 입력
"삼성전자" (O)
"삼성전" (X)

# 3. 종목 코드 직접 입력
"005930" (O)
```

---

### 문제 2: "데이터를 수집할 수 없습니다"
**원인**:
- 다음 금융 서버 에러 (503)
- 네트워크 문제
- Allowlist 차단

**디버깅**:
```python
# config.py에 DEBUG_MODE 추가
DEBUG_MODE = "true"

# app_chat.py에서 에러 정보 표시
if get_env('DEBUG_MODE', 'false').lower() == 'true':
    response += "**디버그 정보:**\n" + "\n".join(error_details) + "\n\n"
```

---

### 문제 3: 캐시 문제
**증상**: 오래된 데이터 표시

**해결**:
```python
# 캐시 강제 초기화
from cache_manager import get_cache
cache = get_cache()
cache.clear()

# 또는 TTL 조정
CACHE_TTL_PRICE = 30  # 1분 → 30초로 단축
```

---

## 🚀 향후 개선 방향

### 1. 성능 개선
- [ ] asyncio를 통한 병렬 요청
- [ ] Redis 기반 분산 캐시 (멀티 프로세스 지원)
- [ ] HTML 파싱 결과 캐싱

### 2. 기능 추가
- [ ] 차트 이미지 생성 및 표시
- [ ] 종목 비교 기능 (A vs B)
- [ ] 실시간 알림 (가격 변동 시)
- [ ] PDF 보고서 생성

### 3. 보안 강화
- [ ] Rate Limiting (요청 제한)
- [ ] 사용자 인증 (로그인)
- [ ] API 키 암호화 저장

### 4. UX 개선
- [ ] 음성 입력/출력
- [ ] 다크 모드
- [ ] 종목 즐겨찾기
- [ ] 대화 기록 저장/불러오기

---

## 📚 주요 기술 스택 및 라이브러리

| 항목 | 기술/라이브러리 | 역할 |
|-----|----------------|------|
| **프론트엔드** | Streamlit | 웹 UI 프레임워크 |
| **HTTP 클라이언트** | requests | HTTP 요청 처리 |
| **HTML 파싱** | BeautifulSoup4 (lxml) | HTML 파싱 및 데이터 추출 |
| **LLM** | OpenAI API / Anthropic API | 자연어 처리 및 답변 생성 (선택) |
| **캐싱** | 메모리 기반 TTL 캐시 | 성능 최적화 |
| **세션 관리** | Streamlit session_state | 사용자별 상태 관리 |
| **환경 변수** | python-dotenv | .env 파일 로드 |

---

## 📝 개발자를 위한 팁

### 새로운 질문 유형 추가하기

1. **config.py에 유형 추가**:
```python
QUESTION_TYPE_TECHNICAL_ANALYSIS = "F_기술적분석형"
KEYWORDS_TECHNICAL = ["차트", "기술적", "RSI", "MACD"]
```

2. **intent.py에 분류 로직 추가**:
```python
if any(keyword in text_lower for keyword in KEYWORDS_TECHNICAL):
    return QUESTION_TYPE_TECHNICAL_ANALYSIS
```

3. **planner.py에 계획 추가**:
```python
elif question_type == QUESTION_TYPE_TECHNICAL_ANALYSIS:
    plans.append(FetchPlan(
        plan_id="F1",
        description="차트 데이터 확인 (기술적 분석)",
        url=get_chart_api_url(code, period="months"),
        parser_name="parse_chart_json",
        is_json=True
    ))
```

4. **answer.py에 답변 템플릿 추가**:
```python
elif question_type == QUESTION_TYPE_TECHNICAL_ANALYSIS:
    answer = "**[기술적 분석 결과]**\n\n"
    if chart_data:
        answer += f"{chart_data.evidence_snippet}\n\n"
    # ...
```

---

### 새로운 파서 추가하기

1. **parsers.py에 함수 추가**:
```python
def parse_financial_statements(html: str) -> Dict[str, Any]:
    """
    재무제표 파싱
    """
    soup = BeautifulSoup(html, 'lxml')
    data = {}

    # 매출액, 영업이익 등 추출
    # ...

    return data
```

2. **planner.py에 파서 연결**:
```python
plans.append(FetchPlan(
    plan_id="G1",
    description="재무제표 확인",
    url=get_financial_url(code),
    parser_name="parse_financial_statements"  # ← 여기에 함수명
))
```

3. **summarizer.py에 요약 함수 추가**:
```python
def _summarize_financial_data(data: Dict[str, Any]) -> str:
    # 재무 데이터 요약
    pass
```

---

## 🎓 학습 가이드

### 초보자를 위한 학습 순서

1. **UI 레이어 이해** (app_chat.py)
   - Streamlit 기본 사용법
   - 채팅 인터페이스 구현 방법

2. **데이터 수집** (daum_fetch.py, parsers.py)
   - HTTP 요청 및 응답 처리
   - HTML 파싱 및 데이터 추출

3. **비즈니스 로직** (intent.py, planner.py, answer.py)
   - 의도 분석 알고리즘
   - 계획 수립 패턴
   - 답변 생성 로직

4. **상태 관리** (state.py, cache_manager.py)
   - 세션 상태 관리
   - 캐싱 전략

---

## 🤝 기여 가이드

### 코드 컨벤션
- **함수명**: snake_case (예: `analyze_intent`)
- **클래스명**: PascalCase (예: `IntentResult`)
- **상수**: UPPER_SNAKE_CASE (예: `CACHE_TTL_PRICE`)
- **주석**: 함수 시작 부분에 docstring 작성

### 커밋 메시지
```
feat: 새로운 기능 추가
fix: 버그 수정
refactor: 코드 리팩토링
docs: 문서 수정
test: 테스트 추가/수정
```

---

## 📞 문의 및 지원

- **이슈**: [GitHub Issues](https://github.com/your-repo/issues)
- **문서**: 이 파일 (CODE_REVIEW.md)
- **기타 문서**:
  - README.md: 사용자 가이드
  - DEPLOYMENT.md: 배포 가이드
  - TROUBLESHOOTING_DAUM.md: 문제 해결 가이드

---

**마지막 업데이트**: 2024-02-11

**작성자**: Claude Code 🤖

**라이선스**: MIT License

---

## ✨ 맺음말

이 문서를 통해 다음 금융 투자 챗봇의 전체 구조와 동작 방식을 이해하셨기를 바랍니다.

코드를 읽을 때는:
1. **UI → 비즈니스 로직 → 데이터 레이어** 순서로 따라가면 이해하기 쉽습니다
2. **주요 흐름 시나리오**를 먼저 이해한 후, 세부 구현을 살펴보세요
3. **주석과 docstring**을 참고하여 각 함수의 역할을 파악하세요

궁금한 점이 있으면 언제든 문의해 주세요! 🚀

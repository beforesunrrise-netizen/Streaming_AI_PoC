# 주식도사 - 다음 금융 전용 투자 Q&A 챗봇

## 프로젝트 개요

사용자의 주식 투자 관련 질문에 **다음 금융(finance.daum.net) 데이터만** 사용하여 답변하는 GPT 스타일 대화형 챗봇.

## 절대 규칙

### 데이터 소스 제한
- **반드시 finance.daum.net 데이터만 사용**
- 허용 도메인: `finance.daum.net`, `m.finance.daum.net`, `ssl.daumcdn.net`
- 네이버 금융, 한국거래소(pykrx), 증권사 API 등 외부 소스 사용 금지
- 모든 fetch 요청은 `daum_fetch.py`의 allowlist를 통과해야 함
- LLM의 학습된 지식으로 답변 생성 금지. 반드시 수집한 데이터 기반으로만 답변

### 모든 답변에 출처 명시
- 답변 하단에 "참고한 다음 금융 페이지" 섹션 포함
- 클릭 가능한 다음 금융 URL 링크 제공
- 면책 조항 포함: "투자 판단은 본인 책임"

## 4단계 처리 파이프라인

사용자 질문은 반드시 아래 4단계를 거쳐 처리하고, 각 단계의 사고 과정을 사용자에게 보여줄 것:

### [1단계] 질문 의도 분석 (`intent.py`)
- 종목명/종목코드 추출 (예: "삼성전자" → 005930)
- 질문 유형 분류:
  - `A_매수판단형`: 매수, 사야, 투자, 추천 등
  - `B_시세상태형`: 가격, 시세, 현재가, 거래량 등
  - `C_여론요약형`: 의견, 토론, 반응, 사람들 등
  - `D_뉴스공시형`: 뉴스, 공시, 기사, 발표 등
  - `E_기타`: 위에 해당하지 않는 경우

### [2단계] 탐색 계획 수립 (`planner.py`)
- 질문 유형에 따라 수집할 다음 금융 페이지 목록 생성
- 직접 URL 생성 + Tavily 검색 URL 병합

### [3단계] 데이터 수집 및 분석 (`daum_fetch.py`, `tavily_search.py`, `summarizer.py`)
- Allowlist 검증 후 다음 금융 페이지에서 데이터 수집
- 수집된 데이터를 요약하고 핵심 정보 추출

### [4단계] 최종 답변 생성 (`answer.py`)
- 초보 투자자가 이해하기 쉬운 답변 문구 생성
- 출처(다음 금융 URL) 명시

## Tavily 사용 규칙

다음 금융의 뉴스/공시/토론 직접 URL이 404를 반환하는 문제가 있어서 Tavily로 우회함.

### Tavily의 역할: URL 탐색 전용
- `site:finance.daum.net` + `include_domains=["finance.daum.net"]`으로 검색
- Tavily가 반환한 URL도 `daum_fetch.py` allowlist로 재검증 (이중 안전장치)
- Tavily의 answer/summary는 사용하지 않음. URL만 수집

### 질문 유형별 Tavily 전략
- **매수판단형**: 뉴스, 증권 분석, 시장 전망 검색 (최대 5개)
- **시세상태형**: 최소한 사용 (직접 URL로 충분)
- **여론요약형**: 토론, 의견, 투자자 반응 검색 (최대 8개)
- **뉴스공시형**: 뉴스, 공시, 기사 검색 (최대 8개)

## 다음 금융 URL 패턴

```
시세:     https://finance.daum.net/quotes/A{종목코드}
뉴스:     https://finance.daum.net/quotes/A{종목코드}/news
토론:     https://finance.daum.net/quotes/A{종목코드}/talks
공시:     https://finance.daum.net/quotes/A{종목코드}/disclosures
기업정보: https://finance.daum.net/quotes/A{종목코드}/company
검색:     https://finance.daum.net/search/search?q={종목명}
```

- 종목코드는 6자리 숫자 (예: 005930)
- URL에는 `A` 접두사를 붙임 (예: A005930)

## 다음 금융 접근 시 알려진 문제

- **React SPA**: JavaScript 렌더링 필요한 페이지가 있음 → Selenium 또는 Tavily로 우회
- **차트 API 차단**: `/api/charts/` 엔드포인트 403 → 제거함 (시세 정보로 대체)
- **뉴스/공시/토론 404**: 직접 URL 접근 시 404 → Tavily로 실제 존재하는 URL 탐색

## 기술 스택

- **UI**: Streamlit (모바일 반응형)
- **언어**: Python 3.8+
- **HTTP**: requests + BeautifulSoup4
- **웹 검색**: Tavily (finance.daum.net URL 탐색용)
- **LLM**: OpenAI API (답변 생성, 선택사항)
- **워크플로우**: LangGraph (선택사항)
- **배포**: Streamlit Cloud

## 파일 구조

```
app_chat.py         # 메인 UI (GPT 스타일 채팅)
intent.py           # [1단계] 질문 의도 분석
planner.py          # [2단계] 탐색 계획 수립
daum_fetch.py       # [3단계] 데이터 수집 (Allowlist 강제)
tavily_search.py    # [3단계] Tavily URL 검색
summarizer.py       # [3단계] 데이터 요약
answer.py           # [4단계] 답변 생성
config.py           # 설정 (도메인 허용목록, 질문유형, 키워드)
endpoints.py        # 다음 금융 URL 생성
state.py            # 대화 상태 관리 (멀티턴)
stock_mapping.py    # 종목명 ↔ 종목코드 매핑
cache_manager.py    # TTL 캐시
```

## 코딩 규칙

- 새 외부 도메인을 절대 추가하지 말 것
- fetch 관련 코드 수정 시 allowlist 검증 로직을 제거하거나 우회하지 말 것
- 종목코드는 항상 6자리 숫자로 처리, URL에는 `A` 접두사 필수
- 에러 발생 시 사용자에게 "확인 불가" 표시, 임의 데이터 생성 금지
- 캐시 TTL: 시세 60초, 뉴스 300초, 검색 120초

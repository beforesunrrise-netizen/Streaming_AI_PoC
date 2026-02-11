# Tavily 통합 가이드

## 개요

이 프로젝트는 **Tavily**를 URL 검색 엔진으로 활용하여 `finance.daum.net`에서 정보를 더 완전하게 수집합니다.

### Tavily의 역할

- ✅ `site:finance.daum.net` 검색으로 관련 URL 후보 탐색
- ✅ 직접 URL 생성 방식으로 놓칠 수 있는 페이지 발견
- ❌ Tavily의 summary/content는 **사용하지 않음**
- ❌ 오직 URL만 수집하고, 실제 데이터는 `web_fetch`로 직접 가져옴

### 보안 원칙

1. **Allowlist 강제**: `daum_fetch.py`에서 `finance.daum.net`만 허용
2. **Tavily는 URL 탐색만**: 실제 콘텐츠는 web_fetch로만 수집
3. **이중 검증**: Tavily 결과도 allowlist 재검증

---

## 설정 방법

### 1. Tavily API 키 발급

1. [https://tavily.com](https://tavily.com) 접속
2. 회원가입 및 로그인
3. API 키 발급

### 2. `.env` 파일 설정

`.env` 파일에 다음 항목을 추가합니다:

```bash
# Tavily API Key (for searching finance.daum.net URLs)
# Get your API key from: https://tavily.com
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxx
```

### 3. 패키지 설치

```bash
pip install tavily-python
```

또는:

```bash
pip install -r requirements.txt
```

---

## 사용 방법

### 자동 활성화

Tavily는 기본적으로 **자동 활성화**됩니다:

- API 키가 설정되어 있으면 자동으로 Tavily 검색 실행
- API 키가 없으면 기존 직접 URL 생성 방식만 사용

### 수동 비활성화

Tavily를 사용하지 않으려면 `planner.py`에서:

```python
plans = create_plan(intent, use_tavily=False)
```

---

## 작동 방식

### 1. 질문 분석

```
사용자: "삼성전자 지금 사면 좋을까?"
  ↓
질문 유형: A_매수판단형
종목: 삼성전자 (005930)
```

### 2. 탐색 계획 수립

**직접 URL 생성 (기존 방식):**

- `https://finance.daum.net/quotes/A005930` (시세)
- `https://finance.daum.net/quotes/A005930/news` (뉴스)
- `https://finance.daum.net/api/charts/A005930/days` (차트 API)

**Tavily 검색 추가:**

```python
search_query = "site:finance.daum.net 삼성전자 시세 현재가"
                "site:finance.daum.net 삼성전자 뉴스"
                "site:finance.daum.net 삼성전자 차트"
```

Tavily 결과:
- `https://finance.daum.net/quotes/A005930/investors` (투자자별 매매)
- `https://finance.daum.net/quotes/A005930/foreign` (외국인 매매)

### 3. URL 병합 및 중복 제거

```
최종 Fetch Plan:
1. A1: 현재 시세 정보 확인
2. A2: 최근 뉴스 확인
3. A3: 차트 데이터 확인
4. T1: Tavily 추천 페이지 1 (투자자별 매매)
5. T2: Tavily 추천 페이지 2 (외국인 매매)
```

### 4. Web Fetch (Allowlist 강제)

각 URL에 대해 `daum_fetch.py`가:

1. ✅ `finance.daum.net` 도메인 검증
2. ✅ 캐시 확인
3. ✅ HTTP 요청
4. ✅ HTML/JSON 파싱
5. ❌ 다른 도메인은 즉시 차단

### 5. 답변 생성 + Reference

```markdown
### [4] 최종 답변

**[다음 금융 데이터 기반 분석]**

**현재 상태:**
삼성전자(005930) 현재가: 75,000원 (전일대비 +1.35%)
...

---

### 📎 참고한 다음 금융 페이지

1. [현재 시세 정보 확인](https://finance.daum.net/quotes/A005930)
2. [최근 뉴스 확인](https://finance.daum.net/quotes/A005930/news)
3. [차트 데이터 확인](https://finance.daum.net/api/charts/A005930/days)
4. [Tavily 추천 페이지 1](https://finance.daum.net/quotes/A005930/investors)
5. [Tavily 추천 페이지 2](https://finance.daum.net/quotes/A005930/foreign)
```

---

## 장점

### 1. 더 완전한 정보 수집

- 직접 URL 생성으로는 놓칠 수 있는 페이지 발견
- 다음 금융 내부 구조 변경 시 유연하게 대응

### 2. 안전성 보장

- Allowlist로 `finance.daum.net`만 허용
- Tavily 결과도 이중 검증

### 3. 투명성

- 모든 참고 URL을 클릭 가능한 링크로 제공
- 사용자가 직접 확인 가능

---

## 문제 해결

### Tavily 검색이 작동하지 않음

```
⚠️ TAVILY_API_KEY not found - skipping Tavily search
```

**해결:**

1. `.env` 파일에 `TAVILY_API_KEY` 설정 확인
2. Tavily 계정에서 API 키 재확인
3. 환경 변수 로드 확인

### Tavily 패키지 설치 오류

```
⚠️ tavily-python not installed - skipping Tavily search
```

**해결:**

```bash
pip install tavily-python
```

### URL이 차단됨

```
도메인 허용 목록에 없음: https://example.com
```

**원인:**

- Tavily가 `finance.daum.net` 이외의 URL을 반환
- `daum_fetch.py`의 allowlist가 정상 작동하여 차단

**해결:**

- 정상 동작 (안전장치가 작동한 것)
- Tavily 검색 쿼리에 `include_domains=["finance.daum.net"]` 설정 확인

---

## 참고

### 관련 파일

- `tavily_search.py`: Tavily 검색 로직
- `planner.py`: 탐색 계획 수립 (Tavily 통합)
- `daum_fetch.py`: Allowlist 기반 안전한 fetch
- `answer.py`: 답변 생성 + Reference 섹션

### 비용

- Tavily Free Tier: 월 1,000회 검색 무료
- 질문당 평균 2-3회 검색 사용
- 약 300-500개 질문 처리 가능

### 대안

Tavily를 사용하지 않아도 프로젝트는 정상 작동합니다:

- 기존 직접 URL 생성 방식 사용
- 다만 일부 페이지는 놓칠 수 있음

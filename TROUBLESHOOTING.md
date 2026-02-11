# 다음 금융 데이터 수집 문제 해결 가이드

## 문제 상황
다음 금융(finance.daum.net)에서 시세 데이터를 가져오지 못하는 문제가 발생하고 있습니다.

## 원인 분석
1. **페이지 구조 변경**: 다음 금융이 React 기반 SPA로 변경되어 동적 렌더링을 사용
2. **API 엔드포인트 변경**: 기존 내부 API가 변경되었거나 접근 방식이 달라짐
3. **클라우드플레어 방어**: Bot 방어 시스템이 작동할 가능성

## 해결 방법

### 방법 1: 차트 API 활용 (추천)
다음 금융의 차트 API는 아직 동작하는 것으로 보입니다.

```python
# 차트 API로 최신 시세 가져오기
url = f"https://finance.daum.net/api/charts/A{code}/days"
```

**장점:**
- JSON 형식으로 깔끔한 데이터 제공
- 안정적인 접근 가능

**단점:**
- 실시간이 아닌 일봉 데이터

### 방법 2: 네이버 금융으로 전환
네이버 금융은 더 안정적인 데이터 제공:

```python
# 네이버 금융 시세 페이지
url = f"https://finance.naver.com/item/main.naver?code={code}"
```

**장점:**
- 안정적인 HTML 구조
- 더 다양한 데이터 제공
- 실시간 시세 제공

**단점:**
- 프로젝트 전체 리팩토링 필요

### 방법 3: Selenium/Playwright 사용
동적 페이지 렌더링을 위한 브라우저 자동화:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    # 데이터 추출
```

**장점:**
- JavaScript 렌더링 완료 후 데이터 추출
- 실제 브라우저처럼 동작

**단점:**
- 리소스 소모가 큼
- Streamlit Cloud에서 추가 설정 필요
- 속도가 느림

### 방법 4: 한국투자증권 Open API (추천)
공식 API 사용으로 안정성 보장:

**장점:**
- 공식 API로 안정적
- 실시간 데이터 제공
- 법적 문제 없음

**단점:**
- API 키 발급 필요
- 일일 호출 제한 존재

## 임시 해결책 (현재 적용)

### 1. API 엔드포인트 우선 시도
```python
# planner.py 수정됨
- 먼저 /api/quotes/ 엔드포인트 시도
- 실패 시 HTML 페이지로 폴백
```

### 2. 파서 개선
```python
# parsers.py 수정됨
- 다양한 CSS 선택자 지원
- JSON 데이터 추출 시도
- 여러 페이지 구조 대응
```

### 3. 에러 메시지 개선
```python
# app_chat.py 수정됨
- 실패 시 상세한 에러 정보 제공
- DEBUG_MODE에서 디버깅 정보 출력
```

## 테스트 방법

### 1. API 엔드포인트 테스트
```bash
python test_daum_api.py
```

### 2. 파서 구조 분석
```bash
python test_parser.py
```

### 3. Streamlit 앱에서 테스트
```bash
streamlit run test_connectivity.py
```

## 권장 조치

### 단기 (즉시 적용 가능)
1. ✅ 차트 API 활용 (이미 적용)
2. ✅ 파서 개선 (이미 적용)
3. ⬜ 에러 메시지에 대체 방법 안내 추가

### 중기 (1-2주)
1. ⬜ 네이버 금융으로 전환 고려
2. ⬜ 한국투자증권 API 연동 검토

### 장기 (1개월+)
1. ⬜ 다중 소스 지원 (다음 + 네이버 + KIS API)
2. ⬜ 자동 폴백 시스템 구축

## 디버깅 체크리스트

다음을 순서대로 확인하세요:

- [ ] 차트 API가 동작하는가? (`test_daum_api.py`)
- [ ] HTML 페이지를 가져올 수 있는가? (`test_connectivity.py`)
- [ ] 가져온 HTML에 데이터가 있는가? (`test_parser.py`)
- [ ] 네트워크 연결은 정상인가?
- [ ] 다음 금융 사이트가 정상 작동하는가? (브라우저에서 직접 확인)

## Streamlit Cloud 디버깅

### 디버그 모드 활성화

Streamlit Cloud에서 더 자세한 에러 정보를 확인하려면:

1. https://share.streamlit.io/ 접속 → "Manage app" 클릭
2. 왼쪽 메뉴에서 "Secrets" 클릭
3. 다음 내용 추가:

```toml
DEBUG_MODE = "true"

# 기존 API 키들도 유지
ANTHROPIC_API_KEY = "your_key_here"
OPENAI_API_KEY = "your_key_here"
```

4. "Save" 클릭 → 앱 자동 재시작

### Streamlit Cloud 특정 문제

**HTTP 403 (접근 거부)**
- 원인: 다음 금융이 Streamlit Cloud IP 차단
- 해결: 프록시 서버, CloudFlare Workers, 자체 API 서버 사용

**Timeout (시간 초과)**
- 원인: 네트워크 지연
- 해결: `config.py`의 `DEFAULT_TIMEOUT` 증가

**DNS 해석 실패**
- 원인: Streamlit Cloud DNS 문제
- 해결: 다른 클라우드 플랫폼 고려 (Heroku, Railway, Render)

### 로그 확인
- Streamlit Cloud: "Manage app" → "Logs" 탭
- 로컬 테스트: `streamlit run app_chat.py --logger.level=debug`

### 프록시 대안

**ScraperAPI 사용 예시:**
```python
# config.py에 추가
SCRAPER_API_KEY = get_env('SCRAPER_API_KEY')
PROXY_ENABLED = get_env('PROXY_ENABLED', 'false').lower() == 'true'

# daum_fetch.py 수정
if PROXY_ENABLED and SCRAPER_API_KEY:
    proxy_url = f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"
    response = requests.get(url, headers=headers, proxies={"http": proxy_url, "https": proxy_url})
```

## 추가 리소스

- 다음 금융 고객센터: https://cs.daum.net/faq/19.html
- 네이버 금융: https://finance.naver.com
- 한국투자증권 Open API: https://apiportal.koreainvestment.com
- 공공데이터포털 금융 API: https://www.data.go.kr

## 현재 상태

**적용된 수정사항:**
- ✅ `endpoints.py`: API 엔드포인트 추가
- ✅ `planner.py`: API 우선 시도 로직 추가
- ✅ `parsers.py`: 개선된 파서 및 API 파서 추가
- ✅ `summarizer.py`: API 파서 지원 추가

**다음 단계:**
1. 실제 환경에서 테스트
2. 결과에 따라 추가 조치 결정

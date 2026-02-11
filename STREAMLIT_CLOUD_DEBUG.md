# Streamlit Cloud 디버깅 가이드

## 현재 문제: 다음 금융 데이터 가져오기 실패

Streamlit Cloud에서 다음 금융(finance.daum.net)에 접근할 때 데이터를 가져오지 못하는 문제가 발생할 수 있습니다.

## 디버그 모드 활성화

### 1. Streamlit Cloud 대시보드 접속
- https://share.streamlit.io/ 접속
- 해당 앱의 "Manage app" 클릭

### 2. Secrets 설정
- 왼쪽 메뉴에서 "Secrets" 클릭
- 다음 내용 추가:

```toml
DEBUG_MODE = "true"

# 기존 API 키들도 유지
ANTHROPIC_API_KEY = "your_key_here"
OPENAI_API_KEY = "your_key_here"
```

### 3. 앱 재시작
- "Save" 클릭
- 앱이 자동으로 재시작됨

### 4. 에러 메시지 확인
이제 앱에서 더 자세한 에러 메시지가 표시됩니다:
```
❌ 다음 금융에서 데이터를 가져올 수 없습니다.

디버그 정보:
- price_data: 접근 거부 (HTTP 403)
- news_data: 도메인 허용 목록에 없음: https://...
```

## 가능한 원인과 해결 방법

### 1. HTTP 403 (접근 거부)
**원인:** 다음 금융이 Streamlit Cloud의 IP를 차단
**해결방법:**
- 프록시 서버 사용
- CloudFlare Workers 사용
- 자체 API 서버 구축

### 2. Timeout (요청 시간 초과)
**원인:** 네트워크 지연
**해결방법:**
- `config.py`에서 `DEFAULT_TIMEOUT` 증가
- 캐시 TTL 증가

### 3. DNS 해석 실패
**원인:** Streamlit Cloud의 DNS 문제
**해결방법:**
- 다른 클라우드 플랫폼 고려 (Heroku, Railway, Render)

## 대안 1: 프록시 사용

### ScraperAPI 사용
```python
# config.py에 추가
SCRAPER_API_KEY = get_env('SCRAPER_API_KEY')
PROXY_ENABLED = get_env('PROXY_ENABLED', 'false').lower() == 'true'

# daum_fetch.py 수정
if PROXY_ENABLED and SCRAPER_API_KEY:
    proxy_url = f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001"
    response = requests.get(url, headers=headers, proxies={"http": proxy_url, "https": proxy_url})
```

## 대안 2: 자체 API 서버

### Flask/FastAPI 서버 구축
```python
# api_server.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/fetch')
def fetch_daum():
    url = request.args.get('url')
    response = requests.get(url, headers=DEFAULT_HEADERS)
    return jsonify({
        "status_code": response.status_code,
        "content": response.text
    })
```

서버를 Heroku나 Railway에 배포하고, Streamlit 앱에서 이 API를 호출합니다.

## 대안 3: CloudFlare Workers

### Worker 스크립트
```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url).searchParams.get('url')
  
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 ...',
      'Referer': 'https://finance.daum.net/'
    }
  })
  
  return new Response(await response.text(), {
    headers: { 'Access-Control-Allow-Origin': '*' }
  })
}
```

## 로그 확인

### Streamlit Cloud 로그 보기
1. "Manage app" 클릭
2. "Logs" 탭 선택
3. 실시간 로그 확인

### 로컬 테스트
```bash
# 로컬에서 동일한 환경 재현
streamlit run app_chat.py

# 더 자세한 로그
streamlit run app_chat.py --logger.level=debug
```

## 네트워크 테스트

### 간단한 테스트 스크립트
```python
# test_network.py
import requests
from config import DEFAULT_HEADERS

urls = [
    "https://finance.daum.net/",
    "https://finance.daum.net/search/search?q=삼성전자",
    "https://finance.daum.net/quotes/005930"
]

for url in urls:
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        print(f"✅ {url}: {response.status_code}")
    except Exception as e:
        print(f"❌ {url}: {str(e)}")
```

## 문의하기

문제가 계속되면:
1. GitHub Issues에 에러 메시지 첨부
2. Streamlit Cloud 로그 복사하여 공유
3. 디버그 모드 활성화 후 스크린샷 공유

# 차트 API 제거 및 Tavily 강화

## 📋 변경 사항 요약

### 2026-02-11 업데이트

다음 금융 API 접근 제한 문제를 해결하기 위해 시스템을 다음과 같이 수정했습니다.

---

## 🔧 주요 변경 사항

### 1. ✂️ 차트 API 제거

**문제점:**
- 다음 금융의 차트 API (`/api/charts/`)가 403 에러를 반환
- 직접적인 차트 데이터 접근이 차단됨

**해결 방법:**
- 차트 API 호출을 완전히 제거
- 시세 정보만으로도 충분한 답변이 가능하다고 판단

**영향받는 파일:**
- `planner.py`: 차트 API URL 생성 코드 제거
- `answer.py`: 차트 데이터 참조 제거
- `summarizer.py`: 차트 파싱 코드는 유지 (향후 사용 가능성 대비)

---

### 2. 🔍 Tavily 검색 강화

**문제점:**
- 뉴스 페이지 (`/quotes/{code}/news`) → 404 에러
- 공시 페이지 (`/quotes/{code}/disclosures`) → 404 에러
- 토론 페이지 (`/quotes/{code}/talks`) → 404 에러

**해결 방법:**
- Tavily 웹 검색을 활용하여 `finance.daum.net` 내에서 관련 페이지 탐색
- 직접 URL 생성 대신 Tavily가 실제 존재하는 페이지를 찾아줌
- 질문 유형별로 Tavily 검색 쿼리 최적화

**영향받는 파일:**
- `planner.py`: 
  - 뉴스/공시/토론 직접 URL 제거
  - Tavily URL 추가 제한 증가 (질문 유형별로 3~8개)
- `tavily_search.py`:
  - 검색 쿼리 개선 (뉴스/공시/토론에 집중)
  - 질문 유형별 `max_results` 조정

---

## 🎯 질문 유형별 전략

### A. 매수 판단형 (QUESTION_TYPE_BUY_RECOMMENDATION)
- **직접 URL**: 시세 페이지만 조회
- **Tavily**: 뉴스, 증권 분석, 시장 전망 검색 (최대 5개)
- **이유**: 투자 판단에는 다양한 정보가 필요하므로 적극적인 검색

### B. 시세 상태형 (QUESTION_TYPE_PRICE_STATUS)
- **직접 URL**: API + HTML 시세 페이지
- **Tavily**: 최소한으로만 사용 (최대 3개)
- **이유**: 시세는 직접 URL로 충분히 확인 가능

### C. 여론 요약형 (QUESTION_TYPE_PUBLIC_OPINION)
- **직접 URL**: 시세 페이지 (참고용)
- **Tavily**: 토론, 의견, 투자자 반응, 커뮤니티 검색 (최대 8개)
- **이유**: 토론 페이지 404로 인해 Tavily 의존도 높음

### D. 뉴스 공시형 (QUESTION_TYPE_NEWS_DISCLOSURE)
- **직접 URL**: 없음 (모두 404)
- **Tavily**: 뉴스, 공시, 기사, 발표 검색 (최대 8개)
- **이유**: 직접 URL이 작동하지 않아 전적으로 Tavily에 의존

### E. 기타 (QUESTION_TYPE_OTHER)
- **직접 URL**: 기본 시세 + 상세 정보 페이지
- **Tavily**: 일반 정보 검색 (최대 3개)

---

## 📦 설치 및 설정

### 1. Tavily 패키지 설치

```bash
pip install tavily-python
```

### 2. Tavily API 키 설정

`.env` 파일에 다음을 추가:

```bash
# Tavily API Key (recommended)
# Get your API key from: https://tavily.com/
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxx
```

### 3. API 키 발급 방법

1. [https://tavily.com](https://tavily.com) 접속
2. 회원가입 및 로그인
3. API 키 발급
4. `.env` 파일에 복사

---

## ✅ 작동 확인

### 테스트 실행

```bash
# 기본 테스트
python test_fetch.py

# Tavily 통합 테스트
python test_tavily_integration.py
```

### 챗봇 실행

```bash
streamlit run app_chat.py
```

### 테스트 질문

1. **시세 확인** (직접 URL 사용)
   ```
   삼성전자 현재가는?
   ```
   → 정상 작동 예상

2. **뉴스 확인** (Tavily 사용)
   ```
   삼성전자 뉴스 보여줘
   ```
   → Tavily가 뉴스 페이지 탐색

3. **토론 확인** (Tavily 사용)
   ```
   삼성전자 사람들 의견은?
   ```
   → Tavily가 토론 페이지 탐색

---

## 📊 예상 결과

### Tavily API 키가 있을 때
- ✅ 시세 정보: 정상 조회
- ✅ 뉴스: Tavily를 통해 조회
- ✅ 공시: Tavily를 통해 조회
- ✅ 토론: Tavily를 통해 조회

### Tavily API 키가 없을 때
- ✅ 시세 정보: 정상 조회
- ⚠️ 뉴스: "최근 뉴스가 없습니다"
- ⚠️ 공시: "최근 공시가 없습니다"
- ⚠️ 토론: "최근 의견이 없습니다"

**권장:** Tavily API 키를 설정하여 완전한 기능을 사용하세요.

---

## 🔒 보안 유지

### Allowlist 강제
- Tavily가 반환한 URL도 `daum_fetch.py`에서 재검증
- `finance.daum.net` 이외의 도메인은 자동 차단
- 보안 정책 변경 없음

### 이중 검증
1. Tavily 검색 시: `include_domains=["finance.daum.net"]` 설정
2. Fetch 시: `daum_fetch.py`의 allowlist 재확인

---

## 💰 비용

### Tavily Free Tier
- 월 1,000회 검색 무료
- 질문당 평균 2-4회 검색 사용
- 약 250-500개 질문 처리 가능

### 예상 사용량
- **시세 질문**: 1회 검색 (직접 URL이 주로 사용됨)
- **매수 판단**: 3회 검색 (뉴스, 분석, 전망)
- **토론 질문**: 4회 검색 (토론, 의견, 반응, 커뮤니티)
- **뉴스 질문**: 4회 검색 (뉴스, 공시, 기사, 발표)

---

## 🐛 문제 해결

### Tavily 검색이 작동하지 않음

```
⚠️ TAVILY_API_KEY not found - skipping Tavily search
```

**해결:**
1. `.env` 파일에 `TAVILY_API_KEY` 추가
2. 앱 재시작

### "최근 뉴스가 없습니다" 메시지

**원인:**
- Tavily API 키가 설정되지 않았거나
- Tavily가 관련 페이지를 찾지 못함

**해결:**
1. Tavily API 키 설정 확인
2. 검색 쿼리가 너무 구체적인지 확인
3. 다음 금융 사이트에서 직접 확인

### 차트 정보가 표시되지 않음

**정상 동작:**
- 차트 API가 제거되어 더 이상 표시되지 않습니다
- 시세 정보만으로도 충분한 답변이 가능합니다

---

## 📚 관련 문서

- [TAVILY_SETUP.md](./TAVILY_SETUP.md): Tavily 상세 설정 가이드
- [README.md](./README.md): 전체 프로젝트 개요
- [TROUBLESHOOTING_DAUM.md](./TROUBLESHOOTING_DAUM.md): 다음 금융 관련 문제 해결

---

## 🎉 결론

### 변경 전
- ❌ 차트 API: 403 에러
- ❌ 뉴스 페이지: 404 에러
- ❌ 공시 페이지: 404 에러
- ❌ 토론 페이지: 404 에러

### 변경 후
- ✅ 차트: 제거 (불필요하다고 판단)
- ✅ 뉴스: Tavily 검색으로 해결
- ✅ 공시: Tavily 검색으로 해결
- ✅ 토론: Tavily 검색으로 해결
- ✅ 시세: 정상 작동 (변경 없음)

**결과:** 
- Tavily API 키가 있으면 모든 기능이 정상 작동합니다
- Tavily API 키가 없어도 시세 정보는 정상 조회됩니다
- 보안 정책은 변경되지 않았습니다 (allowlist 유지)

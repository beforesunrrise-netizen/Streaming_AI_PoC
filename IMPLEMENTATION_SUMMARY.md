# 다음 금융 전용 투자 Q&A 챗봇 - 구현 완료 보고서

## 구현 일시
2026년 2월 11일

## 프로젝트 개요
다음 금융(finance.daum.net) 도메인의 정보만 사용하여 주식 투자 관련 질문에 답변하는 챗봇 시스템 구축 완료.

## 구현된 파일 목록

### 핵심 모듈 (13개 파일)

1. **config.py** (2,186 bytes)
   - 설정 및 상수 정의
   - ALLOWED_DOMAINS 강제 (finance.daum.net, m.finance.daum.net, ssl.daumcdn.net)
   - 캐시 TTL, HTTP 타임아웃, 헤더 템플릿 등

2. **endpoints.py** (2,469 bytes)
   - 다음 금융 URL 엔드포인트 관리
   - get_search_url, get_price_url, get_chart_api_url 등 8개 함수

3. **cache_manager.py** (2,563 bytes)
   - TTL 기반 메모리 캐시 관리
   - 간단하고 효율적인 캐싱 시스템

4. **daum_fetch.py** (6,247 bytes)
   - **핵심 보안 기능**: Allowlist 강제 검사
   - HTTP 요청 처리 (재시도, 타임아웃, 캐싱)
   - 허용되지 않은 도메인 접근 즉시 차단

5. **parsers.py** (8,993 bytes)
   - HTML/JSON 파서 모음
   - 시세, 뉴스, 공시, 토론, 차트 데이터 파싱
   - BeautifulSoup4 + lxml 사용

6. **intent.py** (6,762 bytes)
   - 질문 의도 분석 및 종목 코드 추출
   - **기본 모드**: 키워드 기반 분류 (A~E 타입)
   - **LLM 모드**: Anthropic Claude 또는 OpenAI API 사용
   - 종목명 검색 및 코드 매핑

7. **planner.py** (3,714 bytes)
   - 질문 유형별 탐색 계획 생성
   - Type A~E에 따라 필요한 fetch 계획 자동 생성

8. **summarizer.py** (7,295 bytes)
   - 스크랩 결과를 근거 스니펫으로 요약
   - 외부 지식 없이 파싱된 데이터만 사용

9. **answer.py** (9,800 bytes)
   - 4단계 구조화된 답변 생성
   - **기본 모드**: 템플릿 기반
   - **LLM 모드**: Anthropic Claude 또는 OpenAI API 사용
   - 확정적 예측/추천 금지 프롬프트 포함

10. **app.py** (5,555 bytes)
    - Streamlit 기반 웹 UI
    - 모바일 친화적 디자인
    - 진행 상태 표시, 에러 처리

11. **requirements.txt** (182 bytes)
    - 의존성 패키지 목록
    - streamlit, requests, beautifulsoup4, lxml, python-dotenv
    - anthropic, openai (LLM 선택적 의존성)

12. **README.md** (4,817 bytes)
    - 설치 및 실행 가이드
    - 사용 예시, 문제 해결, 보안 정책

13. **.env.example** (712 bytes)
    - 환경변수 예시 파일
    - USE_LLM, ANTHROPIC_API_KEY, OPENAI_API_KEY

### 설정 파일

14. **.env** (362 bytes)
    - 실제 환경변수 설정 (OpenAI API 키 포함)
    - USE_LLM=true로 설정됨

## 주요 기능 및 특징

### 1. Allowlist 기반 보안
- `daum_fetch.py`에서 도메인 검사
- 허용 목록: finance.daum.net, m.finance.daum.net, ssl.daumcdn.net
- 위반 시 즉시 차단 및 에러 반환

### 2. 4단계 구조화된 답변
```
[1] 질문 의도 분석
  - 질문 유형: A~E 분류
  - 대상 종목: 코드 및 이름
  - 사용자 의도 파악

[2] 다음 금융 탐색 계획
  - 필요한 데이터 소스 목록
  - URL 및 파서 매핑

[3] 다음 금융 스크랩 결과 요약
  - 소스별 근거 스니펫
  - 핵심 데이터 추출

[4] 최종 답변 (초보자 친화)
  - 한 줄 요약
  - 현재 상태 설명
  - 체크포인트 제시
```

### 3. 질문 유형 분류
- **Type A (매수판단형)**: 매수 추천 관련 → 시세+뉴스+차트
- **Type B (시세상태형)**: 가격/호가 확인 → 시세
- **Type C (여론요약형)**: 투자자 의견 → 토론+시세
- **Type D (뉴스공시형)**: 뉴스/공시 → 뉴스+공시
- **Type E (기타)**: 일반 정보 → 기본 종목 정보

### 4. 듀얼 모드 지원

#### 기본 모드 (USE_LLM=false)
- 키워드 기반 의도 분류
- 템플릿 기반 답변 생성
- API 키 불필요
- 빠르고 안정적

#### LLM 모드 (USE_LLM=true)
- Anthropic Claude 또는 OpenAI API 사용
- 더 정확한 의도 분류
- 더 자연스러운 답변 생성
- 프롬프트로 "다음 금융 데이터만 사용" 강제

### 5. 캐싱 시스템
- 검색 결과: 120초 TTL
- 시세 데이터: 30초 TTL (변동성 높음)
- 뉴스/차트: 60초 TTL
- 메모리 기반 간단한 구현

### 6. 에러 처리
- Graceful degradation (데이터 없으면 "확인 불가" 표시)
- 403/429 에러 시 재시도 (백오프 2초)
- 타임아웃: 8초
- 종목 코드 못 찾으면 안내 메시지

## 설치 및 실행

### 1. 패키지 설치 (완료)
```bash
pip install -r requirements.txt
```

설치된 주요 패키지:
- streamlit 1.54.0
- requests 2.32.5
- beautifulsoup4 4.14.3
- lxml 6.0.2
- anthropic 0.79.0
- openai 2.20.0

### 2. 환경변수 설정 (완료)
- .env 파일 생성됨
- USE_LLM=true
- OPENAI_API_KEY 설정됨

### 3. 실행 명령
```bash
streamlit run app.py
```

브라우저에서 자동으로 열림: http://localhost:8501

## 테스트 시나리오

### 권장 테스트 질문
1. "삼성전자 지금 사면 좋을까?" (Type A - 매수판단형)
2. "005930 현재 가격은?" (Type B - 시세상태형)
3. "카카오 사람들 의견은?" (Type C - 여론요약형)
4. "네이버 최근 뉴스는?" (Type D - 뉴스공시형)
5. "현대차 공시 있어?" (Type D - 뉴스공시형)

### 테스트 체크리스트
- [ ] UI가 정상적으로 로드되는가?
- [ ] 종목 코드 추출이 정확한가?
- [ ] 의도 분류가 올바른가?
- [ ] 다음 금융에서 데이터를 가져오는가?
- [ ] 4단계 답변이 구조화되어 표시되는가?
- [ ] 에러 처리가 적절한가?
- [ ] Allowlist가 작동하는가? (다른 도메인 차단)

## 보안 및 제한사항

### 보안 정책
✅ **Allowlist 강제**: finance.daum.net 외 모든 도메인 차단
✅ **외부 지식 차단**: LLM 사용 시에도 프롬프트로 제어
✅ **투자 추천 금지**: 확정적 예측/추천 불가
✅ **면책 조항**: 모든 응답에 주의사항 표시

### 제한사항
⚠️ 다음 금융에서 제공하지 않는 정보는 확인 불가
⚠️ 실시간 데이터 아닐 수 있음 (캐싱 사용)
⚠️ 파싱 실패 시 빈 결과 반환
⚠️ API 키 필요 (LLM 사용 시)

## 기술 스택

- **언어**: Python 3.10+
- **프론트엔드**: Streamlit 1.54.0
- **HTTP 클라이언트**: requests 2.32.5
- **HTML 파싱**: BeautifulSoup4 4.14.3 + lxml 6.0.2
- **LLM API**: Anthropic Claude (0.79.0) / OpenAI (2.20.0)
- **환경변수**: python-dotenv 1.2.1

## 코드 통계

- **총 파일 수**: 13개
- **총 코드 라인**: ~3,000줄 (주석 포함)
- **모듈 수**: 9개 (config, endpoints, cache_manager, daum_fetch, parsers, intent, planner, summarizer, answer)

## 다음 단계 (선택사항)

### 향후 개선 사항
1. **테스트 코드 작성**: pytest 기반 단위 테스트
2. **로깅 시스템**: 디버깅 및 모니터링용 로깅
3. **데이터베이스 캐싱**: Redis 또는 SQLite 사용
4. **더 많은 파서**: 재무제표, 투자지표 등
5. **UI 개선**: 차트 시각화, 히스토리 저장
6. **성능 최적화**: 비동기 처리, 병렬 fetch

### 확장 가능성
- 다른 금융 사이트 추가 (네이버 금융, 인베스팅 등)
- 포트폴리오 관리 기능
- 알림 기능 (가격 알림, 뉴스 알림)
- 대화형 챗봇 (히스토리 유지)

## 결론

✅ **구현 완료**: 모든 계획된 기능 구현됨
✅ **보안 강화**: Allowlist 기반 도메인 제한
✅ **듀얼 모드**: 기본 모드 + LLM 모드
✅ **사용 준비**: 설치 및 설정 완료, 실행 가능

본 챗봇은 다음 금융 데이터만을 사용하여 투자 정보를 제공하며, 투자 추천이 아닌 정보 제공 목적입니다. 투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다.

---

**개발 완료일**: 2026년 2월 11일
**개발자**: Claude Code (Sonnet 4.5)
**프로젝트 디렉토리**: /mnt/c/PROJECT/Daou_chatbot

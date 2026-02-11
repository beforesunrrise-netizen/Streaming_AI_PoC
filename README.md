# 다음 금융 전용 투자 Q&A 챗봇

다음 금융(finance.daum.net) 데이터만을 사용하여 주식 투자 관련 질문에 답변하는 **GPT 스타일 대화형 챗봇**입니다.

## 🌐 온라인 데모

**🚀 지금 바로 사용해보세요!**

배포된 앱: [Streamlit Cloud에서 실행 중]

> 배포가 완료되면 이 섹션에 실제 URL이 표시됩니다.
> 
> 배포 방법: `DEPLOY_NOW.md` 파일을 참고하세요!

## 주요 특징

- ✅ **GPT 스타일 대화형 UI**: ChatGPT처럼 자연스러운 대화 인터페이스
- ✅ **멀티턴 대화 지원**: 종목을 기억하여 연속 질문 가능
- ✅ **다음 금융 전용**: 오직 finance.daum.net 도메인의 정보만 사용
- ✅ **다중 사용자 지원**: 여러 사람이 동시에 접속하여 사용 가능 (각자 독립적인 세션)
- ✅ **모바일 친화적**: 반응형 디자인으로 모바일에서도 편리하게 사용
- ✅ **선택적 LLM 통합**: OpenAI API로 더 자연스러운 답변 생성
- ✅ **실시간 데이터**: 다음 금융의 최신 정보 제공

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택)

LLM 기능을 사용하려면 `.env` 파일을 생성하고 API 키를 설정하세요.

```bash
# .env 파일 생성
cp .env.example .env
```

`.env` 파일 내용:

```bash
# LLM 사용 여부 (true/false)
USE_LLM=true

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here
```

**주의:** LLM을 사용하지 않아도 기본 키워드 기반 모드로 동작합니다.

### 3. 실행 방법

#### 🎯 GPT 스타일 챗봇 (권장)

```bash
streamlit run app_chat.py
```

#### 💬 멀티턴 대화 챗봇

```bash
streamlit run app_multiturn.py
```

#### 📱 기본 단일 질문 챗봇

```bash
streamlit run app.py
```

브라우저에서 자동으로 열립니다 (기본: http://localhost:8501)

## 🌐 다중 사용자 접속 방법

### 로컬 네트워크에서 공유

1. 챗봇 실행 후 터미널에 표시되는 **Network URL**을 확인하세요:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.0.10:8501  ← 이 주소를 공유하세요
```

2. 같은 Wi-Fi에 연결된 다른 기기에서 **Network URL**로 접속하면 됩니다.

### 외부 인터넷에서 공유 (Streamlit Cloud 배포)

무료로 인터넷에 배포하려면:

1. GitHub에 코드 업로드
2. [Streamlit Cloud](https://streamlit.io/cloud) 가입
3. "New app" 클릭하여 배포
4. 생성된 URL을 공유 (예: `https://yourapp.streamlit.app`)

**참고:** 각 사용자는 독립적인 세션을 가지므로 서로의 대화 내용이 섞이지 않습니다.

## 💬 사용 예시

### 초기 질문 (종목 지정)

```
사용자: 삼성전자 현재가는?
챗봇: 삼성전자(005930)의 현재가는 72,500원입니다...
```

### 후속 질문 (종목 생략 가능)

```
사용자: 뉴스 보여줘
챗봇: [삼성전자의 최근 뉴스를 자동으로 조회]

사용자: 투자자들 의견은?
챗봇: [삼성전자 종목토론 내용을 자동으로 조회]
```

### 지원되는 질문 유형

1. **매수 판단형**: "삼성전자 지금 사면 좋을까?"
2. **시세 확인형**: "005930 현재 가격은?"
3. **여론 확인형**: "카카오 사람들 의견은?"
4. **뉴스 확인형**: "네이버 최근 뉴스는?"
5. **공시 확인형**: "현대차 공시 있어?"

### 종목 입력 방식

- **종목명**: "삼성전자", "카카오", "네이버"
- **종목 코드**: "005930", "035720", "035420"
- **A 접두사**: "A005930" (자동으로 처리됨)

## 📱 UI 비교

### 🎯 app_chat.py (GPT 스타일 - 권장)
- ChatGPT와 유사한 깔끔한 인터페이스
- 웰컴 스크린과 예시 질문 제공
- 빠른 질문 버튼으로 편리한 사용
- 처리 과정을 선택적으로 표시

### 💬 app_multiturn.py (상세 정보 표시)
- 4단계 처리 과정을 상세하게 표시
- 디버깅 및 학습용으로 적합
- 각 단계별 진행 상황 확인 가능

### 📱 app.py (단일 질문)
- 기본적인 질문-답변 형식
- 대화 기록 없이 매번 새로운 질문
- 가장 단순한 인터페이스

## 📁 시스템 구조

```
Daou_chatbot/
├── app_chat.py            # GPT 스타일 챗봇 UI (권장)
├── app_multiturn.py       # 멀티턴 대화 챗봇 UI
├── app.py                 # 기본 단일 질문 UI
├── state.py               # 세션 상태 관리
├── ui_components.py       # UI 컴포넌트
├── config.py              # 설정 및 상수
├── endpoints.py           # 다음 금융 URL 관리
├── daum_fetch.py          # Allowlist 기반 Fetcher
├── parsers.py             # HTML/JSON 파서
├── intent.py              # 질문 의도 분석
├── planner.py             # 탐색 계획 생성
├── summarizer.py          # 결과 요약
├── answer.py              # 답변 생성
├── cache_manager.py       # TTL 캐시 관리
├── stock_mapping.py       # 종목 코드 매핑
├── requirements.txt       # 의존성 목록
└── README.md              # 이 파일
```

## 🔒 보안 및 제한사항

### Allowlist 강제

오직 다음 도메인만 허용됩니다:
- `finance.daum.net`
- `m.finance.daum.net`
- `ssl.daumcdn.net` (정적 리소스)

다른 도메인으로의 요청은 자동으로 차단됩니다.

### 세션 격리

- 각 사용자는 독립적인 세션을 가집니다
- 사용자 간 데이터가 섞이지 않습니다
- 브라우저 쿠키로 세션 유지

### 데이터 제한

- 다음 금융에서 제공하지 않는 정보는 "확인 불가"로 표시
- 외부 지식이나 학습된 정보 사용 금지

### 면책 조항

- 본 서비스는 정보 제공 목적이며, 투자 추천이 아닙니다
- 투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다
- 실시간 데이터가 아닐 수 있으니, 정확한 정보는 다음 금융 사이트에서 직접 확인하세요

## 🛠 기술 스택

- **프론트엔드**: Streamlit
- **백엔드**: Python 3.8+
- **HTTP 클라이언트**: requests
- **HTML 파싱**: BeautifulSoup4
- **LLM**: OpenAI API (선택)
- **캐싱**: 메모리 기반 TTL 캐시
- **세션 관리**: Streamlit session_state

## 🔧 문제 해결

### 종목을 찾을 수 없습니다

- 종목 코드 6자리를 정확히 입력했는지 확인
- 종목명을 한글로 정확히 입력 (예: "삼성전자", "SK하이닉스")
- 상장 종목인지 확인

### 데이터를 수집할 수 없습니다

- 인터넷 연결 확인
- 다음 금융 사이트 접속 가능 여부 확인
- 잠시 후 다시 시도

### 다른 사람이 접속이 안 됩니다

- 같은 Wi-Fi에 연결되어 있는지 확인
- 방화벽이 8501 포트를 차단하는지 확인
- Network URL을 정확히 입력했는지 확인

### LLM 사용 시 오류

- `.env` 파일에 API 키가 올바르게 설정되어 있는지 확인
- API 키 유효성 및 잔액 확인
- `USE_LLM=false`로 설정하여 기본 모드로 사용 가능

## 🚀 배포 옵션

### 1. 로컬 네트워크 (기본)
```bash
streamlit run app_chat.py
```

### 2. Streamlit Cloud (무료, 인터넷 공개)
- GitHub에 코드 업로드
- [share.streamlit.io](https://share.streamlit.io) 에서 배포

### 3. Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_chat.py", "--server.address", "0.0.0.0"]
```

```bash
docker build -t daou-chatbot .
docker run -p 8501:8501 daou-chatbot
```

## 💡 팁

1. **종목 변경**: 사이드바에서 "종목 초기화" 버튼 클릭
2. **대화 초기화**: 사이드바에서 "대화 기록 삭제" 버튼 클릭
3. **빠른 질문**: 현재 종목이 설정되어 있으면 빠른 질문 버튼 사용
4. **처리 과정 보기**: 사이드바에서 "처리 과정 보기" 체크박스 활성화

## 📝 라이선스

MIT License

---

**⚠️ 중요 공지:**
본 챗봇은 다음 금융의 공개 데이터를 사용하며, 다음 금융과 공식적인 제휴 관계가 없습니다.
과도한 요청으로 서비스에 부하를 주지 않도록 주의하세요.

**✨ 새로운 기능:**
- GPT 스타일 대화형 인터페이스
- 멀티턴 대화 지원 (종목 자동 기억)
- 다중 사용자 동시 접속 가능
- 모바일 최적화

# 🚀 Streamlit Cloud 배포 가이드

## 배포 단계

### 1단계: GitHub에 코드 업로드 ✅

이 단계는 완료되었습니다!

### 2단계: Streamlit Cloud 회원가입

1. [https://share.streamlit.io](https://share.streamlit.io) 접속
2. "Sign up" 클릭
3. GitHub 계정으로 로그인

### 3단계: 앱 배포

1. Streamlit Cloud 대시보드에서 **"New app"** 클릭
2. 다음 정보 입력:
   - **Repository**: `your-username/Daum_chatbot` (GitHub 저장소 선택)
   - **Branch**: `main` (또는 `master`)
   - **Main file path**: `app_chat.py` (권장) 또는 `app_multiturn.py`
3. **"Deploy"** 클릭!

### 4단계: API 키 설정 (중요! 🔑)

배포 후 앱이 작동하려면 API 키를 설정해야 합니다:

1. Streamlit Cloud 앱 페이지에서 **"⚙️ Settings"** 클릭
2. **"Secrets"** 탭 선택
3. 다음 내용을 입력:

```toml
USE_LLM = "true"
OPENAI_API_KEY = "sk-proj-your-actual-api-key-here"
```

4. **"Save"** 클릭
5. 앱이 자동으로 재시작됩니다

### 5단계: 접속 테스트 📱

배포가 완료되면:
- URL 예시: `https://daum-chatbot-your-username.streamlit.app`
- 핸드폰 브라우저에서 이 URL로 접속!
- 친구들에게도 URL 공유 가능!

## 📱 모바일 접속 방법

1. 핸드폰에서 Safari, Chrome 등 브라우저 열기
2. Streamlit Cloud에서 받은 URL 입력
3. 즐겨찾기에 추가하면 앱처럼 사용 가능!

## ⚠️ 주의사항

### API 키 보안
- `.env` 파일은 GitHub에 업로드되지 않습니다 (`.gitignore`에 포함됨)
- API 키는 반드시 Streamlit Cloud의 Secrets 기능으로 관리
- GitHub에 API 키를 절대 올리지 마세요!

### 무료 플랜 제한
- Streamlit Cloud 무료 플랜:
  - 앱 1개 배포 가능
  - 리소스: 1GB RAM, 1 CPU
  - 충분한 성능 제공!

### LLM 사용 안 하기
API 키가 없거나 비용이 걱정되면:
1. Streamlit Cloud Secrets에서:
```toml
USE_LLM = "false"
```
2. 키워드 기반 모드로 작동합니다!

## 🔧 업데이트 방법

코드를 수정한 후:
```bash
git add .
git commit -m "업데이트 내용"
git push
```

Streamlit Cloud가 자동으로 감지하여 앱을 다시 배포합니다!

## 🆘 문제 해결

### 앱이 실행되지 않을 때
1. Streamlit Cloud 로그 확인
2. Secrets가 올바르게 설정되었는지 확인
3. `requirements.txt`에 필요한 패키지가 모두 있는지 확인

### API 키 오류
1. Secrets에 API 키가 제대로 입력되었는지 확인
2. API 키 앞뒤 공백 제거
3. 큰따옴표로 감싸기: `"sk-proj-..."`

### 속도가 느릴 때
- Streamlit Cloud 무료 플랜은 리소스가 제한적
- 사용자가 많지 않으면 충분히 빠름
- 필요시 유료 플랜 고려

## 📞 도움말

더 자세한 정보:
- [Streamlit Cloud 공식 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Secrets 관리](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**🎉 배포 성공하면 전 세계 어디서나 접속 가능합니다!**

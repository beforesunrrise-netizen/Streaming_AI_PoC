# 🚀 가장 빠른 방법: ngrok으로 즉시 공개!

## 1분 안에 핸드폰으로 접속 가능!

### 방법 1: ngrok 설치 (Windows)

1. **다운로드**: https://ngrok.com/download
2. **압축 해제**: ngrok.exe를 원하는 폴더에 저장
3. **실행**:

```powershell
# 1단계: 챗봇 실행 (터미널 1)
streamlit run app_chat.py

# 2단계: ngrok 실행 (터미널 2 - 새 터미널 열기)
ngrok http 8501
```

4. **완료!** ngrok이 제공하는 URL로 접속
   - 예: `https://abc123.ngrok.io`
   - 이 URL을 핸드폰에서 입력하면 접속됨!

---

### 방법 2: Streamlit Cloud (5분, 영구적)

더 안정적이고 영구적인 URL을 원하면:

1. https://share.streamlit.io 접속
2. GitHub로 로그인
3. New app 클릭
4. 배포! (DEPLOY_NOW.md 참고)

---

## 비교표

| 방법 | 속도 | 장점 | 단점 |
|-----|------|------|------|
| **ngrok** | ⚡ 1분 | 즉시 사용, 디버깅 쉬움 | 컴퓨터 켜져있어야 함 |
| **Streamlit Cloud** | 🕐 5분 | 영구적, 24/7 가용 | 초기 설정 필요 |

---

## 💡 추천: 지금은 ngrok, 나중에 Streamlit Cloud

1. **지금**: ngrok으로 빠르게 테스트
2. **나중**: Streamlit Cloud로 영구 배포

---

## ngrok 설치 가이드

### Windows (간단)

1. https://ngrok.com/download 접속
2. Windows 버전 다운로드
3. 압축 해제
4. 명령어 실행:
   ```
   ngrok http 8501
   ```

### 또는 Chocolatey로 설치:

```powershell
choco install ngrok
```

---

**지금 ngrok을 설치하고 실행하시겠어요?**

설치하시면 제가 바로 실행을 도와드리겠습니다!

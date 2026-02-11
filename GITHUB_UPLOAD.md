# GitHub 업로드 명령어

저장소를 생성한 후 아래 명령어를 실행하세요:

```bash
# GitHub 저장소 연결
git remote add origin https://github.com/beforesunrrise/Daum_chatbot.git

# 코드 업로드
git branch -M main
git push -u origin main
```

또는 SSH를 사용하는 경우:

```bash
git remote add origin git@github.com:beforesunrrise/Daum_chatbot.git
git branch -M main
git push -u origin main
```

## 다음 단계

업로드 후:
1. https://share.streamlit.io 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. 저장소 선택: beforesunrrise/Daum_chatbot
5. Main file: app_chat.py
6. Deploy 클릭!

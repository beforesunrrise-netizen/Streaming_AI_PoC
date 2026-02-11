"""
Streamlit UI for Daum Finance Q&A Chatbot
"""

import streamlit as st
import os
from dotenv import load_dotenv

from intent import analyze_intent
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="다음 금융 투자 Q&A",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stButton > button {
        width: 100%;
        font-size: 18px;
        padding: 0.5rem;
    }
    h1 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 1.4rem;
        margin-top: 1.5rem;
    }
    h3 {
        font-size: 1.2rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📈 다음 금융 기반 투자 Q&A")
st.markdown("**다음 금융(finance.daum.net) 데이터만을 사용하는 투자 정보 챗봇**")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ 설정")

    use_llm = st.checkbox(
        "LLM 사용 (더 자연스러운 답변)",
        value=os.getenv('USE_LLM', 'false').lower() == 'true',
        help="환경변수에 API 키가 설정되어 있어야 합니다"
    )

    st.markdown("---")
    st.markdown("### 사용 예시")
    st.markdown("""
    - 삼성전자 지금 사면 좋을까?
    - 005930 현재 가격은?
    - 카카오 사람들 의견은?
    - 네이버 최근 뉴스는?
    - 현대차 공시 있어?
    """)

    st.markdown("---")
    st.markdown("### ⚠️ 주의사항")
    st.markdown("""
    - 다음 금융 데이터만 사용
    - 투자 판단은 본인 책임
    - 실시간 데이터 아닐 수 있음
    """)

# Main input area
question = st.text_input(
    "질문을 입력하세요",
    placeholder="예: 삼성전자 지금 사면 좋을까?",
    key="question_input"
)

# Ask button
if st.button("🔍 질문하기", type="primary"):
    if not question or question.strip() == "":
        st.warning("질문을 입력해주세요.")
    else:
        # Processing
        with st.spinner("다음 금융에서 정보를 수집하는 중..."):
            try:
                # Step 1: Analyze intent
                intent = analyze_intent(question, use_llm=use_llm)

                # Check if stock code was found
                if not intent.stock_code:
                    st.error("종목 코드를 찾을 수 없습니다. 종목명 또는 6자리 코드를 포함해주세요.")
                    st.info("예: '삼성전자', 'A005930', '005930'")
                    st.stop()

                # Step 2: Create plan
                plans = create_plan(intent)

                if not plans:
                    st.error("탐색 계획을 생성할 수 없습니다.")
                    st.stop()

                # Step 3: Execute plans and fetch data
                fetch_results = []

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, plan in enumerate(plans):
                    status_text.text(f"진행 중: {plan.description}...")

                    # Determine cache TTL based on data type
                    if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
                        cache_ttl = CACHE_TTL_NEWS
                    elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
                        cache_ttl = CACHE_TTL_PRICE
                    else:
                        cache_ttl = CACHE_TTL_SEARCH

                    # Fetch data
                    result = fetch(
                        url=plan.url,
                        use_cache=True,
                        cache_ttl=cache_ttl,
                        is_json=plan.is_json
                    )

                    fetch_results.append((result, plan))

                    # Update progress
                    progress_bar.progress((i + 1) / len(plans))

                status_text.text("데이터 수집 완료!")
                progress_bar.empty()
                status_text.empty()

                # Step 4: Summarize results
                summaries = summarize_results(fetch_results, plans)

                # Step 5: Generate answer
                answer_text = generate_answer(
                    intent=intent,
                    plans=plans,
                    summaries=summaries,
                    use_llm=use_llm
                )

                # Display answer
                st.markdown("---")
                st.markdown(answer_text)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
                st.info("잠시 후 다시 시도해주세요.")

                # Show error details in expander (for debugging)
                with st.expander("오류 상세 정보"):
                    st.code(str(e))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    <p>본 서비스는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다.</p>
    <p>투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다.</p>
</div>
""", unsafe_allow_html=True)

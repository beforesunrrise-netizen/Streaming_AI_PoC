"""
Streamlit UI for Daum Finance Q&A Chatbot with Multi-turn + HITL support
"""

import streamlit as st
import os
from dotenv import load_dotenv

from state import init_session_state
from ui_components import (
    render_step1_intent,
    render_step2_plan,
    render_step3_scraping,
    render_step3_results,
    render_step4_answer,
    render_stock_choice,
    render_failure_options,
    render_chat_history,
    render_context_info,
    render_quick_actions,
    render_progress_indicator
)
from intent import analyze_intent
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH
from endpoints import get_search_url
from parsers import parse_search_results

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="다음 금융 투자 Q&A (멀티턴)",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .stButton > button {
        font-size: 16px;
    }
    h1 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
state = init_session_state(st.session_state)

# Title
st.title("💬 다음 금융 기반 투자 Q&A (멀티턴)")
st.markdown("**연속 질문 가능 | 종목 자동 유지 | 사용자 선택 지원**")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ 설정")

    use_llm = st.checkbox(
        "LLM 사용",
        value=get_env('USE_LLM', 'false').lower() == 'true',
        help="더 자연스러운 답변 (API 키 필요)"
    )

    step_by_step = st.checkbox(
        "단계별 출력",
        value=True,
        help="4단계를 순차적으로 표시"
    )

    st.markdown("---")

    # Context info
    render_context_info(state.memory)

    st.markdown("---")

    # Reset buttons
    if st.button("🔄 대화 초기화", use_container_width=True):
        state.reset()
        st.rerun()

    st.markdown("---")
    st.markdown("### 사용 예시")
    st.markdown("""
    **첫 질문:**
    - 삼성전자 지금 사도 돼?

    **후속 질문 (종목 생략):**
    - 뉴스는?
    - 사람들 의견은?
    - 차트 어때?
    """)

# Main chat area
st.markdown("---")

# Display chat history (전체 히스토리 표시 - GPT 스타일)
if state.chat_history:
    for msg in state.chat_history:
        with st.chat_message(msg.role):
            st.markdown(msg.content)

# Handle pending choice (HITL)
if state.pending_choice.is_pending():
    st.markdown("---")
    with st.container():
        selected_code = render_stock_choice(
            state.pending_choice.candidates,
            key=f"choice_{len(state.chat_history)}"
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            if st.button("✅ 선택 완료", disabled=not selected_code, use_container_width=True):
                if selected_code:
                    # Find selected stock name
                    selected_name = None
                    for candidate in state.pending_choice.candidates:
                        if candidate['code'] == selected_code:
                            selected_name = candidate['name']
                            break

                    # Update memory with selected stock
                    state.memory.update(
                        stock_code=selected_code,
                        stock_name=selected_name
                    )

                    # Add assistant message
                    state.add_assistant_message(
                        f"✅ {selected_name} ({selected_code}) 종목을 선택하셨습니다. 정보를 조회합니다..."
                    )

                    # Clear pending choice
                    original_query = state.pending_choice.original_user_query
                    state.pending_choice.clear()

                    st.rerun()

        with col2:
            if st.button("❌ 취소", use_container_width=True):
                state.pending_choice.clear()
                state.add_assistant_message("종목 선택을 취소했습니다. 다시 질문해주세요.")
                st.rerun()

# Quick action buttons
quick_action = render_quick_actions(state.memory)
if quick_action:
    # Simulate user input
    st.session_state['quick_question'] = quick_action
    st.rerun()

# Chat input
user_input = st.chat_input(
    "질문을 입력하세요 (예: 삼성전자 시세는?)",
    key="chat_input"
)

# Handle quick action
if 'quick_question' in st.session_state:
    user_input = st.session_state['quick_question']
    del st.session_state['quick_question']

# Process user input
if user_input and not state.pending_choice.is_pending():
    # Add user message
    state.add_user_message(user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    # Process the question
    with st.chat_message("assistant"):
        try:
            # STEP 1: Analyze intent
            if step_by_step:
                status1 = st.status("**[1단계] 질문 의도 분석 중...**", expanded=True)

            intent = analyze_intent(user_input, use_llm=use_llm)

            # Check if stock code is missing - use memory if available
            if not intent.stock_code and state.memory.has_stock_context():
                intent.stock_code = state.memory.last_stock_code
                intent.stock_name = state.memory.last_stock_name

            if step_by_step:
                with status1:
                    st.markdown(f"- **질문 유형:** {intent.question_type}")
                    st.markdown(f"- **대상 종목:** {intent.stock_name or '확인 불가'} ({intent.stock_code or '확인 불가'})")
                status1.update(label="**[1단계] 질문 의도 분석 완료 ✓**", state="complete")

            # If still no stock code, check if we need to search
            if not intent.stock_code:
                # Extract stock name for search
                from intent import _extract_stock_name
                stock_name = _extract_stock_name(user_input)

                if stock_name:
                    # Search for stock
                    search_url = get_search_url(stock_name)
                    search_result = fetch(search_url, use_cache=True, cache_ttl=120)

                    if search_result.success:
                        candidates = parse_search_results(search_result.content)

                        if len(candidates) == 0:
                            # No results
                            response = f"'{stock_name}' 종목을 찾을 수 없습니다. 정확한 종목명 또는 6자리 코드를 입력해주세요."
                            st.warning(response)
                            state.add_assistant_message(response)
                            st.stop()

                        elif len(candidates) == 1:
                            # Single result - use it
                            intent.stock_code = candidates[0]['code']
                            intent.stock_name = candidates[0]['name']

                        else:
                            # Multiple results - ask user to choose
                            state.pending_choice.candidates = candidates
                            state.pending_choice.original_user_query = user_input
                            state.pending_choice.next_action = intent.question_type

                            response = f"'{stock_name}' 검색 결과가 여러 개입니다. 아래에서 선택해주세요."
                            st.info(response)
                            state.add_assistant_message(response)
                            st.rerun()
                else:
                    # No stock context at all
                    response = "종목을 알려주세요. (예: 삼성전자, 005930)"
                    st.warning(response)
                    state.add_assistant_message(response)
                    st.stop()

            # Update memory with confirmed stock
            state.memory.update(
                stock_code=intent.stock_code,
                stock_name=intent.stock_name,
                question_type=intent.question_type
            )

            # STEP 2: Create plan
            if step_by_step:
                status2 = st.status("**[2단계] 다음 금융 탐색 계획 수립 중...**", expanded=True)

            plans = create_plan(intent)

            if step_by_step:
                with status2:
                    if plans:
                        for i, plan in enumerate(plans, 1):
                            st.markdown(f"- **Plan {i}:** {plan.description}")
                    else:
                        st.warning("탐색 계획을 생성할 수 없습니다.")
                status2.update(label="**[2단계] 탐색 계획 수립 완료 ✓**", state="complete")

            if not plans:
                response = "탐색 계획을 생성할 수 없습니다."
                st.error(response)
                state.add_assistant_message(response)
                st.stop()

            # STEP 3: Execute plans and fetch data
            if step_by_step:
                status3 = st.status("**[3단계] 다음 금융 데이터 수집 중...**", expanded=True)

            fetch_results = []
            failed_count = 0

            for i, plan in enumerate(plans):
                # Determine cache TTL
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

                if not result.success:
                    failed_count += 1

                # Update progress
                if step_by_step:
                    with status3:
                        st.text(f"진행: {i+1}/{len(plans)} - {plan.description}")

            if step_by_step:
                status3.update(label="**[3단계] 데이터 수집 완료 ✓**", state="complete")

            # Check if all failed
            if failed_count == len(plans):
                response = "다음 금융에서 데이터를 가져올 수 없습니다. 잠시 후 다시 시도해주세요."
                st.error(response)
                state.add_assistant_message(response)
                st.stop()

            # STEP 3.5: Summarize results
            summaries = summarize_results(fetch_results, plans, stock_code=intent.stock_code)

            # Store summaries in memory
            state.memory.last_sources = [
                {"type": s.source_type, "snippet": s.evidence_snippet}
                for s in summaries
            ]

            # Render summaries
            if step_by_step:
                with st.expander("**[3단계] 수집된 데이터 보기**", expanded=False):
                    for i, summary in enumerate(summaries, 1):
                        st.markdown(f"**{i}. {summary.source_type}**")
                        st.code(summary.evidence_snippet, language=None)

            # STEP 4: Generate answer
            if step_by_step:
                status4 = st.status("**[4단계] 최종 답변 생성 중...**", expanded=True)

            answer_text = generate_answer(
                intent=intent,
                plans=plans,
                summaries=summaries,
                use_llm=use_llm
            )

            if step_by_step:
                with status4:
                    st.markdown(answer_text)
                status4.update(label="**[4단계] 최종 답변 생성 완료 ✓**", state="complete")
            else:
                st.markdown(answer_text)

            # Add assistant response to history
            state.add_assistant_message(answer_text)

        except Exception as e:
            error_msg = f"오류가 발생했습니다: {str(e)}"
            st.error(error_msg)
            state.add_assistant_message(error_msg)

            # Show error details
            with st.expander("오류 상세 정보"):
                st.code(str(e))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    <p><strong>💬 멀티턴 대화 모드</strong> | 후속 질문 시 종목 자동 유지</p>
    <p>본 서비스는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다.</p>
</div>
""", unsafe_allow_html=True)

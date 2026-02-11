"""
Streamlit UI for Daum Finance Q&A Chatbot - GPT Style Chat Interface
"""

import streamlit as st
import os
from dotenv import load_dotenv

from state import init_session_state
from intent import analyze_intent, _extract_stock_name
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH, get_env
from endpoints import get_search_url
from parsers import parse_search_results
from conversation import is_general_conversation, generate_conversational_response

# Load environment variables
load_dotenv()


def _process_stock_query(user_input: str, state, show_steps: bool, use_llm: bool):
    """
    Process stock-related query
    """
    response_placeholder = st.empty()

    try:
        # STEP 1: Analyze intent
        if show_steps:
                with st.status("🔍 질문 분석 중...", expanded=False) as status:
                    intent = analyze_intent(user_input, use_llm=use_llm)

                    # Check memory for stock context
                    if not intent.stock_code and state.memory.has_stock_context():
                        intent.stock_code = state.memory.last_stock_code
                        intent.stock_name = state.memory.last_stock_name

                    st.markdown(f"- 질문 유형: **{intent.question_type}**")
                    st.markdown(f"- 대상 종목: **{intent.stock_name or '미확인'}** ({intent.stock_code or '미확인'})")
                    status.update(label="✅ 질문 분석 완료", state="complete")
            else:
                intent = analyze_intent(user_input, use_llm=use_llm)

                if not intent.stock_code and state.memory.has_stock_context():
                    intent.stock_code = state.memory.last_stock_code
                    intent.stock_name = state.memory.last_stock_name

            # If no stock code, try to search
            if not intent.stock_code:
                stock_name = _extract_stock_name(user_input)

                if stock_name:
                    with st.spinner("🔍 종목 검색 중..."):
                        search_url = get_search_url(stock_name)
                        search_result = fetch(search_url, use_cache=True, cache_ttl=120)

                        if search_result.success:
                            candidates = parse_search_results(search_result.content)

                            if len(candidates) == 0:
                                response = f"❌ '{stock_name}' 종목을 찾을 수 없습니다.\n\n정확한 종목명 또는 6자리 코드를 입력해주세요."
                                response_placeholder.markdown(response)
                                state.add_assistant_message(response)
                                st.stop()

                            elif len(candidates) == 1:
                                intent.stock_code = candidates[0]['code']
                                intent.stock_name = candidates[0]['name']
                                st.success(f"✅ {intent.stock_name} 종목을 찾았습니다!")

                            else:
                                # Multiple results - set pending choice
                                state.pending_choice.candidates = candidates
                                state.pending_choice.original_user_query = user_input
                                state.pending_choice.next_action = intent.question_type

                                response = f"🔍 '{stock_name}' 검색 결과가 **{len(candidates)}개** 있습니다.\n\n아래에서 선택해주세요."
                                response_placeholder.markdown(response)
                                state.add_assistant_message(response)
                                st.rerun()
                else:
                    response = "❌ 종목을 알 수 없습니다.\n\n**종목명** 또는 **6자리 코드**를 입력해주세요.\n\n예: `삼성전자`, `005930`"
                    response_placeholder.markdown(response)
                    state.add_assistant_message(response)
                    st.stop()

            # Update memory
            state.memory.update(
                stock_code=intent.stock_code,
                stock_name=intent.stock_name,
                question_type=intent.question_type
            )

            # STEP 2: Create plan
            if show_steps:
                with st.status("📋 정보 수집 계획 수립 중...", expanded=False) as status:
                    plans = create_plan(intent)

                    if plans:
                        for i, plan in enumerate(plans, 1):
                            st.markdown(f"{i}. {plan.description}")
                    status.update(label="✅ 계획 수립 완료", state="complete")
            else:
                plans = create_plan(intent)

            if not plans:
                response = "❌ 정보 수집 계획을 생성할 수 없습니다."
                response_placeholder.markdown(response)
                state.add_assistant_message(response)
                st.stop()

            # STEP 3: Fetch data
            if show_steps:
                with st.status("📊 데이터 수집 중...", expanded=False) as status:
                    fetch_results = []

                    for i, plan in enumerate(plans):
                        st.markdown(f"⏳ {plan.description}...")

                        # Determine cache TTL
                        if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
                            cache_ttl = CACHE_TTL_NEWS
                        elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
                            cache_ttl = CACHE_TTL_PRICE
                        else:
                            cache_ttl = CACHE_TTL_SEARCH

                        result = fetch(
                            url=plan.url,
                            use_cache=True,
                            cache_ttl=cache_ttl,
                            is_json=plan.is_json
                        )

                        fetch_results.append((result, plan))

                    status.update(label="✅ 데이터 수집 완료", state="complete")
            else:
                with st.spinner("📊 다음 금융에서 정보를 가져오는 중..."):
                    fetch_results = []

                    for plan in plans:
                        if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
                            cache_ttl = CACHE_TTL_NEWS
                        elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
                            cache_ttl = CACHE_TTL_PRICE
                        else:
                            cache_ttl = CACHE_TTL_SEARCH

                        result = fetch(
                            url=plan.url,
                            use_cache=True,
                            cache_ttl=cache_ttl,
                            is_json=plan.is_json
                        )

                        fetch_results.append((result, plan))

            # Check if all failed
            failed_count = sum(1 for result, _ in fetch_results if not result.success)

            # If some succeeded, continue with those results
            # Only show error if ALL failed
            if failed_count == len(plans) and failed_count > 0:
                # Show detailed error for debugging
                error_details = []
                for result, plan in fetch_results:
                    if not result.success:
                        error_details.append(f"- {plan.description}: {result.error_message or 'Unknown error'}")

                response = f"❌ 다음 금융에서 데이터를 가져올 수 없습니다.\n\n"

                # Add debug info in development/debugging
                if get_env('DEBUG_MODE', 'false').lower() == 'true':
                    response += "**디버그 정보:**\n" + "\n".join(error_details) + "\n\n"

                response += "잠시 후 다시 시도해주세요."

                response_placeholder.markdown(response)
                state.add_assistant_message(response)
                st.stop()

            elif failed_count > 0:
                # Some failed but some succeeded - show warning
                success_count = len(plans) - failed_count
                st.warning(f"⚠️ 일부 데이터 소스에 접근할 수 없습니다 ({success_count}/{len(plans)} 성공). 사용 가능한 데이터로 답변합니다.")

            # STEP 4: Summarize
            summaries = summarize_results(fetch_results, plans)

            # Store in memory
            state.memory.last_sources = [
                {"type": s.source_type, "snippet": s.evidence_snippet}
                for s in summaries
            ]

            # STEP 5: Generate answer
            if show_steps:
                with st.status("✍️ 답변 생성 중...", expanded=False) as status:
                    answer_text = generate_answer(
                        intent=intent,
                        plans=plans,
                        summaries=summaries,
                        use_llm=use_llm
                    )
                    status.update(label="✅ 답변 생성 완료", state="complete")
            else:
                with st.spinner("✍️ 답변 생성 중..."):
                    answer_text = generate_answer(
                        intent=intent,
                        plans=plans,
                        summaries=summaries,
                        use_llm=use_llm
                    )

            # Display answer
            response_placeholder.markdown(answer_text)

            # Add to history
            state.add_assistant_message(answer_text)

        except Exception as e:
            error_msg = f"❌ **오류가 발생했습니다**\n\n```\n{str(e)}\n```\n\n잠시 후 다시 시도해주세요."
            response_placeholder.markdown(error_msg)
            state.add_assistant_message(error_msg)

# Page configuration
st.set_page_config(
    page_title="다음 금융 투자 챗봇",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for GPT-like interface
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main chat container */
    .main {
        padding: 0;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem 1.5rem;
    }
    
    /* User message background */
    [data-testid="stChatMessageContent"] {
        background-color: transparent;
    }
    
    /* Input styling */
    .stChatInputContainer {
        border-top: 1px solid #e0e0e0;
        padding: 1rem;
        background: white;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Title */
    h1 {
        text-align: center;
        padding: 1.5rem 0;
        margin: 0;
        border-bottom: 1px solid #e0e0e0;
        background: white;
    }
    
    /* Status boxes */
    .element-container:has(.streamlit-expanderHeader) {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Quick action buttons */
    .quick-action-btn {
        background: #f0f0f0;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        display: inline-block;
        font-size: 0.9rem;
    }
    
    .quick-action-btn:hover {
        background: #e0e0e0;
    }
    
    /* Welcome message */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
    }
    
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .welcome-subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .example-questions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .example-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .example-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    
    .example-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .example-text {
        font-size: 0.95rem;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
state = init_session_state(st.session_state)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    
    use_llm = st.checkbox(
        "🤖 AI 답변 사용",
        value=True,  # 기본값을 True로 변경
        help="OpenAI API를 사용하여 더 자연스러운 답변을 생성합니다"
    )
    
    show_steps = st.checkbox(
        "📊 처리 과정 보기",
        value=True,  # 기본값을 True로 변경
        help="데이터 수집 및 분석 과정을 단계별로 표시합니다"
    )
    
    st.markdown("---")
    
    # Current context
    if state.memory.has_stock_context():
        st.markdown("### 📌 현재 종목")
        st.info(f"**{state.memory.last_stock_name}**\n\n({state.memory.last_stock_code})")
        
        if st.button("🔄 종목 초기화", use_container_width=True):
            state.memory.clear()
            st.success("종목이 초기화되었습니다")
            st.rerun()
    
    st.markdown("---")
    
    # Chat history management
    st.markdown("### 💬 대화 관리")
    
    if state.chat_history:
        st.caption(f"총 {len(state.chat_history)}개의 메시지")
        
        if st.button("🗑️ 대화 기록 삭제", use_container_width=True):
            state.reset()
            st.success("대화 기록이 삭제되었습니다")
            st.rerun()
    else:
        st.caption("대화 기록이 없습니다")
    
    st.markdown("---")
    
    # Guide
    st.markdown("### 📖 사용 가이드")
    st.markdown("""
    **💡 질문 예시:**
    - 삼성전자 현재가는?
    - 뉴스 보여줘
    - 투자자들 의견은?
    - 최근 공시 있어?
    
    **🎯 특징:**
    - 후속 질문 시 종목 자동 기억
    - 다음 금융 실시간 데이터
    - 자연스러운 대화 방식
    """)
    
    st.markdown("---")
    st.caption("⚠️ 투자 판단은 본인 책임입니다")

# Main title
st.title("💬 다음 금융 투자 챗봇")

# Welcome screen (only if no chat history)
if not state.chat_history:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-title">다음 금융 투자 챗봇</div>
        <div class="welcome-subtitle">종목 정보를 실시간으로 조회하고 투자 판단을 도와드립니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 질문 예시를 선택하거나 직접 입력해보세요")
    
    # Example questions
    examples = [
        {"icon": "📈", "text": "키움증권 지금 사면 좋을까?"},
        {"icon": "📰", "text": "삼성전자 거래 현황?"},
        {"icon": "💬", "text": "현대차 관련 사람들 의견이 어때?"},
        {"icon": "📊", "text": "네이버 주가는?"},
    ]
    
    cols = st.columns(len(examples))
    for i, (col, example) in enumerate(zip(cols, examples)):
        with col:
            if st.button(
                f"{example['icon']}\n\n{example['text']}", 
                key=f"example_{i}",
                use_container_width=True
            ):
                st.session_state['example_question'] = example['text']
                st.rerun()

# Display chat history
for msg in state.chat_history:
    with st.chat_message(msg.role):
        st.markdown(msg.content)

# Handle stock selection (HITL)
if state.pending_choice.is_pending():
    with st.chat_message("assistant"):
        st.markdown("🔍 **여러 종목이 검색되었습니다. 하나를 선택해주세요:**")
        
        # Display options as buttons
        selected_code = None
        cols = st.columns(min(len(state.pending_choice.candidates), 3))
        
        for idx, candidate in enumerate(state.pending_choice.candidates):
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(
                    f"**{candidate['name']}**\n{candidate['code']}\n{candidate.get('market', '')}",
                    key=f"stock_choice_{candidate['code']}",
                    use_container_width=True
                ):
                    selected_code = candidate['code']
                    selected_name = candidate['name']
                    
                    # Update memory
                    state.memory.update(
                        stock_code=selected_code,
                        stock_name=selected_name
                    )
                    
                    # Add confirmation message
                    state.add_assistant_message(
                        f"✅ **{selected_name} ({selected_code})** 종목을 선택하셨습니다."
                    )
                    
                    # Clear pending and rerun
                    state.pending_choice.clear()
                    st.rerun()
        
        if st.button("❌ 취소", key="cancel_choice"):
            state.pending_choice.clear()
            state.add_assistant_message("종목 선택이 취소되었습니다. 다시 질문해주세요.")
            st.rerun()

# Quick actions (if stock context exists)
if state.memory.has_stock_context() and not state.pending_choice.is_pending():
    with st.container():
        st.markdown("##### 💡 빠른 질문")
        quick_questions = [
            "현재가는?",
            "뉴스 보여줘",
            "투자 의견은?",
            "공시 있어?",
            "차트 어때?"
        ]
        
        cols = st.columns(len(quick_questions))
        for col, question in zip(cols, quick_questions):
            with col:
                if st.button(question, key=f"quick_{question}", use_container_width=True):
                    st.session_state['quick_input'] = question
                    st.rerun()

# Handle quick input
if 'quick_input' in st.session_state:
    user_input = st.session_state['quick_input']
    del st.session_state['quick_input']
elif 'example_question' in st.session_state:
    user_input = st.session_state['example_question']
    del st.session_state['example_question']
else:
    user_input = st.chat_input(
        "질문을 입력하세요... (예: 삼성전자 시세는?)",
        key="chat_input",
        disabled=state.pending_choice.is_pending()
    )

# Process user input
if user_input and not state.pending_choice.is_pending():
    # Add user message
    state.add_user_message(user_input)
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Check if it's a general conversation
    if is_general_conversation(user_input):
        with st.chat_message("assistant"):
            # Prepare stock context for conversational response
            stock_ctx = None
            if state.memory.has_stock_context():
                stock_ctx = {
                    'name': state.memory.last_stock_name,
                    'code': state.memory.last_stock_code
                }
            
            # Generate conversational response
            with st.spinner("💭 생각하는 중..."):
                response = generate_conversational_response(
                    user_input=user_input,
                    chat_history=state.get_recent_messages(6),
                    stock_context=stock_ctx,
                    use_llm=use_llm
                )
            
            st.markdown(response)
            state.add_assistant_message(response)
    else:
        # Process stock-related query
        with st.chat_message("assistant"):
            _process_stock_query(user_input, state, show_steps, use_llm)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.85rem; padding: 1rem;'>
    <p><strong>💬 다음 금융 투자 챗봇</strong></p>
    <p>본 서비스는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다.</p>
    <p>투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다.</p>
</div>
""", unsafe_allow_html=True)

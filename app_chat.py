"""
Streamlit UI for Daum Finance Q&A Chatbot - GPT Style Chat Interface
"""

import streamlit as st
import os
import logging
from dotenv import load_dotenv

from state import init_session_state
from intent import analyze_intent, _extract_stock_name
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH, get_env
from endpoints import get_search_url
from parsers import parse_search_results
from conversation import is_general_conversation, generate_conversational_response
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer

# Load environment variables
load_dotenv()

# Configure logging for Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import LangGraph workflow (optional)
try:
    from graph.workflow import run_workflow
    LANGGRAPH_AVAILABLE = True
    logger.info("✅ LangGraph available - using advanced workflow")
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("⚠️ LangGraph not installed - using traditional workflow (install: pip install langgraph)")


def _process_stock_query(user_input: str, state, show_steps: bool, use_llm: bool):
    """
    Process stock-related query using LangGraph workflow
    """
    try:
        # Log the query
        logger.info(f"Processing stock query with LangGraph: {user_input[:50]}...")
        
        # Prepare chat history for LLM context
        chat_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in state.get_recent_messages(6)
        ]
        
        # Check memory for stock context
        if state.memory.has_stock_context():
            # Add memory context to query
            user_input_with_context = user_input
            logger.info(f"Using stock context: {state.memory.last_stock_name} ({state.memory.last_stock_code})")
        
        # Run LangGraph workflow
        if show_steps:
            # Show processing steps
            with st.spinner("🔍 질문 분석 중..."):
                pass
            
            # Run workflow and show intermediate steps
            with st.expander("🧠 사고 과정 보기 (전문 애널리스트 분석)", expanded=False):
                st.markdown("### 생각중.....")
                
                # Execute workflow
                final_state = run_workflow(
                    user_query=user_input,
                    chat_history=chat_history,
                    show_steps=show_steps,
                    use_llm=use_llm
                )
                
                # Show workflow results
                if final_state.get('intent_analyzed'):
                    st.markdown("### [1단계] 질문 의도 분석 ✅")
                    st.markdown(f"- **질문 유형:** {final_state.get('question_type')}")
                    st.markdown(f"- **대상 종목:** {final_state.get('stock_name')} ({final_state.get('stock_code')})")
                    st.markdown("---")
                
                if final_state.get('plans_created'):
                    st.markdown("### [2단계] 정보 수집 계획 수립 ✅")
                    plans = final_state.get('fetch_plans', [])
                    st.markdown(f"- **수집 계획 수:** {len(plans)}개")
                    
                    # 계획 상세 표시
                    for i, plan in enumerate(plans[:5], 1):
                        plan_title = plan.get('title', 'N/A')
                        plan_url = plan.get('url', '')
                        st.markdown(f"  {i}. {plan_title}")
                    st.markdown("---")
                
                if final_state.get('data_collected'):
                    st.markdown("### [3단계] 데이터 수집 완료 ✅")
                    success = final_state.get('successful_fetches', 0)
                    failed = final_state.get('failed_fetches', 0)
                    st.markdown(f"- **수집 성공:** {success}/{success + failed}개")
                    st.markdown("---")
                
                if final_state.get('summaries_created'):
                    st.markdown("### [4단계] 전문 애널리스트 분석 ✅")
                    summaries = final_state.get('summaries', [])
                    st.markdown(f"- **분석 데이터 소스:** {len(summaries)}개")
                    st.markdown(f"- **총 데이터 토큰:** ~{final_state.get('total_tokens')} tokens")
                    
                    # 수집된 데이터 상세 표시
                    st.markdown("\n**📋 수집된 데이터:**")
                    for i, summary in enumerate(summaries[:5], 1):
                        source_type = summary.get('source_type', 'Unknown')
                        st.markdown(f"  {i}. [{source_type}] ✓")
                        
                        # 간단한 프리뷰
                        snippet = summary.get('evidence_snippet', '')
                        if snippet:
                            preview = snippet[:100].replace('\n', ' ').strip()
                            st.caption(f"   → {preview}...")
                    
                    st.markdown("\n**🔍 분석 프레임워크:**")
                    st.markdown("  ✓ 시세 분석 (Technical Analysis)")
                    st.markdown("  ✓ 뉴스·리포트 분석 (Fundamental Analysis)")
                    st.markdown("  ✓ 시장 반응 분석 (Market Sentiment)")
                    st.markdown("  ✓ 종합 판단 (Synthesis)")
                    st.markdown("---")
                
                st.markdown("### [5단계] 최종 투자 의견 생성 중... ⏳")
            
            with st.spinner("✍️ 최종 답변 생성 중..."):
                pass
        else:
            # Silent mode - just show spinner
            with st.spinner("💭 생각하는 중..."):
                final_state = run_workflow(
                    user_query=user_input,
                    chat_history=chat_history,
                    show_steps=show_steps,
                    use_llm=use_llm
                )
        
        # Check for errors
        if final_state.get('error'):
            error_msg = f"❌ **오류가 발생했습니다**\n\n{final_state['error']}\n\n잠시 후 다시 시도해주세요."
            st.markdown(error_msg)
            state.add_assistant_message(error_msg)
            return
        
        # Check if answer was generated
        if not final_state.get('answer_generated'):
            response = "❌ 답변을 생성할 수 없습니다.\n\n잠시 후 다시 시도해주세요."
            st.markdown(response)
            state.add_assistant_message(response)
            return
        
        # Update memory and check if stock changed
        stock_changed = False
        if final_state.get('stock_code'):
            old_stock_code = state.memory.last_stock_code if state.memory.has_stock_context() else None
            new_stock_code = final_state['stock_code']
            
            # Check if stock changed
            if old_stock_code and old_stock_code != new_stock_code:
                stock_changed = True
            
            state.memory.update(
                stock_code=new_stock_code,
                stock_name=final_state['stock_name'],
                question_type=final_state['question_type']
            )
            
            # Notify user if stock changed
            if stock_changed:
                st.info(f"🔄 종목이 **{final_state['stock_name']} ({new_stock_code})** 으로 변경되었습니다.")
        
        # Display final answer
        answer_text = final_state.get('final_answer', '')
        st.markdown(answer_text)
        
        # Add to history
        state.add_assistant_message(answer_text)
        
    except Exception as e:
        logger.error(f"Error in LangGraph workflow: {str(e)}", exc_info=True)
        error_msg = f"❌ **오류가 발생했습니다**\n\n```\n{str(e)}\n```\n\n잠시 후 다시 시도해주세요."
        st.markdown(error_msg)
        state.add_assistant_message(error_msg)

# Page configuration
st.set_page_config(
    page_title="키움 금융 투자 챗봇",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Light Mobile App Style
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main chat container - Light mobile style */
    .main {
        padding: 0;
        max-width: 100%;
    }
    
    /* Chat container - Light background */
    .stApp {
        background: linear-gradient(180deg, #E8EAF6 0%, #F5F7FA 100%);
    }
    
    /* Title bar - fixed at top */
    h1 {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        text-align: center;
        padding: 1rem 0;
        margin: 0;
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border-bottom: none;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }
    
    /* Chat messages container - scrollable area */
    .main .block-container {
        padding-top: 4rem;
        padding-bottom: 8rem;
        max-width: 48rem;
        margin: 0 auto;
    }
    
    /* Chat message styling - Mobile app style */
    .stChatMessage {
        padding: 1.2rem;
        margin: 0.5rem 0;
        border-radius: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* User message - Light blue bubble */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        margin-left: 2rem;
    }
    
    /* Assistant message - White bubble */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #FFFFFF;
        margin-right: 2rem;
        border: 1px solid #E8EAF6;
    }
    
    /* Message content */
    [data-testid="stChatMessageContent"] {
        background-color: transparent;
    }
    
    /* User message text color */
    .stChatMessage[data-testid="user-message"] [data-testid="stChatMessageContent"] {
        color: #FFFFFF;
    }
    
    /* Assistant message text color */
    .stChatMessage[data-testid="assistant-message"] [data-testid="stChatMessageContent"] {
        color: #2C3E50;
    }
    
    /* Input container - fixed at bottom with stronger emphasis */
    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 999;
        border-top: 2px solid #667EEA;
        padding: 1rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #F5F7FA 100%);
        max-width: 48rem;
        margin: 0 auto;
        box-shadow: 0 -4px 16px rgba(102, 126, 234, 0.15);
    }
    
    /* Input box styling - more prominent */
    .stChatInput > div {
        background-color: #FFFFFF;
        border: 2px solid #667EEA;
        border-radius: 1.5rem;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
    }
    
    .stChatInput textarea {
        background-color: #FFFFFF;
        color: #2C3E50;
        border: none;
        font-size: 1rem;
        font-weight: 500;
    }
    
    .stChatInput textarea:focus {
        border-color: #667EEA;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
    }
    
    .stChatInput textarea::placeholder {
        color: #667EEA;
        font-weight: 400;
    }
    
    /* Button styling - Modern rounded buttons */
    .stButton > button {
        border-radius: 1rem;
        font-weight: 500;
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border: none;
        transition: all 0.2s;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Status boxes - Light theme */
    .element-container:has(.streamlit-expanderHeader) {
        border-radius: 1rem;
        overflow: hidden;
        background-color: #F5F7FA;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #F5F7FA;
        color: #2C3E50;
        border-radius: 1rem;
    }
    
    /* Quick action buttons - Light pill style */
    .stButton button {
        background-color: #FFFFFF;
        color: #667EEA;
        border: 1px solid #E8EAF6;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        color: white;
        border-color: transparent;
    }
    
    /* Welcome message - Light theme */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
        padding: 2rem;
    }
    
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .welcome-subtitle {
        font-size: 1.2rem;
        color: #718096;
        margin-bottom: 2rem;
    }
    
    /* Example cards - Light theme */
    .example-questions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1rem;
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .example-card {
        background: #FFFFFF;
        border: 1px solid #E8EAF6;
        border-radius: 1rem;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .example-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        border-color: #667EEA;
    }
    
    .example-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .example-text {
        font-size: 0.95rem;
        color: #2C3E50;
    }
    
    /* Sidebar styling - Light theme */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E8EAF6;
    }
    
    .css-1d391kg .sidebar-content, [data-testid="stSidebar"] > div:first-child {
        background-color: #FFFFFF;
    }
    
    /* Sidebar text */
    .css-1d391kg, [data-testid="stSidebar"] {
        color: #2C3E50;
    }
    
    /* Info boxes - Light theme */
    .stInfo {
        background: linear-gradient(135deg, #E3F2FD 0%, #E8EAF6 100%);
        color: #2C3E50;
        border: 1px solid #667EEA;
        border-radius: 1rem;
    }
    
    /* Warning boxes */
    .stWarning {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        color: #2C3E50;
        border: 1px solid #FF9800;
        border-radius: 1rem;
    }
    
    /* Success boxes */
    .stSuccess {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        color: #2C3E50;
        border: 1px solid #4CAF50;
        border-radius: 1rem;
    }
    
    /* Markdown text in messages */
    .stMarkdown {
        color: #2C3E50;
    }
    
    /* Links */
    a {
        color: #667EEA;
        text-decoration: none;
    }
    
    a:hover {
        color: #764BA2;
        text-decoration: underline;
    }
    
    /* Code blocks - Light theme */
    code {
        background-color: #F5F7FA;
        color: #667EEA;
        padding: 0.2rem 0.4rem;
        border-radius: 0.5rem;
        border: 1px solid #E8EAF6;
    }
    
    pre {
        background-color: #F5F7FA;
        border: 1px solid #E8EAF6;
        border-radius: 0.75rem;
    }
    
    /* Scrollbar styling - Light theme */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F5F7FA;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #CBD5E0;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #A0AEC0;
    }
    
    /* Spinner - Light theme */
    .stSpinner > div {
        border-top-color: #667EEA !important;
    }
    
    /* Divider */
    hr {
        border-color: #E8EAF6;
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
        value=True,
        help="OpenAI API를 사용하여 더 자연스러운 답변을 생성합니다"
    )
    
    show_steps = st.checkbox(
        "📊 처리 과정 보기",
        value=True,  # 기본값을 False로 변경 - 깔끔한 ChatGPT 스타일
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
        message_count = len(state.chat_history)
        user_count = sum(1 for msg in state.chat_history if msg.role == 'user')
        st.caption(f"총 {message_count}개 메시지 ({user_count}개 질문)")
        
        if st.button("🗑️ 새 대화 시작", use_container_width=True):
            state.reset()
            st.success("새 대화를 시작합니다")
            st.rerun()
    else:
        st.caption("대화를 시작해보세요!")
    
    st.markdown("---")
    
    # Guide - 더 간결하게
    with st.expander("📖 사용 가이드"):
        st.markdown("""
        **💡 이렇게 물어보세요:**
        - 삼성전자 현재가는?
        - 네이버 뉴스 보여줘
        - 카카오 매수하면 좋을까?
        
        **✨ 특징:**
        - 새 종목 질문 시 자동 변경
        - 빠른 질문 버튼으로 편리하게
        - 쉽고 간단한 답변
        """)
    
    st.markdown("---")
    st.caption("⚠️ 투자 판단은 본인 책임입니다")

# Main title
st.title("💬 키움 금융 투자 챗봇")

# Welcome screen (only if no chat history)
if not state.chat_history:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-title">💬 키움 금융 투자 챗봇</div>
        <div class="welcome-subtitle">종목 정보를 실시간으로 조회하고 투자 판단을 도와드립니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 💡 질문 예시를 선택하거나 아래에서 직접 입력해보세요")
    
    # Example questions in a compact grid
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📈 삼성전자 지금 사면 좋을까?", key="ex1", use_container_width=True):
            st.session_state['example_question'] = "삼성전자 지금 사면 좋을까?"
            st.rerun()
        if st.button("💬 현대차 투자자 의견은?", key="ex3", use_container_width=True):
            st.session_state['example_question'] = "현대차 투자자 의견은?"
            st.rerun()
    
    with col2:
        if st.button("📰 네이버 뉴스 보여줘", key="ex2", use_container_width=True):
            st.session_state['example_question'] = "네이버 뉴스 보여줘"
            st.rerun()
        if st.button("💰 카카오 현재가는?", key="ex4", use_container_width=True):
            st.session_state['example_question'] = "카카오 현재가는?"
            st.rerun()

# Display chat history
for msg in state.chat_history:
    with st.chat_message(msg.role):
        st.markdown(msg.content)

# Handle stock selection (HITL)
if state.pending_choice.is_pending():
    st.markdown("### 🔍 종목 선택")
    st.markdown("여러 종목이 검색되었습니다. 하나를 선택해주세요:")
    
    # Display options as cards
    selected_code = None
    
    # Use 3 columns for better layout
    num_cols = min(len(state.pending_choice.candidates), 3)
    cols = st.columns(num_cols)
    
    for idx, candidate in enumerate(state.pending_choice.candidates):
        col_idx = idx % num_cols
        with cols[col_idx]:
            # Create a styled button for each candidate
            button_label = f"**{candidate['name']}**\n\n{candidate['code']}"
            if candidate.get('market'):
                button_label += f"\n\n`{candidate.get('market')}`"
            
            if st.button(
                button_label,
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
    
    st.markdown("")
    
    # Cancel button
    if st.button("❌ 취소", key="cancel_choice", use_container_width=True):
        state.pending_choice.clear()
        state.add_assistant_message("종목 선택이 취소되었습니다. 다시 질문해주세요.")
        st.rerun()
    
    st.markdown("---")

# Quick actions (if stock context exists and no pending choice)
if state.memory.has_stock_context() and not state.pending_choice.is_pending():
    st.markdown("##### 💡 빠른 질문")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("💰 현재가는?", key="quick_1", use_container_width=True):
            st.session_state['quick_input'] = "현재가는?"
            st.rerun()
    
    with col2:
        if st.button("📰 뉴스", key="quick_2", use_container_width=True):
            st.session_state['quick_input'] = "뉴스 보여줘"
            st.rerun()
    
    with col3:
        if st.button("💬 의견", key="quick_3", use_container_width=True):
            st.session_state['quick_input'] = "투자 의견은?"
            st.rerun()
    
    with col4:
        if st.button("📋 공시", key="quick_4", use_container_width=True):
            st.session_state['quick_input'] = "공시 있어?"
            st.rerun()
    
    with col5:
        if st.button("📊 차트", key="quick_5", use_container_width=True):
            st.session_state['quick_input'] = "차트 어때?"
            st.rerun()
    
    st.markdown("---")

# Chat input at the bottom - 항상 렌더링
placeholder_text = "💬 추가 질문을 입력하세요... (예: 목표가는?, 다른 종목 알려줘)" if state.chat_history else "메시지를 입력하세요... (예: 삼성전자 현재가는?)"

user_input = st.chat_input(
    placeholder_text,
    key="chat_input",
    disabled=state.pending_choice.is_pending()
)

# Handle quick input or example question
is_quick_question = False
if 'quick_input' in st.session_state:
    user_input = st.session_state['quick_input']
    is_quick_question = True  # 빠른 질문 플래그 설정
    del st.session_state['quick_input']
elif 'example_question' in st.session_state:
    user_input = st.session_state['example_question']
    del st.session_state['example_question']

# Process user input
if user_input and not state.pending_choice.is_pending():
    # Add user message
    state.add_user_message(user_input)
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 빠른 질문이거나 일반 대화인 경우 간단하게 처리
    if is_quick_question or is_general_conversation(user_input):
        # Prepare stock context for conversational response
        stock_ctx = None
        if state.memory.has_stock_context():
            stock_ctx = {
                'name': state.memory.last_stock_name,
                'code': state.memory.last_stock_code
            }
        
        # Generate conversational response (silent mode)
        with st.spinner("💭"):
            response = generate_conversational_response(
                user_input=user_input,
                chat_history=state.get_recent_messages(6),
                stock_context=stock_ctx,
                use_llm=use_llm
            )
        
        st.markdown(response)
        state.add_assistant_message(response)
        st.rerun()  # 빠른 질문 버튼이 즉시 나타나도록 페이지 새로고침
    else:
        # Process stock-related query
        _process_stock_query(user_input, state, show_steps, use_llm)
        st.rerun()  # 빠른 질문 버튼이 즉시 나타나도록 페이지 새로고침

# Footer - 더 간결하게
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #8e8ea0; font-size: 0.75rem; padding: 0.5rem; margin-top: 2rem;'>
    <p>본 서비스는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다 | 투자 판단은 본인 책임입니다</p>
</div>
""", unsafe_allow_html=True)

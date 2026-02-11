"""
UI components for step-by-step rendering and HITL interactions
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from intent import IntentResult
from planner import FetchPlan
from summarizer import SourceSummary


def render_step1_intent(intent: IntentResult, with_status: bool = True):
    """
    Render STEP 1: Intent Analysis

    Args:
        intent: Intent analysis result
        with_status: Whether to use st.status widget
    """
    if with_status:
        with st.status("**[1단계] 질문 의도 분석 중...**", expanded=True) as status:
            st.markdown(f"- **질문 유형:** {intent.question_type}")
            st.markdown(f"- **대상 종목:** {intent.stock_name or '확인 불가'} ({intent.stock_code or '확인 불가'})")
            status.update(label="**[1단계] 질문 의도 분석 완료 ✓**", state="complete")
    else:
        st.markdown("### [1] 질문 의도 분석")
        st.markdown(f"- **질문 유형:** {intent.question_type}")
        st.markdown(f"- **대상 종목:** {intent.stock_name or '확인 불가'} ({intent.stock_code or '확인 불가'})")


def render_step2_plan(plans: List[FetchPlan], with_status: bool = True):
    """
    Render STEP 2: Exploration Plan

    Args:
        plans: List of fetch plans
        with_status: Whether to use st.status widget
    """
    if with_status:
        with st.status("**[2단계] 다음 금융 탐색 계획 수립 중...**", expanded=True) as status:
            if plans:
                for i, plan in enumerate(plans, 1):
                    st.markdown(f"- **Plan {i}:** {plan.description}")
            else:
                st.warning("탐색 계획을 생성할 수 없습니다 (종목 정보 부족)")
            status.update(label="**[2단계] 탐색 계획 수립 완료 ✓**", state="complete")
    else:
        st.markdown("### [2] 다음 금융 탐색 계획")
        if plans:
            for i, plan in enumerate(plans, 1):
                st.markdown(f"- **Plan {i}:** {plan.description}")
        else:
            st.warning("탐색 계획을 생성할 수 없습니다 (종목 정보 부족)")


def render_step3_scraping(
    plans: List[FetchPlan],
    progress_callback=None,
    with_status: bool = True
):
    """
    Render STEP 3: Scraping Progress

    Args:
        plans: List of fetch plans
        progress_callback: Callback function for progress updates
        with_status: Whether to use st.status widget

    Returns:
        Status widget or None
    """
    if with_status:
        status = st.status("**[3단계] 다음 금융 데이터 수집 중...**", expanded=True)
        return status
    else:
        st.markdown("### [3] 다음 금융 데이터 수집")
        return None


def render_step3_results(summaries: List[SourceSummary], with_status: bool = True):
    """
    Render STEP 3: Scraping Results

    Args:
        summaries: List of source summaries
        with_status: Whether to use st.status widget
    """
    if with_status:
        with st.status("**[3단계] 데이터 수집 완료 ✓**", expanded=False, state="complete") as status:
            if summaries:
                for i, summary in enumerate(summaries, 1):
                    with st.expander(f"**Source {i}: {summary.source_type}**"):
                        st.code(summary.evidence_snippet, language=None)
            else:
                st.warning("수집된 데이터가 없습니다.")
    else:
        st.markdown("### [3] 다음 금융 스크랩 결과 요약")
        if summaries:
            for i, summary in enumerate(summaries, 1):
                with st.expander(f"**Source {i}: {summary.source_type}**"):
                    st.code(summary.evidence_snippet, language=None)
        else:
            st.warning("수집된 데이터가 없습니다.")


def render_step4_answer(answer_text: str, with_status: bool = True):
    """
    Render STEP 4: Final Answer

    Args:
        answer_text: Final answer text
        with_status: Whether to use st.status widget
    """
    if with_status:
        with st.status("**[4단계] 최종 답변 생성 완료 ✓**", expanded=True, state="complete"):
            st.markdown(answer_text)
    else:
        st.markdown("### [4] 최종 답변")
        st.markdown(answer_text)


def render_stock_choice(candidates: List[Dict[str, str]], key: str = "stock_choice") -> Optional[str]:
    """
    Render HITL stock selection interface

    Args:
        candidates: List of stock candidates [{code, name, market}]
        key: Streamlit widget key

    Returns:
        Selected stock code or None
    """
    st.warning("⚠️ 종목이 여러 개 검색되었습니다. 원하시는 종목을 선택해주세요.")

    # Create options
    options = []
    for candidate in candidates:
        code = candidate.get('code', '?')
        name = candidate.get('name', '알 수 없음')
        market = candidate.get('market', '')
        option_text = f"{name} ({code})"
        if market:
            option_text += f" - {market}"
        options.append(option_text)

    # Radio button for selection
    selected = st.radio(
        "종목 선택:",
        options,
        key=key,
        index=None
    )

    # Extract code from selection
    if selected:
        # Find matching candidate
        for i, option in enumerate(options):
            if option == selected:
                return candidates[i]['code']

    return None


def render_failure_options(error_message: str) -> Optional[str]:
    """
    Render HITL failure recovery options

    Args:
        error_message: Error message to display

    Returns:
        User's choice: 'retry', 'change_stock', 'change_type', or None
    """
    st.error(f"❌ {error_message}")

    st.info("다음 중 선택해주세요:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 다시 시도", use_container_width=True):
            return 'retry'

    with col2:
        if st.button("🔀 다른 종목", use_container_width=True):
            return 'change_stock'

    with col3:
        if st.button("📊 다른 정보 보기", use_container_width=True):
            return 'change_type'

    return None


def render_chat_message(role: str, content: str):
    """
    Render a chat message

    Args:
        role: 'user' or 'assistant'
        content: Message content
    """
    with st.chat_message(role):
        st.markdown(content)


def render_chat_history(messages: List):
    """
    Render entire chat history

    Args:
        messages: List of ChatMessage objects
    """
    for msg in messages:
        render_chat_message(msg.role, msg.content)


def render_context_info(memory) -> None:
    """
    Render current conversation context info

    Args:
        memory: ConversationMemory object
    """
    if memory.has_stock_context():
        st.sidebar.markdown("### 📌 현재 컨텍스트")
        st.sidebar.markdown(f"**종목:** {memory.last_stock_name} ({memory.last_stock_code})")
        st.sidebar.markdown(f"**마지막 질문 유형:** {memory.last_question_type}")

        if st.sidebar.button("🗑️ 컨텍스트 초기화", use_container_width=True):
            memory.clear()
            st.rerun()


def render_progress_indicator(current: int, total: int, description: str):
    """
    Render progress indicator

    Args:
        current: Current step
        total: Total steps
        description: Description of current step
    """
    progress = current / total
    st.progress(progress, text=f"진행 중: {description} ({current}/{total})")


def render_quick_actions(memory):
    """
    Render quick action buttons based on context

    Args:
        memory: ConversationMemory object

    Returns:
        Selected action or None
    """
    if not memory.has_stock_context():
        return None

    st.markdown("#### 💡 빠른 질문")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📈 시세 확인", use_container_width=True):
            return "시세는?"

    with col2:
        if st.button("📰 뉴스 보기", use_container_width=True):
            return "뉴스는?"

    with col3:
        if st.button("💬 의견 보기", use_container_width=True):
            return "사람들 의견은?"

    return None

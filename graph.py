"""
LangGraph implementation for multi-turn HITL orchestration (OPTIONAL)

This module provides graph-based workflow orchestration for complex
multi-turn conversations with human-in-the-loop decision points.

Note: This is an optional advanced feature. The basic multi-turn
functionality in app_multiturn.py works without LangGraph.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: langgraph not installed. Graph-based orchestration unavailable.")

from intent import analyze_intent, IntentResult
from planner import create_plan, FetchPlan
from daum_fetch import fetch
from summarizer import summarize_results, SourceSummary
from answer import generate_answer
from endpoints import get_search_url
from parsers import parse_search_results
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH


class GraphState(TypedDict):
    """
    State for LangGraph workflow
    """
    # Input
    user_query: str
    use_llm: bool

    # Intent analysis
    intent: Optional[IntentResult]

    # Stock resolution
    stock_candidates: List[Dict[str, str]]
    selected_stock_code: Optional[str]
    selected_stock_name: Optional[str]

    # Memory (from previous turn)
    memory_stock_code: Optional[str]
    memory_stock_name: Optional[str]

    # Planning
    plans: List[FetchPlan]

    # Fetching
    fetch_results: List[tuple]

    # Summarization
    summaries: List[SourceSummary]

    # Output
    final_answer: str
    error_message: Optional[str]

    # Control
    needs_user_input: bool
    interrupt_reason: Optional[str]


def classify_intent_node(state: GraphState) -> GraphState:
    """
    Node: Classify user intent
    """
    user_query = state['user_query']
    use_llm = state.get('use_llm', False)

    intent = analyze_intent(user_query, use_llm=use_llm)

    state['intent'] = intent
    return state


def resolve_stock_node(state: GraphState) -> GraphState:
    """
    Node: Resolve stock code (with HITL if ambiguous)
    """
    intent = state['intent']

    # Use memory if stock code not found in query
    if not intent.stock_code:
        if state.get('memory_stock_code'):
            intent.stock_code = state['memory_stock_code']
            intent.stock_name = state.get('memory_stock_name')
            state['intent'] = intent
            return state

    # If still no code, try to search
    if not intent.stock_code:
        from intent import _extract_stock_name
        stock_name = _extract_stock_name(state['user_query'])

        if stock_name:
            # Search
            search_url = get_search_url(stock_name)
            search_result = fetch(search_url, use_cache=True, cache_ttl=120)

            if search_result.success:
                candidates = parse_search_results(search_result.content)

                if len(candidates) == 0:
                    state['error_message'] = f"'{stock_name}' 종목을 찾을 수 없습니다."
                    state['needs_user_input'] = True
                    state['interrupt_reason'] = 'no_stock_found'
                    return state

                elif len(candidates) == 1:
                    # Single result - use it
                    intent.stock_code = candidates[0]['code']
                    intent.stock_name = candidates[0]['name']
                    state['intent'] = intent

                else:
                    # Multiple results - need user choice
                    state['stock_candidates'] = candidates
                    state['needs_user_input'] = True
                    state['interrupt_reason'] = 'multiple_stocks'
                    return state
            else:
                state['error_message'] = "종목 검색 중 오류가 발생했습니다."
                state['needs_user_input'] = True
                state['interrupt_reason'] = 'search_failed'
                return state
        else:
            state['error_message'] = "종목을 알려주세요."
            state['needs_user_input'] = True
            state['interrupt_reason'] = 'no_stock_info'
            return state

    return state


def plan_node(state: GraphState) -> GraphState:
    """
    Node: Create exploration plan
    """
    intent = state['intent']
    plans = create_plan(intent)

    state['plans'] = plans

    if not plans:
        state['error_message'] = "탐색 계획을 생성할 수 없습니다."

    return state


def fetch_and_parse_node(state: GraphState) -> GraphState:
    """
    Node: Fetch data and parse (with allowlist enforcement)
    """
    plans = state['plans']
    fetch_results = []

    for plan in plans:
        # Determine cache TTL
        if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
            cache_ttl = CACHE_TTL_NEWS
        elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
            cache_ttl = CACHE_TTL_PRICE
        else:
            cache_ttl = CACHE_TTL_SEARCH

        # Fetch data (allowlist enforced in daum_fetch.py)
        result = fetch(
            url=plan.url,
            use_cache=True,
            cache_ttl=cache_ttl,
            is_json=plan.is_json
        )

        fetch_results.append((result, plan))

    state['fetch_results'] = fetch_results

    # Check if all failed
    failed_count = sum(1 for r, _ in fetch_results if not r.success)
    if failed_count == len(plans):
        state['error_message'] = "다음 금융에서 데이터를 가져올 수 없습니다."
        state['needs_user_input'] = True
        state['interrupt_reason'] = 'all_fetch_failed'

    return state


def summarize_snippets_node(state: GraphState) -> GraphState:
    """
    Node: Summarize fetch results into evidence snippets
    """
    fetch_results = state['fetch_results']
    plans = state['plans']

    summaries = summarize_results(fetch_results, plans)
    state['summaries'] = summaries

    return state


def generate_answer_node(state: GraphState) -> GraphState:
    """
    Node: Generate final answer (LLM input = snippets only)
    """
    intent = state['intent']
    plans = state['plans']
    summaries = state['summaries']
    use_llm = state.get('use_llm', False)

    final_answer = generate_answer(
        intent=intent,
        plans=plans,
        summaries=summaries,
        use_llm=use_llm
    )

    state['final_answer'] = final_answer
    return state


def should_interrupt(state: GraphState) -> str:
    """
    Conditional edge: Check if we need to interrupt for user input
    """
    if state.get('needs_user_input', False):
        return "interrupt"
    return "continue"


def create_workflow() -> StateGraph:
    """
    Create LangGraph workflow for multi-turn HITL

    Returns:
        StateGraph instance
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph is not installed. Run: pip install langgraph")

    # Create workflow
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("resolve_stock", resolve_stock_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("fetch_and_parse", fetch_and_parse_node)
    workflow.add_node("summarize_snippets", summarize_snippets_node)
    workflow.add_node("generate_answer", generate_answer_node)

    # Set entry point
    workflow.set_entry_point("classify_intent")

    # Add edges
    workflow.add_edge("classify_intent", "resolve_stock")

    # Conditional edge after stock resolution
    workflow.add_conditional_edges(
        "resolve_stock",
        should_interrupt,
        {
            "interrupt": END,  # Stop for user input
            "continue": "plan"
        }
    )

    workflow.add_edge("plan", "fetch_and_parse")

    # Conditional edge after fetching
    workflow.add_conditional_edges(
        "fetch_and_parse",
        should_interrupt,
        {
            "interrupt": END,  # Stop if all failed
            "continue": "summarize_snippets"
        }
    )

    workflow.add_edge("summarize_snippets", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow


def compile_workflow(checkpointer=None):
    """
    Compile workflow for execution

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled graph
    """
    workflow = create_workflow()

    if checkpointer is None:
        checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer, interrupt_before=[])


# Example usage function
def run_workflow_example(user_query: str, use_llm: bool = False, memory=None):
    """
    Example of running the workflow

    Args:
        user_query: User's question
        use_llm: Whether to use LLM
        memory: Optional memory dict with previous context

    Returns:
        Final state dict
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph is not installed")

    # Create initial state
    initial_state = {
        "user_query": user_query,
        "use_llm": use_llm,
        "intent": None,
        "stock_candidates": [],
        "selected_stock_code": None,
        "selected_stock_name": None,
        "memory_stock_code": memory.get('stock_code') if memory else None,
        "memory_stock_name": memory.get('stock_name') if memory else None,
        "plans": [],
        "fetch_results": [],
        "summaries": [],
        "final_answer": "",
        "error_message": None,
        "needs_user_input": False,
        "interrupt_reason": None
    }

    # Compile and run
    app = compile_workflow()
    config = {"configurable": {"thread_id": "1"}}

    result = app.invoke(initial_state, config)

    return result


# Note: To use this in Streamlit, you would:
# 1. Call run_workflow_example() with user query
# 2. Check if result['needs_user_input'] is True
# 3. If True, show UI for user input (stock selection, retry options, etc.)
# 4. Resume workflow with updated state

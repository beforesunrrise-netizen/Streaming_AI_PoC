"""
LangGraph Workflow for Daum Finance Chatbot

This workflow orchestrates the entire chatbot process:
1. Intent analysis
2. Plan creation
3. Data fetching
4. Summarization (with token management)
5. Answer generation
"""
import logging
from langgraph.graph import StateGraph, END
from .state import ChatbotState
from .nodes import (
    intent_node,
    plan_node,
    fetch_node,
    summarize_node,
    answer_node
)

logger = logging.getLogger(__name__)


def should_continue_after_intent(state: ChatbotState) -> str:
    """
    Conditional edge after intent analysis
    
    Returns:
        Next node name or END
    """
    if state.get('error'):
        logger.error(f"[Workflow] Error in intent: {state['error']}")
        return END
    
    if not state.get('stock_code'):
        logger.warning("[Workflow] No stock code found, ending")
        return END
    
    return "plan"


def should_continue_after_plan(state: ChatbotState) -> str:
    """
    Conditional edge after plan creation
    
    Returns:
        Next node name or END
    """
    if state.get('error'):
        logger.error(f"[Workflow] Error in plan: {state['error']}")
        return END
    
    if not state.get('fetch_plans') or len(state['fetch_plans']) == 0:
        logger.warning("[Workflow] No fetch plans created, ending")
        return END
    
    return "fetch"


def should_continue_after_fetch(state: ChatbotState) -> str:
    """
    Conditional edge after data fetching
    
    Returns:
        Next node name or END
    """
    if state.get('error'):
        logger.error(f"[Workflow] Error in fetch: {state['error']}")
        return END
    
    # Allow partial success
    if state.get('successful_fetches', 0) == 0:
        logger.warning("[Workflow] All fetches failed, ending")
        return END
    
    return "summarize"


def should_continue_after_summarize(state: ChatbotState) -> str:
    """
    Conditional edge after summarization
    
    Returns:
        Next node name or END
    """
    if state.get('error'):
        logger.error(f"[Workflow] Error in summarize: {state['error']}")
        return END
    
    if not state.get('summaries') or len(state['summaries']) == 0:
        logger.warning("[Workflow] No summaries created, ending")
        return END
    
    return "answer"


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(ChatbotState)
    
    # Add nodes
    workflow.add_node("intent", intent_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("fetch", fetch_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("answer", answer_node)
    
    # Set entry point
    workflow.set_entry_point("intent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "intent",
        should_continue_after_intent,
        {
            "plan": "plan",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "plan",
        should_continue_after_plan,
        {
            "fetch": "fetch",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "fetch",
        should_continue_after_fetch,
        {
            "summarize": "summarize",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "summarize",
        should_continue_after_summarize,
        {
            "answer": "answer",
            END: END
        }
    )
    
    # Answer node ends the workflow
    workflow.add_edge("answer", END)
    
    # Compile graph
    logger.info("[Workflow] Compiling LangGraph workflow")
    return workflow.compile()

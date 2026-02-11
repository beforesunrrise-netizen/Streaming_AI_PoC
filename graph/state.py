"""
LangGraph State definition for Daum Finance Chatbot
"""
from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass


class ChatbotState(TypedDict):
    """
    State for the chatbot workflow
    
    This state is passed through all nodes in the graph.
    LangGraph automatically manages state updates and token limits.
    """
    # User input
    user_query: str
    chat_history: List[Dict[str, str]]  # For multi-turn conversations
    
    # Intent analysis
    intent_analyzed: bool
    stock_code: Optional[str]
    stock_name: Optional[str]
    question_type: Optional[str]
    
    # Planning
    plans_created: bool
    fetch_plans: List[Dict[str, Any]]
    
    # Data collection
    data_collected: bool
    raw_data: List[Dict[str, Any]]
    successful_fetches: int
    failed_fetches: int
    
    # Summarization (with automatic token management)
    summaries_created: bool
    summaries: List[Dict[str, str]]
    total_tokens: int  # Track token usage
    
    # Final answer
    answer_generated: bool
    final_answer: str
    
    # Error handling
    error: Optional[str]
    
    # Metadata
    show_steps: bool  # Whether to show intermediate steps to user
    use_llm: bool     # Whether to use LLM for answer generation


def create_initial_state(
    user_query: str,
    chat_history: List[Dict[str, str]] = None,
    show_steps: bool = False,
    use_llm: bool = True
) -> ChatbotState:
    """
    Create initial state for the workflow
    
    Args:
        user_query: User's question
        chat_history: Previous chat messages
        show_steps: Whether to show intermediate steps
        use_llm: Whether to use LLM for answer generation
        
    Returns:
        Initial ChatbotState
    """
    return ChatbotState(
        # User input
        user_query=user_query,
        chat_history=chat_history or [],
        
        # Intent analysis
        intent_analyzed=False,
        stock_code=None,
        stock_name=None,
        question_type=None,
        
        # Planning
        plans_created=False,
        fetch_plans=[],
        
        # Data collection
        data_collected=False,
        raw_data=[],
        successful_fetches=0,
        failed_fetches=0,
        
        # Summarization
        summaries_created=False,
        summaries=[],
        total_tokens=0,
        
        # Final answer
        answer_generated=False,
        final_answer="",
        
        # Error handling
        error=None,
        
        # Metadata
        show_steps=show_steps,
        use_llm=use_llm
    )

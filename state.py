"""
Conversation state and memory management for multi-turn dialogue
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ChatMessage:
    """
    Single chat message in conversation history
    """
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationMemory:
    """
    Memory of last interaction for multi-turn support
    """
    last_stock_code: Optional[str] = None
    last_stock_name: Optional[str] = None
    last_question_type: Optional[str] = None
    last_sources: List[Dict[str, Any]] = field(default_factory=list)

    def update(
        self,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        question_type: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Update memory with new interaction
        """
        if stock_code:
            self.last_stock_code = stock_code
        if stock_name:
            self.last_stock_name = stock_name
        if question_type:
            self.last_question_type = question_type
        if sources:
            self.last_sources = sources

    def clear(self):
        """
        Clear all memory
        """
        self.last_stock_code = None
        self.last_stock_name = None
        self.last_question_type = None
        self.last_sources = []

    def has_stock_context(self) -> bool:
        """
        Check if there's a previous stock context
        """
        return self.last_stock_code is not None


@dataclass
class PendingChoice:
    """
    Pending user choice for HITL (Human-in-the-Loop)
    """
    candidates: List[Dict[str, str]] = field(default_factory=list)
    original_user_query: str = ""
    next_action: Optional[str] = None  # Question type to proceed with

    def is_pending(self) -> bool:
        """
        Check if there's a pending choice
        """
        return len(self.candidates) > 0

    def clear(self):
        """
        Clear pending choice
        """
        self.candidates = []
        self.original_user_query = ""
        self.next_action = None


@dataclass
class ConversationState:
    """
    Complete conversation state for multi-turn dialogue
    """
    chat_history: List[ChatMessage] = field(default_factory=list)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    pending_choice: PendingChoice = field(default_factory=PendingChoice)

    def add_user_message(self, content: str):
        """
        Add user message to chat history
        """
        self.chat_history.append(ChatMessage(role='user', content=content))

    def add_assistant_message(self, content: str):
        """
        Add assistant message to chat history
        """
        self.chat_history.append(ChatMessage(role='assistant', content=content))

    def get_recent_messages(self, n: int = 10) -> List[ChatMessage]:
        """
        Get recent n messages
        """
        return self.chat_history[-n:] if len(self.chat_history) > n else self.chat_history

    def clear_history(self):
        """
        Clear chat history
        """
        self.chat_history = []

    def reset(self):
        """
        Reset entire state
        """
        self.chat_history = []
        self.memory.clear()
        self.pending_choice.clear()


def init_session_state(st_session_state) -> ConversationState:
    """
    Initialize Streamlit session state for conversation

    Args:
        st_session_state: Streamlit session state object

    Returns:
        ConversationState instance
    """
    if 'conversation_state' not in st_session_state:
        st_session_state.conversation_state = ConversationState()

    return st_session_state.conversation_state

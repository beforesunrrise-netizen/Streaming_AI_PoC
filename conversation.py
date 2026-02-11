"""
GPT-style conversational response generation
Handles general questions and maintains conversation context
"""

from typing import List, Optional
from config import get_env
from state import ChatMessage


def is_general_conversation(user_input: str) -> bool:
    """
    Check if user input is a general conversation (not stock-specific query)
    
    Args:
        user_input: User's input text
        
    Returns:
        True if it's a general conversation, False if it's a stock query
    """
    # Keywords that indicate stock-related queries
    stock_keywords = [
        '종목', '주가', '시세', '매수', '매도', '투자', '거래량', 
        '호가', '뉴스', '공시', '차트', '상한가', '하한가', '등락',
        '전자', '증권', '은행', '화학', '제약', '건설', '자동차'
    ]
    
    # Check if input contains stock-related keywords
    user_input_lower = user_input.lower()
    has_stock_keyword = any(keyword in user_input_lower for keyword in stock_keywords)
    
    # Check if input contains numbers (likely stock codes)
    has_numbers = any(char.isdigit() for char in user_input)
    
    # General conversation patterns
    greeting_patterns = ['안녕', '하이', '헬로', '반가', '좋은']
    question_patterns = ['어떻게', '무엇', '왜', '어디', '누구', '언제']
    thanks_patterns = ['고마', '감사', '땡큐', 'ㄳ']
    
    is_greeting = any(pattern in user_input_lower for pattern in greeting_patterns)
    is_question = any(pattern in user_input_lower for pattern in question_patterns)
    is_thanks = any(pattern in user_input_lower for pattern in thanks_patterns)
    
    # Short messages (< 5 chars) are usually general
    is_short = len(user_input) < 5
    
    # Decision logic
    if has_stock_keyword or has_numbers:
        return False  # Stock query
    
    if is_greeting or is_thanks or (is_short and not has_stock_keyword):
        return True  # General conversation
    
    return False


def generate_conversational_response(
    user_input: str,
    chat_history: List[ChatMessage],
    stock_context: Optional[dict] = None,
    use_llm: bool = True
) -> str:
    """
    Generate conversational response using LLM
    
    Args:
        user_input: User's input text
        chat_history: Recent chat history
        stock_context: Current stock context (if any)
        use_llm: Whether to use LLM (default: True)
        
    Returns:
        Conversational response text
    """
    # Fallback responses for common patterns (when LLM is not available)
    if not use_llm:
        return _generate_fallback_response(user_input, stock_context)
    
    # Check if LLM is available
    api_key = get_env('ANTHROPIC_API_KEY') or get_env('OPENAI_API_KEY')
    if not api_key:
        return _generate_fallback_response(user_input, stock_context)
    
    # Prepare conversation history
    history_text = ""
    if chat_history:
        recent_history = chat_history[-6:]  # Last 3 exchanges
        for msg in recent_history:
            role = "사용자" if msg.role == "user" else "챗봇"
            history_text += f"{role}: {msg.content}\n"
    
    # Prepare stock context
    context_text = ""
    if stock_context:
        context_text = f"\n현재 대화 중인 종목: {stock_context.get('name', '없음')} ({stock_context.get('code', '없음')})"
    
    # Create prompt
    prompt = f"""당신은 친근하고 도움이 되는 다음 금융 투자 챗봇입니다.

**역할:**
- 사용자와 자연스럽게 대화합니다
- 주식/투자에 관한 질문에는 다음 금융 데이터 기반으로 답변할 수 있음을 안내합니다
- 친절하고 간결하게 응답합니다

**대화 기록:**
{history_text}

**현재 상황:**{context_text}

**사용자 입력:** {user_input}

**응답 가이드:**
1. 인사말에는 친근하게 답하고 무엇을 도와드릴지 물어봅니다
2. 감사 인사에는 자연스럽게 응대합니다
3. 일반 질문에는 챗봇의 기능을 간단히 설명합니다
4. 2-3문장으로 간결하게 답변합니다
5. 이모지는 적절히 사용합니다 (😊, 📈, 💡 등)

자연스럽게 응답해주세요:"""

    try:
        # Use Anthropic Claude
        if get_env('ANTHROPIC_API_KEY'):
            import anthropic
            
            client = anthropic.Anthropic(api_key=get_env('ANTHROPIC_API_KEY'))
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
        
        # Use OpenAI
        elif get_env('OPENAI_API_KEY'):
            from openai import OpenAI
            
            client = OpenAI(api_key=get_env('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content
        
        # Fallback
        return _generate_fallback_response(user_input, stock_context)
        
    except Exception as e:
        print(f"Error in conversational response: {e}")
        return _generate_fallback_response(user_input, stock_context)


def _generate_fallback_response(user_input: str, stock_context: Optional[dict] = None) -> str:
    """
    Generate fallback response without LLM
    
    Args:
        user_input: User's input text
        stock_context: Current stock context
        
    Returns:
        Fallback response text
    """
    user_input_lower = user_input.lower()
    
    # Greetings
    if any(word in user_input_lower for word in ['안녕', '하이', '헬로', '반가']):
        if stock_context:
            return f"안녕하세요! 😊\n\n현재 **{stock_context['name']}** 종목에 대해 대화 중이시네요. 궁금한 점을 물어보세요!"
        else:
            return "안녕하세요! 다음 금융 투자 챗봇입니다. 😊\n\n종목 정보, 시세, 뉴스 등을 확인할 수 있어요. 무엇을 도와드릴까요?"
    
    # Thanks
    if any(word in user_input_lower for word in ['고마', '감사', '땡큐', 'ㄳ']):
        return "천만에요! 😊 다른 궁금한 점이 있으시면 언제든 물어보세요."
    
    # Help
    if any(word in user_input_lower for word in ['도움', '사용법', '기능', '어떻게']):
        return """**💡 사용 가이드**

이렇게 물어보세요:
- "삼성전자 주가는?" (시세 확인)
- "네이버 뉴스 보여줘" (뉴스 확인)
- "카카오 사면 좋을까?" (투자 정보)
- "키움증권 의견은?" (투자자 의견)

종목명 또는 6자리 코드를 입력하시면 됩니다!"""
    
    # Goodbye
    if any(word in user_input_lower for word in ['잘가', '안녕히', '바이', 'bye']):
        return "안녕히 가세요! 좋은 투자 되시길 바랍니다. 📈"
    
    # Default
    if stock_context:
        return f"현재 **{stock_context['name']}** 종목에 대해 무엇이 궁금하신가요?\n\n예: 현재가는? / 뉴스 보여줘 / 투자 의견은?"
    else:
        return "무엇을 도와드릴까요? 😊\n\n종목명을 말씀해주시면 관련 정보를 찾아드릴게요.\n\n예: 삼성전자, 네이버, 카카오"


def should_use_conversational_mode(user_input: str, stock_context: Optional[dict] = None) -> bool:
    """
    Decide whether to use conversational mode or stock query mode
    
    Args:
        user_input: User's input text
        stock_context: Current stock context
        
    Returns:
        True if conversational mode should be used
    """
    # Very short inputs
    if len(user_input.strip()) < 2:
        return True
    
    # Check for general conversation
    if is_general_conversation(user_input):
        return True
    
    # Check if it's a follow-up question that needs context
    follow_up_words = ['그래서', '그럼', '그런데', '근데', '그리고', '또', '더', '추가로']
    starts_with_followup = any(user_input.startswith(word) for word in follow_up_words)
    
    # If starts with follow-up word and has stock context, use conversational mode
    if starts_with_followup and stock_context:
        return False  # Actually, we want to continue with stock context
    
    return False

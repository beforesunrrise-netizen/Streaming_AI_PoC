"""
Question intent analysis and stock code extraction
"""

import re
import os
from typing import Optional
from dataclasses import dataclass

from config import (
    QUESTION_TYPE_BUY_RECOMMENDATION,
    QUESTION_TYPE_PRICE_STATUS,
    QUESTION_TYPE_PUBLIC_OPINION,
    QUESTION_TYPE_NEWS_DISCLOSURE,
    QUESTION_TYPE_OTHER,
    KEYWORDS_BUY,
    KEYWORDS_PRICE,
    KEYWORDS_OPINION,
    KEYWORDS_NEWS
)
from endpoints import get_search_url
from daum_fetch import fetch
from parsers import parse_search_results


@dataclass
class IntentResult:
    """
    Result of intent analysis
    """
    question_type: str
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    keywords: list = None
    confidence: float = 1.0


def _extract_stock_code(text: str) -> Optional[str]:
    """
    Extract stock code from text
    Args:
        text: Question text
    Returns:
        Stock code (6 digits) or None
    """
    # Pattern 1: A + 6 digits
    match = re.search(r'A(\d{6})', text)
    if match:
        return match.group(1)

    # Pattern 2: Just 6 digits
    match = re.search(r'\b(\d{6})\b', text)
    if match:
        return match.group(1)

    return None


def _extract_stock_name(text: str) -> Optional[str]:
    """
    Extract Korean stock name from text
    Args:
        text: Question text
    Returns:
        Stock name or None
    """
    # Common Korean company names pattern
    # This is a simple heuristic - may need improvement
    match = re.search(r'([가-힣]{2,10}(?:전자|중공업|제약|바이오|화학|건설|증권|은행|카드|생명|화재|그룹)?)', text)
    if match:
        candidate = match.group(1)
        # Filter out common non-company words
        exclude = ['사람들', '의견', '뉴스', '공시', '가격', '시세', '거래량', '지금', '요즘', '최근']
        if candidate not in exclude:
            return candidate

    return None


def _search_stock_code(stock_name: str) -> Optional[tuple]:
    """
    Search for stock code by name using stock mapping and Daum Finance search
    Args:
        stock_name: Stock name to search
    Returns:
        (code, name) tuple or None
    """
    try:
        # First, try stock mapping (fast and reliable)
        from stock_mapping import get_stock_code
        mapping_result = get_stock_code(stock_name)
        if mapping_result:
            return mapping_result

        # Fallback to Daum Finance search
        url = get_search_url(stock_name)
        result = fetch(url, use_cache=True, cache_ttl=120)

        if not result.success or not result.content:
            return None

        search_results = parse_search_results(result.content)

        if search_results:
            # Return first result
            first = search_results[0]
            return (first['code'], first['name'])

        return None

    except Exception:
        return None


def _classify_question_basic(text: str) -> str:
    """
    Classify question using keyword matching (basic mode)
    Args:
        text: Question text
    Returns:
        Question type
    """
    text_lower = text.lower()

    # Check each category
    if any(keyword in text_lower for keyword in KEYWORDS_BUY):
        return QUESTION_TYPE_BUY_RECOMMENDATION

    if any(keyword in text_lower for keyword in KEYWORDS_PRICE):
        return QUESTION_TYPE_PRICE_STATUS

    if any(keyword in text_lower for keyword in KEYWORDS_OPINION):
        return QUESTION_TYPE_PUBLIC_OPINION

    if any(keyword in text_lower for keyword in KEYWORDS_NEWS):
        return QUESTION_TYPE_NEWS_DISCLOSURE

    return QUESTION_TYPE_OTHER


def _classify_question_llm(text: str) -> tuple:
    """
    Classify question using LLM (optional mode)
    Args:
        text: Question text
    Returns:
        (question_type, confidence) tuple
    """
    try:
        # Check if LLM is available
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Fallback to basic mode
            return (_classify_question_basic(text), 0.5)

        prompt_text = f"""다음 질문을 분석하여 유형을 분류하세요.

질문: {text}

유형:
- A_매수판단형: 매수/투자 추천 관련 질문
- B_시세상태형: 가격/시세/호가/거래량 확인 질문
- C_여론요약형: 사람들 의견/토론/반응 확인 질문
- D_뉴스공시형: 뉴스/공시/이슈 확인 질문
- E_기타: 위에 해당하지 않는 질문

다음 형식으로만 답변하세요:
유형: [A_매수판단형/B_시세상태형/C_여론요약형/D_뉴스공시형/E_기타]
신뢰도: [0.0-1.0]"""

        response_text = ""

        # Use Anthropic Claude if available
        if os.getenv('ANTHROPIC_API_KEY'):
            import anthropic
            from config import LLM_MODEL_ANTHROPIC, LLM_MAX_TOKENS, LLM_TEMPERATURE

            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            message = client.messages.create(
                model=LLM_MODEL_ANTHROPIC,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt_text}]
            )

            response_text = message.content[0].text

        # Use OpenAI if Anthropic is not available
        elif os.getenv('OPENAI_API_KEY'):
            from openai import OpenAI
            from config import LLM_MODEL_OPENAI, LLM_MAX_TOKENS, LLM_TEMPERATURE

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model=LLM_MODEL_OPENAI,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt_text}]
            )

            response_text = response.choices[0].message.content

        # Parse response
        if response_text:
            type_match = re.search(r'유형:\s*([A-E]_[가-힣]+)', response_text)
            conf_match = re.search(r'신뢰도:\s*(0?\.\d+|1\.0)', response_text)

            if type_match:
                question_type = type_match.group(1)
                confidence = float(conf_match.group(1)) if conf_match else 0.8
                return (question_type, confidence)

        # Fallback to basic mode
        return (_classify_question_basic(text), 0.5)

    except Exception:
        # Fallback to basic mode
        return (_classify_question_basic(text), 0.5)


def analyze_intent(question: str, use_llm: bool = False) -> IntentResult:
    """
    Analyze question intent and extract stock information

    Args:
        question: User's question
        use_llm: Whether to use LLM for classification (default: False)

    Returns:
        IntentResult object
    """
    # Extract stock code directly from question
    stock_code = _extract_stock_code(question)

    # Extract stock name
    stock_name = _extract_stock_name(question)

    # If we have name but not code, search for it
    if stock_name and not stock_code:
        search_result = _search_stock_code(stock_name)
        if search_result:
            stock_code, stock_name = search_result

    # Classify question
    if use_llm:
        question_type, confidence = _classify_question_llm(question)
    else:
        question_type = _classify_question_basic(question)
        confidence = 1.0

    # Extract keywords (simple word splitting for now)
    keywords = [word for word in question.split() if len(word) > 1]

    return IntentResult(
        question_type=question_type,
        stock_code=stock_code,
        stock_name=stock_name,
        keywords=keywords,
        confidence=confidence
    )

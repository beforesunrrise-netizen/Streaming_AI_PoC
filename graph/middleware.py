"""
LangGraph Middleware for Token Management
Automatically summarizes content when token limit is exceeded
"""
import logging
from typing import Dict, Any, List
from config import get_env

logger = logging.getLogger(__name__)

# Token limits
MAX_EVIDENCE_TOKENS = 8000  # Maximum tokens for evidence before summarization
MAX_SUMMARY_LENGTH = 500    # Maximum characters per summary snippet


def estimate_tokens(text: str) -> int:
    """
    Estimate token count (rough approximation)
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    # Rough estimate: 1 token ≈ 4 characters for English, 1.5 chars for Korean
    # Use conservative estimate
    return len(text) // 2


def truncate_summary(text: str, max_length: int = MAX_SUMMARY_LENGTH) -> str:
    """
    Truncate summary to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length - 3] + "..."


def compress_summaries_if_needed(summaries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Compress summaries if total tokens exceed limit
    
    Args:
        summaries: List of summary dictionaries
        
    Returns:
        Compressed summaries
    """
    # Calculate total tokens
    total_text = ' '.join([s.get('evidence_snippet', '') for s in summaries])
    total_tokens = estimate_tokens(total_text)
    
    logger.info(f"[Middleware] Total tokens: {total_tokens}")
    
    # If under limit, return as is
    if total_tokens <= MAX_EVIDENCE_TOKENS:
        logger.info(f"[Middleware] Tokens under limit, no compression needed")
        return summaries
    
    # Compression needed
    logger.warning(f"[Middleware] Tokens exceed limit ({total_tokens} > {MAX_EVIDENCE_TOKENS}), compressing...")
    
    compressed = []
    for summary in summaries:
        compressed_summary = summary.copy()
        
        # Truncate evidence snippet
        original_snippet = summary.get('evidence_snippet', '')
        compressed_snippet = truncate_summary(original_snippet, MAX_SUMMARY_LENGTH)
        
        compressed_summary['evidence_snippet'] = compressed_snippet
        compressed.append(compressed_summary)
    
    # Recalculate tokens
    new_total_text = ' '.join([s.get('evidence_snippet', '') for s in compressed])
    new_total_tokens = estimate_tokens(new_total_text)
    
    logger.info(f"[Middleware] Compression complete: {total_tokens} → {new_total_tokens} tokens")
    
    return compressed


def smart_summarize_with_llm(summaries: List[Dict[str, str]], max_tokens: int = 2000) -> str:
    """
    Use LLM to intelligently summarize when data is too large
    
    Args:
        summaries: List of summary dictionaries
        max_tokens: Maximum allowed tokens
        
    Returns:
        Condensed summary text
    """
    try:
        # Check if LLM is available
        api_key = get_env('OPENAI_API_KEY') or get_env('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("[Middleware] No LLM API key, using simple truncation")
            # Fall back to simple compression
            compressed = compress_summaries_if_needed(summaries)
            return '\n\n'.join([
                f"[{s['source_type']}]\n{s['evidence_snippet']}"
                for s in compressed
            ])
        
        # Prepare content for summarization
        full_content = '\n\n'.join([
            f"[{s['source_type']}]\n{s['evidence_snippet']}"
            for s in summaries
        ])
        
        # Use OpenAI for smart summarization
        if get_env('OPENAI_API_KEY'):
            from openai import OpenAI
            
            client = OpenAI(api_key=get_env('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for summarization
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": f"""다음은 다음 금융에서 수집한 데이터입니다. 핵심 정보만 간결하게 요약해주세요.

**원본 데이터:**
{full_content}

**요약 지침:**
- 시세, 뉴스, 의견 등 각 카테고리별 핵심만 추출
- 구체적인 숫자와 사실만 포함
- 불필요한 수식어 제거
- 최대한 간결하게

요약:"""
                }]
            )
            
            summarized = response.choices[0].message.content
            logger.info(f"[Middleware] LLM summarization complete")
            return summarized
        
        # Use Anthropic if available
        elif get_env('ANTHROPIC_API_KEY'):
            import anthropic
            
            client = anthropic.Anthropic(api_key=get_env('ANTHROPIC_API_KEY'))
            
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",  # Use faster model for summarization
                max_tokens=max_tokens,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""다음은 다음 금융에서 수집한 데이터입니다. 핵심 정보만 간결하게 요약해주세요.

**원본 데이터:**
{full_content}

**요약 지침:**
- 시세, 뉴스, 의견 등 각 카테고리별 핵심만 추출
- 구체적인 숫자와 사실만 포함
- 불필요한 수식어 제거
- 최대한 간결하게

요약:"""
                }]
            )
            
            summarized = message.content[0].text
            logger.info(f"[Middleware] LLM summarization complete")
            return summarized
    
    except Exception as e:
        logger.error(f"[Middleware] LLM summarization failed: {str(e)}")
        # Fall back to simple compression
        compressed = compress_summaries_if_needed(summaries)
        return '\n\n'.join([
            f"[{s['source_type']}]\n{s['evidence_snippet']}"
            for s in compressed
        ])

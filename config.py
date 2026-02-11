"""
Configuration and constants for the Daum Finance Q&A Chatbot
"""
import os
import streamlit as st

# Allowlist: Only these domains are allowed
ALLOWED_DOMAINS = [
    "finance.daum.net",
    "m.finance.daum.net",
    "ssl.daumcdn.net",
]

# Cache TTL settings (in seconds)
CACHE_TTL_PRICE = 60      # 1 minute for price data
CACHE_TTL_NEWS = 300      # 5 minutes for news
CACHE_TTL_SEARCH = 120    # 2 minutes for search results
CACHE_TTL_DEFAULT = 300   # Default cache TTL (5 minutes)

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# HTTP request settings
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

DEFAULT_TIMEOUT = 10      # Request timeout in seconds
RETRY_DELAY = 1           # Delay between retries in seconds
MAX_RETRIES = 2           # Maximum number of retries

# Question type constants
QUESTION_TYPE_BUY_RECOMMENDATION = "A_매수판단형"
QUESTION_TYPE_PRICE_STATUS = "B_시세상태형"
QUESTION_TYPE_PUBLIC_OPINION = "C_여론요약형"
QUESTION_TYPE_NEWS_DISCLOSURE = "D_뉴스공시형"
QUESTION_TYPE_OTHER = "E_기타"

# Keywords for each question type
KEYWORDS_BUY = [
    "매수", "사야", "살까", "투자", "추천", "사는게", "살만", "사볼만", "추천해", 
    "사도될까", "사도돼", "괜찮을까", "어때", "어떨까", "사면", "좋을까", "좋나", "좋아"
]

KEYWORDS_PRICE = [
    "가격", "시세", "얼마", "호가", "현재가", "가격은", "시세는", "거래량", 
    "매수호가", "매도호가", "상한가", "하한가", "등락률"
]

KEYWORDS_OPINION = [
    "의견", "토론", "반응", "평가", "생각", "사람들", "여론", "댓글", 
    "분위기", "인식", "느낌"
]

KEYWORDS_NEWS = [
    "뉴스", "공시", "이슈", "소식", "발표", "기사", "언론", "보도", 
    "공개", "최근", "요즘"
]

# LLM settings
LLM_MODEL_ANTHROPIC = "claude-3-5-sonnet-20241022"
LLM_MODEL_OPENAI = "gpt-4o-mini"
LLM_MAX_TOKENS = 1024
LLM_TEMPERATURE = 0.3

# Function to get environment variables (compatible with both local .env and Streamlit Cloud Secrets)
def get_env(key: str, default: str = None) -> str:
    """
    Get environment variable from either:
    1. Streamlit secrets (when deployed)
    2. OS environment variables (local)
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    # Fall back to OS environment variables (for local development)
    return os.getenv(key, default)

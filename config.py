"""
Configuration and constants for Daum Finance Q&A Chatbot
"""

# Allowlist - Only these domains are allowed
ALLOWED_DOMAINS = [
    "finance.daum.net",
    "m.finance.daum.net",
    "ssl.daumcdn.net"  # For static resources
]

# HTTP Request Settings
DEFAULT_TIMEOUT = 8  # seconds
RETRY_DELAY = 2  # seconds for backoff
MAX_RETRIES = 1  # Number of retries on 403/429

# Default headers template
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

# Cache settings (TTL in seconds)
CACHE_TTL_SEARCH = 120  # Search results
CACHE_TTL_PRICE = 30    # Price/quote data (more volatile)
CACHE_TTL_NEWS = 60     # News list
CACHE_TTL_CHART = 60    # Chart data
CACHE_TTL_TALKS = 60    # Discussions/talks
CACHE_TTL_DEFAULT = 60  # Default TTL

# LLM Settings (optional)
USE_LLM_DEFAULT = False  # Can be overridden by environment variable
LLM_MODEL_ANTHROPIC = "claude-sonnet-4-5-20250929"
LLM_MODEL_OPENAI = "gpt-4-turbo-preview"
LLM_MAX_TOKENS = 1000
LLM_TEMPERATURE = 0.3  # Lower for more deterministic responses

# Question types
QUESTION_TYPE_BUY_RECOMMENDATION = "A_매수판단형"
QUESTION_TYPE_PRICE_STATUS = "B_시세상태형"
QUESTION_TYPE_PUBLIC_OPINION = "C_여론요약형"
QUESTION_TYPE_NEWS_DISCLOSURE = "D_뉴스공시형"
QUESTION_TYPE_OTHER = "E_기타"

# Keywords for intent classification (basic mode)
KEYWORDS_BUY = ["사면", "살까", "사도", "사야", "추천", "매수", "투자하면", "괜찮을까", "좋을까", "어때", "괜찮나"]
KEYWORDS_PRICE = ["가격", "시세", "호가", "거래량", "현재가", "종가", "얼마"]
KEYWORDS_OPINION = ["의견", "토론", "사람들", "반응", "여론", "평가"]
KEYWORDS_NEWS = ["뉴스", "공시", "이슈", "발표", "소식"]

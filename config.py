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

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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

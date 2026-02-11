"""
Daum Finance URL endpoint management
All URLs for Daum Finance pages and APIs
"""

def get_search_url(query: str) -> str:
    """
    Get search URL for stock search
    Args:
        query: Stock name or code to search
    Returns:
        Search URL
    """
    from urllib.parse import quote
    return f"https://finance.daum.net/search/search?q={quote(query)}"


def get_price_url(code: str) -> str:
    """
    Get price/quote page URL
    Args:
        code: Stock code (6 digits, with or without 'A' prefix)
    Returns:
        Price page URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/quotes/{clean_code}"


def get_chart_api_url(code: str, period: str = "days") -> str:
    """
    Get chart data API URL
    Args:
        code: Stock code
        period: 'days', 'weeks', 'months' (default: 'days')
    Returns:
        Chart API URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/api/charts/{clean_code}/{period}"


def get_news_url(code: str, page: int = 1) -> str:
    """
    Get news list URL for a stock
    Args:
        code: Stock code
        page: Page number (default: 1)
    Returns:
        News list URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/quotes/{clean_code}/news?page={page}"


def get_disclosure_url(code: str, page: int = 1) -> str:
    """
    Get disclosure list URL for a stock
    Args:
        code: Stock code
        page: Page number (default: 1)
    Returns:
        Disclosure list URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/quotes/{clean_code}/disclosures?page={page}"


def get_talks_url(code: str) -> str:
    """
    Get talks/discussion page URL
    Args:
        code: Stock code
    Returns:
        Talks page URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/quotes/{clean_code}/talks"


def get_stock_info_url(code: str) -> str:
    """
    Get basic stock information page URL
    Args:
        code: Stock code
    Returns:
        Stock info URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/quotes/{clean_code}/company"


def get_realtime_quote_api(code: str) -> str:
    """
    Get realtime quote API endpoint (if available)
    This is an internal API that Daum Finance might use
    Args:
        code: Stock code
    Returns:
        API URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/api/quote/{clean_code}"


def get_finance_api_url(code: str) -> str:
    """
    Alternative API endpoint for stock data
    Args:
        code: Stock code
    Returns:
        API URL
    """
    # Add 'A' prefix if not exists
    clean_code = code if code.startswith('A') else f'A{code}'
    return f"https://finance.daum.net/api/quotes/{clean_code}"

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
    # Remove 'A' prefix if exists
    clean_code = code.replace('A', '') if code.startswith('A') else code
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
    clean_code = code.replace('A', '') if code.startswith('A') else code
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
    clean_code = code.replace('A', '') if code.startswith('A') else code
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
    clean_code = code.replace('A', '') if code.startswith('A') else code
    return f"https://finance.daum.net/quotes/{clean_code}/disclosures?page={page}"


def get_talks_url(code: str) -> str:
    """
    Get talks/discussion page URL
    Args:
        code: Stock code
    Returns:
        Talks page URL
    """
    clean_code = code.replace('A', '') if code.startswith('A') else code
    return f"https://finance.daum.net/quotes/{clean_code}/talks"


def get_stock_info_url(code: str) -> str:
    """
    Get basic stock information page URL
    Args:
        code: Stock code
    Returns:
        Stock info URL
    """
    clean_code = code.replace('A', '') if code.startswith('A') else code
    return f"https://finance.daum.net/quotes/{clean_code}/company"

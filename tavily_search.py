"""
Tavily integration for searching finance.daum.net URLs
Tavily is ONLY used for finding URLs within finance.daum.net
Actual data collection is done by web_fetch with allowlist enforcement
"""

from typing import List, Optional
from dataclasses import dataclass
from config import get_env


@dataclass
class TavilySearchResult:
    """
    Result from Tavily search
    """
    title: str
    url: str
    score: float = 0.0


def search_daum_finance_urls(
    query: str,
    stock_name: Optional[str] = None,
    stock_code: Optional[str] = None,
    max_results: int = 5
) -> List[TavilySearchResult]:
    """
    Search for URLs within finance.daum.net using Tavily

    IMPORTANT: This function ONLY returns URLs.
    Do NOT use Tavily's content/summary - only use URLs for web_fetch.

    Args:
        query: User question
        stock_name: Stock name (optional, for context)
        stock_code: Stock code (optional, for context)
        max_results: Maximum number of URLs to return (default: 5)

    Returns:
        List of TavilySearchResult objects with URLs only
    """
    try:
        from tavily import TavilyClient

        # Get API key
        api_key = get_env('TAVILY_API_KEY')
        if not api_key:
            print("⚠️ TAVILY_API_KEY not found - skipping Tavily search")
            return []

        # Initialize client
        client = TavilyClient(api_key=api_key)

        # Build search query - enforce site:finance.daum.net
        search_query = f"site:finance.daum.net {query}"

        # Add stock context if available
        if stock_name:
            search_query += f" {stock_name}"
        if stock_code:
            search_query += f" {stock_code}"

        # Execute search
        # CRITICAL: Only use include_domains to ensure finance.daum.net only
        response = client.search(
            query=search_query,
            search_depth="basic",
            max_results=max_results,
            include_domains=["finance.daum.net"],
            include_answer=False,  # Don't use Tavily's answer
            include_raw_content=False,  # Don't use Tavily's content
        )

        # Extract URLs only - ignore content/summary
        results = []
        for item in response.get('results', []):
            url = item.get('url', '')
            title = item.get('title', '')
            score = item.get('score', 0.0)

            # Verify domain (double-check)
            if 'finance.daum.net' in url:
                results.append(TavilySearchResult(
                    title=title,
                    url=url,
                    score=score
                ))

        return results

    except ImportError:
        print("⚠️ tavily-python not installed - skipping Tavily search")
        print("   Install with: pip install tavily-python")
        return []

    except Exception as e:
        print(f"⚠️ Tavily search failed: {str(e)}")
        return []


def get_tavily_urls_by_question_type(
    question_type: str,
    stock_name: Optional[str] = None,
    stock_code: Optional[str] = None
) -> List[str]:
    """
    Get relevant URLs from Tavily based on question type

    Args:
        question_type: Question type (A_매수판단형, B_시세상태형, etc.)
        stock_name: Stock name
        stock_code: Stock code

    Returns:
        List of URLs from finance.daum.net
    """
    from config import (
        QUESTION_TYPE_BUY_RECOMMENDATION,
        QUESTION_TYPE_PRICE_STATUS,
        QUESTION_TYPE_PUBLIC_OPINION,
        QUESTION_TYPE_NEWS_DISCLOSURE,
    )

    # Define search queries based on question type
    # Focus on news/disclosures/talks since direct URLs often return 404
    queries = []

    if question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
        # For buy recommendations, search for news and analysis
        queries = [
            f"{stock_name} 최신 뉴스",
            f"{stock_name} 증권 분석",
            f"{stock_name} 시장 전망"
        ]

    elif question_type == QUESTION_TYPE_PRICE_STATUS:
        # For price queries, minimal Tavily usage (direct URLs work fine)
        queries = [
            f"{stock_name} 현재가 시세"
        ]

    elif question_type == QUESTION_TYPE_PUBLIC_OPINION:
        # For opinions, aggressively search for community discussions
        queries = [
            f"{stock_name} 토론",
            f"{stock_name} 의견",
            f"{stock_name} 투자자 반응",
            f"{stock_name} 커뮤니티"
        ]

    elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
        # For news/disclosures, focus heavily on finding these pages
        queries = [
            f"{stock_name} 뉴스",
            f"{stock_name} 공시",
            f"{stock_name} 기사",
            f"{stock_name} 발표"
        ]

    else:
        queries = [f"{stock_name} 정보"]

    # Collect URLs from all queries
    all_urls = set()

    # Increase max_results for question types that need more URL discovery
    if question_type in [QUESTION_TYPE_NEWS_DISCLOSURE, QUESTION_TYPE_PUBLIC_OPINION]:
        max_results_per_query = 5  # More aggressive for problematic types
    else:
        max_results_per_query = 3

    for query in queries:
        results = search_daum_finance_urls(
            query=query,
            stock_name=stock_name,
            stock_code=stock_code,
            max_results=max_results_per_query
        )

        for result in results:
            all_urls.add(result.url)

    return list(all_urls)

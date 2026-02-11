"""
Exploration plan generation based on question intent
Combines direct URL generation + Tavily search for comprehensive coverage
"""

import logging
from typing import List
from dataclasses import dataclass

from config import (
    QUESTION_TYPE_BUY_RECOMMENDATION,
    QUESTION_TYPE_PRICE_STATUS,
    QUESTION_TYPE_PUBLIC_OPINION,
    QUESTION_TYPE_NEWS_DISCLOSURE,
    QUESTION_TYPE_OTHER
)
from intent import IntentResult
from endpoints import (
    get_price_url,
    get_chart_api_url,
    get_news_url,
    get_disclosure_url,
    get_talks_url,
    get_stock_info_url,
    get_realtime_quote_api,
    get_finance_api_url
)
from tavily_search import get_tavily_urls_by_question_type, get_tavily_news_by_question_type

logger = logging.getLogger(__name__)


@dataclass
class FetchPlan:
    """
    Plan for a single fetch operation
    """
    plan_id: str
    description: str
    url: str
    parser_name: str
    is_json: bool = False
    title: str = None  # Optional: pre-fetched title (for Tavily news results)

    @property
    def source_type(self) -> str:
        """Alias for description for backward compatibility"""
        return self.description


def create_plan(intent: IntentResult, use_tavily: bool = True) -> List[FetchPlan]:
    """
    Create exploration plan based on intent
    Combines direct URL generation + Tavily search for comprehensive coverage

    Args:
        intent: IntentResult from intent analysis
        use_tavily: Whether to use Tavily for additional URL discovery (default: True)

    Returns:
        List of FetchPlan objects
    """
    logger.info(f"Creating plan for question_type={intent.question_type}, stock={intent.stock_name} ({intent.stock_code})")
    
    plans = []

    # If no stock code found, return empty plan
    if not intent.stock_code:
        logger.warning(f"No stock code found in intent, returning empty plan")
        return plans

    code = intent.stock_code
    question_type = intent.question_type

    # Type A: Buy recommendation - need price + news
    if question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
        plans.append(FetchPlan(
            plan_id="A1",
            description="현재 시세 정보 확인",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))

        # Get latest news from Tavily
        logger.info(f"[Planner] Getting latest news from Tavily for {intent.stock_name}")
        try:
            news_results = get_tavily_news_by_question_type(
                question_type=question_type,
                stock_name=intent.stock_name,
                stock_code=intent.stock_code,
                max_results=3  # Latest 3 news articles
            )

            for i, news in enumerate(news_results, 1):
                plans.append(FetchPlan(
                    plan_id=f"A{i+1}",
                    description="최신 뉴스",
                    url=news.url,
                    parser_name="tavily_news",
                    title=news.title
                ))

            logger.info(f"[Planner] Added {len(news_results)} news articles from Tavily")

        except Exception as e:
            logger.error(f"[Planner] Failed to get Tavily news: {str(e)}")

    # Type B: Price status - need price + quote (no chart API)
    elif question_type == QUESTION_TYPE_PRICE_STATUS:
        # Try API endpoint first
        plans.append(FetchPlan(
            plan_id="B1",
            description="실시간 시세 API 조회",
            url=get_finance_api_url(code),
            parser_name="parse_api_quote",
            is_json=True
        ))
        # HTML page as backup
        plans.append(FetchPlan(
            plan_id="B2",
            description="시세 페이지 조회 (백업)",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))

    # Type C: Public opinion - need talks/discussions
    # Note: Direct talk URLs often return 404, rely on Tavily search
    elif question_type == QUESTION_TYPE_PUBLIC_OPINION:
        plans.append(FetchPlan(
            plan_id="C1",
            description="현재 시세 확인 (참고용)",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))
        # Talks/opinions will be searched via Tavily

    # Type D: News/disclosure - use Tavily for news with titles
    elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
        # Use Tavily to get latest news with titles (top 3)
        logger.info(f"[Planner] Getting latest news from Tavily for {intent.stock_name}")
        try:
            news_results = get_tavily_news_by_question_type(
                question_type=question_type,
                stock_name=intent.stock_name,
                stock_code=intent.stock_code,
                max_results=3  # Latest 3 news articles
            )

            for i, news in enumerate(news_results, 1):
                plans.append(FetchPlan(
                    plan_id=f"D{i}",
                    description="최신 뉴스",
                    url=news.url,
                    parser_name="tavily_news",  # Special parser that uses pre-fetched title
                    title=news.title  # Store the title from Tavily
                ))

            logger.info(f"[Planner] Added {len(news_results)} news articles from Tavily")

        except Exception as e:
            logger.error(f"[Planner] Failed to get Tavily news: {str(e)}")

        # Still add disclosure URL as fallback
        plans.append(FetchPlan(
            plan_id="D99",
            description="공시 페이지 조회",
            url=get_disclosure_url(code),
            parser_name="parse_disclosure_list"
        ))
        # Additional URLs will be searched via Tavily

    # Type E: Other - basic stock info
    else:
        # Try API first for better data
        plans.append(FetchPlan(
            plan_id="E1",
            description="실시간 시세 API 조회",
            url=get_finance_api_url(code),
            parser_name="parse_api_quote",
            is_json=True
        ))
        plans.append(FetchPlan(
            plan_id="E2",
            description="기본 종목 정보 확인",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))
        plans.append(FetchPlan(
            plan_id="E3",
            description="종목 상세 정보 확인",
            url=get_stock_info_url(code),
            parser_name="parse_price_page"  # Reuse price parser for now
        ))

    # STEP 2: Enhance with Tavily search results
    # Tavily is used ONLY for finding additional URLs within finance.daum.net
    # This helps discover pages that direct URL generation might miss
    # Especially important for news/disclosures/talks which often return 404
    if use_tavily:
        try:
            logger.info(f"[Planner] Requesting Tavily URLs for {intent.stock_name}")
            print(f"[Planner] Using Tavily to find additional URLs for {intent.stock_name}")

            tavily_urls = get_tavily_urls_by_question_type(
                question_type=question_type,
                stock_name=intent.stock_name,
                stock_code=intent.stock_code
            )

            logger.info(f"[Planner] Tavily returned {len(tavily_urls)} URLs")
            print(f"[Planner] Tavily found {len(tavily_urls)} additional URLs")

        except Exception as e:
            # If Tavily fails, continue with existing plans
            logger.error(f"[Planner] Tavily search failed: {str(e)}", exc_info=True)
            print(f"[Planner] Tavily search failed: {str(e)}")
            tavily_urls = []

        # Add Tavily URLs that aren't duplicates
        existing_urls = {plan.url for plan in plans}
        tavily_plan_counter = 1

        # Set limit based on question type
        # For problematic types (news/disclosures/talks), allow more Tavily URLs
        if question_type in [QUESTION_TYPE_NEWS_DISCLOSURE, QUESTION_TYPE_PUBLIC_OPINION]:
            max_tavily_additions = 8  # More URLs for problematic types
        elif question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
            max_tavily_additions = 5  # Moderate for buy recommendations
        else:
            max_tavily_additions = 3  # Default for price queries

        for url in tavily_urls:
            if url not in existing_urls:
                # Skip individual article URLs (React SPAs that require JavaScript)
                # These URLs have patterns like: /news/stock/[article_id] or /news/[article_id]
                if _is_individual_article_url(url):
                    logger.info(f"[Planner] Skipping individual article URL (React SPA): {url}")
                    continue

                # Determine parser based on URL pattern
                parser_name = _infer_parser_from_url(url)

                plans.append(FetchPlan(
                    plan_id=f"T{tavily_plan_counter}",
                    description=f"Tavily 추천 페이지 {tavily_plan_counter}",
                    url=url,
                    parser_name=parser_name,
                    is_json=url.endswith('.json') or '/api/' in url
                ))

                tavily_plan_counter += 1
                existing_urls.add(url)

                # Limit based on question type
                if tavily_plan_counter > max_tavily_additions:
                    break

    logger.info(f"Created {len(plans)} plans for execution")
    return plans


def _is_individual_article_url(url: str) -> bool:
    """
    Check if URL is an individual article page (React SPA)
    These pages require JavaScript to render and cannot be parsed from HTML

    Args:
        url: URL to check

    Returns:
        True if it's an individual article URL, False otherwise
    """
    import re

    # Pattern 1: /news/stock/[article_id] or /news/economy/[article_id]
    if re.search(r'/news/(stock|economy|industry|world)/[a-zA-Z0-9]+$', url):
        return True

    # Pattern 2: /news/[numeric_article_id]
    if re.search(r'/news/\d{14,}$', url):
        return True

    # Pattern 3: Mobile site individual articles
    if 'm.finance.daum.net' in url and re.search(r'/(news|disclosure)/', url) and not url.endswith('/news') and not url.endswith('/disclosures'):
        return True

    return False


def _infer_parser_from_url(url: str) -> str:
    """
    Infer appropriate parser based on URL pattern

    Args:
        url: URL to analyze

    Returns:
        Parser name
    """
    url_lower = url.lower()

    if '/api/charts/' in url_lower:
        return 'parse_chart_json'
    elif '/api/' in url_lower:
        return 'parse_api_quote'
    elif '/news' in url_lower:
        return 'parse_news_list'
    elif '/disclosures' in url_lower:
        return 'parse_disclosure_list'
    elif '/talks' in url_lower:
        return 'parse_talks_list'
    elif '/company' in url_lower:
        return 'parse_price_page'
    else:
        # Default to price page parser
        return 'parse_price_page'

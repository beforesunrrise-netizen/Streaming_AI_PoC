"""
Exploration plan generation based on question intent
"""

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
    get_stock_info_url
)


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


def create_plan(intent: IntentResult) -> List[FetchPlan]:
    """
    Create exploration plan based on intent

    Args:
        intent: IntentResult from intent analysis

    Returns:
        List of FetchPlan objects
    """
    plans = []

    # If no stock code found, return empty plan
    if not intent.stock_code:
        return plans

    code = intent.stock_code
    question_type = intent.question_type

    # Type A: Buy recommendation - need price + news + chart
    if question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
        plans.append(FetchPlan(
            plan_id="A1",
            description="현재 시세 정보 확인",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))
        plans.append(FetchPlan(
            plan_id="A2",
            description="최근 뉴스 확인",
            url=get_news_url(code),
            parser_name="parse_news_list"
        ))
        plans.append(FetchPlan(
            plan_id="A3",
            description="차트 데이터 확인 (최근 추세)",
            url=get_chart_api_url(code),
            parser_name="parse_chart_json",
            is_json=True
        ))

    # Type B: Price status - need price + quote
    elif question_type == QUESTION_TYPE_PRICE_STATUS:
        plans.append(FetchPlan(
            plan_id="B1",
            description="현재 시세 및 호가 정보 확인",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))

    # Type C: Public opinion - need talks/discussions
    elif question_type == QUESTION_TYPE_PUBLIC_OPINION:
        plans.append(FetchPlan(
            plan_id="C1",
            description="토론/의견 확인",
            url=get_talks_url(code),
            parser_name="parse_talks_list"
        ))
        plans.append(FetchPlan(
            plan_id="C2",
            description="현재 시세 확인 (참고용)",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))

    # Type D: News/disclosure - need news + disclosure
    elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
        plans.append(FetchPlan(
            plan_id="D1",
            description="최근 뉴스 확인",
            url=get_news_url(code),
            parser_name="parse_news_list"
        ))
        plans.append(FetchPlan(
            plan_id="D2",
            description="최근 공시 확인",
            url=get_disclosure_url(code),
            parser_name="parse_disclosure_list"
        ))

    # Type E: Other - basic stock info
    else:
        plans.append(FetchPlan(
            plan_id="E1",
            description="기본 종목 정보 확인",
            url=get_price_url(code),
            parser_name="parse_price_page"
        ))
        plans.append(FetchPlan(
            plan_id="E2",
            description="종목 상세 정보 확인",
            url=get_stock_info_url(code),
            parser_name="parse_price_page"  # Reuse price parser for now
        ))

    return plans

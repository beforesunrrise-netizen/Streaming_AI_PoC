"""
Scraping result summarization
Converts fetch results into evidence snippets
"""

from typing import List, Dict, Any
from dataclasses import dataclass

from daum_fetch import FetchResult
import parsers


@dataclass
class SourceSummary:
    """
    Summary of a single data source
    """
    source_url: str
    source_type: str
    key_data: Dict[str, Any]
    evidence_snippet: str


def _summarize_price_data(data: Dict[str, Any]) -> str:
    """
    Create evidence snippet for price data
    Args:
        data: Parsed price data
    Returns:
        Evidence snippet string
    """
    if not data:
        return "시세 정보를 확인할 수 없습니다."

    parts = []

    if 'current_price' in data and data['current_price']:
        price = data['current_price']
        if isinstance(price, (int, float)):
            parts.append(f"현재가 {price:,}원")
        else:
            parts.append(f"현재가 {price}")

    if 'change' in data and 'change_rate' in data:
        parts.append(f"전일비 {data['change']} ({data['change_rate']})")

    if 'volume' in data and data['volume']:
        volume = data['volume']
        if isinstance(volume, (int, float)):
            parts.append(f"거래량 {volume:,}")
        else:
            parts.append(f"거래량 {volume}")

    if 'open_price' in data and data['open_price']:
        parts.append(f"시가 {data['open_price']}")

    if 'high_price' in data and 'low_price' in data:
        if data['high_price'] and data['low_price']:
            parts.append(f"고가 {data['high_price']}, 저가 {data['low_price']}")

    # Add data source info if available
    if 'data_source' in data:
        if data['data_source'] == 'chart_api':
            parts.append("(차트 API 기준)")
    
    # Add date info if available
    if 'date' in data and data['date']:
        parts.append(f"[{data['date']}]")

    return ", ".join(parts) if parts else "시세 정보를 확인할 수 없습니다."


def _summarize_news_data(news_list: List[Dict[str, str]]) -> str:
    """
    Create evidence snippet for news data
    Args:
        news_list: List of news items
    Returns:
        Evidence snippet string
    """
    if not news_list:
        return "최근 뉴스가 없습니다."

    # Take top 5 news
    top_news = news_list[:5]
    snippets = []

    for i, news in enumerate(top_news, 1):
        title = news.get('title', '제목 없음')
        date = news.get('date', '')
        snippet = f"{i}. {title}"
        if date:
            snippet += f" ({date})"
        snippets.append(snippet)

    return "\n".join(snippets)


def _summarize_talks_data(talks_list: List[Dict[str, str]]) -> str:
    """
    Create evidence snippet for talks/opinion data
    Args:
        talks_list: List of talk items
    Returns:
        Evidence snippet string
    """
    if not talks_list:
        return "최근 의견이 없습니다."

    # Take top 5 talks
    top_talks = talks_list[:5]
    snippets = []

    for i, talk in enumerate(top_talks, 1):
        content = talk.get('content', '내용 없음')[:100]  # Limit length
        date = talk.get('date', '')
        snippet = f"{i}. {content}"
        if date:
            snippet += f" ({date})"
        snippets.append(snippet)

    return "\n".join(snippets)


def _summarize_disclosure_data(disc_list: List[Dict[str, str]]) -> str:
    """
    Create evidence snippet for disclosure data
    Args:
        disc_list: List of disclosure items
    Returns:
        Evidence snippet string
    """
    if not disc_list:
        return "최근 공시가 없습니다."

    # Take top 5 disclosures
    top_disc = disc_list[:5]
    snippets = []

    for i, disc in enumerate(top_disc, 1):
        title = disc.get('title', '제목 없음')
        date = disc.get('date', '')
        disc_type = disc.get('type', '')
        snippet = f"{i}. [{disc_type}] {title}"
        if date:
            snippet += f" ({date})"
        snippets.append(snippet)

    return "\n".join(snippets)


def _summarize_chart_data(chart_list: List[Dict[str, Any]]) -> str:
    """
    Create evidence snippet for chart data
    Args:
        chart_list: List of chart data points
    Returns:
        Evidence snippet string
    """
    if not chart_list:
        return "차트 데이터를 확인할 수 없습니다."

    # Take last 5 days
    recent = chart_list[-5:] if len(chart_list) >= 5 else chart_list

    if len(recent) < 2:
        return "충분한 차트 데이터가 없습니다."

    # Calculate trend
    first_close = recent[0].get('close', 0)
    last_close = recent[-1].get('close', 0)

    if first_close > 0:
        change_pct = ((last_close - first_close) / first_close) * 100
        trend = "상승" if change_pct > 0 else "하락"
        snippet = f"최근 {len(recent)}일간 {trend} 추세 ({change_pct:+.2f}%)"
    else:
        snippet = "추세를 확인할 수 없습니다."

    # Add latest data
    latest = recent[-1]
    snippet += f"\n최근 종가: {latest.get('close', 0):,}원"

    return snippet


def summarize_results(
    fetch_results: List[tuple],
    plans: List
) -> List[SourceSummary]:
    """
    Summarize all fetch results into evidence snippets
    Only includes successful fetches with valid data

    Args:
        fetch_results: List of (FetchResult, FetchPlan) tuples
        plans: List of FetchPlan objects (for reference)

    Returns:
        List of SourceSummary objects (only successful ones)
    """
    summaries = []

    for fetch_result, plan in fetch_results:
        # Special handling for Tavily news - don't need successful fetch
        if plan.parser_name == "tavily_news":
            try:
                parsed_data = {"title": plan.title, "url": plan.url}
                snippet = f"📰 {plan.title}" if plan.title else "최신 뉴스"
                source_type = "뉴스"  # Always use "뉴스" for consistent matching

                summaries.append(SourceSummary(
                    source_url=plan.url,
                    source_type=source_type,
                    key_data=parsed_data,
                    evidence_snippet=snippet
                ))
            except Exception as e:
                pass  # Skip on error
            continue  # Move to next result

        if not fetch_result.success:
            # Skip failed fetches instead of adding them
            # This allows graceful degradation
            continue

        # Parse based on parser_name
        parser_name = plan.parser_name
        parsed_data = None

        try:
            if parser_name == "parse_price_page":
                parsed_data = parsers.parse_price_page(fetch_result.content or "")
                snippet = _summarize_price_data(parsed_data)
                source_type = "시세 정보"

            elif parser_name == "parse_chart_for_price":
                parsed_data = parsers.parse_chart_for_price(fetch_result.json_data or {})
                snippet = _summarize_price_data(parsed_data)
                source_type = "시세 정보 (차트 API)"

            elif parser_name == "parse_api_quote":
                parsed_data = parsers.parse_api_quote(fetch_result.json_data or {})
                snippet = _summarize_price_data(parsed_data)
                source_type = "시세 정보 (API)"

            elif parser_name == "parse_news_list":
                parsed_data = parsers.parse_news_list(fetch_result.content or "")
                snippet = _summarize_news_data(parsed_data)
                source_type = "뉴스"

            elif parser_name == "parse_talks_list":
                parsed_data = parsers.parse_talks_list(fetch_result.content or "")
                snippet = _summarize_talks_data(parsed_data)
                source_type = "토론/의견"

            elif parser_name == "parse_disclosure_list":
                parsed_data = parsers.parse_disclosure_list(fetch_result.content or "")
                snippet = _summarize_disclosure_data(parsed_data)
                source_type = "공시"

            elif parser_name == "parse_chart_json":
                parsed_data = parsers.parse_chart_json(fetch_result.json_data or {})
                snippet = _summarize_chart_data(parsed_data)
                source_type = "차트"

            else:
                parsed_data = {}
                snippet = "알 수 없는 데이터 형식입니다."
                source_type = plan.description

            # Only add if we got valid data
            if parsed_data or snippet != "시세 정보를 확인할 수 없습니다.":
                summaries.append(SourceSummary(
                    source_url=fetch_result.url or plan.url,
                    source_type=source_type,
                    key_data=parsed_data if isinstance(parsed_data, dict) else {"data": parsed_data},
                    evidence_snippet=snippet
                ))

        except Exception as e:
            # Skip parsing errors instead of adding them
            # This allows graceful degradation
            continue

    return summaries

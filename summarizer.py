"""
Scraping result summarization
Converts fetch results into evidence snippets
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from daum_fetch import FetchResult
import parsers

# Daum Fetch imports (requests 기반 - Streamlit Cloud 호환)
import daum_fetch
import endpoints


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

    # 현재가
    if 'current_price' in data and data['current_price']:
        price = data['current_price']
        if isinstance(price, (int, float)):
            parts.append(f"현재가 {price:,}원")
        else:
            parts.append(f"현재가 {price}")

    # 전일대비 및 등락률
    if 'change' in data and 'change_rate' in data:
        change = data['change']
        change_rate = data['change_rate']
        
        # 등락 기호
        if isinstance(change, (int, float)):
            if change > 0:
                parts.append(f"전일비 ▲{change:,}원 (+{change_rate}%)")
            elif change < 0:
                parts.append(f"전일비 ▼{abs(change):,}원 ({change_rate}%)")
            else:
                parts.append(f"전일비 보합 (0%)")
        else:
            parts.append(f"전일비 {change} ({change_rate})")

    # 거래량
    if 'volume' in data and data['volume']:
        volume = data['volume']
        if isinstance(volume, (int, float)):
            parts.append(f"거래량 {volume:,}주")
        else:
            parts.append(f"거래량 {volume}")

    # 시가
    if 'open_price' in data and data['open_price']:
        open_price = data['open_price']
        if isinstance(open_price, (int, float)):
            parts.append(f"시가 {open_price:,}원")
        else:
            parts.append(f"시가 {open_price}")

    # 고가/저가
    if 'high_price' in data and 'low_price' in data:
        if data['high_price'] and data['low_price']:
            high = data['high_price']
            low = data['low_price']
            if isinstance(high, (int, float)) and isinstance(low, (int, float)):
                parts.append(f"고가 {high:,}원, 저가 {low:,}원")
            else:
                parts.append(f"고가 {high}, 저가 {low}")

    # 시가총액 (pykrx 데이터인 경우)
    if 'market_cap' in data and data['market_cap']:
        market_cap = data['market_cap']
        if isinstance(market_cap, (int, float)):
            parts.append(f"시가총액 {market_cap:,}원")

    # 데이터 출처 정보
    if 'data_source' in data:
        source = data['data_source']
        if 'pykrx' in source.lower():
            parts.append("(한국거래소 공식 데이터)")
        elif source == 'chart_api':
            parts.append("(차트 API 기준)")
        else:
            parts.append(f"({source})")
    
    # 날짜 정보
    if 'data_date' in data and data['data_date']:
        parts.append(f"[기준: {data['data_date']}]")
    elif 'date' in data and data['date']:
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
        summary = news.get('summary', '')
        
        # Build snippet with title
        snippet = f"{i}. **{title}**"
        if date:
            snippet += f" ({date})"
        
        # Add summary if available (helps LLM understand context)
        if summary:
            snippet += f"\n   > {summary}"
        
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


def get_realtime_stock_summary_from_daum(stock_code: str) -> Optional[SourceSummary]:
    """
    다음 금융에서 실시간 주식 데이터를 가져와서 SourceSummary로 변환
    requests를 사용하여 API/HTML 파싱 (Streamlit Cloud 호환)
    
    Args:
        stock_code: 종목 코드 (예: "005930")
    
    Returns:
        SourceSummary 객체 또는 None (실패 시)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 1. Finance API 시도 (가장 안정적, 테스트 완료)
        api_url = endpoints.get_finance_api_url(stock_code)
        result = daum_fetch.fetch(api_url, is_json=True, use_cache=False)
        
        data = None
        if result.success and result.json_data:
            data = parsers.parse_api_quote(result.json_data)
            if data:
                logger.info("✅ Finance API로 데이터 가져오기 성공")
        
        # 2. Chart API 시도 (폴백)
        if not data:
            chart_url = endpoints.get_chart_api_url(stock_code, "days")
            result = daum_fetch.fetch(chart_url, is_json=True, use_cache=False)
            
            if result.success and result.json_data:
                data = parsers.parse_chart_for_price(result.json_data)
                if data:
                    logger.info("✅ Chart API로 데이터 가져오기 성공")
        
        # 3. HTML 페이지 파싱 시도 (최후 수단)
        if not data:
            price_url = endpoints.get_price_url(stock_code)
            result = daum_fetch.fetch(price_url, use_cache=False)
            
            if result.success:
                data = parsers.parse_price_page(result.content)
                if data:
                    logger.info("✅ HTML 파싱으로 데이터 가져오기 성공")
        
        if not data:
            logger.warning(f"Failed to get stock data from Daum for {stock_code}")
            return None
        
        snippet = _summarize_price_data(data)
        
        return SourceSummary(
            source_url=f"https://finance.daum.net/quotes/A{stock_code}",
            source_type="실시간 시세 (다음 금융)",
            key_data=data,
            evidence_snippet=snippet
        )
    except Exception as e:
        logger.error(f"Failed to get stock data from Daum Finance: {str(e)}")
        return None


def get_realtime_stock_summary(stock_code: str) -> Optional[SourceSummary]:
    """
    다음 금융에서 실시간 주식 데이터를 가져와서 SourceSummary로 변환
    
    ⚠️ 중요: 반드시 다음 금융(finance.daum.net)에서만 데이터를 가져옵니다.
    
    Args:
        stock_code: 종목 코드 (예: "005930")
    
    Returns:
        SourceSummary 객체 또는 None (실패 시)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 다음 금융 (Selenium)만 사용
    daum_result = get_realtime_stock_summary_from_daum(stock_code)
    
    if daum_result:
        logger.info("✅ Successfully got data from Daum Finance (finance.daum.net)")
        return daum_result
    else:
        logger.warning("❌ Failed to get data from Daum Finance")
        return None


def get_talks_summary_from_daum(stock_code: str, stock_name: str = None) -> Optional[SourceSummary]:
    """
    Tavily를 사용하여 종목 관련 투자자 의견/분석을 검색
    다음 금융 토론 페이지가 404를 반환하므로 Tavily로 대체
    
    Args:
        stock_code: 종목 코드
        stock_name: 종목명 (optional)
    
    Returns:
        SourceSummary 객체 또는 None (실패 시)
    """
    import logging
    import os
    logger = logging.getLogger(__name__)
    
    try:
        from tavily import TavilyClient
        
        # Tavily API 키 확인
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        if not tavily_api_key:
            logger.warning("Tavily API key not found, skipping investor opinions search")
            return None
        
        client = TavilyClient(api_key=tavily_api_key)
        
        # 검색 쿼리 구성
        search_query = f"{stock_name or stock_code} 종목 투자 의견 분석 전망"
        
        # Tavily 검색
        response = client.search(
            query=search_query,
            search_depth="basic",
            max_results=3
        )
        
        if not response or 'results' not in response or len(response['results']) == 0:
            logger.warning(f"No investor opinions found via Tavily for {stock_code}")
            return None
        
        # 검색 결과 요약
        snippets = []
        for i, result in enumerate(response['results'][:3], 1):
            title = result.get('title', '제목 없음')
            content = result.get('content', '')[:150]
            
            snippet_line = f"{i}. {title}"
            if content:
                snippet_line += f"\n   {content}..."
            snippets.append(snippet_line)
        
        snippet = "\n\n".join(snippets)
        
        logger.info(f"✅ Tavily로 {len(response['results'])}개의 투자 의견 검색 완료")
        
        return SourceSummary(
            source_url="Tavily 검색 결과",
            source_type="투자자 의견 및 분석",
            key_data={'results': response['results'][:3]},
            evidence_snippet=f"💬 **투자자 의견 및 분석:**\n\n{snippet}"
        )
    except ImportError:
        logger.warning("Tavily not installed, skipping investor opinions search")
        return None
    except Exception as e:
        logger.error(f"Failed to search investor opinions via Tavily: {str(e)}")
        return None


def summarize_results(
    fetch_results: List[tuple],
    plans: List,
    stock_code: Optional[str] = None,
    stock_name: Optional[str] = None,
    include_realtime: bool = True
) -> List[SourceSummary]:
    """
    Summarize all fetch results into evidence snippets
    Only includes successful fetches with valid data

    Args:
        fetch_results: List of (FetchResult, FetchPlan) tuples
        plans: List of FetchPlan objects (for reference)
        stock_code: 종목 코드 (실시간 데이터 가져오기용, optional)
        stock_name: 종목명 (optional, Tavily 검색에 사용)
        include_realtime: 실시간 데이터 포함 여부 (기본: True)

    Returns:
        List of SourceSummary objects (only successful ones)
    """
    import logging
    logger = logging.getLogger(__name__)
    summaries = []
    
    # 1. 다음 금융에서 실시간 데이터 수집 (requests + API)
    if include_realtime and stock_code:
        logger.info(f"📊 Fetching stock data from Daum Finance for {stock_code}")
        
        # 시세 데이터
        realtime_summary = get_realtime_stock_summary(stock_code)
        if realtime_summary:
            summaries.append(realtime_summary)
            logger.info(f"✅ Added stock price data from finance.daum.net")
        
        # 투자자 의견 (Tavily 검색)
        logger.info(f"💬 Searching investor opinions via Tavily for {stock_code}")
        talks_summary = get_talks_summary_from_daum(stock_code, stock_name)
        if talks_summary:
            summaries.append(talks_summary)
            logger.info(f"✅ Added investor opinions via Tavily search")

    # 2. 기존 Daum Finance 데이터 처리
    for fetch_result, plan in fetch_results:
        # Special handling for Tavily news - use pre-fetched content OR fetch actual page
        if plan.parser_name == "tavily_news":
            try:
                # Use Tavily's content if available and substantial
                content_text = plan.content if hasattr(plan, 'content') and plan.content else ""
                
                # If Tavily content is too short or empty, try fetching the actual page
                if len(content_text.strip()) < 100:
                    logger.info(f"Tavily content too short ({len(content_text)} chars), fetching actual page: {plan.url}")
                    
                    # Try to fetch and parse the news page
                    from daum_fetch import fetch
                    
                    # Only fetch if it's a news list page (not individual article)
                    if '/news' in plan.url and not any(x in plan.url for x in ['/stock/', '/economy/', '/industry/', '/world/']):
                        fetch_result_actual = fetch(plan.url, use_cache=True)
                        
                        if fetch_result_actual.success and fetch_result_actual.content:
                            # Try to parse news list
                            news_list = parsers.parse_news_list(fetch_result_actual.content)
                            
                            if news_list and len(news_list) > 0:
                                # Use top 3 news from the page
                                news_snippets = []
                                for i, news_item in enumerate(news_list[:3], 1):
                                    title = news_item.get('title', '')
                                    date = news_item.get('date', '')
                                    snippet_text = f"{i}. **{title}**"
                                    if date:
                                        snippet_text += f" ({date})"
                                    news_snippets.append(snippet_text)
                                
                                snippet = "📰 **최신 뉴스:**\n" + "\n".join(news_snippets)
                                parsed_data = {
                                    "title": plan.title or "뉴스 목록",
                                    "url": plan.url,
                                    "news_list": news_list[:3]
                                }
                                
                                summaries.append(SourceSummary(
                                    source_url=plan.url,
                                    source_type="뉴스",
                                    key_data=parsed_data,
                                    evidence_snippet=snippet
                                ))
                                logger.info(f"Successfully fetched and parsed {len(news_list[:3])} news items from {plan.url}")
                                continue
                
                # Use Tavily content if available
                if plan.title and content_text:
                    # Extract first 300 chars of content for snippet
                    content_preview = content_text[:300].replace('\n', ' ').strip()
                    if len(content_preview) > 0:
                        snippet = f"📰 **{plan.title}**\n\n{content_preview}..."
                    else:
                        snippet = f"📰 **{plan.title}**"
                elif plan.title:
                    snippet = f"📰 **{plan.title}**"
                else:
                    # Skip if no title and no content
                    logger.warning(f"Skipping Tavily news with no title and no content: {plan.url}")
                    continue
                
                parsed_data = {
                    "title": plan.title,
                    "url": plan.url,
                    "content": content_text[:1000] if content_text else ""  # First 1000 chars for LLM
                }
                source_type = "뉴스"

                summaries.append(SourceSummary(
                    source_url=plan.url,
                    source_type=source_type,
                    key_data=parsed_data,
                    evidence_snippet=snippet
                ))
                logger.info(f"Added Tavily news: {plan.title} ({len(content_text)} chars)")
            except Exception as e:
                logger.error(f"Error processing Tavily news: {str(e)}", exc_info=True)
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

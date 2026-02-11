"""
HTML/JSON parsers for Daum Finance pages
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re


def parse_search_results(html: str) -> List[Dict[str, str]]:
    """
    Parse search results to extract stock codes and names
    Args:
        html: Search page HTML
    Returns:
        List of {code, name, market} dicts
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Find stock items in search results
        items = soup.select('.searchStockList .item_stock')

        for item in items:
            try:
                # Extract stock code
                link = item.select_one('a')
                if not link or 'href' not in link.attrs:
                    continue

                href = link['href']
                code_match = re.search(r'/quotes/(\d{6})', href)
                if not code_match:
                    continue

                code = code_match.group(1)

                # Extract stock name
                name_elem = item.select_one('.txt_name')
                name = name_elem.get_text(strip=True) if name_elem else ''

                # Extract market info if available
                market_elem = item.select_one('.txt_sub')
                market = market_elem.get_text(strip=True) if market_elem else ''

                if code and name:
                    results.append({
                        'code': code,
                        'name': name,
                        'market': market
                    })

            except Exception:
                continue

        return results

    except Exception:
        return []


def parse_price_page(html: str) -> Dict[str, Any]:
    """
    Parse price/quote page to extract current price, change, volume, etc.
    Args:
        html: Price page HTML
    Returns:
        Dict with price data
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        data = {}

        # Current price
        price_elem = soup.select_one('.price')
        if price_elem:
            price_text = price_elem.get_text(strip=True).replace(',', '')
            try:
                data['current_price'] = int(price_text)
            except ValueError:
                data['current_price'] = price_text

        # Change and change rate
        change_elem = soup.select_one('.change')
        if change_elem:
            change_text = change_elem.get_text(strip=True)
            data['change'] = change_text

        rate_elem = soup.select_one('.rate')
        if rate_elem:
            rate_text = rate_elem.get_text(strip=True)
            data['change_rate'] = rate_text

        # Additional info from summary table
        info_items = soup.select('.tb_summary tr')
        for item in info_items:
            th = item.select_one('th')
            td = item.select_one('td')

            if th and td:
                key = th.get_text(strip=True)
                value = td.get_text(strip=True)

                if '거래량' in key:
                    data['volume'] = value
                elif '거래대금' in key:
                    data['transaction_amount'] = value
                elif '시가' in key:
                    data['open_price'] = value
                elif '고가' in key:
                    data['high_price'] = value
                elif '저가' in key:
                    data['low_price'] = value
                elif '전일' in key:
                    data['previous_close'] = value

        return data

    except Exception:
        return {}


def parse_chart_json(json_data: Any) -> List[Dict[str, Any]]:
    """
    Parse chart API JSON data
    Args:
        json_data: JSON response from chart API
    Returns:
        List of {date, open, high, low, close, volume} dicts
    """
    try:
        if not isinstance(json_data, dict):
            return []

        data_list = json_data.get('data', [])
        results = []

        for item in data_list:
            if isinstance(item, dict):
                results.append({
                    'date': item.get('date', ''),
                    'open': item.get('openingPrice', 0),
                    'high': item.get('highPrice', 0),
                    'low': item.get('lowPrice', 0),
                    'close': item.get('tradePrice', 0),
                    'volume': item.get('accTradeVolume', 0)
                })

        return results

    except Exception:
        return []


def parse_news_list(html: str) -> List[Dict[str, str]]:
    """
    Parse news list page
    Args:
        html: News page HTML
    Returns:
        List of {title, date, link} dicts
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Find news items
        items = soup.select('.newsList .item_news')

        for item in items:
            try:
                # Title and link
                link_elem = item.select_one('.link_news')
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                link = link_elem.get('href', '')

                # Date
                date_elem = item.select_one('.txt_date')
                date = date_elem.get_text(strip=True) if date_elem else ''

                # Summary (if available)
                summary_elem = item.select_one('.txt_summary')
                summary = summary_elem.get_text(strip=True) if summary_elem else ''

                results.append({
                    'title': title,
                    'date': date,
                    'link': link,
                    'summary': summary
                })

            except Exception:
                continue

        return results[:10]  # Limit to 10 news items

    except Exception:
        return []


def parse_disclosure_list(html: str) -> List[Dict[str, str]]:
    """
    Parse disclosure list page
    Args:
        html: Disclosure page HTML
    Returns:
        List of {title, date, type} dicts
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Find disclosure items
        items = soup.select('.disclosureList .item_disclosure')

        for item in items:
            try:
                # Title
                title_elem = item.select_one('.link_disclosure')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Date
                date_elem = item.select_one('.txt_date')
                date = date_elem.get_text(strip=True) if date_elem else ''

                # Type
                type_elem = item.select_one('.txt_category')
                disc_type = type_elem.get_text(strip=True) if type_elem else ''

                results.append({
                    'title': title,
                    'date': date,
                    'type': disc_type
                })

            except Exception:
                continue

        return results[:10]  # Limit to 10 items

    except Exception:
        return []


def parse_talks_list(html: str) -> List[Dict[str, str]]:
    """
    Parse talks/discussion page
    Args:
        html: Talks page HTML
    Returns:
        List of {content, author, date} dicts
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        results = []

        # Find talk items
        items = soup.select('.talkList .item_talk, .commentList .item_comment')

        for item in items:
            try:
                # Content
                content_elem = item.select_one('.txt_talk, .txt_comment')
                if not content_elem:
                    continue

                content = content_elem.get_text(strip=True)

                # Author
                author_elem = item.select_one('.txt_writer')
                author = author_elem.get_text(strip=True) if author_elem else '익명'

                # Date
                date_elem = item.select_one('.txt_date')
                date = date_elem.get_text(strip=True) if date_elem else ''

                results.append({
                    'content': content[:200],  # Limit content length
                    'author': author,
                    'date': date
                })

            except Exception:
                continue

        return results[:10]  # Limit to 10 items

    except Exception:
        return []


def extract_stock_code_from_html(html: str) -> Optional[str]:
    """
    Extract stock code from any Daum Finance page
    Args:
        html: HTML content
    Returns:
        Stock code or None
    """
    try:
        # Try to find code in meta tags or scripts
        code_match = re.search(r'"symbolCode"\s*:\s*"(\d{6})"', html)
        if code_match:
            return code_match.group(1)

        code_match = re.search(r'/quotes/(\d{6})', html)
        if code_match:
            return code_match.group(1)

        return None

    except Exception:
        return None

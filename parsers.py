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

        # Try to extract JSON data from script tags (for React/SPA pages)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'tradePrice' in script.string:
                import json
                import re
                
                # Try to find JSON objects in script content
                try:
                    # Look for window.__INITIAL_STATE__ or similar patterns
                    json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});', script.string, re.DOTALL)
                    if not json_match:
                        json_match = re.search(r'__NEXT_DATA__["\']?\s*type=["\']application/json["\']>(\{.+?\})</script>', script.string, re.DOTALL)
                    
                    if json_match:
                        json_data = json.loads(json_match.group(1))
                        # Extract data from JSON structure
                        # This will need to be adjusted based on actual structure
                        return _extract_price_from_json(json_data)
                except:
                    pass

        # Fallback: Try multiple CSS selectors for different page structures
        price_selectors = [
            '.price',
            '.txt_price',
            '.num_price',
            '[data-id="priceValue"]',
            '[class*="price"]',
            'span[class*="Price"]',
            'em[class*="price"]'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace(',', '')
                try:
                    data['current_price'] = int(price_text)
                    break
                except ValueError:
                    data['current_price'] = price_text
                    break

        # Change and change rate - try multiple selectors
        change_selectors = ['.change', '.txt_change', '[class*="change"]']
        for selector in change_selectors:
            change_elem = soup.select_one(selector)
            if change_elem:
                data['change'] = change_elem.get_text(strip=True)
                break

        rate_selectors = ['.rate', '.txt_rate', '[class*="rate"]']
        for selector in rate_selectors:
            rate_elem = soup.select_one(selector)
            if rate_elem:
                data['change_rate'] = rate_elem.get_text(strip=True)
                break

        # Additional info from summary table - try multiple selectors
        table_selectors = [
            '.tb_summary tr',
            'table[class*="summary"] tr',
            '[class*="info"] tr',
            'dl[class*="info"]'
        ]
        
        for table_selector in table_selectors:
            info_items = soup.select(table_selector)
            if info_items:
                for item in info_items:
                    th = item.select_one('th, dt')
                    td = item.select_one('td, dd')

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
                break

        return data

    except Exception:
        return {}


def _extract_price_from_json(json_data: dict) -> Dict[str, Any]:
    """
    Extract price data from JSON structure
    """
    data = {}
    
    # Try different common JSON structures
    if isinstance(json_data, dict):
        # Look for common keys
        if 'tradePrice' in json_data:
            data['current_price'] = json_data.get('tradePrice')
        if 'change' in json_data:
            data['change'] = json_data.get('change')
        if 'changeRate' in json_data:
            data['change_rate'] = json_data.get('changeRate')
        if 'accTradeVolume' in json_data:
            data['volume'] = json_data.get('accTradeVolume')
        
        # Recursively search nested structures
        for key, value in json_data.items():
            if isinstance(value, dict):
                nested_data = _extract_price_from_json(value)
                if nested_data:
                    data.update(nested_data)
                    break
    
    return data


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


def parse_chart_for_price(json_data: Any) -> Dict[str, Any]:
    """
    Parse chart API data to extract latest price information
    This converts chart data into a price-like format
    
    Args:
        json_data: JSON response from chart API
    Returns:
        Dict with price data extracted from latest candle
    """
    try:
        chart_data = parse_chart_json(json_data)
        
        if not chart_data:
            return {}
        
        # Get the latest data point
        latest = chart_data[-1]
        
        # Convert to price data format
        data = {
            'current_price': latest.get('close', 0),
            'open_price': latest.get('open', 0),
            'high_price': latest.get('high', 0),
            'low_price': latest.get('low', 0),
            'volume': latest.get('volume', 0),
        }
        
        # Calculate change if we have at least 2 data points
        if len(chart_data) >= 2:
            previous = chart_data[-2]
            prev_close = previous.get('close', 0)
            curr_close = latest.get('close', 0)
            
            if prev_close > 0:
                change = curr_close - prev_close
                change_rate = (change / prev_close) * 100
                
                data['previous_close'] = prev_close
                data['change'] = f"{change:+,}원" if change else "0원"
                data['change_rate'] = f"{change_rate:+.2f}%"
        
        # Add data freshness info
        data['date'] = latest.get('date', '')
        data['data_source'] = 'chart_api'
        
        return data
    
    except Exception:
        return {}


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


def parse_api_quote(json_data: Any) -> Dict[str, Any]:
    """
    Parse API quote response (JSON format)
    This handles responses from Daum Finance internal API
    
    Args:
        json_data: JSON response from API
    Returns:
        Dict with price data
    """
    try:
        if not isinstance(json_data, dict):
            return {}
        
        data = {}
        
        # Check for common API response structures
        # Structure 1: Direct data in root
        if 'tradePrice' in json_data:
            data['current_price'] = json_data.get('tradePrice')
            data['change'] = json_data.get('change')
            data['change_rate'] = json_data.get('changeRate')
            data['volume'] = json_data.get('accTradeVolume')
            data['open_price'] = json_data.get('openingPrice')
            data['high_price'] = json_data.get('highPrice')
            data['low_price'] = json_data.get('lowPrice')
            data['previous_close'] = json_data.get('prevClosingPrice')
        
        # Structure 2: Data nested in 'data' key
        elif 'data' in json_data:
            nested = json_data['data']
            if isinstance(nested, dict):
                data['current_price'] = nested.get('tradePrice') or nested.get('price')
                data['change'] = nested.get('change') or nested.get('changePrice')
                data['change_rate'] = nested.get('changeRate') or nested.get('changeRatio')
                data['volume'] = nested.get('accTradeVolume') or nested.get('volume')
                data['open_price'] = nested.get('openingPrice') or nested.get('open')
                data['high_price'] = nested.get('highPrice') or nested.get('high')
                data['low_price'] = nested.get('lowPrice') or nested.get('low')
                data['previous_close'] = nested.get('prevClosingPrice') or nested.get('previousClose')
        
        # Structure 3: Data nested in 'quote' or 'stock' key
        elif 'quote' in json_data or 'stock' in json_data:
            nested = json_data.get('quote') or json_data.get('stock')
            if isinstance(nested, dict):
                data['current_price'] = nested.get('tradePrice') or nested.get('price')
                data['change'] = nested.get('change')
                data['change_rate'] = nested.get('changeRate')
                data['volume'] = nested.get('volume')
        
        # Clean up None values
        data = {k: v for k, v in data.items() if v is not None}
        
        return data
    
    except Exception as e:
        return {}

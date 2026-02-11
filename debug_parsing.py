"""
HTML 파싱 디버그 테스트
"""

import sys
import io
from bs4 import BeautifulSoup

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from daum_fetch import fetch
from parsers import parse_price_page

def debug_html_parsing():
    """HTML 파싱 디버그"""
    print("=" * 80)
    print("HTML 파싱 디버그")
    print("=" * 80)
    
    url = "https://finance.daum.net/quotes/A005930"
    
    print(f"\n[1] Fetching URL: {url}")
    result = fetch(url, use_cache=False)
    
    if not result.success:
        print(f"[ERROR] Fetch 실패: {result.error_message}")
        return
    
    print(f"[OK] Fetch 성공 (status: {result.status_code})")
    print(f"[INFO] Content length: {len(result.content)} bytes\n")
    
    # HTML 미리보기
    print("[2] HTML 미리보기 (처음 1000자):")
    print("-" * 80)
    print(result.content[:1000])
    print("-" * 80)
    print()
    
    # BeautifulSoup으로 파싱
    print("[3] BeautifulSoup 파싱...")
    soup = BeautifulSoup(result.content, 'lxml')
    
    # 가격 관련 요소 찾기
    print("\n[4] 가격 관련 요소 탐색:")
    print("-" * 80)
    
    price_selectors = [
        '.price',
        '.txt_price',
        '.num_price',
        '[data-id="priceValue"]',
        '[class*="price"]',
        'span[class*="Price"]',
        'em[class*="price"]',
        '[class*="tradePrice"]',
        '[class*="currentPrice"]'
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"\n  Selector: {selector}")
            for i, elem in enumerate(elements[:3], 1):  # 최대 3개만
                print(f"    {i}. Text: {elem.get_text(strip=True)[:100]}")
                print(f"       Classes: {elem.get('class', [])}")
    
    print("\n" + "-" * 80)
    
    # Script 태그 내 JSON 데이터 탐색
    print("\n[5] Script 태그 내 JSON 데이터 탐색:")
    print("-" * 80)
    
    scripts = soup.find_all('script')
    print(f"  총 {len(scripts)}개의 script 태그 발견")
    
    for i, script in enumerate(scripts):
        if script.string and ('tradePrice' in script.string or 'currentPrice' in script.string or '__INITIAL' in script.string):
            print(f"\n  Script {i+1}:")
            print(f"    Length: {len(script.string)} chars")
            print(f"    Preview: {script.string[:500]}...")
    
    print("\n" + "-" * 80)
    
    # 파서 실행
    print("\n[6] parse_price_page 실행:")
    print("-" * 80)
    parsed_data = parse_price_page(result.content)
    
    if parsed_data:
        print("  [OK] 파싱 성공!")
        for key, value in parsed_data.items():
            print(f"    {key}: {value}")
    else:
        print("  [FAIL] 파싱 실패 - 빈 딕셔너리 반환")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    debug_html_parsing()

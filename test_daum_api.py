"""
Test script to check various Daum Finance API endpoints
"""

from daum_fetch import fetch
from endpoints import (
    get_price_url,
    get_chart_api_url,
    get_finance_api_url,
    get_realtime_quote_api
)
from parsers import parse_api_quote, parse_chart_json, parse_price_page
import json

def test_endpoint(name, url, is_json=False):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    result = fetch(url, use_cache=False, is_json=is_json)
    
    if result.success:
        print(f"✅ SUCCESS (HTTP {result.status_code})")
        
        if is_json:
            print("\nJSON Response:")
            if result.json_data:
                print(json.dumps(result.json_data, indent=2, ensure_ascii=False)[:1000])
                if len(json.dumps(result.json_data)) > 1000:
                    print("...[truncated]")
        else:
            print(f"\nContent length: {len(result.content)} bytes")
            # Show first 500 chars
            print("\nContent preview:")
            print(result.content[:500])
            if len(result.content) > 500:
                print("...[truncated]")
    else:
        print(f"❌ FAILED")
        print(f"Error: {result.error_message}")
        if result.status_code:
            print(f"Status code: {result.status_code}")
    
    return result


def main():
    code = "005930"  # Samsung Electronics
    
    print("\n" + "="*60)
    print("DAUM FINANCE API ENDPOINT TEST")
    print("Stock: Samsung Electronics (005930)")
    print("="*60)
    
    # Test 1: Chart API (known to work)
    chart_result = test_endpoint(
        "Chart API (Days)",
        get_chart_api_url(code),
        is_json=True
    )
    
    if chart_result.success and chart_result.json_data:
        parsed = parse_chart_json(chart_result.json_data)
        print(f"\nParsed {len(parsed)} data points")
        if parsed:
            print(f"Latest: {parsed[-1]}")
    
    # Test 2: Regular price page (HTML)
    price_result = test_endpoint(
        "Price Page (HTML)",
        get_price_url(code),
        is_json=False
    )
    
    if price_result.success:
        parsed = parse_price_page(price_result.content)
        print(f"\nParsed data: {parsed}")
    
    # Test 3: Try API endpoint variations
    api_urls = [
        ("Finance API (/api/quotes/)", get_finance_api_url(code)),
        ("Realtime Quote API (/api/quote/)", get_realtime_quote_api(code)),
    ]
    
    for name, url in api_urls:
        result = test_endpoint(name, url, is_json=True)
        
        if result.success and result.json_data:
            parsed = parse_api_quote(result.json_data)
            print(f"\nParsed data: {parsed}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✅ = Working, ❌ = Not working\n")
    
    results = {
        "Chart API": chart_result.success,
        "Price Page (HTML)": price_result.success,
    }
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")


if __name__ == "__main__":
    main()

"""
Quick test to verify chart API works
"""

from daum_fetch import fetch
from parsers import parse_chart_for_price, parse_chart_json
import json

code = "005930"  # Samsung
url = f"https://finance.daum.net/api/charts/A{code}/days"

print(f"Testing Chart API for {code}")
print(f"URL: {url}\n")

result = fetch(url, use_cache=False, is_json=True)

if result.success:
    print("✅ Fetch SUCCESS!\n")
    
    # Show raw data (first 500 chars)
    raw = json.dumps(result.json_data, ensure_ascii=False)
    print("Raw JSON (preview):")
    print(raw[:500])
    print("...\n" if len(raw) > 500 else "\n")
    
    # Parse as chart data
    chart_data = parse_chart_json(result.json_data)
    print(f"Parsed {len(chart_data)} chart data points")
    if chart_data:
        print(f"Latest: {chart_data[-1]}\n")
    
    # Parse as price data
    price_data = parse_chart_for_price(result.json_data)
    print("Extracted price data:")
    for key, value in price_data.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    if price_data.get('current_price'):
        print(f"✅ SUCCESS! Current price: {price_data['current_price']:,}원")
    else:
        print("❌ FAILED! No price data extracted")
else:
    print("❌ Fetch FAILED!")
    print(f"Error: {result.error_message}")
    if result.status_code:
        print(f"Status: {result.status_code}")

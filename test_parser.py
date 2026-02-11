"""
Test parser to check current Daum Finance HTML structure
"""

from daum_fetch import fetch
from bs4 import BeautifulSoup
import json

# Test URL
url = "https://finance.daum.net/quotes/A005930"

print(f"Fetching: {url}\n")
result = fetch(url, use_cache=False)

if result.success:
    print(f"✅ Success! Status: {result.status_code}")
    print(f"Content length: {len(result.content)} bytes\n")
    
    # Parse HTML
    soup = BeautifulSoup(result.content, 'lxml')
    
    print("=" * 60)
    print("PAGE TITLE")
    print("=" * 60)
    print(soup.title.string if soup.title else "No title")
    print()
    
    print("=" * 60)
    print("CHECKING FOR REACT/SPA")
    print("=" * 60)
    print(f"Has 'data-reactroot': {'data-reactroot' in result.content}")
    print(f"Has 'react' in content: {'react' in result.content.lower()}")
    print(f"Has '__NEXT_DATA__': {'__NEXT_DATA__' in result.content}")
    print()
    
    # Try to find price element with different selectors
    print("=" * 60)
    print("SEARCHING FOR PRICE DATA")
    print("=" * 60)
    
    selectors_to_try = [
        '.price',
        '[class*="price"]',
        '[data-test="price"]',
        '.txt_price',
        '.num_price',
        '#priceValue',
    ]
    
    for selector in selectors_to_try:
        elements = soup.select(selector)
        if elements:
            print(f"✅ Found with selector '{selector}':")
            for elem in elements[:3]:  # Show first 3
                print(f"  - {elem.get_text(strip=True)}")
        else:
            print(f"❌ Not found: {selector}")
    
    print()
    
    # Check for JSON data in script tags
    print("=" * 60)
    print("CHECKING SCRIPT TAGS FOR JSON DATA")
    print("=" * 60)
    
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    for i, script in enumerate(scripts):
        if script.string and ('symbolCode' in script.string or 'tradePrice' in script.string or 'quotes' in script.string):
            print(f"\n📍 Script tag #{i} contains relevant data:")
            content = script.string.strip()
            if len(content) > 500:
                print(content[:500] + "...[truncated]")
            else:
                print(content)
            
            # Try to parse as JSON
            try:
                # Look for JSON objects
                import re
                json_matches = re.findall(r'\{[^{}]*(?:"symbolCode"|"tradePrice"|"quotes")[^{}]*\}', content)
                if json_matches:
                    print("\n  Extracted JSON snippets:")
                    for match in json_matches[:2]:
                        print(f"  {match}")
            except:
                pass
    
    print()
    
    # Check for specific classes/IDs that might contain data
    print("=" * 60)
    print("CHECKING COMMON DATA CONTAINERS")
    print("=" * 60)
    
    containers = [
        ('stockInfo', 'class'),
        ('stock-info', 'class'),
        ('priceInfo', 'class'),
        ('price-info', 'class'),
        ('quote', 'class'),
        ('stockContent', 'id'),
        ('root', 'id'),
    ]
    
    for name, attr_type in containers:
        if attr_type == 'class':
            elements = soup.select(f'.{name}')
        else:
            elements = soup.select(f'#{name}')
        
        if elements:
            print(f"✅ Found element with {attr_type}='{name}':")
            for elem in elements[:1]:
                text = elem.get_text(strip=True)
                if len(text) > 200:
                    print(f"  {text[:200]}...")
                else:
                    print(f"  {text}")
        else:
            print(f"❌ Not found: {attr_type}='{name}'")

else:
    print(f"❌ Failed!")
    print(f"Error: {result.error_message}")
    print(f"Status code: {result.status_code}")

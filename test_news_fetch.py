"""
Test script to find working news endpoints
"""
import requests
import json
from bs4 import BeautifulSoup

# Headers to mimic browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://finance.daum.net/"
}

code = "A039490"
base_url = f"https://finance.daum.net/quotes/{code}"

print(f"Fetching: {base_url}")
response = requests.get(base_url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'lxml')

    # Try to find script tags with data
    scripts = soup.find_all('script')

    for i, script in enumerate(scripts):
        if script.string and ('news' in script.string.lower() or 'article' in script.string.lower()):
            content = script.string[:500]
            print(f"\n=== Script {i} (contains 'news') ===")
            print(content)
            print("...")

    # Check for news sections in HTML
    print("\n\n=== Looking for news sections in HTML ===")
    news_sections = soup.find_all(class_=lambda x: x and 'news' in x.lower())
    print(f"Found {len(news_sections)} elements with 'news' in class name")

    for section in news_sections[:3]:
        print(f"\nClass: {section.get('class')}")
        print(f"Content preview: {section.get_text()[:200]}")

else:
    print(f"Failed: {response.status_code}")

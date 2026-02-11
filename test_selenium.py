"""
Selenium을 사용한 브라우저 기반 스크래핑 테스트
"""

import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

from bs4 import BeautifulSoup

def test_browser_scraping():
    """브라우저 기반 스크래핑 테스트"""
    
    if not HAS_SELENIUM:
        print("[ERROR] Selenium이 설치되지 않았습니다.")
        print("설치 명령: py -m pip install selenium")
        return
    
    print("=" * 80)
    print("Selenium 브라우저 스크래핑 테스트")
    print("=" * 80)
    
    url = "https://finance.daum.net/quotes/A005930"
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--lang=ko-KR')
    
    print(f"\n[1] Chrome 브라우저 시작 중...")
    print(f"[2] URL 접속: {url}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # 페이지 로드 대기
        print(f"[3] 페이지 로딩 대기 중...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 추가 대기 (JavaScript 실행)
        import time
        time.sleep(3)
        
        # 페이지 소스 가져오기
        html = driver.page_source
        print(f"[OK] 페이지 로드 완료 (length: {len(html)} bytes)")
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html, 'lxml')
        
        # 가격 정보 찾기
        print("\n[4] 가격 정보 탐색:")
        print("-" * 80)
        
        # 다양한 선택자 시도
        selectors = [
            ('.price', 'class=price'),
            ('.txt_price', 'class=txt_price'),
            ('[data-id="priceValue"]', 'data-id=priceValue'),
            ('[class*="price"]', 'class contains price'),
            ('span[class*="Price"]', 'span class contains Price'),
            ('em[class*="price"]', 'em class contains price'),
        ]
        
        for selector, desc in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n  찾음: {desc}")
                for i, elem in enumerate(elements[:3], 1):
                    text = elem.get_text(strip=True)
                    if text:
                        print(f"    {i}. {text}")
        
        # 전체 텍스트 검색 (가격 패턴)
        print("\n[5] 숫자 패턴 검색 (가격일 가능성):")
        print("-" * 80)
        
        import re
        price_pattern = re.compile(r'[\d,]+원?')
        text_content = soup.get_text()
        matches = price_pattern.findall(text_content)
        
        # 중복 제거 및 필터링
        seen = set()
        for match in matches:
            if match not in seen and len(match) >= 4:  # 최소 4자 (예: 1,000)
                seen.add(match)
                if len(seen) <= 10:  # 상위 10개만
                    print(f"    {match}")
        
        print("\n" + "-" * 80)
        
        # HTML 일부 저장
        with open('browser_output.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n[INFO] 전체 HTML 저장: browser_output.html")
        
        driver.quit()
        
    except Exception as e:
        print(f"\n[ERROR] 브라우저 스크래핑 실패: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_browser_scraping()

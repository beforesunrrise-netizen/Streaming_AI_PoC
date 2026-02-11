"""
다음 금융 API 엔드포인트 직접 테스트
"""

import sys
import io
import json

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from daum_fetch import fetch
from endpoints import get_finance_api_url, get_realtime_quote_api, get_chart_api_url

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("=" * 80)
    print("다음 금융 API 엔드포인트 테스트")
    print("=" * 80)
    
    code = "005930"
    
    apis = [
        ("Finance API", get_finance_api_url(code), True),
        ("Realtime Quote API", get_realtime_quote_api(code), True),
        ("Chart API (days)", get_chart_api_url(code, "days"), True),
    ]
    
    for name, url, is_json in apis:
        print(f"\n[{name}]")
        print(f"URL: {url}")
        print("-" * 80)
        
        result = fetch(url, use_cache=False, is_json=is_json)
        
        if result.success:
            print(f"[OK] 성공 (status: {result.status_code})")
            
            if is_json and result.json_data:
                print("\nJSON 데이터:")
                print(json.dumps(result.json_data, ensure_ascii=False, indent=2)[:1000])
            elif result.content:
                print(f"\n내용 미리보기 ({len(result.content)} bytes):")
                print(result.content[:500])
        else:
            print(f"[FAIL] 실패 (status: {result.status_code})")
            print(f"에러: {result.error_message}")
        
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    test_api_endpoints()

"""
파서 테스트 - API JSON 데이터 파싱
"""

import sys
import io
import json

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from daum_fetch import fetch
from endpoints import get_finance_api_url
from parsers import parse_api_quote
from summarizer import _summarize_price_data

def test_parser():
    """파서 테스트"""
    print("=" * 80)
    print("파서 테스트 - API JSON 데이터 파싱")
    print("=" * 80)
    
    code = "005930"
    url = get_finance_api_url(code)
    
    print(f"\n[1] API 호출: {url}")
    result = fetch(url, use_cache=False, is_json=True)
    
    if not result.success:
        print(f"[FAIL] API 호출 실패: {result.error_message}")
        return
    
    print(f"[OK] API 호출 성공")
    print(f"\n[2] 원본 JSON 데이터:")
    print(json.dumps(result.json_data, ensure_ascii=False, indent=2)[:500])
    
    print(f"\n[3] 파서 실행: parse_api_quote()")
    parsed_data = parse_api_quote(result.json_data)
    
    print(f"\n[4] 파싱 결과:")
    if parsed_data:
        print("[OK] 파싱 성공!")
        for key, value in parsed_data.items():
            print(f"  {key}: {value}")
    else:
        print("[FAIL] 파싱 실패 - 빈 딕셔너리 반환")
        return
    
    print(f"\n[5] 요약 생성: _summarize_price_data()")
    snippet = _summarize_price_data(parsed_data)
    print(f"\n요약 결과:")
    print(snippet)
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_parser()

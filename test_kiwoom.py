"""
Test script for Kiwoom Securities stock recognition
"""

from intent import analyze_intent, _extract_stock_name
from stock_mapping import get_stock_code

# Test cases
test_cases = [
    "키움증권 사면 좋아?",
    "키움증권 주가는?",
    "키움증권 어때?",
]

print("=" * 60)
print("Testing Kiwoom Securities Recognition")
print("=" * 60)

for test_query in test_cases:
    print(f"\n🔍 Testing: '{test_query}'")
    print("-" * 60)
    
    # Test 1: Extract stock name
    stock_name = _extract_stock_name(test_query)
    print(f"1. Extracted stock name: {stock_name}")
    
    # Test 2: Get stock code from mapping
    if stock_name:
        mapping_result = get_stock_code(stock_name)
        print(f"2. Stock mapping result: {mapping_result}")
    
    # Test 3: Full intent analysis
    intent = analyze_intent(test_query, use_llm=False)
    print(f"3. Intent analysis:")
    print(f"   - Question type: {intent.question_type}")
    print(f"   - Stock code: {intent.stock_code}")
    print(f"   - Stock name: {intent.stock_name}")
    print(f"   - Confidence: {intent.confidence}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

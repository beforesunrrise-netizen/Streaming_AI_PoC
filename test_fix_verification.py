"""
Test script to verify the fixes for chat continuity and Tavily search
"""

import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("🧪 대화 연속성 및 Tavily 검색 테스트")
print("=" * 60)

# Test 1: Check Tavily API key
print("\n[1] Tavily API 키 확인")
from config import get_env

tavily_key = get_env('TAVILY_API_KEY')
if tavily_key:
    print(f"✅ Tavily API 키 설정됨: {tavily_key[:15]}...")
else:
    print("❌ Tavily API 키가 설정되지 않았습니다!")
    sys.exit(1)

# Test 2: Test Tavily search
print("\n[2] Tavily 검색 테스트 (키움증권)")
from tavily_search import get_tavily_urls_by_question_type
from config import QUESTION_TYPE_BUY_RECOMMENDATION

try:
    urls = get_tavily_urls_by_question_type(
        question_type=QUESTION_TYPE_BUY_RECOMMENDATION,
        stock_name="키움증권",
        stock_code="039490"
    )

    print(f"✅ Tavily가 {len(urls)}개의 URL을 찾았습니다:")
    for i, url in enumerate(urls[:5], 1):
        print(f"   {i}. {url}")

    if len(urls) == 0:
        print("⚠️ Tavily가 URL을 찾지 못했습니다. 이는 정상일 수 있습니다.")

except Exception as e:
    print(f"❌ Tavily 검색 실패: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 3: Test intent classification
print("\n[3] 질문 분류 테스트")
from intent import analyze_intent

test_question = "키움증권 지금 사면 좋을까?"
print(f"질문: '{test_question}'")

intent = analyze_intent(test_question, use_llm=False)
print(f"분류 결과: {intent.question_type}")
print(f"종목명: {intent.stock_name}")
print(f"종목코드: {intent.stock_code}")

if intent.question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
    print("✅ 올바르게 'A_매수판단형'으로 분류되었습니다!")
else:
    print(f"❌ 잘못 분류되었습니다. 예상: A_매수판단형, 실제: {intent.question_type}")

# Test 4: Test full pipeline
print("\n[4] 전체 파이프라인 테스트")
from planner import create_plan

if intent.stock_code:
    plans = create_plan(intent, use_tavily=True)

    print(f"✅ {len(plans)}개의 계획이 생성되었습니다:")
    for i, plan in enumerate(plans, 1):
        print(f"   {i}. {plan.description}")
        print(f"      URL: {plan.url[:80]}...")

    # Count Tavily plans
    tavily_plans = [p for p in plans if p.plan_id.startswith('T')]
    print(f"\n   Tavily로 찾은 URL: {len(tavily_plans)}개")

    if len(tavily_plans) == 0:
        print("⚠️ Tavily가 추가 URL을 찾지 못했습니다.")
        print("   이는 다음 중 하나 때문일 수 있습니다:")
        print("   - Tavily가 finance.daum.net에서 관련 페이지를 찾지 못함")
        print("   - API 요청 실패 (로그 확인)")
        print("   - 네트워크 문제")
else:
    print("❌ 종목 코드를 찾을 수 없어 계획을 생성할 수 없습니다!")

print("\n" + "=" * 60)
print("✅ 테스트 완료!")
print("=" * 60)
print("\n💡 다음 단계:")
print("1. Streamlit 앱 실행: streamlit run app_chat.py")
print("2. '키움증권 지금 사면 좋을까?' 질문 입력")
print("3. 터미널에서 Tavily 로그 확인")
print("4. 후속 질문 ('그럼 최근 뉴스는?') 테스트로 대화 연속성 확인")

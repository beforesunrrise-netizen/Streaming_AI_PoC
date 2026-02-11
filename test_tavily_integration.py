"""
Test script for Tavily integration
This script tests the complete flow:
1. Tavily search for finance.daum.net URLs
2. URL validation with allowlist
3. Web fetch from discovered URLs
"""

from dotenv import load_dotenv
load_dotenv()

from tavily_search import search_daum_finance_urls, get_tavily_urls_by_question_type
from daum_fetch import fetch
from config import QUESTION_TYPE_BUY_RECOMMENDATION


def test_tavily_search():
    """Test basic Tavily search functionality"""
    print("=" * 60)
    print("TEST 1: Tavily Search for finance.daum.net URLs")
    print("=" * 60)

    query = "삼성전자 시세"
    stock_name = "삼성전자"
    stock_code = "005930"

    print(f"\n🔍 Searching for: {query}")
    print(f"   Stock: {stock_name} ({stock_code})")

    results = search_daum_finance_urls(
        query=query,
        stock_name=stock_name,
        stock_code=stock_code,
        max_results=5
    )

    if results:
        print(f"\n✅ Found {len(results)} URLs:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score}")
    else:
        print("\n⚠️ No results found (Tavily might not be configured)")

    return results


def test_tavily_by_question_type():
    """Test Tavily search by question type"""
    print("\n" + "=" * 60)
    print("TEST 2: Tavily Search by Question Type")
    print("=" * 60)

    stock_name = "삼성전자"
    stock_code = "005930"
    question_type = QUESTION_TYPE_BUY_RECOMMENDATION

    print(f"\n🔍 Question Type: {question_type}")
    print(f"   Stock: {stock_name} ({stock_code})")

    urls = get_tavily_urls_by_question_type(
        question_type=question_type,
        stock_name=stock_name,
        stock_code=stock_code
    )

    if urls:
        print(f"\n✅ Found {len(urls)} unique URLs:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
    else:
        print("\n⚠️ No URLs found (Tavily might not be configured)")

    return urls


def test_fetch_tavily_urls(urls):
    """Test fetching content from Tavily-discovered URLs"""
    print("\n" + "=" * 60)
    print("TEST 3: Fetch Content from Tavily URLs")
    print("=" * 60)

    if not urls:
        print("\n⚠️ No URLs to fetch (skip this test)")
        return

    print(f"\n📊 Attempting to fetch {len(urls)} URLs...")

    for i, url in enumerate(urls[:3], 1):  # Test first 3 URLs only
        print(f"\n{i}. Fetching: {url}")

        result = fetch(url, use_cache=False)

        if result.success:
            content_preview = result.content[:200] if result.content else "No content"
            print(f"   ✅ Success (Status: {result.status_code})")
            print(f"   Preview: {content_preview}...")
        else:
            print(f"   ❌ Failed: {result.error_message}")


def test_full_integration():
    """Test the complete integration flow"""
    print("\n" + "=" * 60)
    print("TEST 4: Full Integration Test")
    print("=" * 60)

    from intent import analyze_intent
    from planner import create_plan

    user_question = "삼성전자 지금 사면 좋을까?"

    print(f"\n❓ User Question: {user_question}")

    # Step 1: Analyze intent
    print("\n1️⃣ Analyzing intent...")
    intent = analyze_intent(user_question, use_llm=False)

    print(f"   - Type: {intent.question_type}")
    print(f"   - Stock: {intent.stock_name} ({intent.stock_code})")

    # Manually set stock code for testing
    if not intent.stock_code:
        print("   - Setting stock code manually: 005930")
        intent.stock_code = "005930"
        intent.stock_name = "삼성전자"

    # Step 2: Create plan with Tavily
    print("\n2️⃣ Creating fetch plan (with Tavily)...")
    plans = create_plan(intent, use_tavily=True)

    print(f"   - Total plans: {len(plans)}")

    tavily_plans = [p for p in plans if p.plan_id.startswith('T')]
    direct_plans = [p for p in plans if not p.plan_id.startswith('T')]

    print(f"   - Direct URL plans: {len(direct_plans)}")
    print(f"   - Tavily URL plans: {len(tavily_plans)}")

    print("\n   Direct URLs:")
    for plan in direct_plans:
        print(f"     - {plan.plan_id}: {plan.description}")
        print(f"       {plan.url}")

    if tavily_plans:
        print("\n   Tavily URLs:")
        for plan in tavily_plans:
            print(f"     - {plan.plan_id}: {plan.description}")
            print(f"       {plan.url}")
    else:
        print("\n   ⚠️ No Tavily URLs (Tavily might not be configured)")

    # Step 3: Test fetch from one Tavily URL
    if tavily_plans:
        print("\n3️⃣ Testing fetch from first Tavily URL...")
        first_tavily_plan = tavily_plans[0]

        result = fetch(first_tavily_plan.url, use_cache=False)

        if result.success:
            print(f"   ✅ Success")
            print(f"   Content length: {len(result.content) if result.content else 0} chars")
        else:
            print(f"   ❌ Failed: {result.error_message}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 TAVILY INTEGRATION TEST SUITE")
    print("=" * 60)

    # Test 1: Basic search
    results = test_tavily_search()

    # Test 2: Search by question type
    urls = test_tavily_by_question_type()

    # Test 3: Fetch from Tavily URLs
    test_fetch_tavily_urls(urls)

    # Test 4: Full integration
    test_full_integration()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

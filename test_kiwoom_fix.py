"""
Quick test to verify the Kiwoom fix
"""
from dotenv import load_dotenv
load_dotenv()

from intent import analyze_intent
from planner import create_plan

# Test query
test_query = "키움증권 지금 사면 좋을까?"

print("=" * 60)
print(f"Testing: {test_query}")
print("=" * 60)

# Step 1: Intent analysis
print("\n[1] Intent Analysis")
intent = analyze_intent(test_query, use_llm=False)
print(f"   Question Type: {intent.question_type}")
print(f"   Stock Name: {intent.stock_name}")
print(f"   Stock Code: {intent.stock_code}")

# Step 2: Create plan
print("\n[2] Create Plan (with Tavily)")
plans = create_plan(intent, use_tavily=True)
print(f"   Total Plans: {len(plans)}")

# Show all plans
for i, plan in enumerate(plans, 1):
    print(f"\n   Plan {i}:")
    print(f"      ID: {plan.plan_id}")
    print(f"      Description: {plan.description}")
    print(f"      URL: {plan.url}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

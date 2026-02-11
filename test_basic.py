"""
간단한 통합 테스트
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("다음 금융 Q&A 챗봇 - 기본 테스트")
print("=" * 60)

# Test 1: Intent Analysis
print("\n[테스트 1] 질문 의도 분석")
print("-" * 60)

from intent import analyze_intent

test_questions = [
    "삼성전자 지금 사면 좋을까?",
    "005930 현재 가격은?",
    "카카오 사람들 의견은?",
]

for q in test_questions:
    print(f"\n질문: {q}")
    intent = analyze_intent(q, use_llm=False)
    print(f"  - 유형: {intent.question_type}")
    print(f"  - 종목코드: {intent.stock_code}")
    print(f"  - 종목명: {intent.stock_name}")

# Test 2: Planner
print("\n\n[테스트 2] 탐색 계획 생성")
print("-" * 60)

from planner import create_plan

intent = analyze_intent("삼성전자 지금 사면 좋을까?", use_llm=False)
plans = create_plan(intent)

print(f"\n생성된 계획 개수: {len(plans)}")
for i, plan in enumerate(plans, 1):
    print(f"\nPlan {i}:")
    print(f"  - ID: {plan.plan_id}")
    print(f"  - 설명: {plan.description}")
    print(f"  - URL: {plan.url[:80]}...")

# Test 3: Fetch (with allowlist)
print("\n\n[테스트 3] Allowlist 테스트")
print("-" * 60)

from daum_fetch import fetch

# Test allowed domain
print("\n[OK] 허용된 도메인 테스트:")
result = fetch("https://finance.daum.net/api/search/ranks?limit=10", use_cache=False)
print(f"  - 성공 여부: {result.success}")
print(f"  - 상태 코드: {result.status_code}")
if not result.success:
    print(f"  - 오류: {result.error_message}")

# Test blocked domain
print("\n[BLOCK] 차단된 도메인 테스트:")
result = fetch("https://www.naver.com", use_cache=False)
print(f"  - 성공 여부: {result.success}")
print(f"  - 오류: {result.error_message}")

# Test 4: Real fetch and parse
print("\n\n[테스트 4] 실제 데이터 수집 테스트 (삼성전자)")
print("-" * 60)

from endpoints import get_price_url, get_news_url
from parsers import parse_price_page, parse_news_list

stock_code = "005930"

# Fetch price
print(f"\n시세 정보 수집 중...")
price_url = get_price_url(stock_code)
print(f"URL: {price_url}")

result = fetch(price_url, use_cache=False)
if result.success:
    price_data = parse_price_page(result.content)
    print(f"[OK] 시세 정보 수집 성공:")
    if price_data:
        print(f"  - 현재가: {price_data.get('current_price', 'N/A')}")
        print(f"  - 전일비: {price_data.get('change', 'N/A')}")
        print(f"  - 등락률: {price_data.get('change_rate', 'N/A')}")
    else:
        print(f"  [WARN] 파싱된 데이터 없음")
else:
    print(f"[FAIL] 실패: {result.error_message}")

# Fetch news
print(f"\n뉴스 정보 수집 중...")
news_url = get_news_url(stock_code)
print(f"URL: {news_url}")

result = fetch(news_url, use_cache=False)
if result.success:
    news_list = parse_news_list(result.content)
    print(f"[OK] 뉴스 정보 수집 성공:")
    print(f"  - 뉴스 개수: {len(news_list)}")
    if news_list:
        print(f"  - 최신 뉴스: {news_list[0].get('title', 'N/A')[:50]}...")
else:
    print(f"[FAIL] 실패: {result.error_message}")

# Test 5: Full pipeline
print("\n\n[테스트 5] 전체 파이프라인 테스트")
print("-" * 60)

from summarizer import summarize_results
from answer import generate_answer

question = "삼성전자 지금 사면 좋을까?"
print(f"\n질문: {question}")

print("\n1단계: 의도 분석...")
intent = analyze_intent(question, use_llm=False)
print(f"  [OK] 완료 - {intent.stock_name} ({intent.stock_code})")

print("\n2단계: 계획 생성...")
plans = create_plan(intent)
print(f"  [OK] 완료 - {len(plans)}개 계획")

print("\n3단계: 데이터 수집...")
fetch_results = []
for plan in plans[:2]:  # 처음 2개만 테스트
    result = fetch(plan.url, use_cache=True, is_json=plan.is_json)
    fetch_results.append((result, plan))
    status = "[OK]" if result.success else "[FAIL]"
    print(f"  {status} {plan.description}")

print("\n4단계: 요약 생성...")
summaries = summarize_results(fetch_results, plans[:2])
print(f"  [OK] 완료 - {len(summaries)}개 요약")

print("\n5단계: 최종 답변 생성...")
answer_text = generate_answer(intent, plans[:2], summaries, use_llm=False)
print(f"  [OK] 완료 - {len(answer_text)} 글자")

print("\n" + "=" * 60)
print("최종 답변 미리보기 (처음 500자):")
print("=" * 60)
print(answer_text[:500] + "...")

print("\n" + "=" * 60)
print("[OK] 모든 테스트 완료!")
print("=" * 60)
print(f"\n브라우저에서 확인: http://localhost:8501")

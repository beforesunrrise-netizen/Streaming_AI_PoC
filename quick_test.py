"""
삼성전자 거래 현황 질의 빠른 테스트 (UTF-8)
"""

import json
import sys
import io
from datetime import datetime

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from intent import analyze_intent
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH


def test_samsung_query():
    """삼성전자 거래 현황 질의 테스트"""
    print("=" * 80)
    print("삼성전자 거래 현황 질의 테스트")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 질의 설정
    user_query = "삼성전자 거래 현황?"
    
    # STEP 1: Intent 분석
    print("[STEP 1] Intent 분석 중...")
    intent = analyze_intent(user_query, use_llm=False)
    
    print(f"  - 질문 유형: {intent.question_type}")
    print(f"  - 종목 코드: {intent.stock_code}")
    print(f"  - 종목명: {intent.stock_name}")
    print(f"  - Confidence: {intent.confidence}")
    print()
    
    # STEP 2: Plan 생성 (Tavily 활성화)
    print("[STEP 2] Plan 생성 중...")
    plans = create_plan(intent, use_tavily=True)  # Tavily 활성화
    
    if not plans:
        print("  [ERROR] Plan 생성 실패!")
        return
    
    print(f"  - 총 {len(plans)}개 plan 생성됨")
    for i, plan in enumerate(plans, 1):
        print(f"    Plan {i}: {plan.description}")
        print(f"    URL: {plan.url}")
    print()
    
    # STEP 3: Fetch 실행
    print("[STEP 3] 데이터 수집 중...")
    fetch_results = []
    
    for i, plan in enumerate(plans, 1):
        print(f"\n  Fetch {i}/{len(plans)}: {plan.description}")
        print(f"  URL: {plan.url}")
        
        # cache_ttl 결정
        if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
            cache_ttl = CACHE_TTL_NEWS
        elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
            cache_ttl = CACHE_TTL_PRICE
        else:
            cache_ttl = CACHE_TTL_SEARCH
        
        try:
            result = fetch(
                url=plan.url,
                use_cache=False,  # 캐시 비활성화 (테스트용)
                cache_ttl=cache_ttl,
                is_json=plan.is_json
            )
            
            if result.success:
                print(f"  [OK] 성공 (status: {result.status_code})")
                if result.content:
                    content_preview = result.content[:200] if isinstance(result.content, str) else str(result.content)[:200]
                    print(f"  내용 미리보기: {content_preview}...")
                else:
                    print(f"  [WARN] 내용 없음")
            else:
                print(f"  [FAIL] 실패 (status: {result.status_code})")
                print(f"  에러: {result.error_message}")
            
            fetch_results.append((result, plan))
            
        except Exception as e:
            print(f"  [EXCEPTION] 예외 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print()
    
    # 결과 통계
    success_count = sum(1 for result, _ in fetch_results if result.success)
    failed_count = len(fetch_results) - success_count
    
    print(f"[STEP 3 결과]")
    print(f"  - 성공: {success_count}/{len(fetch_results)}")
    print(f"  - 실패: {failed_count}/{len(fetch_results)}")
    print()
    
    # STEP 4: Summarize
    if success_count > 0:
        print("[STEP 4] 데이터 요약 중...")
        try:
            summaries = summarize_results(fetch_results, plans)
            print(f"  - 총 {len(summaries)}개 요약 생성됨")
            
            for i, summary in enumerate(summaries, 1):
                print(f"\n  Summary {i}:")
                print(f"    Source: {summary.source_type}")
                print(f"    URL: {summary.source_url}")
                print(f"    스니펫: {summary.evidence_snippet[:150]}...")
            print()
        except Exception as e:
            print(f"  [FAIL] 요약 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            summaries = []
    else:
        print("[STEP 4] [WARN] 성공한 fetch가 없어 요약 생략")
        summaries = []
    
    # STEP 5: Generate answer
    if summaries:
        print("\n[STEP 5] 최종 답변 생성 중...")
        try:
            answer = generate_answer(
                intent=intent,
                plans=plans,
                summaries=summaries,
                use_llm=False,
                show_details=True
            )
            
            print("\n" + "=" * 80)
            print("최종 답변:")
            print("=" * 80)
            print(answer)
            print("=" * 80)
            
        except Exception as e:
            print(f"  [FAIL] 답변 생성 실패: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[STEP 5] [WARN] 요약 데이터가 없어 답변 생성 불가")
    
    print(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 디버깅을 위한 상세 정보 저장
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'query': user_query,
        'intent': {
            'question_type': intent.question_type,
            'stock_code': intent.stock_code,
            'stock_name': intent.stock_name,
            'confidence': intent.confidence
        },
        'plans': [
            {
                'description': plan.description,
                'url': plan.url,
                'is_json': plan.is_json
            }
            for plan in plans
        ],
        'fetch_results': [
            {
                'plan': plan.description,
                'success': result.success,
                'status_code': result.status_code,
                'error_message': result.error_message,
                'has_content': bool(result.content)
            }
            for result, plan in fetch_results
        ],
        'summaries_count': len(summaries) if summaries else 0
    }
    
    debug_file = f"debug_samsung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(debug_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DEBUG] 디버그 정보 저장: {debug_file}")


if __name__ == "__main__":
    test_samsung_query()

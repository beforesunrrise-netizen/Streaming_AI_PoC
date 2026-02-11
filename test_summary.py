"""
간단한 테스트 스크립트 - 10개 샘플만 테스트
"""

from test_fetch import TEST_STOCKS, TEST_QUERIES, run_fetch_test, TestResult
from datetime import datetime
import json

def main():
    print("=" * 80)
    print("다음 금융 데이터 가져오기 샘플 테스트 (10개)")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    test_result = TestResult()
    
    # 상위 10개 종목만 테스트
    test_count = 0
    for stock_code, stock_name in TEST_STOCKS[:5]:  # 5개 종목
        for question_type, query_templates in TEST_QUERIES.items():
            query_template = query_templates[0]  # 각 유형에서 첫 번째 질문만
            query = query_template.format(stock=stock_name)
            
            print(f"{test_count + 1}. 테스트: {stock_name} - {query}")
            
            try:
                plans, results = run_fetch_test(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    query=query,
                    question_type=question_type
                )
                
                test_result.add_test(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    query=query,
                    question_type=question_type,
                    plans=plans,
                    results=results
                )
                
                # 간단한 결과 출력
                success_count = sum(1 for r, _ in results if r.success)
                total_count = len(results)
                print(f"   결과: {success_count}/{total_count} 성공")
                
            except Exception as e:
                print(f"   오류: {str(e)}")
            
            test_count += 1
            print()
    
    # 결과 요약
    summary = test_result.get_summary()
    
    print("\n")
    print("=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    
    print(f"\n[전체 통계]")
    print(f"  - 총 테스트 수: {summary['total_tests']}")
    print(f"  - 총 fetch 시도: {summary['total_fetches']}")
    print(f"  - 성공한 fetch: {summary['successful_fetches']}")
    print(f"  - 실패한 fetch: {summary['failed_fetches']}")
    print(f"  - 성공률: {summary['success_rate']}")
    
    print(f"\n[질문 유형별 성공 횟수]")
    for qtype, count in summary['success_by_type'].items():
        print(f"  - {qtype}: {count}회")
    
    if summary['fail_by_type']:
        print(f"\n[질문 유형별 실패 횟수]")
        for qtype, count in summary['fail_by_type'].items():
            print(f"  - {qtype}: {count}회")
    
    # 실패 상세 정보
    if summary['failed_details']:
        print(f"\n[실패 상세 정보]")
        for i, detail in enumerate(summary['failed_details'], 1):
            print(f"\n  {i}. {detail['stock']} - {detail['query']}")
            print(f"     질문 유형: {detail['question_type']}")
            print(f"     작업: {detail['plan']}")
            print(f"     에러: {detail['error']}")
    
    # 결과를 JSON 파일로 저장
    output_file = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n[파일 저장 완료] {output_file}")
    print(f"[종료 시간] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return summary


if __name__ == "__main__":
    main()

"""
다음 금융 데이터 가져오기 테스트 스크립트
100개 이상의 테스트 케이스로 fetch 기능을 검증합니다.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm

from intent import analyze_intent
from planner import create_plan
from daum_fetch import fetch
from config import (
    CACHE_TTL_PRICE, 
    CACHE_TTL_NEWS, 
    CACHE_TTL_SEARCH,
    QUESTION_TYPE_BUY_RECOMMENDATION,
    QUESTION_TYPE_PRICE_STATUS,
    QUESTION_TYPE_PUBLIC_OPINION,
    QUESTION_TYPE_NEWS_DISCLOSURE,
    QUESTION_TYPE_OTHER
)


# 테스트할 종목 리스트 (주요 종목들)
TEST_STOCKS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("035420", "NAVER"),
    ("035720", "카카오"),
    ("051910", "LG화학"),
    ("006400", "삼성SDI"),
    ("207940", "삼성바이오로직스"),
    ("005380", "현대차"),
    ("000270", "기아"),
    ("068270", "셀트리온"),
    ("028260", "삼성물산"),
    ("105560", "KB금융"),
    ("055550", "신한지주"),
    ("012330", "현대모비스"),
    ("017670", "SK텔레콤"),
    ("034730", "SK"),
    ("036570", "엔씨소프트"),
    ("003550", "LG"),
    ("096770", "SK이노베이션"),
    ("009150", "삼성전기"),
    ("032830", "삼성생명"),
    ("018260", "삼성에스디에스"),
    ("086790", "하나금융지주"),
    ("003670", "포스코홀딩스"),
    ("010950", "S-Oil"),
]

# 질문 유형별 테스트 쿼리
TEST_QUERIES = {
    QUESTION_TYPE_BUY_RECOMMENDATION: [
        "{stock} 지금 사면 좋을까?",
        "{stock} 투자해도 될까요?",
        "{stock} 매수 추천해?",
        "{stock} 사도 괜찮아?",
    ],
    QUESTION_TYPE_PRICE_STATUS: [
        "{stock} 현재가는?",
        "{stock} 주가 알려줘",
        "{stock} 시세 얼마야?",
        "{stock} 가격 확인",
    ],
    QUESTION_TYPE_PUBLIC_OPINION: [
        "{stock} 사람들 의견은?",
        "{stock} 투자자들 생각은?",
        "{stock} 토론 보여줘",
        "{stock} 커뮤니티 반응은?",
    ],
    QUESTION_TYPE_NEWS_DISCLOSURE: [
        "{stock} 뉴스 보여줘",
        "{stock} 최근 공시 있어?",
        "{stock} 소식 알려줘",
        "{stock} 관련 기사는?",
    ],
}


class TestResult:
    """테스트 결과를 저장하는 클래스"""
    def __init__(self):
        self.total_tests = 0
        self.total_fetches = 0
        self.successful_fetches = 0
        self.failed_fetches = 0
        self.failed_details = []
        self.success_by_type = {}
        self.fail_by_type = {}
        
    def add_test(self, stock_code: str, stock_name: str, query: str, 
                 question_type: str, plans: List, results: List):
        """테스트 결과 추가"""
        self.total_tests += 1
        
        for i, (result, plan) in enumerate(results):
            self.total_fetches += 1
            
            if result.success:
                self.successful_fetches += 1
                self.success_by_type[question_type] = self.success_by_type.get(question_type, 0) + 1
            else:
                self.failed_fetches += 1
                self.fail_by_type[question_type] = self.fail_by_type.get(question_type, 0) + 1
                self.failed_details.append({
                    'stock': f"{stock_name}({stock_code})",
                    'query': query,
                    'question_type': question_type,
                    'plan': plan.description,
                    'url': plan.url,
                    'error': result.error_message or f"HTTP {result.status_code}"
                })
    
    def get_summary(self) -> Dict[str, Any]:
        """테스트 결과 요약 반환"""
        return {
            'total_tests': self.total_tests,
            'total_fetches': self.total_fetches,
            'successful_fetches': self.successful_fetches,
            'failed_fetches': self.failed_fetches,
            'success_rate': f"{(self.successful_fetches / self.total_fetches * 100):.2f}%" if self.total_fetches > 0 else "0%",
            'success_by_type': self.success_by_type,
            'fail_by_type': self.fail_by_type,
            'failed_details': self.failed_details
        }


def run_fetch_test(stock_code: str, stock_name: str, query: str, 
                   question_type: str, use_llm: bool = False) -> tuple:
    """
    단일 fetch 테스트 실행
    
    Returns:
        (plans, fetch_results) tuple
    """
    # Intent 분석 (LLM 없이 패턴 기반으로)
    from intent import IntentResult
    intent = IntentResult(
        question_type=question_type,
        stock_code=stock_code,
        stock_name=stock_name,
        confidence=1.0
    )
    
    # Plan 생성
    plans = create_plan(intent)
    
    # Fetch 실행
    fetch_results = []
    for plan in plans:
        # cache_ttl 결정
        if 'news' in plan.url.lower() or 'disclosure' in plan.url.lower():
            cache_ttl = CACHE_TTL_NEWS
        elif 'price' in plan.url.lower() or 'quote' in plan.url.lower():
            cache_ttl = CACHE_TTL_PRICE
        else:
            cache_ttl = CACHE_TTL_SEARCH
        
        result = fetch(
            url=plan.url,
            use_cache=True,
            cache_ttl=cache_ttl,
            is_json=plan.is_json
        )
        
        fetch_results.append((result, plan))
    
    return plans, fetch_results


def main():
    """메인 테스트 실행 함수"""
    print("=" * 80)
    print("다음 금융 데이터 가져오기 테스트")
    print("=" * 80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"테스트 종목 수: {len(TEST_STOCKS)}")
    print(f"질문 유형 수: {len(TEST_QUERIES)}")
    print(f"예상 테스트 수: {len(TEST_STOCKS) * sum(len(queries) for queries in TEST_QUERIES.values())}")
    print("=" * 80)
    print()
    
    test_result = TestResult()
    
    # 진행률 표시를 위한 총 테스트 수 계산
    total_tests = len(TEST_STOCKS) * sum(len(queries) for queries in TEST_QUERIES.values())
    
    with tqdm(total=total_tests, desc="테스트 진행") as pbar:
        for stock_code, stock_name in TEST_STOCKS:
            for question_type, query_templates in TEST_QUERIES.items():
                for query_template in query_templates:
                    query = query_template.format(stock=stock_name)
                    
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
                        
                    except Exception as e:
                        print(f"\n오류 발생: {stock_name} - {query}")
                        print(f"에러 메시지: {str(e)}")
                    
                    pbar.update(1)
    
    # 결과를 JSON 파일로 먼저 저장 (출력 오류를 방지)
    summary = test_result.get_summary()
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 결과 출력
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
    
    # 실패 상세 정보 (최대 20개만 표시)
    if summary['failed_details']:
        print(f"\n[실패 상세 정보 (최대 20개)]")
        for i, detail in enumerate(summary['failed_details'][:20], 1):
            print(f"\n  {i}. {detail['stock']} - {detail['query']}")
            print(f"     질문 유형: {detail['question_type']}")
            print(f"     작업: {detail['plan']}")
            print(f"     URL: {detail['url'][:80]}...")
            print(f"     에러: {detail['error']}")
        
        if len(summary['failed_details']) > 20:
            print(f"\n  ... 외 {len(summary['failed_details']) - 20}개 더 있음")
    
    print(f"\n[파일 저장 완료] {output_file}")
    print(f"[종료 시간] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return summary


if __name__ == "__main__":
    main()

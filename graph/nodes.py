"""
LangGraph Node definitions for Daum Finance Chatbot
Each node performs a specific task and updates the state
"""
import logging
from typing import Dict, Any
from .state import ChatbotState
from intent import analyze_intent, IntentResult
from planner import create_plan
from daum_fetch import fetch
from summarizer import summarize_results
from answer import generate_answer
from config import CACHE_TTL_PRICE, CACHE_TTL_NEWS, CACHE_TTL_SEARCH

logger = logging.getLogger(__name__)


def intent_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Node 1: Analyze user intent
    
    Determines:
    - Stock code and name
    - Question type
    
    Returns:
        State updates
    """
    logger.info(f"[IntentNode] Analyzing query: {state['user_query'][:50]}...")
    
    try:
        # Analyze intent using existing logic
        intent: IntentResult = analyze_intent(
            state['user_query'],
            use_llm=state['use_llm']
        )
        
        return {
            'intent_analyzed': True,
            'stock_code': intent.stock_code,
            'stock_name': intent.stock_name,
            'question_type': intent.question_type
        }
    
    except Exception as e:
        logger.error(f"[IntentNode] Error: {str(e)}")
        return {
            'intent_analyzed': False,
            'error': f"Intent analysis failed: {str(e)}"
        }


def plan_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Node 2: Create fetch plans
    
    Based on intent, creates plans for data collection
    
    Returns:
        State updates
    """
    logger.info(f"[PlanNode] Creating plans for {state['stock_name']} ({state['stock_code']})")
    
    try:
        # Create IntentResult from state
        from intent import IntentResult
        intent = IntentResult(
            stock_code=state['stock_code'],
            stock_name=state['stock_name'],
            question_type=state['question_type']
        )
        
        # Create plans using existing logic
        plans = create_plan(intent, use_tavily=True)
        
        # Convert plans to dict format for state
        fetch_plans = [
            {
                'plan_id': plan.plan_id,
                'description': plan.description,
                'url': plan.url,
                'parser_name': plan.parser_name,
                'is_json': plan.is_json,
                'title': plan.title
            }
            for plan in plans
        ]
        
        return {
            'plans_created': True,
            'fetch_plans': fetch_plans
        }
    
    except Exception as e:
        logger.error(f"[PlanNode] Error: {str(e)}")
        return {
            'plans_created': False,
            'error': f"Plan creation failed: {str(e)}"
        }


def fetch_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Node 3: Fetch data from sources
    
    Executes all fetch plans and collects data
    
    Returns:
        State updates
    """
    logger.info(f"[FetchNode] Fetching data from {len(state['fetch_plans'])} sources")
    
    try:
        raw_data = []
        successful = 0
        failed = 0
        
        for plan in state['fetch_plans']:
            # Determine cache TTL
            url = plan['url']
            if 'news' in url.lower() or 'disclosure' in url.lower():
                cache_ttl = CACHE_TTL_NEWS
            elif 'price' in url.lower() or 'quote' in url.lower():
                cache_ttl = CACHE_TTL_PRICE
            else:
                cache_ttl = CACHE_TTL_SEARCH
            
            # Fetch data
            result = fetch(
                url=url,
                use_cache=True,
                cache_ttl=cache_ttl,
                is_json=plan['is_json']
            )
            
            # Store result
            raw_data.append({
                'plan': plan,
                'result': {
                    'success': result.success,
                    'content': result.content if result.success else None,
                    'error': result.error_message
                }
            })
            
            if result.success:
                successful += 1
            else:
                failed += 1
        
        return {
            'data_collected': True,
            'raw_data': raw_data,
            'successful_fetches': successful,
            'failed_fetches': failed
        }
    
    except Exception as e:
        logger.error(f"[FetchNode] Error: {str(e)}")
        return {
            'data_collected': False,
            'error': f"Data collection failed: {str(e)}"
        }


def summarize_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Node 4: Summarize collected data
    
    Converts raw data into structured summaries
    Manages token limits automatically with middleware
    
    Returns:
        State updates
    """
    logger.info(f"[SummarizeNode] Summarizing {len(state['raw_data'])} data sources")
    
    try:
        # Convert raw_data back to fetch results format
        from planner import FetchPlan
        from daum_fetch import FetchResult
        from .middleware import compress_summaries_if_needed, estimate_tokens
        
        fetch_results = []
        plans = []
        
        for item in state['raw_data']:
            plan_dict = item['plan']
            result_dict = item['result']
            
            # Reconstruct plan
            plan = FetchPlan(
                plan_id=plan_dict['plan_id'],
                description=plan_dict['description'],
                url=plan_dict['url'],
                parser_name=plan_dict['parser_name'],
                is_json=plan_dict.get('is_json', False),
                title=plan_dict.get('title')
            )
            plans.append(plan)
            
            # Reconstruct result
            result = FetchResult(
                url=plan_dict['url'],
                success=result_dict['success'],
                content=result_dict.get('content'),
                error_message=result_dict.get('error')
            )
            
            fetch_results.append((result, plan))
        
        # Summarize using existing logic
        summaries = summarize_results(fetch_results, plans)
        
        # Convert summaries to dict format
        summary_dicts = [
            {
                'source_type': s.source_type,
                'source_url': s.source_url,
                'key_data': s.key_data,
                'evidence_snippet': s.evidence_snippet
            }
            for s in summaries
        ]
        
        # Calculate token count
        total_text = ' '.join([s['evidence_snippet'] for s in summary_dicts])
        total_tokens = estimate_tokens(total_text)
        
        logger.info(f"[SummarizeNode] Initial token count: {total_tokens}")
        
        # Apply middleware: compress if needed
        summary_dicts = compress_summaries_if_needed(summary_dicts)
        
        # Recalculate after compression
        compressed_text = ' '.join([s['evidence_snippet'] for s in summary_dicts])
        final_tokens = estimate_tokens(compressed_text)
        
        logger.info(f"[SummarizeNode] Final token count: {final_tokens}")
        
        return {
            'summaries_created': True,
            'summaries': summary_dicts,
            'total_tokens': final_tokens
        }
    
    except Exception as e:
        logger.error(f"[SummarizeNode] Error: {str(e)}")
        return {
            'summaries_created': False,
            'error': f"Summarization failed: {str(e)}"
        }


def answer_node(state: ChatbotState) -> Dict[str, Any]:
    """
    Node 5: Generate final answer
    
    Uses LLM to combine all information and generate answer
    
    Returns:
        State updates
    """
    logger.info(f"[AnswerNode] Generating final answer using LLM={state['use_llm']}")
    
    try:
        # Reconstruct objects for answer generation
        from intent import IntentResult
        from planner import FetchPlan
        from summarizer import SourceSummary
        
        intent = IntentResult(
            stock_code=state['stock_code'],
            stock_name=state['stock_name'],
            question_type=state['question_type']
        )
        
        plans = [
            FetchPlan(
                plan_id=p['plan_id'],
                description=p['description'],
                url=p['url'],
                parser_name=p['parser_name'],
                is_json=p.get('is_json', False),
                title=p.get('title')
            )
            for p in state['fetch_plans']
        ]
        
        summaries = [
            SourceSummary(
                source_type=s['source_type'],
                source_url=s['source_url'],
                key_data=s.get('key_data', {}),
                evidence_snippet=s['evidence_snippet']
            )
            for s in state['summaries']
        ]
        
        # Generate answer
        answer_text = generate_answer(
            intent=intent,
            plans=plans,
            summaries=summaries,
            use_llm=state['use_llm'],
            show_details=False,  # Details are shown via state
            chat_history=state['chat_history']
        )
        
        return {
            'answer_generated': True,
            'final_answer': answer_text
        }
    
    except Exception as e:
        logger.error(f"[AnswerNode] Error: {str(e)}")
        return {
            'answer_generated': False,
            'error': f"Answer generation failed: {str(e)}",
            'final_answer': f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}"
        }

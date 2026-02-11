"""
4-step answer generation
"""

import os
from typing import List

from intent import IntentResult
from planner import FetchPlan
from summarizer import SourceSummary
from config import (
    QUESTION_TYPE_BUY_RECOMMENDATION,
    QUESTION_TYPE_PRICE_STATUS,
    QUESTION_TYPE_PUBLIC_OPINION,
    QUESTION_TYPE_NEWS_DISCLOSURE,
    QUESTION_TYPE_OTHER,
    get_env
)


def _get_intent_description(question_type: str) -> str:
    """
    Get human-readable description of question type
    Args:
        question_type: Question type code
    Returns:
        Description string
    """
    descriptions = {
        QUESTION_TYPE_BUY_RECOMMENDATION: "매수/투자 판단에 대한 정보를 원하시는 것으로 보입니다",
        QUESTION_TYPE_PRICE_STATUS: "현재 시세 및 가격 정보를 확인하고자 하시는 것으로 보입니다",
        QUESTION_TYPE_PUBLIC_OPINION: "다른 투자자들의 의견과 반응을 알고 싶으신 것으로 보입니다",
        QUESTION_TYPE_NEWS_DISCLOSURE: "최근 뉴스 및 공시 내용을 확인하고자 하시는 것으로 보입니다",
        QUESTION_TYPE_OTHER: "종목에 대한 일반적인 정보를 원하시는 것으로 보입니다"
    }
    return descriptions.get(question_type, "질문 의도를 파악하기 어렵습니다")


def _generate_final_answer_basic(
    intent: IntentResult,
    summaries: List[SourceSummary]
) -> str:
    """
    Generate final answer using template (basic mode)
    Args:
        intent: Intent analysis result
        summaries: Source summaries
    Returns:
        Final answer text
    """
    question_type = intent.question_type

    # Extract key data from summaries
    price_data = None
    news_data = None
    talks_data = None

    for summary in summaries:
        # Match price data from any source (HTML, API)
        if "시세 정보" in summary.source_type:
            price_data = summary
        elif summary.source_type == "뉴스":
            news_data = summary
        elif summary.source_type == "토론/의견":
            talks_data = summary

    # Generate answer based on question type
    if question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
        answer = "**[다음 금융 데이터 기반 분석]**\n\n"

        if price_data:
            answer += f"**현재 상태:**\n{price_data.evidence_snippet}\n\n"

        if news_data:
            answer += f"**최근 뉴스:**\n{news_data.evidence_snippet}\n\n"

        if talks_data:
            answer += f"**투자자 의견:**\n{talks_data.evidence_snippet}\n\n"

        answer += "**체크포인트:**\n"
        answer += "- 위 정보는 다음 금융에서 수집한 현재 시점 데이터입니다\n"
        answer += "- 투자 결정은 본인의 투자 성향과 재무 상황을 고려하여 신중히 결정하세요\n"
        answer += "- 추가로 기업 재무제표, 업종 동향 등을 확인하는 것이 좋습니다\n"

    elif question_type == QUESTION_TYPE_PRICE_STATUS:
        answer = "**[현재 시세 정보]**\n\n"

        if price_data:
            answer += f"{price_data.evidence_snippet}\n\n"
        else:
            answer += "시세 정보를 확인할 수 없습니다.\n\n"

        answer += "*※ 실시간 데이터가 아닐 수 있으며, 정확한 정보는 다음 금융 사이트에서 확인하세요.*\n"

    elif question_type == QUESTION_TYPE_PUBLIC_OPINION:
        answer = "**[투자자 의견 요약]**\n\n"

        if talks_data:
            answer += f"{talks_data.evidence_snippet}\n\n"
        else:
            answer += "최근 의견을 확인할 수 없습니다.\n\n"

        if price_data:
            answer += f"**참고 - 현재 시세:**\n{price_data.evidence_snippet}\n\n"

        answer += "*※ 개인 의견이므로 참고만 하시고, 투자 판단은 본인의 책임하에 하세요.*\n"

    elif question_type == QUESTION_TYPE_NEWS_DISCLOSURE:
        answer = "**[최근 뉴스 및 공시]**\n\n"

        if news_data:
            answer += f"**뉴스:**\n{news_data.evidence_snippet}\n\n"

        found_disclosure = False
        for summary in summaries:
            if summary.source_type == "공시":
                answer += f"**공시:**\n{summary.evidence_snippet}\n\n"
                found_disclosure = True
                break

        if not news_data and not found_disclosure:
            answer += "최근 뉴스나 공시를 확인할 수 없습니다.\n\n"

    else:
        answer = "**[종목 정보]**\n\n"

        if price_data:
            answer += f"{price_data.evidence_snippet}\n\n"
        else:
            answer += "종목 정보를 확인할 수 없습니다.\n\n"

    return answer


def _generate_final_answer_llm(
    intent: IntentResult,
    summaries: List[SourceSummary],
    chat_history: List = None
) -> str:
    """
    Generate final answer using LLM (optional mode)
    Args:
        intent: Intent analysis result
        summaries: Source summaries
        chat_history: Previous chat messages for context (optional)
    Returns:
        Final answer text
    """
    try:
        # Check if OpenAI API key is available
        if not get_env('OPENAI_API_KEY'):
            import logging
            logger = logging.getLogger(__name__)
            logger.info("No OpenAI API key found, using basic template mode")
            return _generate_final_answer_basic(intent, summaries)

        # Prepare evidence snippets
        evidence = "\n\n".join([
            f"[{summary.source_type}]\n{summary.evidence_snippet}"
            for summary in summaries
        ])

        # Check if we have any evidence
        if not evidence.strip():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("No evidence data available for LLM")
            return _generate_final_answer_basic(intent, summaries)

        # Prepare chat history context
        history_context = ""
        if chat_history and len(chat_history) > 0:
            history_context = "\n**이전 대화 내용:**\n"
            for msg in chat_history[-6:]:  # Last 3 exchanges
                # Handle both dict and object formats
                role_value = msg.get('role') if isinstance(msg, dict) else msg.role
                content_value = msg.get('content') if isinstance(msg, dict) else msg.content
                role = "사용자" if role_value == "user" else "챗봇"
                history_context += f"{role}: {content_value[:200]}...\n"
            history_context += "\n"

        # Get current date
        from datetime import datetime
        current_date = datetime.now().strftime('%Y년 %m월 %d일')
        
        prompt_text = f"""당신은 초보 투자자를 돕는 친절한 주식 가이드입니다.
다음 금융에서 수집한 데이터를 **쉽고 간단하게** 정리해서 알려주세요.

**오늘 날짜:** {current_date}

{history_context}**종목:** {intent.stock_name} ({intent.stock_code})

**수집한 정보:**
{evidence}

---

## 📝 답변 작성 가이드

**매우 중요 - 답변 순서:**
1. **결론부터 먼저 말하기** (가장 위에)
2. 그 다음에 이유/근거 설명

**답변 구조:**

### ✅ 결론 (제일 먼저!)
- 질문에 대한 답을 **첫 문장에 바로** 제시
- 예: "삼성전자는 현재 상승세를 보이고 있어 긍정적으로 평가됩니다"
- 예: "네이버는 최근 약세를 보이고 있어 신중한 접근이 필요해 보입니다"
- 단, 직접적인 "사세요/파세요" 표현은 금지

### 📊 현재 상황 ({current_date} 기준)
- 현재가, 등락률을 **한 줄로** 간단히
- 예: "현재 50,000원으로 전일 대비 2% 상승 중입니다"

### 📰 주요 이유/근거
- 뉴스나 리포트의 **핵심 내용만** 2-3줄로 요약
- 목표가나 실적 같은 중요한 숫자 포함
- 예: "증권사에서 목표가 60,000원을 제시했고, 실적 개선이 예상됩니다"

### 💬 시장 반응
- 투자자들의 의견을 **한 줄로**
- 예: "투자자들은 대체로 긍정적인 반응입니다"

### ⚠️ 참고
- 투자 유의사항 한 문장

**작성 규칙:**
- ✅ **결론을 맨 처음에 먼저 말하기**
- ✅ {current_date} 기준 데이터임을 명시
- ✅ 쉬운 말로 짧고 명확하게
- ✅ 핵심만 간추려서
- ❌ "매수하세요" 같은 직접 권유 금지
- ❌ "~할 것입니다" 같은 확정 예측 금지

---

위 가이드에 따라 **결론부터 먼저 제시하고, 그 다음 근거를 설명하는 답변**을 작성하세요:"""

        # Use OpenAI API
        from openai import OpenAI
        from config import LLM_MODEL_OPENAI, LLM_MAX_TOKENS, LLM_TEMPERATURE
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Calling OpenAI API with model: {LLM_MODEL_OPENAI}")
        
        client = OpenAI(api_key=get_env('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model=LLM_MODEL_OPENAI,
            max_completion_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt_text}]
        )

        logger.info("OpenAI API call successful")
        return response.choices[0].message.content

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LLM answer generation failed: {str(e)}", exc_info=True)
        logger.info("Falling back to basic template mode")
        return _generate_final_answer_basic(intent, summaries)


def generate_answer(
    intent: IntentResult,
    plans: List[FetchPlan],
    summaries: List[SourceSummary],
    use_llm: bool = False,
    show_details: bool = True,
    chat_history: List = None
) -> str:
    """
    Generate 4-step structured answer

    Args:
        intent: Intent analysis result
        plans: Fetch plans
        summaries: Source summaries
        use_llm: Whether to use LLM for answer generation (default: False)
        show_details: Whether to show detailed steps 1-3 (default: True)
        chat_history: Previous chat messages for context (optional)

    Returns:
        Complete answer as markdown string
    """
    output = []

    # Show detailed steps only if requested
    if show_details:
        # Step 1: Intent Analysis
        output.append("### [1] 질문 의도 분석\n")
        output.append(f"- **질문 유형:** {intent.question_type}")
        output.append(f"- **대상 종목:** {intent.stock_name or '확인 불가'} ({intent.stock_code or '확인 불가'})")
        output.append(f"- **사용자가 원하는 것:** {_get_intent_description(intent.question_type)}\n")

        # Step 2: Exploration Plan
        output.append("### [2] 다음 금융 탐색 계획\n")
        if plans:
            for i, plan in enumerate(plans, 1):
                output.append(f"- **Plan {i}:** {plan.description}")
                output.append(f"  - URL: `{plan.url}`")
        else:
            output.append("- 탐색 계획을 생성할 수 없습니다 (종목 정보 부족)\n")
        output.append("")

        # Step 3: Scraping Results Summary
        output.append("### [3] 다음 금융 스크랩 결과 요약\n")
        if summaries:
            for i, summary in enumerate(summaries, 1):
                output.append(f"**Source {i}: {summary.source_type}**")
                output.append(f"- URL: `{summary.source_url}`")
                output.append(f"- 근거 스니펫:\n```\n{summary.evidence_snippet}\n```\n")
        else:
            output.append("- 수집된 데이터가 없습니다.\n")

        # Step 4: Final Answer
        output.append("### [4] 최종 답변 (초보자 친화)\n")

    # Generate final answer (always shown)
    if summaries:
        if use_llm:
            final_answer = _generate_final_answer_llm(intent, summaries, chat_history)
        else:
            final_answer = _generate_final_answer_basic(intent, summaries)
        output.append(final_answer)
    else:
        output.append("질문에 답변할 수 있는 충분한 데이터를 수집하지 못했습니다.")
        output.append("종목 코드를 확인하거나, 다시 시도해주세요.\n")

    # Reference section - ALWAYS show (even when show_details=False)
    # This ensures users can verify all data comes from finance.daum.net
    output.append("\n---")
    
    if show_details:
        output.append("### 📎 참고한 다음 금융 페이지\n")
    else:
        output.append("**📎 참고한 다음 금융 페이지**\n")

    if summaries:
        # Collect unique URLs
        reference_urls = []
        seen_urls = set()

        for summary in summaries:
            url = summary.source_url
            if url and url not in seen_urls:
                seen_urls.add(url)
                reference_urls.append({
                    'type': summary.source_type,
                    'url': url
                })

        # Display as clickable links
        if reference_urls:
            for i, ref in enumerate(reference_urls[:7], 1):  # Limit to 7 references
                # Extract a friendly name from URL or use source type
                friendly_name = ref['type'] or f"참고 {i}"
                output.append(f"{i}. [{friendly_name}]({ref['url']})")
        else:
            output.append("- 참고 URL 없음")
    else:
        output.append("- 수집된 데이터 없음")

    output.append("")

    # Footer - compact version
    if show_details:
        output.append("---")
        output.append("**⚠️ 주의사항:**")
        output.append("- 본 정보는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다")
        output.append("- 투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다")
        output.append("- 실시간 데이터가 아닐 수 있으니, 정확한 정보는 직접 확인하세요")
    else:
        # Minimal footer for clean mode
        output.append("\n\n---")
        output.append("*본 정보는 다음 금융 데이터 기반이며, 투자 판단은 본인 책임입니다*")

    return "\n".join(output)

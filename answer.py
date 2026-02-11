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
    QUESTION_TYPE_OTHER
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
    chart_data = None

    for summary in summaries:
        if summary.source_type == "시세 정보":
            price_data = summary
        elif summary.source_type == "뉴스":
            news_data = summary
        elif summary.source_type == "토론/의견":
            talks_data = summary
        elif summary.source_type == "차트":
            chart_data = summary

    # Generate answer based on question type
    if question_type == QUESTION_TYPE_BUY_RECOMMENDATION:
        answer = "**[다음 금융 데이터 기반 분석]**\n\n"

        if price_data:
            answer += f"**현재 상태:**\n{price_data.evidence_snippet}\n\n"

        if chart_data:
            answer += f"**최근 추세:**\n{chart_data.evidence_snippet}\n\n"

        if news_data:
            answer += f"**최근 뉴스:**\n{news_data.evidence_snippet}\n\n"

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
    summaries: List[SourceSummary]
) -> str:
    """
    Generate final answer using LLM (optional mode)
    Args:
        intent: Intent analysis result
        summaries: Source summaries
    Returns:
        Final answer text
    """
    try:
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            return _generate_final_answer_basic(intent, summaries)

        # Prepare evidence snippets
        evidence = "\n\n".join([
            f"[{summary.source_type}]\n{summary.evidence_snippet}"
            for summary in summaries
        ])

        prompt_text = f"""당신은 다음 금융 데이터만을 사용하는 투자 정보 도우미입니다.
**절대 외부 지식이나 학습된 정보를 사용하지 마세요.**

아래 근거 스니펫만을 바탕으로 초보 투자자가 이해하기 쉽게 답변을 생성하세요.

질문 유형: {intent.question_type}
종목: {intent.stock_name} ({intent.stock_code})

근거 스니펫:
{evidence}

다음 형식으로 답변하세요:

**[한 줄 요약]**
(핵심 내용을 한 문장으로)

**[현재 상태]**
(근거 스니펫의 데이터를 바탕으로 현재 상태 설명)

**[체크포인트]**
- 확인한 데이터 출처 명시 (다음 금융)
- 투자 판단 시 주의사항
- 추가로 확인하면 좋을 정보

**중요:**
- 확정적 예측이나 추천은 절대 금지
- "~할 것이다", "~하세요" 같은 표현 금지
- "현재 상태는 ~입니다", "~를 확인해보세요" 형식 사용
"""

        # Use Anthropic Claude if available
        if os.getenv('ANTHROPIC_API_KEY'):
            import anthropic
            from config import LLM_MODEL_ANTHROPIC, LLM_MAX_TOKENS, LLM_TEMPERATURE

            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            message = client.messages.create(
                model=LLM_MODEL_ANTHROPIC,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt_text}]
            )

            return message.content[0].text

        # Use OpenAI if Anthropic is not available
        elif os.getenv('OPENAI_API_KEY'):
            from openai import OpenAI
            from config import LLM_MODEL_OPENAI, LLM_MAX_TOKENS, LLM_TEMPERATURE

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model=LLM_MODEL_OPENAI,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt_text}]
            )

            return response.choices[0].message.content

        # Fallback to basic mode
        return _generate_final_answer_basic(intent, summaries)

    except Exception:
        return _generate_final_answer_basic(intent, summaries)


def generate_answer(
    intent: IntentResult,
    plans: List[FetchPlan],
    summaries: List[SourceSummary],
    use_llm: bool = False
) -> str:
    """
    Generate 4-step structured answer

    Args:
        intent: Intent analysis result
        plans: Fetch plans
        summaries: Source summaries
        use_llm: Whether to use LLM for answer generation (default: False)

    Returns:
        Complete 4-step answer as markdown string
    """
    output = []

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
    if summaries:
        if use_llm:
            final_answer = _generate_final_answer_llm(intent, summaries)
        else:
            final_answer = _generate_final_answer_basic(intent, summaries)
        output.append(final_answer)
    else:
        output.append("질문에 답변할 수 있는 충분한 데이터를 수집하지 못했습니다.")
        output.append("종목 코드를 확인하거나, 다시 시도해주세요.\n")

    # Footer
    output.append("\n---")
    output.append("**⚠️ 주의사항:**")
    output.append("- 본 정보는 다음 금융(finance.daum.net) 데이터를 기반으로 합니다")
    output.append("- 투자 판단 및 결과에 대한 책임은 투자자 본인에게 있습니다")
    output.append("- 실시간 데이터가 아닐 수 있으니, 정확한 정보는 직접 확인하세요")

    return "\n".join(output)

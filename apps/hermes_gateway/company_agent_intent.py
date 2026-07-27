"""Shared deterministic intent and response-mode policy for company agents."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


AGENT_INTENTS = (
    "write", "rewrite", "summarize", "extract_facts", "review", "evaluate",
    "recommend", "compare", "plan", "research", "status",
    "approve_or_publish", "execute", "general",
)

AGENT_INTENT_CAPABILITIES = {
    "hermes": {
        "status": "executive_status", "summarize": "executive_summary",
        "plan": "coordination_plan", "evaluate": "executive_evaluation",
        "recommend": "executive_recommendation", "write": "general_business_draft",
        "review": "cross_function_review",
    },
    "kasumi": {
        "research": "research_report", "summarize": "research_summary",
        "compare": "internal_external_comparison", "extract_facts": "evidence_extraction",
        "recommend": "research_based_recommendation", "write": "research_based_draft",
    },
    "meiko": {
        "review": "operations_risk_review", "plan": "execution_checklist",
        "summarize": "operations_summary", "extract_facts": "requirements_extraction",
        "evaluate": "operational_feasibility", "write": "operations_document_draft",
        "approve_or_publish": "compliance_approval_review",
    },
    "marin": {
        "write": "design_concept_writing", "recommend": "design_direction",
        "review": "design_review", "compare": "design_option_comparison",
        "summarize": "design_summary", "plan": "design_development_plan",
        "evaluate": "design_feasibility",
    },
    "lucy": {
        "write": "copywriting", "rewrite": "copy_rewrite", "review": "copy_review",
        "approve_or_publish": "publish_review", "summarize": "content_summary",
        "extract_facts": "brand_fact_extraction", "recommend": "content_direction",
    },
    "reze": {
        "evaluate": "business_evaluation", "compare": "strategic_comparison",
        "recommend": "strategic_recommendation", "plan": "priority_roadmap",
        "summarize": "strategy_summary", "review": "business_risk_review",
        "write": "strategy_document_draft",
    },
}

INTENT_PATH_HINTS = {
    "write": ("소개", "copy", "content", "draft", "제안서", "homepage", "portfolio"),
    "review": ("review", "검토", "계약", "체크", "requirements"),
    "status": ("status", "progress", "진행", "회의", "결정", "일정"),
    "research": ("research", "조사", "공고", "시장", "경쟁사"),
    "plan": ("plan", "roadmap", "계획", "일정", "단계"),
    "compare": ("compare", "비교", "경쟁사", "차이"),
    "summarize": ("summary", "요약", "정리"),
}

INTENT_QUERY_HINTS = {
    "write": "소개 기업 소개 홈페이지 서비스 사업영역 프로젝트 포트폴리오 강점 작업방식",
    "rewrite": "기존 문구 브랜드 톤 표현 정확성 가독성",
    "summarize": "기존 자료 핵심 내용 결정사항 요약",
    "extract_facts": "확인된 사실 수치 결정사항 근거",
    "review": "검토 요구사항 위험 오류 정확성",
    "evaluate": "평가 기준 근거 가능성 위험 우선순위",
    "recommend": "대안 추천 이유 적용 조건",
    "compare": "비교 기준 공통점 차이점 장단점",
    "plan": "계획 단계 일정 담당 선행조건",
    "research": "조사 자료 출처 조건 일정",
    "status": "진행상황 완료 결정사항 일정 담당 다음 단계",
}

OUTPUT_RULES = {
    "write": "Provide the finished draft first. Do not output approval, hold, or review status.",
    "rewrite": "Provide the revised text first and briefly explain changes. Rewrite only the supplied source text.",
    "summarize": "Summarize only the supplied evidence. Do not force new recommendations.",
    "extract_facts": "List confirmed facts only, cite them, and mark unknown items.",
    "review": "Give findings, problems, revision direction, and a concrete revision example. Do not invent approval state.",
    "evaluate": "Separate criteria, evidence, strengths, risks, judgment, and uncertainty.",
    "recommend": "Give a recommendation, reasons, alternatives, and conditions.",
    "compare": "Separate comparison criteria, similarities, differences, tradeoffs, and selection conditions.",
    "plan": "Give goal, stages, priorities, prerequisites, and checks.",
    "research": "Separate findings, evidence, confirmed facts, and unknowns.",
    "status": "Use completed, in progress, blockers, and next steps.",
    "approve_or_publish": "Use publishable, publish after revision, or hold. This is the only default publication-decision mode.",
    "execute": "Do not execute. Apply the existing approval and external-action gate.",
    "general": "Answer the request directly within the agent's professional perspective.",
}


@dataclass(frozen=True)
class AgentIntentDecision:
    intent: str
    confidence: str
    reason: str
    source_text_present: bool
    source_text: str
    approval_required: bool
    user_instruction_misclassified_as_source_text: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentResponseMode:
    agent_name: str
    intent: str
    mode: str
    fixed_role_template_used: bool = False


_QUOTED = re.compile(r"[\"“](.{12,}?)[\"”]", re.S)
_CODE = re.compile(r"```(?:\w+)?\s*(.*?)```", re.S)
_EXPLICIT_SOURCE = re.compile(r"(?:원문|source(?:\s+text)?)\s*[:：]\s*(.{12,})", re.I | re.S)


def extract_source_text(
    user_message: str,
    *,
    route: dict[str, Any] | None = None,
    replied_message_content: str | None = None,
) -> tuple[str, str]:
    if replied_message_content and str(replied_message_content).strip():
        return str(replied_message_content).strip()[:6000], "reply_message"
    route_source = (route or {}).get("source_text")
    if route_source and str(route_source).strip():
        return str(route_source).strip()[:6000], "route_metadata"
    text = str(user_message or "")
    for pattern, reason in ((_CODE, "code_block"), (_QUOTED, "quoted_text"), (_EXPLICIT_SOURCE, "explicit_source_label")):
        match = pattern.search(text)
        if match and match.group(1).strip():
            return match.group(1).strip()[:6000], reason
    if ":" in text:
        candidate = text.split(":", 1)[1].strip()
        if len(candidate) >= 30 and not candidate.startswith("//"):
            return candidate[:6000], "colon_source_text"
    return "", "no_source_text"


def _has(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def classify_agent_intent(
    *,
    user_message: str,
    selected_agent: str,
    route: dict[str, Any] | None = None,
    replied_message_content: str | None = None,
) -> AgentIntentDecision:
    del selected_agent
    text = str(user_message or "").strip()
    source_text, _source_reason = extract_source_text(
        text, route=route, replied_message_content=replied_message_content
    )
    rules = (
        ("execute", ("게시해줘", "전송해줘", "업로드해줘", "삭제해줘", "승인 처리해줘", "publish now", "send now", "deploy")),
        ("approve_or_publish", ("게시해도", "발행 가능", "공개해도", "최종 승인", "보내도 돼", "올려도 되는지")),
        ("review", ("검토해줘", "문제점", "피드백", "어색한지", "리스크를 확인")),
        ("rewrite", ("다듬어줘", "고쳐줘", "자연스럽게 바꿔", "짧게 바꿔", "다시 써줘", "톤을 바꿔")),
        ("write", ("써줘", "작성해줘", "초안", "소개문", "카피", "문장을 만들어", "문구를 새로")),
        ("compare", ("비교해줘", "차이를 정리", "중 뭐가 나은", "비교")),
        ("evaluate", ("판단해줘", "사업성", "가능성을 평가", "우선순위를 매겨", "타당성")),
        ("recommend", ("추천해줘", "방향을 제안", "골라줘", "대안을 제시")),
        ("plan", ("계획을 세워", "로드맵", "순서를 정해", "실행 단계", "일정을 짜", "절차를 단계")),
        ("research", ("조사해줘", "찾아줘", "리서치", "자료를 수집", "최신 정보를 확인")),
        ("status", ("어디까지", "현재 상태", "진행 상황", "무엇이 남았", "최근 결정사항")),
        ("summarize", ("요약해줘", "핵심만", "간단히 정리", "한눈에", "요약")),
        ("extract_facts", ("사실만", "수치만", "결정된 내용만")),
    )
    for intent, terms in rules:
        if _has(text, terms):
            if intent == "rewrite" and not source_text:
                continue
            return AgentIntentDecision(
                intent, "high", f"explicit_{intent}_request", bool(source_text),
                source_text, intent == "execute"
            )
    return AgentIntentDecision("general", "low", "no_explicit_intent_signal", bool(source_text), source_text, False)


def resolve_agent_response_mode(*, agent_name: str, intent: str) -> AgentResponseMode:
    agent = str(agent_name or "hermes").lower()
    normalized_intent = intent if intent in AGENT_INTENTS else "general"
    mode = AGENT_INTENT_CAPABILITIES.get(agent, {}).get(normalized_intent, "general_role_response")
    return AgentResponseMode(agent, normalized_intent, mode, False)


def build_intent_prompt_context(
    *, agent_name: str, decision: AgentIntentDecision, response_mode: AgentResponseMode
) -> str:
    rule = OUTPUT_RULES.get(decision.intent, OUTPUT_RULES["general"])
    return (
        "[AGENT_RESPONSE_CONTEXT]\n"
        f"selected_agent: {agent_name.upper()}\n"
        f"user_intent: {decision.intent}\n"
        f"response_mode: {response_mode.mode}\n"
        f"source_text_present: {str(decision.source_text_present).lower()}\n"
        f"approval_required: {str(decision.approval_required).lower()}\n\n"
        "Follow the user's intent first.\n"
        "Use the agent role as professional perspective, not as a fixed output template.\n"
        "Do not use review, approval, or recommendation formatting unless the intent requires it.\n"
        "Do not treat the user's task instruction as source copy.\n"
        "Do not reuse fixture or example project text.\n"
        f"Output rule: {rule}\n"
        "[/AGENT_RESPONSE_CONTEXT]"
    )


def build_agent_rag_query(*, agent_name: str, intent: str, user_message: str) -> str:
    del agent_name
    hint = INTENT_QUERY_HINTS.get(intent, "")
    return f"{user_message.strip()} {hint}".strip()[:900]


def intent_metadata_boost(intent: str, result: dict[str, Any]) -> float:
    hints = INTENT_PATH_HINTS.get(intent, ())
    haystack = " ".join(str(result.get(key) or "") for key in ("relative_path", "source_label", "asset_type")).casefold()
    return 0.04 if any(hint.casefold() in haystack for hint in hints) else 0.0


def assess_rag_sufficiency(results: list[dict[str, Any]], intent: str) -> dict[str, Any]:
    text_results = [item for item in results if str(item.get("media_type") or "").lower() not in {"image", "image_metadata"}]
    image_results = [item for item in results if item not in text_results]
    relevant = sum(1 for item in results if intent_metadata_boost(intent, item) > 0)
    evidence_chars = sum(len(str(item.get("snippet") or "")) for item in text_results)
    low = len(text_results) < 1 or evidence_chars < 200 or (intent in INTENT_PATH_HINTS and relevant == 0)
    return {
        "rag_sufficiency": "low" if low else "medium",
        "text_source_count": len(text_results),
        "image_metadata_source_count": len(image_results),
        "intent_relevant_source_count": relevant,
        "evidence_char_count": evidence_chars,
    }


def build_intent_aware_deterministic_fallback(
    *, agent_name: str, intent: str, user_message: str,
    source_text: str | None = None, rag_context: Any | None = None,
) -> dict[str, Any]:
    del rag_context
    request = " ".join(str(user_message or "").split())[:240]
    headings = {
        "write": ("완성 초안", "확인된 내부 정보", "추가 확인이 필요한 정보"),
        "rewrite": ("수정 결과", "변경 이유", "확인 사항"),
        "summarize": ("핵심 요약", "확인된 자료", "미확인 사항"),
        "extract_facts": ("확인된 사실", "근거", "미확인 사항"),
        "review": ("검토 결과", "문제점", "수정 방향", "수정 예시"),
        "evaluate": ("평가", "근거", "위험", "불확실성"),
        "recommend": ("추천안", "추천 이유", "대안", "적용 조건"),
        "compare": ("비교 기준", "공통점", "차이점", "선택 조건"),
        "plan": ("목표", "실행 단계", "우선순위", "확인 사항"),
        "research": ("조사 결과", "근거", "미확인 사항"),
        "status": ("완료", "진행 중", "막힌 점", "다음 단계"),
        "approve_or_publish": ("판정", "근거", "수정 필요 사항"),
        "execute": ("외부 실행 차단", "필요한 승인", "다음 단계"),
        "general": ("답변", "확인 사항"),
    }
    body = [f"[{agent_name.upper()}_STOXL]", f"요청: {request}"]
    for index, heading in enumerate(headings.get(intent, headings["general"])):
        detail = "제공된 자료에서 확인 필요" if index else (
            str(source_text).strip()[:400] if source_text else "현재 확인 가능한 범위에서 초안을 준비했습니다."
        )
        body.extend(("", f"{heading}:", detail))
    return {
        "content": "\n".join(body),
        "deterministic_fallback_intent_aware": True,
        "fixed_role_template_used": False,
    }

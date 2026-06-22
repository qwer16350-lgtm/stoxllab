"""Company agent response builder with deterministic fallback by default."""

from __future__ import annotations

import os
from typing import Any, Mapping

from company_agent_llm import generate_agent_reply
from company_agent_registry import get_agent, get_report_format


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _reply_mode(env: Mapping[str, str] | None = None) -> str:
    env_map = os.environ if env is None else env
    return str(env_map.get("HERMES_COMPANY_AGENT_REPLY_MODE", "deterministic_fallback") or "deterministic_fallback")


def _llm_enabled(env: Mapping[str, str] | None = None) -> bool:
    env_map = os.environ if env is None else env
    return _flag(env_map.get("HERMES_COMPANY_AGENT_LLM_ENABLED", "false"))


def build_prompt_envelope(agent_id: str, message: str, route: dict[str, Any]) -> dict[str, Any]:
    agent = get_agent(agent_id) or {}
    return {
        "envelope_type": "company_agent_prompt_envelope",
        "agent_id": agent_id,
        "agent_display_name": agent.get("display_name"),
        "prompt_path": agent.get("prompt_path"),
        "report_format": get_report_format(agent_id),
        "route_reason": route.get("reason"),
        "external_execution_allowed": False,
        "messages_preview": [
            {"role": "system", "content": f"Use {agent.get('display_name', agent_id)} persona. External execution is forbidden."},
            {"role": "user", "content": message[:1200]},
        ],
    }


def _summary(message: str) -> str:
    return (message or "요청 내용 없음").strip()[:300]


def _external_requested(message: str, route: dict[str, Any]) -> bool:
    if route.get("external_execution_requested"):
        return True
    lowered = str(message or "").lower()
    return any(
        word in lowered
        for word in (
            "publish",
            "deploy",
            "submit",
            "send email",
            "sns 게시",
            "게시",
            "배포",
            "제출",
            "업로드",
        )
    )


def build_approval_draft(agent_id: str, message: str, route: dict[str, Any]) -> dict[str, Any]:
    agent = get_agent(agent_id) or {}
    reviewer = "lucy" if agent_id == "marin" else "meiko" if agent_id == "kasumi" else agent_id
    external_requested = _external_requested(message, route)
    content = (
        "[APPROVAL_REQUEST]\n"
        f"작성 agent: {agent_id}\n"
        f"검토 agent: {reviewer}\n"
        f"관련 채널: {route.get('source_channel')}\n"
        f"요청 요약: {_summary(message)}\n"
        "결정 필요사항: 진행 여부와 공개/제출 여부를 사람이 결정해야 합니다.\n"
        "추천안: 승인 전까지 초안/검토 상태로 보류합니다.\n"
        "리스크: 공개, 제출, 배포, 외부 발송은 승인 전 실행할 수 없습니다.\n"
        "다음 액션: 결정권자 검토 후 승인/보류/폐기를 선택합니다.\n"
        f"external_execution_requested: {str(external_requested).lower()}\n"
        "external_execution_performed: false"
    )
    return {
        "approval_draft_created": True,
        "approval_channel": "최종-승인요청",
        "external_execution_requested": external_requested,
        "external_execution_performed": False,
        "content": content,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _template_for_agent(agent_id: str, message: str, route: dict[str, Any]) -> str:
    summary = _summary(message)
    if agent_id == "marin":
        return (
            "[MARIN_STOXL / 마린]\n"
            "소속: 마케팅팀 주니어\n"
            "업무: 초안 생성\n\n"
            f"요청 요약:\n{summary}\n\n"
            "초안:\n"
            "1. 핵심 장점을 먼저 보여주는 짧은 문구\n"
            "2. 사용자가 바로 이해할 수 있는 보조 문구\n"
            "3. SNS/홈페이지에 맞게 다듬을 수 있는 대안 문구\n\n"
            "체크 필요:\n"
            "- 어색한 말투\n"
            "- 브랜드 적합성\n"
            "- 게시 가능성\n\n"
            "handoff:\n"
            "to: lucy-검토\n"
            "reason: 마케팅 시니어 검토 필요"
        )
    if agent_id == "lucy":
        return (
            "[LUCY_STOXL / 루시]\n"
            "소속: 마케팅팀 시니어\n"
            "업무: 검토 / 발행 판단\n\n"
            "검토 결과:\n"
            "- 판정: 수정 필요\n"
            "- 이유: 공개 전 브랜드 톤과 과장 표현을 한 번 더 확인해야 합니다.\n"
            "- 수정 제안: 핵심 이점은 유지하고 단정적인 표현은 낮춥니다.\n\n"
            "최종승인 필요 여부:\n"
            "true\n\n"
            "next:\n"
            "최종-승인요청"
        )
    if agent_id == "kasumi":
        return (
            "[KASUMI_STOXL / 카스미]\n"
            "소속: 운영팀 주니어\n"
            "업무: 리서치 / 후보 정리\n\n"
            "리서치 후보:\n"
            "1. 이름: 후보 1\n"
            "   목적: 지원 가능성 확인\n"
            "   마감: 확인 필요\n"
            "   필요자료: 사업자 정보, 소개서, 예산안\n"
            "   리스크: 조건 불확실\n\n"
            "handoff:\n"
            "to: meiko-검토\n"
            "reason: 운영 시니어 판단 필요"
        )
    if agent_id == "meiko":
        return (
            "[MEIKO_STOXL / 메이코]\n"
            "소속: 운영팀 선임\n"
            "업무: 실행 판단 / 일정 / 리스크\n\n"
            "판단:\n"
            "- 추천 / 보류 / 비추천: 보류\n\n"
            "이유:\n"
            "- 마감, 제출자료, 내부 담당이 아직 확정되지 않았습니다.\n\n"
            "실행 조건:\n"
            "- 필요자료: 공고 원문, 회사 소개자료, 예산 정보\n"
            "- 마감: 확인 필요\n"
            "- 해당: 운영팀 검토\n\n"
            "리스크:\n"
            "- 승인 전 제출 금지\n\n"
            "next:\n"
            "최종-승인요청 또는 kasumi-리서치"
        )
    if agent_id == "reze":
        return (
            "[REZE_STOXL / 레제]\n"
            "소속: 전략기획실\n"
            "업무: 브랜드 전략/제품 방향 비평\n\n"
            "전략 판단:\n"
            "- 방향성: 검토 가치 있음\n"
            "- 스톡스 적합성: 브랜드 톤과 연결 가능\n"
            "- 리스크: 실행 범위가 커지면 승인 필요\n"
            "- 실험 가능성: 작은 메시지 테스트부터 가능\n"
            "- 우선순위: 중간\n\n"
            "보고:\n"
            "to: 대표-회의실"
        )
    return f"[{agent_id.upper()}]\n요청 요약:\n{summary}\nexternal_execution_allowed: false"


def build_deterministic_company_agent_reply(agent_id: str, message: str, route: dict[str, Any]) -> dict[str, Any]:
    agent = get_agent(agent_id) or {}
    target = route.get("target_channel") or agent.get("default_channel")
    handoff = route.get("handoff_to") or agent.get("handoff_target")
    handoff_channel = route.get("handoff_channel") or target
    content = _template_for_agent(agent_id, message, route)
    return {
        "response_type": "company_agent_response",
        "reply_text_source": "deterministic_fallback",
        "agent_id": agent_id,
        "webhook_persona": agent.get("webhook_persona"),
        "target_channel": target,
        "handoff_to": handoff,
        "handoff_channel": handoff_channel,
        "content": content,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_response(
    agent_id: str,
    message: str,
    route: dict[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    mode = _reply_mode(env)
    if _llm_enabled(env) and mode in {"llm", "llm_with_deterministic_fallback"}:
        llm_result = generate_agent_reply(agent_id, message, route, dict(env or os.environ))
        if llm_result.get("llm_succeeded"):
            agent = get_agent(agent_id) or {}
            return {
                "response_type": "company_agent_response",
                "reply_text_source": "llm",
                "agent_id": agent_id,
                "webhook_persona": agent.get("webhook_persona"),
                "target_channel": route.get("target_channel") or agent.get("default_channel"),
                "handoff_to": route.get("handoff_to") or agent.get("handoff_target"),
                "handoff_channel": route.get("handoff_channel") or route.get("target_channel") or agent.get("default_channel"),
                "content": llm_result.get("response_text", ""),
                "llm_result": llm_result,
                "llm_api_call_attempted": True,
                "llm_api_called": bool(llm_result.get("llm_api_called")),
                "rag_called": False,
                "external_execution": False,
                "raw_content_logged": False,
                "raw_discord_ids_logged": False,
                "secret_values_logged": False,
            }
        deterministic = build_deterministic_company_agent_reply(agent_id, message, route)
        deterministic["llm_result"] = llm_result
        deterministic["llm_api_call_attempted"] = bool(llm_result.get("llm_attempted"))
        deterministic["llm_api_called"] = bool(llm_result.get("llm_api_called", False))
        deterministic["fallback_used"] = "deterministic"
        return deterministic
    if mode == "llm" and not _llm_enabled(env):
        deterministic = build_deterministic_company_agent_reply(agent_id, message, route)
        deterministic["llm_result"] = {
            "llm_attempted": False,
            "llm_succeeded": False,
            "fallback_used": "deterministic",
            "rag_called": False,
            "embedding_called": False,
            "external_execution": False,
        }
        return deterministic
    return build_deterministic_company_agent_reply(agent_id, message, route)

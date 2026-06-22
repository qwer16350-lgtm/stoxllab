"""Company agent response builder with deterministic fallback by default."""

from __future__ import annotations

import os
from typing import Any, Mapping

from company_agent_llm import generate_agent_reply, redact_company_agent_text
from company_agent_registry import get_agent, get_report_format
from company_persistent_memory import append_memory_record


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
    return redact_company_agent_text((message or "요청 내용 없음").strip(), 300)


def _handoff_excerpt(content: str) -> str:
    safe = redact_company_agent_text(content, 900)
    lines = [
        line
        for line in safe.splitlines()
        if not (
            (line.startswith("[") and "_STOXL" in line)
            or line.startswith("소속:")
            or line.startswith("업무:")
        )
    ]
    return "\n".join(lines).strip()


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
    persisted = append_memory_record(
        "approval",
        {
            "source_agent": agent_id,
            "target_channel": "최종-승인요청",
            "title": f"{_summary(message)[:90]} 승인 요청",
            "summary": _summary(message),
            "content": content,
            "recommendation": "승인 전까지 초안/검토 상태로 보류",
            "risk": "공개, 제출, 배포, 외부 발송은 승인 전 실행 금지",
            "external_execution_requested": external_requested,
            "external_execution_performed": False,
            "status": "pending",
        },
    )
    return {
        "approval_draft_created": True,
        "approval_channel": "최종-승인요청",
        "external_execution_requested": external_requested,
        "external_execution_performed": False,
        "content": content,
        "persistent_approval_written": bool(persisted.get("record_written")),
        "persistent_memory_warning": persisted.get("warning_code"),
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _template_for_agent(agent_id: str, message: str, route: dict[str, Any]) -> str:
    summary = _summary(message)
    context = route.get("handoff_context") if isinstance(route.get("handoff_context"), dict) else None
    context_source = str((context or {}).get("source_agent") or "").lower()
    context_content = _handoff_excerpt(str((context or {}).get("handoff_content") or ""))
    if agent_id == "meiko" and context and context_source == "kasumi":
        return (
            "[MEIKO_STOXL / 메이코]\n"
            "소속: 운영팀 선임\n"
            "업무: 실행 판단 / 일정 / 리스크\n"
            "판단:\n"
            "- 추천 / 보류 / 비추천: 보류\n\n"
            "이유:\n"
            "카스미가 넘긴 내용 기준으로 보면, 현재 자료만으로 즉시 신청을 확정하기보다 "
            "후보의 실제 공고 조건을 검증하는 것이 맞습니다.\n\n"
            "전달 근거:\n"
            f"{context_content}\n\n"
            "1차 판단:\n"
            "- 추천도: 보류\n"
            "- 이유: 마감/자격/자부담/평가항목이 특정되지 않은 후보 단계\n"
            "- 가능성: 시제품/PoC/사업화 지원 유형은 STOXL 제품 개발과 연결 가능\n\n"
            "실행 조건:\n"
            "우선 확인:\n"
            "1. 실제 공고명\n"
            "2. 마감일\n"
            "3. 신청 자격\n"
            "4. 자부담 여부\n"
            "5. 제출물\n"
            "6. STOXL 사업자 조건 적합성\n\n"
            "리스크:\n"
            "- 최신 공고 조건 확인 전 신청 여부를 확정하면 일정과 자격 판단이 틀릴 수 있음\n\n"
            "next:\n"
            "카스미가 실제 공고 URL/마감/자격을 확인하면 메이코가 최종 지원 여부를 판단합니다."
        )
    if agent_id == "lucy" and context and context_source == "marin":
        return (
            "[LUCY_STOXL / 루시]\n"
            "소속: 마케팅팀 시니어\n"
            "업무: 검토 / 발행 판단\n\n"
            "마린이 넘긴 초안 기준 검토 결과:\n"
            "판정: 수정 필요\n\n"
            "검토 대상:\n"
            f"{context_content}\n\n"
            "이유:\n"
            "- 제품 특징과 사용 장면이 함께 드러나는 문장을 우선해야 합니다.\n"
            "- 사실 확인 전에는 조합 방식이나 효과를 단정하지 않는 편이 안전합니다.\n\n"
            "수정 제안:\n"
            "1. 첫 문장: '작은 구조가 만드는 큰 변화, MML.'\n"
            "2. 보조 문장: '쌓고 돌리며 배치를 바꾸는 미니 모듈 라이트입니다.'\n"
            "3. 이미지 캡션: '책상 위 작은 구조, MML.'\n\n"
            "최종승인 필요 여부:\n"
            "true\n\n"
            "next:\n"
            "제품 사양 확인 후 최종-승인요청"
        )
    if agent_id == "reze" and context:
        return (
            "[REZE_STOXL / 레제]\n"
            "소속: 전략기획실\n"
            "업무: 브랜드 전략/제품 방향 비평\n\n"
            "대표-회의실 전달 내용 기준 전략 판단:\n"
            f"{context_content}\n\n"
            "- 브랜드 방향성: 전달안의 중심 가설을 한 문장으로 고정할 필요가 있음\n"
            "- 스톡슬 적합성: 구조와 사용 논리가 드러나는지 우선 검증\n"
            "- 리스크: 실행 항목이 늘어나면 핵심 가설이 흐려짐\n"
            "- 실험 가능성: 가장 작은 고객 반응 테스트 1개로 축소\n"
            "- 우선순위: 가설 선명화 후 판단"
        )
    if agent_id == "marin":
        return (
            "[MARIN_STOXL / 마린]\n"
            "소속: 마케팅팀 주니어\n"
            "업무: 초안 생성\n\n"
            f"요청 요약:\n{summary}\n\n"
            "초안:\n"
            "1. [인스타 첫 문장] 작은 구조가 만드는 큰 변화, MML.\n"
            "2. [인스타 보조 문장] 쌓고, 돌리고, 바꾸며 내 공간에 맞추는 미니 모듈 라이트.\n"
            "3. [홈페이지 소개] 책상 위 작은 구조에서 시작하는 모듈 조명, MML.\n\n"
            "체크 필요:\n"
            "Lucy 검토 포인트:\n"
            "- '모듈'과 조합 방식이 실제 제품 사양과 맞는지\n"
            "- '작은 건축'의 스톡슬 톤 적합성과 과장 여부\n"
            "- 제품 이미지가 없을 때도 첫 문장이 이해되는지\n\n"
            "handoff:\n"
            "to: lucy-검토\n"
            "reason: 마케팅 시니어 검토 필요"
        )
    if agent_id == "lucy":
        return (
            "[LUCY_STOXL / 루시]\n"
            "소속: 마케팅팀 시니어\n"
            "업무: 검토 / 발행 판단\n\n"
            "판정: 수정 필요\n"
            "이유:\n"
            "- '작은 건축'은 스톡슬다운 표현이지만 제품 기능을 단독으로 설명하지는 못합니다.\n"
            "- '내 공간에 맞춘다'는 문장은 실제 조합 방식이 확인될 때만 사용할 수 있습니다.\n\n"
            "수정 제안:\n"
            "1. 첫 문장: '작은 구조가 만드는 큰 변화, MML.'\n"
            "2. 보조 문장: '쌓고 돌리며 배치를 바꾸는 미니 모듈 라이트입니다.'\n"
            "3. 이미지 캡션: '책상 위 작은 구조, MML.'\n\n"
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
            "1. 디자인 지원사업 후보\n"
            "   후보: 제품/브랜드 홍보 또는 전시 지원 분야\n"
            "   마감: 확인 필요\n"
            "   필요자료: 공고문, 신청 자격, 제출물 목록\n"
            "   리스크: 현재 실시간 검색 미사용으로 최신성 검증 필요\n\n"
            "Meiko 판단 포인트:\n"
            "- 공고 원문 확인 후 일정 대비 준비 비용이 타당한지\n"
            "- 전시/홍보 목적이 현재 제품 단계와 맞는지\n\n"
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
            "- 현재 공고명/마감/지원조건이 확정되지 않았습니다.\n"
            "- 지원 가능성은 있으나 일정과 제출물 확인이 먼저입니다.\n\n"
            "실행 조건:\n"
            "- 공고 URL 확인\n"
            "- 제출물 목록 정리\n"
            "담당:\n"
            "- Kasumi: 공고 원문과 제출물 확인\n"
            "- Meiko: 일정 및 투입 비용 판단\n"
            "마감:\n"
            "- 공고 마감일 확인 전 일정 확정 금지\n\n"
            "리스크:\n"
            "- 최신 공고 미확인 상태에서 자격과 일정을 단정할 수 없음\n"
            "- 승인 전 제출 금지\n\n"
            "next:\n"
            "Kasumi가 공고 원문을 확보한 뒤 Meiko가 지원 여부를 재판정"
        )
    if agent_id == "reze":
        return (
            "[REZE_STOXL / 레제]\n"
            "소속: 전략기획실\n"
            "업무: 브랜드 전략/제품 방향 비평\n\n"
            "전략 판단:\n"
            "- 브랜드 방향성: 로우테크를 외형이 아니라 사용자가 구조를 이해하고 바꾸는 경험으로 정의해야 함\n"
            "- 스톡슬 적합성: 구조와 조립 논리가 보일 때 강함; 단순 빈티지 스타일이면 약함\n"
            "- 리스크: 제품군 기준 없이 소재와 형태만 늘리면 브랜드가 소품 모음처럼 보임\n"
            "- 실험 가능성: 대표 구조 1개를 정해 조합 전후 이미지와 설명 문구를 소규모 비교\n"
            "- 우선순위: 높음, 단 제품 확장보다 시리즈 원칙 정의가 먼저\n\n"
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
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "handoff_context_used": bool(route.get("handoff_context")),
        "handoff_context_source_agent": (route.get("handoff_context") or {}).get("source_agent")
        if isinstance(route.get("handoff_context"), dict)
        else None,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _decision_value(agent_id: str, content: str) -> str:
    if agent_id == "lucy":
        for value in ("발행 가능", "수정 필요", "보류"):
            if value in content:
                return value
    if agent_id == "meiko":
        for value in ("비추천", "추천", "보류"):
            if value in content:
                return value
    if agent_id == "reze" and any(marker in content for marker in ("전략 판단", "우선순위", "스톡슬 적합성")):
        return "전략 판단"
    return ""


def _with_persistent_decision(
    response: dict[str, Any],
    agent_id: str,
    message: str,
    route: dict[str, Any],
) -> dict[str, Any]:
    if agent_id not in {"lucy", "meiko", "reze"}:
        return response
    content = str(response.get("content") or "")
    decision = _decision_value(agent_id, content)
    if not decision:
        return response
    persisted = append_memory_record(
        "decision",
        {
            "agent": agent_id,
            "channel": route.get("source_channel") or route.get("target_channel"),
            "title": f"{_summary(message)[:90]} 판단",
            "summary": _summary(message),
            "content": content,
            "decision": decision,
            "risk": "응답 내 리스크 항목 확인",
            "next_action": "응답의 next 항목에 따라 담당자 검토",
            "status": "open",
        },
    )
    return {
        **response,
        "persistent_decision_written": bool(persisted.get("record_written")),
        "persistent_memory_warning": persisted.get("warning_code"),
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
            response = {
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
            return _with_persistent_decision(response, agent_id, message, route)
        deterministic = build_deterministic_company_agent_reply(agent_id, message, route)
        deterministic["llm_result"] = llm_result
        deterministic["llm_api_call_attempted"] = bool(llm_result.get("llm_attempted"))
        deterministic["llm_api_called"] = bool(llm_result.get("llm_api_called", False))
        deterministic["fallback_used"] = "deterministic"
        return _with_persistent_decision(deterministic, agent_id, message, route)
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
        return _with_persistent_decision(deterministic, agent_id, message, route)
    deterministic = build_deterministic_company_agent_reply(agent_id, message, route)
    return _with_persistent_decision(deterministic, agent_id, message, route)

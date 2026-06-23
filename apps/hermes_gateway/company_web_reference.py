"""Role-scoped, manually gated read-only web reference for company agents."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

from company_persistent_memory import append_memory_record
from company_web_research import (
    fetch_readonly_page_summary as _fetch_readonly_page_summary,
    run_readonly_web_search as _run_provider_search,
)
from llm_client import redact_text


SUPPORTED_MODES = ("off", "manual_command_only")
ALLOWED_AGENTS = ("lucy", "marin", "meiko", "kasumi", "reze")
AGENT_SCOPES = {
    "kasumi": "research_discovery",
    "meiko": "operational_verification",
    "marin": "content_reference",
    "lucy": "publication_review",
    "reze": "strategy_market_reference",
}
GENERIC_TERMS = ("최신", "검색", "찾아줘", "조사", "검증", "공고", "마감", "트렌드", "경쟁사", "레퍼런스", "사례", "시장", "요즘", "현재")
AGENT_TERMS = {
    "kasumi": ("지원사업", "공모전", "전시", "정부지원", "창업지원", "후보", "자료조사", "디자인 지원"),
    "meiko": ("공고 원문", "자격", "자격요건", "제출서류", "자부담", "리스크", "넣을만한지"),
    "marin": ("sns", "인스타", "홈페이지", "콘텐츠", "유사 표현", "캠페인", "문구"),
    "lucy": ("발행", "표현 리스크", "브랜드 문맥", "공개", "오해 가능성", "검토"),
    "reze": ("시장 흐름", "포지셔닝", "제품 방향", "브랜드 방향", "전략", "방향성"),
}
WEB_COMMANDS = {"web", "search", "research", "find", "검증"}
SearchRunner = Callable[[str, list[str], int], dict[str, Any]]


def _env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(os.environ if env is None else env)


def _flag(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _mode(env: dict[str, Any] | None = None) -> str:
    selected = str(_env(env).get("HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE", "off") or "off").strip().lower()
    return selected if selected in SUPPORTED_MODES else "off"


def is_web_reference_enabled(env: dict[str, Any] | None = None) -> bool:
    env_map = _env(env)
    return _flag(env_map.get("HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED", "false")) and _mode(env_map) == "manual_command_only"


def resolve_agent_web_scope(agent_id: str) -> str:
    return AGENT_SCOPES.get(str(agent_id or "").strip().lower(), "blocked")


def detect_web_reference_intent(agent_id: str, message: str, context: dict[str, Any] | None = None) -> bool:
    selected_agent = str(agent_id or "").strip().lower()
    if selected_agent not in ALLOWED_AGENTS:
        return False
    command = str((context or {}).get("command") or "").strip().lower()
    if command in WEB_COMMANDS:
        return True
    lowered = str(message or "").strip().lower()
    terms = GENERIC_TERMS + AGENT_TERMS.get(selected_agent, ())
    return any(term.lower() in lowered for term in terms)


def _manual_command(agent_id: str, message: str, context: dict[str, Any] | None = None) -> bool:
    command = str((context or {}).get("command") or "").strip().lower()
    if command in WEB_COMMANDS or command in ALLOWED_AGENTS or command == "agent":
        return True
    normalized = str(message or "").lstrip().lower()
    prefixes = tuple(f"!{command_name} " for command_name in WEB_COMMANDS | {str(agent_id).lower()})
    return normalized.startswith(prefixes)


def build_agent_search_queries(agent_id: str, message: str, context: dict[str, Any] | None = None) -> list[str]:
    cleaned = re.sub(
        r"^!(?:web|search|research|find|검증|lucy|marin|meiko|kasumi|reze|agent\s+\w+)\s+",
        "",
        str(message or "").strip(),
        flags=re.IGNORECASE,
    )
    cleaned = redact_text(cleaned, 320).strip() or "최신 자료 확인"
    scope_terms = {
        "kasumi": "공식 모집 공고 지원대상 마감",
        "meiko": "공식 공고 자격요건 마감 제출서류 자부담",
        "marin": "브랜드 캠페인 콘텐츠 사례",
        "lucy": "공개 표현 브랜드 커뮤니케이션 사례",
        "reze": "시장 경쟁사 브랜드 포지셔닝 트렌드",
    }
    year = datetime.now(timezone.utc).year
    queries = [cleaned, f"{cleaned} {scope_terms.get(agent_id, '')} {year}".strip()]
    return list(dict.fromkeys(queries))[:3]


def run_readonly_web_search(
    agent_id: str,
    queries: list[str],
    limit: int = 5,
    env: dict[str, Any] | None = None,
    opener: Any | None = None,
) -> dict[str, Any]:
    result = _run_provider_search(queries, limit, env, opener)
    return {
        **result,
        "agent_scope": resolve_agent_web_scope(agent_id),
        "read_only": True,
        "external_execution": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def fetch_readonly_page_summary(url: str, opener: Any | None = None) -> dict[str, Any]:
    result = _fetch_readonly_page_summary(url, opener)
    return {
        **result,
        "read_only": True,
        "external_execution": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
    }


def _normalized_results(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in results:
        normalized.append(
            {
                "title": redact_text(str(item.get("title") or "제목 확인 필요"), 240),
                "source": redact_text(str(item.get("institution") or item.get("source") or "출처 확인 필요"), 160),
                "url": str(item.get("url") or "")[:800] or "확인 필요",
                "summary": redact_text(str(item.get("snippet") or item.get("summary") or "요약 확인 필요"), 600),
                "needs_verification": "검색 결과 기준, 최종 사용 전 원문 확인 필요",
            }
        )
    return normalized


def _common_reference_block(agent_id: str, query: str, results: list[dict[str, str]]) -> list[str]:
    lines = [
        "[WEB_REFERENCE]",
        "검색 기준:",
        f"- agent: {agent_id}",
        f"- query: {redact_text(query, 320)}",
        f"- 검색 시점: {datetime.now(timezone.utc).isoformat()}",
        "- 최신성: 검색 결과 기준, 최종 사용 전 원문 확인 필요",
        "",
        "결과:",
    ]
    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"{index}. 제목: {item['title']}",
                f"   출처: {item['source']}",
                f"   URL: {item['url']}",
                f"   요약: {item['summary']}",
                f"   확인 필요: {item['needs_verification']}",
                "",
            ]
        )
    lines.append("[/WEB_REFERENCE]")
    return lines


def format_agent_web_reference_block(agent_id: str, results: list[dict[str, Any]], query: str = "") -> str:
    normalized = _normalized_results(results)
    lines = _common_reference_block(agent_id, query, normalized)
    first = normalized[0] if normalized else {"title": "확인 필요", "source": "확인 필요", "url": "확인 필요", "summary": "확인 필요"}
    if agent_id == "kasumi":
        lines.extend(
            [
                "",
                "지원사업 후보:",
                f"1. 후보명: {first['title']}",
                f"   기관: {first['source']}",
                "   마감: 확인 필요",
                "   지원대상: 확인 필요",
                f"   지원내용: {first['summary']}",
                "   필요자료: 확인 필요",
                f"   URL: {first['url']}",
                "   리스크: 최종 신청 전 공고 원문 검증 필요",
                "   확인 필요: 자격, 마감, 자부담, 제출자료",
            ]
        )
    elif agent_id == "meiko":
        lines.extend(
            [
                "",
                "검증 결과:",
                "- 판단: 보류",
                f"- 근거 URL: {first['url']}",
                "- 자격요건: 확인 필요",
                "- 마감: 확인 필요",
                "- 제출서류: 확인 필요",
                "- 리스크: 검색 요약만으로 실행 여부 확정 불가",
                "- 다음 액션: 공고 원문과 STOXL 조건 대조",
            ]
        )
    elif agent_id == "marin":
        lines.extend(
            [
                "",
                "레퍼런스 참고:",
                f"- 참고한 톤/표현: {first['title']}의 공개 표현 구조 참고",
                "- 그대로 베끼지 않고 STOXL 톤으로 재작성",
                "- 초안 3개:",
                "  1. 구조가 보이면, 쓰임도 선명해집니다.",
                "  2. 오래 쓰기 위해 단순하게 만든 가구.",
                "  3. 형태보다 구조에서 시작하는 STOXL.",
            ]
        )
    elif agent_id == "lucy":
        lines.extend(
            [
                "",
                "검토 결과:",
                "- 발행 가능성: 수정 후 검토",
                "- 표현 리스크: 외부 사례와 동일하거나 단정적인 표현인지 확인 필요",
                "- 최신성/오해 가능성: 검색 결과와 실제 제품 사양의 일치 여부 확인 필요",
                "- 수정안: 출처 표현을 복제하지 말고 제품의 확인된 구조와 쓰임으로 재작성",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "전략 판단:",
                f"- 시장/경쟁 맥락: {first['summary']}",
                "- 스톡슬 적합성: 구조와 사용 논리로 차별화 가능한지 확인 필요",
                "- 리스크: 트렌드 모방으로 보일 가능성",
                "- 실험 가능성: 핵심 메시지 1개로 소규모 반응 비교",
                "- 우선순위: 근거 원문 검토 후 결정",
            ]
        )
    return "\n".join(lines)[:6000]


def format_agent_web_failure(agent_id: str, reason: str) -> str:
    return (
        f"[{agent_id.upper()}_STOXL]\n"
        "현재 read-only web reference를 수행하지 못했습니다.\n"
        f"reason: {reason}\n"
        "fallback: 공식 원문을 수동 확인하고, 확인되지 않은 값은 확인 필요로 유지합니다.\n"
        "external_execution: false"
    )


def build_company_agent_web_reference_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    env_map = _env(env)
    provider = str(env_map.get("HERMES_WEB_SEARCH_PROVIDER", "disabled") or "disabled").lower()
    return {
        "report_type": "company_agent_web_reference_report",
        "web_reference_available": True,
        "default_web_reference_enabled": False,
        "default_web_reference_mode": "off",
        "current_web_reference_enabled": is_web_reference_enabled(env_map),
        "current_web_reference_mode": _mode(env_map),
        "supported_modes": list(SUPPORTED_MODES),
        "allowed_agents": list(ALLOWED_AGENTS),
        "agent_scopes": dict(AGENT_SCOPES),
        "provider_configured": provider in {"serper", "brave", "tavily", "custom"},
        "api_key_present": bool(env_map.get("HERMES_WEB_SEARCH_API_KEY")),
        "read_only": True,
        "external_execution_allowed": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_web_reference_dry_run(agent_id: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    intent = detect_web_reference_intent(agent_id, message, context)
    manual = _manual_command(agent_id, message, context or {"command": agent_id})
    return {
        "report_type": "company_agent_web_reference_dry_run",
        "selected_agent": agent_id,
        "agent_scope": resolve_agent_web_scope(agent_id),
        "intent_detected": intent,
        "manual_command": manual,
        "would_search_web": intent and manual and agent_id in ALLOWED_AGENTS,
        "actual_web_called": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_company_agent_web_reference_one_shot(
    agent_id: str,
    message: str,
    *,
    allow_web_reference: bool = False,
    env: dict[str, Any] | None = None,
    search_runner: SearchRunner | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    env_map = _env(env)
    intent = detect_web_reference_intent(agent_id, message, context)
    manual = _manual_command(agent_id, message, context or {"command": agent_id})
    if not allow_web_reference:
        reason = "blocked_by_policy"
    elif not is_web_reference_enabled(env_map):
        reason = "web_reference_disabled"
    elif agent_id not in ALLOWED_AGENTS or not intent or not manual:
        reason = "blocked_by_policy"
    else:
        reason = ""
    queries = build_agent_search_queries(agent_id, message, context)
    if reason:
        search = {"search_succeeded": False, "failure_reason": reason, "provider": "unknown", "results": []}
    else:
        search = (search_runner or (lambda a, q, n: run_readonly_web_search(a, q, n, env_map)))(agent_id, queries, 5)
    success = bool(search.get("search_succeeded")) and bool(search.get("results"))
    report_text = (
        format_agent_web_reference_block(agent_id, list(search.get("results") or []), queries[0])
        if success
        else format_agent_web_failure(agent_id, str(search.get("failure_reason") or "no_results"))
    )
    memory = {"record_written": False}
    if success:
        memory = append_memory_record(
            "recent_item",
            {
                "item_type": "web_reference",
                "agent": agent_id,
                "title": f"{redact_text(queries[0], 100)} web reference",
                "summary": f"{agent_id} web reference {len(search.get('results') or [])}건",
                "content": report_text,
                "source_urls_present": any(item.get("url") for item in search.get("results") or []),
                "external_execution_performed": False,
                "rag_called": False,
                "embedding_called": False,
                "status": "open",
            },
        )
    block = f"[WEB_REFERENCE_RESULTS]\n{report_text}\n[/WEB_REFERENCE_RESULTS]" if success else ""
    return {
        "report_type": "company_agent_web_reference_one_shot",
        "selected_agent": agent_id,
        "agent_scope": resolve_agent_web_scope(agent_id),
        "allow_web_reference": bool(allow_web_reference),
        "intent_detected": intent,
        "manual_command": manual,
        "web_search_attempted": not bool(reason),
        "web_search_succeeded": success,
        "failure_reason": search.get("failure_reason") or ("no_results" if not success and not reason else reason),
        "provider": search.get("provider", "unknown"),
        "result_count": len(search.get("results") or []),
        "reference_report": report_text,
        "web_reference_results_block": block,
        "persistent_memory_written": bool(memory.get("record_written")),
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "read_only": True,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }

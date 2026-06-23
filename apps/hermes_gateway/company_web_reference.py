"""Role-scoped, manually gated read-only web reference for company agents."""

from __future__ import annotations

import os
import re
import urllib.parse
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
KOREAN_GENERIC_TERMS = ("최신", "검색", "찾아줘", "조사", "검증", "공고", "마감", "트렌드", "경쟁사", "레퍼런스", "사례", "시장", "요즘", "현재")
KOREAN_AGENT_TERMS = {
    "kasumi": ("지원사업", "공모전", "공시", "정부지원", "창업지원", "후보", "자료조사", "디자인 지원"),
    "meiko": ("공고 원문", "자격", "자격요건", "제출서류", "지원금", "리스크", "넣을만한지"),
    "marin": ("sns", "인스타", "홈페이지", "콘텐츠", "유사 표현", "캠페인", "문구"),
    "lucy": ("발행", "표현 리스크", "브랜드 문맥", "공개", "오해 가능성", "검토"),
    "reze": ("시장 흐름", "사업방식", "제품 방향", "브랜드 방향", "전략", "방향성"),
}
AGENT_TERMS = {
    "kasumi": ("지원사업", "공모전", "전시", "정부지원", "창업지원", "후보", "자료조사", "디자인 지원"),
    "meiko": ("공고 원문", "자격", "자격요건", "제출서류", "자부담", "리스크", "넣을만한지"),
    "marin": ("sns", "인스타", "홈페이지", "콘텐츠", "유사 표현", "캠페인", "문구"),
    "lucy": ("발행", "표현 리스크", "브랜드 문맥", "공개", "오해 가능성", "검토"),
    "reze": ("시장 흐름", "포지셔닝", "제품 방향", "브랜드 방향", "전략", "방향성"),
}
WEB_COMMANDS = {"web", "search", "research", "find", "검증"}
SearchRunner = Callable[[str, list[str], int], dict[str, Any]]

OFFICIAL_SOURCE_HOSTS = {
    "bizinfo.go.kr",
    "k-startup.go.kr",
    "kidp.or.kr",
    "busan.go.kr",
    "dcb.or.kr",
    "seouldesign.or.kr",
    "rdcdp.or.kr",
    "gov.kr",
    "mss.go.kr",
    "seoul.go.kr",
    "gyeonggi.go.kr",
    "incheon.go.kr",
}
INTERMEDIARY_SOURCE_HOSTS = {
    "govhelpers.com",
    "blog.naver.com",
    "tistory.com",
    "brunch.co.kr",
    "medium.com",
    "namu.wiki",
}
RESULT_GUIDE_KEYWORDS = (
    "선정평가 결과",
    "선정 결과",
    "결과 안내",
    "최종 선정",
    "선정기업",
    "지원과제 선정",
)
DEADLINE_PATTERNS = (
    re.compile(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?\s*[~\-]\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?"),
    re.compile(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})\s*[~\-]\s*(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})"),
    re.compile(r"(?:신청기간|모집기간)\s*[:.]?\s*[^~\n]{0,30}~\s*(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})(?:\.[^0-9]|[^0-9]|$)"),
    re.compile(r"(?:공고일|공고일자)?\s*[^~\n]{0,20}~\s*(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})(?:\.[^0-9]|[^0-9]|$)"),
    re.compile(r"마감(?:까지)?\s*[:.]?\s*(D-\d+)", re.IGNORECASE),
)


def _env(env: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(os.environ if env is None else env)


def _flag(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _host_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or ""))
    return (parsed.hostname or "").lower().removeprefix("www.")


def classify_source_type(url: str) -> str:
    host = _host_from_url(url)
    if not host:
        return "unknown"
    if any(host == official or host.endswith(f".{official}") for official in OFFICIAL_SOURCE_HOSTS):
        return "official"
    if any(host == intermediary or host.endswith(f".{intermediary}") for intermediary in INTERMEDIARY_SOURCE_HOSTS):
        return "intermediary"
    return "unknown"


def _source_rank(source_type: str) -> int:
    return {"official": 0, "unknown": 1, "intermediary": 2}.get(source_type, 1)


def rank_search_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[tuple[int, str, int, dict[str, Any]]] = []
    for index, item in enumerate(results):
        enriched = dict(item)
        host = _host_from_url(str(item.get("url") or ""))
        source_type = classify_source_type(str(item.get("url") or ""))
        enriched["host"] = host
        enriched["source_type"] = source_type
        ranked.append((_source_rank(source_type), host, index, enriched))
    return [value[3] for value in sorted(ranked, key=lambda value: value[:3])]


def _current_year_month() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}년 {now.month}월"


def normalize_search_query(agent_id: str, message: str, context: dict[str, Any] | None = None) -> str:
    cleaned = re.sub(
        r"^!(?:web|search|research|find|검증|lucy|marin|meiko|kasumi|reze|agent\s+\w+)\s+",
        "",
        str(message or "").strip(),
        flags=re.IGNORECASE,
    )
    cleaned = redact_text(cleaned, 320).strip() or "최신 자료 확인"
    lowered = cleaned.lower()
    when = _current_year_month() if any(term in lowered for term in ("이번 달", "이번달", "이달", "현재", "요즘")) else ""
    base = f"{when} {cleaned}".strip()
    if agent_id == "kasumi":
        terms = ["전국", "중소기업", "공고", "신청기간", "마감", "지원대상", "지원내용"]
        if "디자인" in cleaned or "design" in lowered:
            terms.insert(2, "디자인")
            terms.insert(3, "디자인개발")
        if "지원사업" in cleaned or "공고" in cleaned or "후보" in cleaned:
            return " ".join(dict.fromkeys((base, *terms, "모집")).keys())
    scope_terms = {
        "meiko": "공식 공고 자격요건 마감 제출서류 지원금",
        "marin": "콘텐츠 사례 레퍼런스 캠페인 표현",
        "lucy": "공개 표현 브랜드 커뮤니케이션 최신 사례 리스크",
        "reze": "시장 경쟁사 브랜드 전략 트렌드",
    }
    return f"{base} {scope_terms.get(agent_id, '')}".strip()


def extract_deadline(text: str) -> str:
    source = str(text or "")
    for pattern in DEADLINE_PATTERNS:
        match = pattern.search(source)
        if not match:
            continue
        groups = match.groups()
        if groups[-1].upper().startswith("D-"):
            return groups[-1].upper()
        year, month, day = groups[-3], groups[-2], groups[-1]
        return f"{int(year):04d}년 {int(month)}월 {int(day)}일"
    return "확인 필요"


def classify_candidate_status(text: str) -> str:
    source = str(text or "")
    if any(keyword in source for keyword in RESULT_GUIDE_KEYWORDS):
        return "선정결과/결과안내"
    if "마감" in source:
        return "마감 추정"
    if any(keyword in source for keyword in ("모집", "신청", "접수", "공고")):
        return "모집중 추정"
    return "확인 필요"


def _first_matching_sentence(text: str, keywords: tuple[str, ...]) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    for sentence in re.split(r"(?<=[.!?。])\s+|[|\n]", compact):
        if any(keyword in sentence for keyword in keywords):
            return redact_text(sentence, 220)
    return "확인 필요"


def build_candidate_cards(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for item in rank_search_results(results)[:5]:
        title = redact_text(str(item.get("title") or "후보명 확인 필요"), 240)
        summary = str(item.get("snippet") or item.get("summary") or "")
        host = str(item.get("host") or _host_from_url(str(item.get("url") or "")) or "확인 필요")
        combined = f"{title} {summary}"
        cards.append(
            {
                "candidate_name": title,
                "institution": redact_text(str(item.get("institution") or item.get("source") or host), 160) or host,
                "region": _first_matching_sentence(combined, ("전국", "서울", "부산", "인천", "경기", "경상북도", "금천구")),
                "deadline": extract_deadline(combined),
                "eligibility": _first_matching_sentence(combined, ("지원대상", "모집대상", "신청대상", "자격", "중소기업", "기업")),
                "support_details": _first_matching_sentence(combined, ("지원내용", "지원금", "디자인개발", "BI", "CI", "패키지", "UX", "UI")),
                "required_materials": _first_matching_sentence(combined, ("필요자료", "제출서류", "신청서", "사업계획서")),
                "url": str(item.get("url") or "")[:800] or "확인 필요",
                "source_type": str(item.get("source_type") or classify_source_type(str(item.get("url") or ""))),
                "source_type": str(item.get("source_type") or classify_source_type(str(item.get("url") or ""))),
                "current_status": classify_candidate_status(combined),
                "risk": "최종 신청 전 원문 공고 검증 필요",
                "needs_verification": "자격, 마감, 지원금, 제출자료",
            }
        )
    return cards


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
    terms = GENERIC_TERMS + KOREAN_GENERIC_TERMS + AGENT_TERMS.get(selected_agent, ()) + KOREAN_AGENT_TERMS.get(selected_agent, ())
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


def build_agent_search_queries(agent_id: str, message: str, context: dict[str, Any] | None = None) -> list[str]:
    normalized = normalize_search_query(agent_id, message, context)
    year = datetime.now(timezone.utc).year
    queries = [normalized, f"{normalized} {year}".strip()]
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
    for item in rank_search_results(results):
        normalized.append(
            {
                "title": redact_text(str(item.get("title") or "제목 확인 필요"), 240),
                "source": redact_text(str(item.get("institution") or item.get("source") or "출처 확인 필요"), 160),
                "url": str(item.get("url") or "")[:800] or "확인 필요",
                "source_type": str(item.get("source_type") or classify_source_type(str(item.get("url") or ""))),
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
                f"   source_type: {item['source_type']}",
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
    if agent_id == "kasumi":
        cards = build_candidate_cards(results)
        lines.extend(["", "지원사업 후보:"])
        for index, card in enumerate(cards, start=1):
            lines.extend(
                [
                    f"{index}. 후보명: {card['candidate_name']}",
                    f"   기관: {card['institution']}",
                    f"   지역: {card['region']}",
                    f"   마감: {card['deadline']}",
                    f"   지원대상: {card['eligibility']}",
                    f"   지원내용: {card['support_details']}",
                    f"   필요자료: {card['required_materials']}",
                    f"   URL: {card['url']}",
                    f"   출처유형: {card['source_type']}",
                    f"   현재상태: {card['current_status']}",
                    f"   리스크: {card['risk']}",
                    f"   확인 필요: {card['needs_verification']}",
                    "",
                ]
            )
        return "\n".join(lines)[:6000]
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
    ranked_results = rank_search_results(list(search.get("results") or []))
    search = {**search, "results": ranked_results}
    candidate_cards = build_candidate_cards(ranked_results) if agent_id == "kasumi" else []
    official_result_count = sum(1 for item in ranked_results if item.get("source_type") == "official")
    intermediary_result_count = sum(1 for item in ranked_results if item.get("source_type") == "intermediary")
    success = bool(search.get("search_succeeded")) and bool(ranked_results)
    report_text = (
        format_agent_web_reference_block(agent_id, ranked_results, queries[0])
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
                "summary": f"{agent_id} web reference {len(ranked_results)}건",
                "content": report_text,
                "source_urls_present": any(item.get("url") for item in ranked_results),
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
        "result_count": len(ranked_results),
        "original_query": redact_text(str(message or ""), 320),
        "normalized_search_query": queries[0],
        "official_result_count": official_result_count,
        "intermediary_result_count": intermediary_result_count,
        "candidate_count": len(candidate_cards) if agent_id == "kasumi" else len(ranked_results),
        "candidate_extraction_succeeded": success and (agent_id != "kasumi" or bool(candidate_cards)),
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

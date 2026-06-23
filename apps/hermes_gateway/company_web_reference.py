"""Role-scoped, manually gated read-only web reference for company agents."""

from __future__ import annotations

import os
import re
import socket
import html
import urllib.error
import urllib.parse
import urllib.request
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
OfficialFetcher = Callable[[str], dict[str, Any]]
AGENT_COMMAND_WEB_INTENT_TERMS = (
    "찾아줘",
    "검색",
    "조사",
    "리서치",
    "후보",
    "공고",
    "지원사업",
    "마감",
    "최신",
    "현재",
    "요즘",
    "이번 달",
    "이번달",
    "검증",
    "확인",
    "레퍼런스",
    "reference",
    "web",
    "search",
    "research",
    "trend",
    "market",
)

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
HTML_REMOVE_RE = re.compile(
    r"<(script|style|noscript|nav|footer|header)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
AD_BLOCK_RE = re.compile(
    r"<[^>]*(?:class|id)=['\"][^'\"]*(?:advertisement|advert|banner|popup)[^'\"]*['\"][^>]*>.*?</[^>]+>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
SECTION_PATTERNS = {
    "application_period": ("신청기간", "접수기간", "모집기간", "공고기간"),
    "eligibility": ("지원대상", "신청대상", "모집대상", "지원자격", "신청자격", "대상기업", "참여기업", "중소기업", "소상공인"),
    "support_content": ("지원내용", "지원규모", "지원금", "지원한도", "사업비", "디자인개발", "제품디자인", "시각디자인", "브랜드", "BI", "CI", "패키지", "UX", "UI"),
    "support_scale": ("지원금", "지원규모", "지원한도", "총사업비", "지원비율"),
    "self_payment": ("자부담", "기업부담금", "부담금", "민간부담", "매칭", "현금부담", "총사업비"),
    "required_documents": ("제출서류", "신청서", "사업계획서", "구비서류", "첨부서류", "증빙서류", "사업자등록증", "개인정보", "동의서"),
    "application_method": ("신청방법", "접수방법", "온라인 접수", "이메일 접수", "방문 접수", "우편 접수", "기업마당", "홈페이지", "신청서 제출"),
    "contact": ("문의처", "문의", "담당자", "전화", "이메일"),
    "host_institution": ("주관기관", "수행기관", "소관부처", "기관명"),
    "region": ("전국", "서울", "부산", "인천", "경기", "경상북도", "금천구"),
}


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


def cleanup_html_to_text(raw_html: str) -> str:
    cleaned = HTML_REMOVE_RE.sub(" ", str(raw_html or ""))
    cleaned = AD_BLOCK_RE.sub(" ", cleaned)
    text = html.unescape(TAG_RE.sub(" ", cleaned))
    return re.sub(r"\s+", " ", text).strip()


def fetch_official_source_text(url: str, opener: Any | None = None) -> dict[str, Any]:
    source_type = classify_source_type(url)
    if source_type != "official":
        return {
            "fetch_attempted": False,
            "fetch_succeeded": False,
            "failure_reason": "non_official_source",
            "source_type": source_type,
            "text": "",
            "read_only": True,
            "external_execution": False,
            "rag_called": False,
            "embedding_called": False,
            "vector_index_created": False,
            "api_key_value_logged": False,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    request = urllib.request.Request(url, headers={"User-Agent": "STOXL-Hermes-Reference/0.7B"}, method="GET")
    try:
        with (opener or urllib.request.urlopen)(request, timeout=15) as response:
            raw = response.read(300_000).decode("utf-8", errors="replace")
    except (TimeoutError, socket.timeout):
        reason = "timeout"
        raw = ""
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        reason = "provider_exception"
        raw = ""
    else:
        reason = ""
    text = cleanup_html_to_text(raw) if raw else ""
    return {
        "fetch_attempted": True,
        "fetch_succeeded": bool(text),
        "failure_reason": reason or ("" if text else "empty_body"),
        "source_type": source_type,
        "text": redact_text(text, 10_000),
        "read_only": True,
        "external_execution": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _field_sentence(text: str, field: str) -> str:
    return _first_matching_sentence(text, SECTION_PATTERNS[field])


def extract_application_period(text: str) -> str:
    source = str(text or "")
    for pattern in DEADLINE_PATTERNS[:4]:
        match = pattern.search(source)
        if not match:
            continue
        groups = match.groups()
        if len(groups) >= 6:
            return f"{int(groups[0]):04d}년 {int(groups[1])}월 {int(groups[2])}일 ~ {int(groups[3]):04d}년 {int(groups[4])}월 {int(groups[5])}일"
        year, month, day = groups[-3], groups[-2], groups[-1]
        return f"확인 필요 ~ {int(year):04d}년 {int(month)}월 {int(day)}일"
    return "확인 필요"


def _deadline_date_tuple(deadline: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", str(deadline or ""))
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def classify_program_status(text: str, source_type: str = "unknown", deadline: str = "확인 필요") -> str:
    if source_type == "intermediary":
        return "참고용 비공식"
    source = str(text or "")
    if any(keyword in source for keyword in RESULT_GUIDE_KEYWORDS + ("평가 결과", "선정 공고")):
        return "선정결과/결과안내"
    deadline_tuple = _deadline_date_tuple(deadline)
    if deadline_tuple:
        now = datetime.now(timezone.utc)
        if deadline_tuple < (now.year, now.month, now.day):
            return "마감 추정"
        return "모집중 추정"
    if any(keyword in source for keyword in ("예정", "공고예정")):
        return "예정/공고전"
    if any(keyword in source for keyword in ("모집", "신청", "접수", "공고")):
        return "모집중 추정"
    return "확인 필요"


def _confidence_label(score: float, status: str) -> str:
    if status == "선정결과/결과안내":
        return "낮음"
    if score >= 0.8:
        return "높음"
    if score >= 0.45:
        return "중간"
    return "낮음"


def parse_support_program_details(result: dict[str, Any], source_text: str = "") -> dict[str, Any]:
    title = redact_text(str(result.get("title") or "후보명 확인 필요"), 240)
    url = str(result.get("url") or "")[:800] or "확인 필요"
    source_type = str(result.get("source_type") or classify_source_type(url))
    summary = str(result.get("snippet") or result.get("summary") or "")
    text = f"{title} {summary} {source_text}".strip()
    application_period = extract_application_period(text)
    deadline = extract_deadline(text)
    status = classify_program_status(text, source_type, deadline)
    official_verified = source_type == "official" and bool(source_text)
    extracted_fields = [
        _field_sentence(text, "eligibility"),
        _field_sentence(text, "support_content"),
        _field_sentence(text, "support_scale"),
        _field_sentence(text, "self_payment"),
        _field_sentence(text, "required_documents"),
        _field_sentence(text, "application_method"),
    ]
    non_empty_count = sum(1 for value in extracted_fields if value != "확인 필요")
    if source_type == "intermediary":
        confidence_score = 0.2
    elif official_verified:
        confidence_score = min(0.95, 0.45 + non_empty_count * 0.1)
    else:
        confidence_score = 0.5
    confidence = _confidence_label(confidence_score, status)
    if status == "선정결과/결과안내":
        risk = "신규 신청 공고가 아닐 가능성 높음"
    elif source_type == "intermediary":
        risk = "비공식 요약 기준으로 공식 원문 확인 필요"
    else:
        risk = "최종 신청 전 원문 공고 검증 필요"
    return {
        "candidate_name": title,
        "title": title,
        "institution": redact_text(str(result.get("institution") or result.get("source") or _host_from_url(url) or "확인 필요"), 160),
        "host_institution": _field_sentence(text, "host_institution"),
        "region": _field_sentence(text, "region"),
        "application_period": application_period,
        "deadline": deadline,
        "eligibility": extracted_fields[0],
        "support_details": extracted_fields[1],
        "support_content": extracted_fields[1],
        "support_scale": extracted_fields[2],
        "self_payment": extracted_fields[3],
        "required_materials": extracted_fields[4],
        "required_documents": extracted_fields[4],
        "application_method": extracted_fields[5],
        "contact": _field_sentence(text, "contact"),
        "url": url,
        "source_type": source_type,
        "source_verified": "원문확인 성공" if official_verified else ("원문확인 실패" if source_type == "official" else "비공식 참고"),
        "official_source_fetched": official_verified,
        "current_status": status,
        "confidence": confidence,
        "source_confidence_score": round(confidence_score, 2),
        "risk": risk,
        "needs_verification": "자격, 마감, 자부담, 제출서류, STOXL 업종 적합성",
    }


def extract_official_source_details(
    results: list[dict[str, Any]],
    official_fetcher: OfficialFetcher | None = None,
    opener: Any | None = None,
) -> dict[str, Any]:
    ranked = rank_search_results(results)
    official_count = sum(1 for item in ranked if item.get("source_type") == "official")
    details: list[dict[str, Any]] = []
    attempted = 0
    success_count = 0
    failed_count = 0
    fetcher = official_fetcher or (lambda url: fetch_official_source_text(url, opener=opener))
    seen_keys: set[tuple[str, str, str]] = set()
    for item in ranked:
        title = str(item.get("title") or "")
        url = str(item.get("url") or "")
        key = (title.casefold(), _host_from_url(url), url)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        source_text = ""
        if item.get("source_type") == "official":
            attempted += 1
            fetched = fetcher(url)
            if fetched.get("fetch_succeeded"):
                success_count += 1
                source_text = str(fetched.get("text") or "")
            else:
                failed_count += 1
        detail = parse_support_program_details(item, source_text)
        if item.get("source_type") == "intermediary" and official_count > 0:
            continue
        details.append(detail)
        if len(details) >= 5:
            break
    verification_block = build_source_verification_block(details, official_count, success_count)
    return {
        "official_extract_attempted": attempted > 0,
        "official_extract_attempt_count": attempted,
        "official_extract_success_count": success_count,
        "official_extract_failed_count": failed_count,
        "candidate_count": len(details),
        "candidate_extraction_succeeded": bool(details),
        "verification_block_written": bool(verification_block),
        "ready_for_meiko_verification": bool(details),
        "ready_for_rag_phase": bool(details),
        "candidates": details,
        "verification_block": verification_block,
        "read_only": True,
        "external_execution": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_source_verification_block(candidates: list[dict[str, Any]], official_source_count: int, official_extract_success_count: int) -> str:
    lines = [
        "[SUPPORT_PROGRAM_VERIFICATION]",
        f"candidate_count: {len(candidates)}",
        f"official_source_count: {official_source_count}",
        f"extracted_from_official_pages: {official_extract_success_count}",
        "requires_manual_confirmation: true",
        "",
    ]
    for index, card in enumerate(candidates[:5], start=1):
        lines.extend(
            [
                f"Candidate {index}:",
                f"- title: {card.get('title', '확인 필요')}",
                f"- source_type: {card.get('source_type', 'unknown')}",
                f"- original_url: {card.get('url', '확인 필요')}",
                f"- deadline: {card.get('deadline', '확인 필요')}",
                f"- eligibility: {card.get('eligibility', '확인 필요')}",
                f"- support_content: {card.get('support_content', '확인 필요')}",
                f"- required_documents: {card.get('required_documents', '확인 필요')}",
                f"- self_payment: {card.get('self_payment', '확인 필요')}",
                f"- confidence: {card.get('confidence', '낮음')}",
                f"- status: {card.get('current_status', '확인 필요')}",
                "- meiko_checkpoints:",
                "  - STOXL 소재지/업종 적합성",
                "  - 중소기업/디자인 전문기업 해당 여부",
                "  - 자부담 존재 여부",
                "  - 마감일까지 준비 가능 여부",
                "  - 제출서류 준비 가능 여부",
                "",
            ]
        )
    lines.append("[/SUPPORT_PROGRAM_VERIFICATION]")
    return "\n".join(lines)


def build_candidate_cards(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for item in rank_search_results(results)[:5]:
        if item.get("source_verified") and item.get("application_period"):
            details = dict(item)
        else:
            details = parse_support_program_details(item, str(item.get("official_text") or ""))
        cards.append({key: redact_text(value, 600) if isinstance(value, str) else value for key, value in details.items()})
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


def detect_agent_command_web_intent(agent_id: str, message: str, context: dict[str, Any] | None = None) -> bool:
    selected_agent = str(agent_id or "").strip().lower()
    if selected_agent not in ALLOWED_AGENTS:
        return False
    command = str((context or {}).get("command") or "").strip().lower()
    if command not in ALLOWED_AGENTS and command != "agent":
        return False
    lowered = str(message or "").strip().lower()
    if not lowered.startswith(f"!{selected_agent}") and command != "agent":
        return False
    return any(term.lower() in lowered for term in AGENT_COMMAND_WEB_INTENT_TERMS) or detect_web_reference_intent(selected_agent, message, context)


def build_web_reference_bridge_failure_response(agent_id: str, reason: str) -> dict[str, Any]:
    safe_reason = str(reason or "web_reference_runtime_exception").strip() or "web_reference_runtime_exception"
    return {
        "report_type": "company_agent_web_reference_bridge_failure",
        "response_type": "company_agent_response",
        "agent_id": agent_id,
        "reply_text_source": "web_reference_bridge_failure",
        "content": (
            f"[{str(agent_id or 'hermes').upper()}_STOXL]\n"
            "웹 참조 작업을 시작했지만 완료하지 못했습니다.\n"
            f"reason: {safe_reason}\n"
            "다시 시도하거나 `!web <검색어>`로 실행해 주세요."
        ),
        "web_reference_bridge_failed": True,
        "web_reference_failure_reason": safe_reason,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


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
                    f"   신청기간: {card['application_period']}",
                    f"   마감일: {card['deadline']}",
                    f"   지원대상: {card['eligibility']}",
                    f"   지원내용: {card['support_details']}",
                    f"   지원금/지원규모: {card['support_scale']}",
                    f"   자부담: {card['self_payment']}",
                    f"   필요자료: {card['required_materials']}",
                    f"   신청방법: {card['application_method']}",
                    f"   문의처: {card['contact']}",
                    f"   URL: {card['url']}",
                    f"   출처유형: {card['source_type']}",
                    f"   원문확인: {card['source_verified']}",
                    f"   현재상태: {card['current_status']}",
                    f"   신뢰도: {card['confidence']}",
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
    official_fetcher: OfficialFetcher | None = None,
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
    official_extraction = (
        extract_official_source_details(ranked_results, official_fetcher=official_fetcher)
        if success and agent_id == "kasumi"
        else {
            "official_extract_attempted": False,
            "official_extract_attempt_count": 0,
            "official_extract_success_count": 0,
            "official_extract_failed_count": 0,
            "candidate_count": len(candidate_cards) if agent_id == "kasumi" else len(ranked_results),
            "candidate_extraction_succeeded": success,
            "verification_block_written": False,
            "ready_for_meiko_verification": False,
            "ready_for_rag_phase": False,
            "candidates": candidate_cards,
            "verification_block": "",
        }
    )
    if agent_id == "kasumi":
        candidate_cards = list(official_extraction.get("candidates") or candidate_cards)
    report_text = (
        format_agent_web_reference_block(agent_id, candidate_cards if agent_id == "kasumi" else ranked_results, queries[0])
        if success
        else format_agent_web_failure(agent_id, str(search.get("failure_reason") or "no_results"))
    )
    if success and agent_id == "kasumi" and official_extraction.get("verification_block"):
        report_text = f"{report_text}\n\n{official_extraction['verification_block']}"
    memory = {"record_written": False}
    if success:
        memory = append_memory_record(
            "recent_item",
            {
                "item_type": "web_reference",
                "type": "web_reference_support_program_candidates" if agent_id == "kasumi" else "web_reference",
                "agent": agent_id,
                "title": f"{redact_text(queries[0], 100)} web reference",
                "summary": f"{agent_id} web reference {len(ranked_results)}건",
                "content": report_text,
                "original_query": redact_text(str(message or ""), 320),
                "normalized_search_query": queries[0],
                "candidate_count": len(candidate_cards) if agent_id == "kasumi" else len(ranked_results),
                "official_source_count": official_result_count,
                "official_extract_success_count": int(official_extraction.get("official_extract_success_count") or 0),
                "candidates": candidate_cards[:5],
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
        "official_extract_attempted": bool(official_extraction.get("official_extract_attempted")),
        "official_extract_success_count": int(official_extraction.get("official_extract_success_count") or 0),
        "official_extract_failed_count": int(official_extraction.get("official_extract_failed_count") or 0),
        "candidate_extraction_succeeded": bool(official_extraction.get("candidate_extraction_succeeded")) if agent_id == "kasumi" else success,
        "verification_block_written": bool(official_extraction.get("verification_block_written")),
        "ready_for_meiko_verification": bool(official_extraction.get("ready_for_meiko_verification")),
        "ready_for_rag_phase": bool(official_extraction.get("ready_for_rag_phase")),
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

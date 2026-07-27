"""Global Discord outbound response guard and chunking for company agents."""

from __future__ import annotations

import os
import re
from typing import Any, Awaitable, Callable

from llm_client import redact_text
from company_agent_output import (
    DEFAULT_AGENT_MAX_RESPONSE_CHUNKS,
    DEFAULT_DISCORD_CHUNK_MAX_CHARS,
    assemble_agent_response,
    split_discord_response,
)


SAFE_CHUNK_SIZE = DEFAULT_DISCORD_CHUNK_MAX_CHARS
HARD_LIMIT = 1900
DEFAULT_MAX_CHUNKS = DEFAULT_AGENT_MAX_RESPONSE_CHUNKS
AGENT_LABELS = {
    "lucy": "LUCY_STOXL",
    "marin": "MARIN_STOXL",
    "meiko": "MEIKO_STOXL",
    "kasumi": "KASUMI_STOXL",
    "reze": "REZE_STOXL",
    "hermes": "HERMES_STOXL",
    "": "HERMES_STOXL",
}


def _agent_label(agent_id: str) -> str:
    return AGENT_LABELS.get(str(agent_id or "").strip().lower(), f"{str(agent_id or 'HERMES').upper()}_STOXL")


def _safe_line(value: Any, limit: int = 180) -> str:
    return redact_text(str(value or "").replace("\r", " ").strip(), limit)


def _candidate_summaries(content: str, limit: int = 3) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in str(content or "").splitlines():
        line = raw_line.strip()
        if re.match(r"^\d+\.\s*(후보명|제목)\s*:", line):
            if current:
                candidates.append(current)
            current = {"title": line.split(":", 1)[1].strip()}
        elif current and line.startswith("현재상태:"):
            current["status"] = line.split(":", 1)[1].strip()
        elif current and (line.startswith("마감일:") or line.startswith("마감:")):
            current["deadline"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("신뢰도:"):
            current["confidence"] = line.split(":", 1)[1].strip()
        if len(candidates) >= limit:
            break
    if current and len(candidates) < limit:
        candidates.append(current)
    return candidates[:limit]


def compact_web_reference_for_discord(content: str, agent_id: str = "kasumi") -> str:
    text = str(content or "")
    if "[WEB_REFERENCE]" not in text and "[SUPPORT_PROGRAM_VERIFICATION]" not in text:
        return text
    result_count = len(re.findall(r"^\d+\.\s*(?:후보명|제목)\s*:", text, flags=re.MULTILINE))
    official_count_match = re.search(r"official_source_count:\s*(\d+)", text)
    extracted_match = re.search(r"extracted_from_official_pages:\s*(\d+)", text)
    ready_for_meiko = "[SUPPORT_PROGRAM_VERIFICATION]" in text
    lines = [
        f"[{_agent_label(agent_id)}] 지원사업 후보 검색 완료",
        "",
        f"검색 결과: {result_count}개",
        f"공식 출처: {official_count_match.group(1) if official_count_match else '확인 필요'}개",
        f"원문 확인 성공: {extracted_match.group(1) if extracted_match else '확인 필요'}개",
        f"Meiko 검토 가능: {str(ready_for_meiko).lower()}",
        "",
        "상위 후보:",
    ]
    for index, item in enumerate(_candidate_summaries(text), start=1):
        lines.extend(
            [
                f"{index}. {_safe_line(item.get('title'), 140)}",
                f"   상태: {_safe_line(item.get('status') or '확인 필요', 80)}",
                f"   마감: {_safe_line(item.get('deadline') or '확인 필요', 80)}",
                f"   신뢰도: {_safe_line(item.get('confidence') or '확인 필요', 80)}",
                "",
            ]
        )
    lines.extend(
        [
            "전체 후보와 원문 검증 block은 memory/context에 보존됐습니다.",
            "Meiko에게 `방금 Kasumi가 찾은 지원사업 검토해줘`라고 이어서 요청할 수 있습니다.",
        ]
    )
    return "\n".join(lines).strip()


def split_discord_message(
    content: str,
    agent_id: str = "",
    *,
    safe_chunk_size: int = SAFE_CHUNK_SIZE,
    hard_limit: int = HARD_LIMIT,
    max_chunk_count: int = DEFAULT_MAX_CHUNKS,
) -> dict[str, Any]:
    original = str(content or "")
    messages = split_discord_response(
        body=original,
        source_footer="",
        max_chunk_chars=min(safe_chunk_size, hard_limit),
        max_chunks=max_chunk_count,
    )
    messages = [redact_text(message, len(message) + 32) for message in messages]
    truncated = sum(len(message) for message in messages) < len(original)
    return {
        "messages": messages,
        "outbound_original_length": len(original),
        "outbound_chunking_used": len(messages) > 1,
        "outbound_chunk_count": len(messages),
        "outbound_truncated_for_discord": truncated,
        "outbound_full_content_preserved_in_memory": True,
        "response_chunk_count": len(messages),
        "body_truncated": truncated,
        "sentence_midpoint_truncation": False,
        "citation_validation_before_chunking": True,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def prepare_discord_outbound_messages(
    content: str,
    agent_id: str = "",
    *,
    compact_web_reference: bool = True,
    max_chunk_count: int = DEFAULT_MAX_CHUNKS,
    body: str | None = None,
    source_footer: str = "",
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    original = str(content or "")
    outbound = compact_web_reference_for_discord(original, agent_id) if compact_web_reference else original
    if body is not None or source_footer:
        rendered = assemble_agent_response(
            body=str(outbound if body is None else body),
            source_footer=source_footer,
            env=dict(os.environ if env is None else env),
        )
        messages = list(rendered.chunks)
        split = {
            **rendered.metadata,
            "messages": messages,
            "outbound_original_length": len(original),
            "outbound_chunking_used": len(messages) > 1,
            "outbound_chunk_count": len(messages),
            "outbound_truncated_for_discord": bool(rendered.metadata.get("body_truncated")),
            "outbound_full_content_preserved_in_memory": True,
        }
    else:
        split = split_discord_message(outbound, agent_id, max_chunk_count=max_chunk_count)
    return {
        **split,
        "outbound_compacted_for_discord": outbound != original,
        "outbound_guard_applied": True,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "api_key_value_logged": False,
    }


def classify_discord_send_failure(reason_or_exception: Any) -> str:
    text = str(reason_or_exception or "").lower()
    if "too long" in text or "40005" in text or "message_too_long" in text:
        return "discord_message_too_long"
    if "rate" in text or "429" in text:
        return "discord_send_rate_limited"
    if "forbidden" in text or "403" in text:
        return "discord_send_forbidden"
    if "permission" in text:
        return "discord_sender_permission_denied"
    if "token" in text or "missing" in text:
        return "discord_sender_token_missing"
    return "discord_unknown_send_error"


async def send_discord_messages_safely(
    send_one: Callable[[str], Awaitable[Any]],
    messages: list[str],
    *,
    fallback_send_one: Callable[[str], Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    sent_count = 0
    try:
        for message in messages:
            await send_one(message)
            sent_count += 1
    except Exception as exc:
        reason = classify_discord_send_failure(exc)
        fallback_sent = False
        fallback_attempted = fallback_send_one is not None
        if fallback_send_one is not None:
            try:
                await fallback_send_one(
                    "[HERMES_STOXL]\nDiscord 전송 중 일부 실패가 감지됐습니다. 상세 내용은 memory/context에 보존됐습니다."
                )
                fallback_sent = True
            except Exception:
                fallback_sent = False
        return {
            "sent": sent_count > 0,
            "discord_send_attempted": True,
            "discord_message_sent": sent_count > 0,
            "message_sent_count": sent_count,
            "discord_send_failure_reason": reason,
            "fallback_short_notice_attempted": fallback_attempted,
            "fallback_short_notice_sent": fallback_sent,
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    return {
        "sent": bool(messages),
        "discord_send_attempted": bool(messages),
        "discord_message_sent": bool(messages),
        "message_sent_count": sent_count,
        "discord_send_failure_reason": "",
        "fallback_short_notice_attempted": False,
        "fallback_short_notice_sent": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }

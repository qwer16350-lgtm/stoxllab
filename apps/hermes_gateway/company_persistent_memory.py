"""JSONL work memory for STOXL company agents. This is not a RAG backend."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from llm_client import redact_text


SCHEMA_VERSION = 1
RECORD_TYPES = ("handoff", "approval", "decision", "recent_item")
FILE_NAMES = {
    "handoff": "handoffs.jsonl",
    "approval": "approvals.jsonl",
    "decision": "decisions.jsonl",
    "recent_item": "recent_items.jsonl",
}
DEFAULT_MEMORY_DIR = Path(__file__).resolve().parent / "local" / "company_memory"
DISCORD_WEBHOOK_RE = re.compile(r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\S+", re.IGNORECASE)
SENSITIVE_KEY_RE = re.compile(r"token|api.?key|password|secret|webhook.?url|discord.?id|message.?id|user.?id|channel.?id|\.env", re.IGNORECASE)
ALLOWED_FIELDS = {
    "source_agent",
    "target_agent",
    "agent",
    "source_channel",
    "target_channel",
    "channel",
    "title",
    "summary",
    "content",
    "next_action",
    "recommendation",
    "risk",
    "decision",
    "status",
    "external_execution_requested",
    "external_execution_performed",
    "item_type",
}


def _memory_dir(memory_dir: str | Path | None = None) -> Path:
    configured = memory_dir or os.environ.get("HERMES_COMPANY_MEMORY_DIR") or DEFAULT_MEMORY_DIR
    return Path(configured)


def _safe_text(value: Any, max_chars: int = 1800) -> str:
    safe = redact_text(str(value or ""), max_chars)
    return DISCORD_WEBHOOK_RE.sub("[REDACTED_WEBHOOK_URL]", safe)[:max(max_chars, 0)]


def ensure_memory_dir(memory_dir: str | Path | None = None) -> Path:
    selected = _memory_dir(memory_dir)
    try:
        selected.mkdir(parents=True, exist_ok=True)
        for file_name in FILE_NAMES.values():
            (selected / file_name).touch(exist_ok=True)
    except OSError:
        pass
    return selected


def redact_memory_record(record: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in dict(record or {}).items():
        normalized_key = str(key)
        if normalized_key not in ALLOWED_FIELDS or SENSITIVE_KEY_RE.search(normalized_key):
            continue
        if isinstance(value, bool):
            safe[normalized_key] = value
        elif value is not None:
            max_chars = 1800 if normalized_key == "content" else 600
            safe[normalized_key] = _safe_text(value, max_chars)
    safe["external_execution_performed"] = False
    safe["raw_discord_ids_logged"] = False
    safe["secret_values_logged"] = False
    return safe


def _record_payload(record_type: str, record: dict[str, Any]) -> dict[str, Any]:
    safe = redact_memory_record(record)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **safe,
    }


def _append_line(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def append_memory_record(
    record_type: str,
    record: dict[str, Any],
    memory_dir: str | Path | None = None,
) -> dict[str, Any]:
    selected_type = str(record_type or "").strip().lower()
    if selected_type not in RECORD_TYPES:
        return {
            "record_written": False,
            "record_type": selected_type,
            "memory_backend": "jsonl",
            "warning_code": "unsupported_memory_record_type",
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    directory = ensure_memory_dir(memory_dir)
    payload = _record_payload(selected_type, record)
    recent_written = selected_type == "recent_item"
    try:
        _append_line(directory / FILE_NAMES[selected_type], payload)
        recent_written = True
        if selected_type != "recent_item":
            recent = _record_payload(
                "recent_item",
                {
                    **record,
                    "item_type": selected_type,
                    "content": str(record.get("summary") or record.get("content") or ""),
                },
            )
            _append_line(directory / FILE_NAMES["recent_item"], recent)
    except OSError:
        return {
            "record_written": False,
            "record_type": selected_type,
            "memory_backend": "jsonl",
            "warning_code": "memory_write_failed",
            "raw_discord_ids_logged": False,
            "secret_values_logged": False,
        }
    return {
        "record_written": True,
        "record_type": selected_type,
        "memory_backend": "jsonl",
        "recent_item_written": recent_written,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def _read_records(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
    return records


def load_recent_records(
    record_type: str,
    limit: int = 10,
    memory_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    selected_type = str(record_type or "").strip().lower()
    if selected_type not in RECORD_TYPES:
        return []
    path = ensure_memory_dir(memory_dir) / FILE_NAMES[selected_type]
    selected_limit = max(0, min(int(limit), 100))
    if selected_limit == 0:
        return []
    records = _read_records(path)
    return [redact_memory_record(record) | {
        "schema_version": SCHEMA_VERSION,
        "record_type": str(record.get("record_type") or selected_type),
        "created_at": _safe_text(record.get("created_at"), 80),
    } for record in reversed(records[-selected_limit:])]


def search_memory_records(
    keyword: str,
    record_types: Iterable[str] | None = None,
    limit: int = 10,
    memory_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    query = _safe_text(keyword, 200).strip().casefold()
    if not query:
        return []
    selected_types = tuple(record_types or RECORD_TYPES)
    matches: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for record_type in selected_types:
        for record in load_recent_records(record_type, 100, memory_dir):
            haystack = " ".join(str(record.get(key, "")) for key in ALLOWED_FIELDS).casefold()
            if query in haystack:
                identity = (
                    str(record.get("item_type") or record.get("record_type") or ""),
                    str(record.get("title") or ""),
                    str(record.get("summary") or ""),
                )
                if identity in seen:
                    continue
                seen.add(identity)
                matches.append(record)
    matches.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return matches[: max(0, min(int(limit), 100))]


def build_memory_summary(records: list[dict[str, Any]]) -> str:
    if not records:
        return "[MEMORY]\n저장된 관련 기록 없음"
    lines = ["[MEMORY]", f"results: {len(records)}", ""]
    for index, record in enumerate(records, start=1):
        record_type = str(record.get("item_type") or record.get("record_type") or "memory")
        lines.append(f"{index}. [{record_type}] {record.get('title') or '제목 없음'}")
        if record.get("source_agent") or record.get("target_agent"):
            lines.append(f"   source: {record.get('source_agent') or '-'} -> {record.get('target_agent') or '-'}")
        if record.get("agent"):
            lines.append(f"   agent: {record.get('agent')}")
        if record.get("summary"):
            lines.append(f"   summary: {_safe_text(record.get('summary'), 220)}")
        if record.get("decision"):
            lines.append(f"   decision: {_safe_text(record.get('decision'), 120)}")
        if record.get("next_action"):
            lines.append(f"   next: {_safe_text(record.get('next_action'), 180)}")
        lines.append(f"   status: {record.get('status') or '-'}")
        lines.append("")
    return "\n".join(lines).strip()[:1900]


def memory_dir_is_gitignored() -> bool:
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    try:
        text = gitignore.read_text(encoding="utf-8")
    except OSError:
        return False
    return "apps/hermes_gateway/local/" in text or "apps/hermes_gateway/local/*" in text


def build_company_agent_memory_report(memory_dir: str | Path | None = None) -> dict[str, Any]:
    directory = ensure_memory_dir(memory_dir)
    return {
        "report_type": "company_agent_memory_report",
        "persistent_memory_available": directory.exists(),
        "memory_backend": "jsonl",
        "memory_dir_configured": True,
        "memory_dir_gitignored": memory_dir_is_gitignored(),
        "record_types_supported": list(RECORD_TYPES),
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_memory_query_report(
    query: str,
    limit: int = 10,
    memory_dir: str | Path | None = None,
) -> dict[str, Any]:
    records = search_memory_records(query, limit=limit, memory_dir=memory_dir)
    return {
        "report_type": "company_agent_memory_query",
        "query": _safe_text(query, 200),
        "results_count": len(records),
        "records": [
            {
                "record_type": record.get("item_type") or record.get("record_type"),
                "title": record.get("title") or "제목 없음",
                "summary_present": bool(record.get("summary")),
                "content_preview_present": bool(record.get("content")),
            }
            for record in records
        ],
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }


def build_memory_command_response(command: str, argument: str = "") -> dict[str, Any]:
    normalized = str(command or "").strip().lower()
    scope = str(argument or "").strip().lower()
    if normalized == "recall":
        records = search_memory_records(scope, limit=10)
        summary = build_memory_summary(records)
        content = summary.replace("[MEMORY]", f"[MEMORY]\nquery: {_safe_text(scope, 200)}", 1)
    else:
        mapping = {
            "recent": "recent_item",
            "handoffs": "handoff",
            "approvals": "approval",
            "decisions": "decision",
        }
        selected_type = mapping.get(scope or "recent", "recent_item")
        records = load_recent_records(selected_type, 10 if selected_type == "recent_item" else 5)
        content = build_memory_summary(records)
    return {
        "response_type": "company_agent_memory_response",
        "reply_text_source": "persistent_memory",
        "content": content,
        "results_count": len(records),
        "discord_api_send_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_called": False,
        "vector_index_created": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
    }

"""Persistent audit artifacts for read-only live Discord events."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "phase30_audit_persistence"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+[a-z0-9._-]+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(value: str | None = None) -> str:
    return (value or utc_now())[:10].replace("-", "")


def redact_content_preview(text: str | None, max_chars: int = 120) -> str:
    if not text:
        return ""
    normalized = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", normalized)
    redacted = LONG_ID_RE.sub(lambda match: f"discord_id_redacted:{match.group(0)[-4:]}", redacted)
    return redacted[:max_chars]


def _route_from_workflow(workflow_role: str) -> str:
    mapping = {
        "marketing_intake": "marin",
        "junior_draft": "marin",
        "sns_content": "marin",
        "homepage_copy": "marin",
        "senior_review": "lucy",
        "operation_intake": "kasumi",
        "junior_research": "kasumi",
        "grant_competition": "kasumi",
        "deadline_management": "kasumi",
        "senior_operation_review": "meiko",
        "strategy_planning": "reze",
        "rag_summary": "reze",
        "new_business": "reze",
        "product_ideas": "reze",
        "final_approval": "decision_maker_review",
        "owner_meeting": "decision_maker_review",
    }
    return mapping.get(workflow_role or "", "unrouted")


def build_live_event_audit_record(visibility_event: dict[str, Any], content: str | None = None) -> dict[str, Any]:
    record = {
        "record_type": "live_event_audit_record",
        "version": VERSION,
        "created_at": visibility_event.get("created_at") or utc_now(),
        "event_id": visibility_event.get("event_id", ""),
        "event_type": visibility_event.get("event_type", "live_discord_message_create"),
        "decision": visibility_event.get("decision", ""),
        "reason": visibility_event.get("reason", ""),
        "guild_configured": bool(visibility_event.get("guild_configured")),
        "channel_mapped": bool(visibility_event.get("channel_mapped")),
        "channel_name": visibility_event.get("channel_name", ""),
        "workflow_role": visibility_event.get("workflow_role", ""),
        "agent_route_candidate": _route_from_workflow(visibility_event.get("workflow_role", "")),
        "author_id": visibility_event.get("author_id", ""),
        "author_is_bot": bool(visibility_event.get("author_is_bot")),
        "content_present": bool(visibility_event.get("content_present")),
        "content_length": int(visibility_event.get("content_length") or 0),
        "content_preview": redact_content_preview(content),
        "message_sent": False,
        "will_send": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "safety_assertions": {
            "raw_token_logged": False,
            "raw_discord_ids_logged": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
        },
    }
    assert_audit_record_safe(record)
    return record


def assert_audit_record_safe(record: dict[str, Any]) -> None:
    if record.get("message_sent") or record.get("will_send") or record.get("external_execution") or record.get("llm_called") or record.get("rag_called"):
        raise ValueError("Live event audit record has unsafe execution flags.")
    text = json.dumps(record, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text:
        raise ValueError("Live event audit record contains secret-like text.")
    if re.search(r"\b\d{15,25}\b", text):
        raise ValueError("Live event audit record contains raw Discord-like IDs.")


def get_live_event_audit_log_path(root: str | Path | None = None, created_at: str | None = None) -> Path:
    repo_root = Path(root or Path.cwd()).resolve()
    return repo_root / "logs" / "hermes_gateway" / "live_events" / f"readonly_events_{_date_stamp(created_at)}.jsonl"


def append_live_event_audit_record(record: dict[str, Any], root: str | Path | None = None) -> Path:
    assert_audit_record_safe(record)
    path = get_live_event_audit_log_path(root, record.get("created_at"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    build_daily_live_event_manifest(root=root, date=record.get("created_at"))
    return path


def get_daily_manifest_path(root: str | Path | None = None, date: str | None = None) -> Path:
    repo_root = Path(root or Path.cwd()).resolve()
    return repo_root / "logs" / "hermes_gateway" / "live_events" / "manifests" / f"readonly_manifest_{_date_stamp(date)}.json"


def build_daily_live_event_manifest(root: str | Path | None = None, date: str | None = None) -> dict[str, Any]:
    log_path = get_live_event_audit_log_path(root, date)
    records = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    decisions = Counter(item.get("decision", "unknown") for item in records)
    manifest = {
        "manifest_type": "live_event_daily_manifest",
        "version": VERSION,
        "created_at": utc_now(),
        "date": _date_stamp(date),
        "log_path": str(log_path),
        "record_count": len(records),
        "decision_counts": dict(sorted(decisions.items())),
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
        "safety_assertions": {
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
        },
    }
    path = get_daily_manifest_path(root, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_sample_visibility_event() -> dict[str, Any]:
    return {
        "created_at": "2026-06-13T00:00:00+00:00",
        "event_type": "live_discord_message_create",
        "decision": "accepted_mapped_channel",
        "reason": "accepted_mapped_channel",
        "guild_configured": True,
        "channel_mapped": True,
        "channel_name": "marketing-brief",
        "workflow_role": "marketing_intake",
        "author_is_bot": False,
        "author_id": "discord_id_redacted:0000",
        "content_present": True,
        "content_length": 74,
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
    }

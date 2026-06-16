"""Phase 40T redacted read-only capture writer.

The writer accepts only the Phase 40T redacted capture schema. It never writes
raw message content, raw Discord IDs, tokens, API keys, or approval phrases.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CAPTURE_SCHEMA_VERSION = "phase40t_redacted_readonly_capture_v1"
ALLOWED_EVENT_FIELDS = {
    "event_id_hash",
    "message_id_hash",
    "channel_scope",
    "author_kind",
    "is_self",
    "is_bot",
    "is_duplicate",
    "decision",
    "timestamp_iso",
}
FORBIDDEN_CAPTURE_FIELDS = {
    "raw_message_content",
    "content",
    "author_id",
    "channel_id",
    "guild_id",
    "discord_token",
    "api_key",
    "approval_phrase",
}
ALLOWED_CHANNEL_SCOPES = {"private_test", "public_blocked", "team_blocked", "unknown"}
ALLOWED_AUTHOR_KINDS = {"human", "self", "bot", "unknown"}
ALLOWED_DECISIONS = {"capture_only", "skip_self", "skip_bot", "skip_duplicate", "block_public_team"}
LOCAL_CAPTURE_ROOT = Path("apps/hermes_gateway/local/captures")
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)"
)
APPROVAL_RE = re.compile(r"I_APPROVE_[A-Z0-9_]+")


def _hash_value(value: Any) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_capture_root(root: str | Path | None = None) -> Path:
    base = Path(root) if root else Path.cwd()
    return (base / LOCAL_CAPTURE_ROOT).resolve()


def validate_capture_root(capture_root: str | Path | None, root: str | Path | None = None) -> tuple[bool, str, Path]:
    path = Path(capture_root) if capture_root else default_capture_root(root)
    if not path.is_absolute():
        path = (Path(root) if root else Path.cwd()) / path
    resolved = path.resolve()
    expected = default_capture_root(root)
    try:
        resolved.relative_to(expected)
    except ValueError:
        return False, "capture_root_not_local_ignored_path", resolved
    return True, "", resolved


def sanitize_capture_event(event: dict[str, Any]) -> dict[str, Any]:
    forbidden = FORBIDDEN_CAPTURE_FIELDS.intersection(event.keys())
    if forbidden:
        raise ValueError(f"Forbidden capture fields present: {sorted(forbidden)}")
    channel_scope = str(event.get("channel_scope", "unknown") or "unknown")
    author_kind = str(event.get("author_kind", "unknown") or "unknown")
    decision = str(event.get("decision", "capture_only") or "capture_only")
    if channel_scope not in ALLOWED_CHANNEL_SCOPES:
        channel_scope = "unknown"
    if author_kind not in ALLOWED_AUTHOR_KINDS:
        author_kind = "unknown"
    if decision not in ALLOWED_DECISIONS:
        decision = "capture_only"
    item = {
        "event_id_hash": str(event.get("event_id_hash") or _hash_value(event.get("event_id"))),
        "message_id_hash": str(event.get("message_id_hash") or _hash_value(event.get("message_id"))),
        "channel_scope": channel_scope,
        "author_kind": author_kind,
        "is_self": bool(event.get("is_self")),
        "is_bot": bool(event.get("is_bot")),
        "is_duplicate": bool(event.get("is_duplicate")),
        "decision": decision,
        "timestamp_iso": str(event.get("timestamp_iso") or _timestamp()),
    }
    _assert_no_sensitive_values(item)
    return item


def build_redacted_capture_payload(events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    safe_events = [sanitize_capture_event(event) for event in (events or [])]
    payload = {
        "capture_schema_version": CAPTURE_SCHEMA_VERSION,
        "events": safe_events,
        "safety": {
            "raw_content_included": False,
            "raw_discord_ids_included": False,
            "secret_values_included": False,
            "discord_send_called": False,
            "message_sent_count": 0,
        },
    }
    assert_redacted_capture_payload_safe(payload)
    return payload


def write_redacted_capture_file(
    events: Iterable[dict[str, Any]] | None = None,
    *,
    capture_root: str | Path | None = None,
    root: str | Path | None = None,
    filename: str = "phase40t_readonly_capture.json",
) -> dict[str, Any]:
    valid_root, reason, resolved_root = validate_capture_root(capture_root, root)
    if not valid_root:
        return {
            "capture_file_written": False,
            "reason": reason,
            "capture_file_path_logged": False,
            "capture_file_contains_raw_content": False,
            "capture_file_contains_raw_discord_ids": False,
            "capture_file_contains_secret_values": False,
        }
    payload = build_redacted_capture_payload(events)
    resolved_root.mkdir(parents=True, exist_ok=True)
    path = resolved_root / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "capture_file_written": True,
        "capture_file_path": str(path),
        "capture_file_path_logged": True,
        "captured_event_count": len(payload["events"]),
        "capture_file_contains_raw_content": False,
        "capture_file_contains_raw_discord_ids": False,
        "capture_file_contains_secret_values": False,
        "payload": payload,
    }


def assert_redacted_capture_payload_safe(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T capture payload contains sensitive values.")
    events = payload.get("events", [])
    if not isinstance(events, list):
        raise ValueError("Phase 40T capture events must be a list.")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Phase 40T capture event must be an object.")
        extra = set(event.keys()) - ALLOWED_EVENT_FIELDS
        forbidden = FORBIDDEN_CAPTURE_FIELDS.intersection(event.keys())
        if extra or forbidden:
            raise ValueError("Phase 40T capture event contains forbidden fields.")
    safety = payload.get("safety", {})
    for key in ("raw_content_included", "raw_discord_ids_included", "secret_values_included", "discord_send_called"):
        if safety.get(key):
            raise ValueError(f"Phase 40T capture unsafe safety flag is true: {key}")
    if int(safety.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40T capture message_sent_count must remain 0.")


def _assert_no_sensitive_values(obj: Any) -> None:
    text = json.dumps(obj, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text) or APPROVAL_RE.search(text):
        raise ValueError("Phase 40T capture object contains sensitive values.")

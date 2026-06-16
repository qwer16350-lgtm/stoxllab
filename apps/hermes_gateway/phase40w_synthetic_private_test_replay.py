"""Phase 40W synthetic redacted private-test replay fixtures."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping


VERSION = "phase40w_synthetic_private_test_replay"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def build_synthetic_event(
    *,
    channel_scope: str = "private_test_only",
    author_type: str = "human",
    is_self: bool = False,
    is_bot: bool = False,
    is_duplicate: bool = False,
) -> dict[str, Any]:
    event = {
        "event_type": "redacted_private_test_human_message" if channel_scope == "private_test_only" and author_type == "human" else "redacted_negative_message",
        "event_id_hash": "evt_hash_example",
        "message_id_hash": "msg_hash_example",
        "channel_scope": channel_scope,
        "author_type": author_type,
        "is_self": bool(is_self),
        "is_bot": bool(is_bot),
        "is_duplicate": bool(is_duplicate),
        "content_present": True,
        "content_length_bucket": "nonzero_redacted",
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "token_value_logged": False,
        "api_key_value_logged": False,
        "approval_phrase_value_logged": False,
    }
    assert_synthetic_event_safe(event)
    return event


def build_phase40w_synthetic_private_test_replay() -> dict[str, Any]:
    fixtures = {
        "private_test_human": build_synthetic_event(),
        "self_message": build_synthetic_event(author_type="self", is_self=True),
        "bot_message": build_synthetic_event(author_type="bot", is_bot=True),
        "duplicate_message": build_synthetic_event(is_duplicate=True),
        "public_channel": build_synthetic_event(channel_scope="public"),
        "team_channel": build_synthetic_event(channel_scope="team"),
    }
    report = {
        "report_type": "phase40w_synthetic_private_test_replay",
        "version": VERSION,
        "report_only": True,
        "synthetic_fixture_available": True,
        "fixtures": fixtures,
        "raw_content_logged": False,
        "raw_discord_ids_logged": False,
        "secret_values_logged": False,
        "discord_api_send_called": False,
        "discord_message_sent": False,
        "message_sent_count": 0,
        "llm_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "external_execution": False,
        "ready_for_phase40x_reply_decision_dry_run": True,
    }
    assert_phase40w_synthetic_private_test_replay_safe(report)
    return report


def assert_synthetic_event_safe(event: Mapping[str, Any]) -> None:
    text = json.dumps(event, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Phase 40W synthetic event contains sensitive values.")
    for key in ("raw_content_logged", "raw_discord_ids_logged", "secret_values_logged", "token_value_logged", "api_key_value_logged", "approval_phrase_value_logged"):
        if event.get(key):
            raise ValueError(f"Phase 40W synthetic event unsafe flag is true: {key}")


def assert_phase40w_synthetic_private_test_replay_safe(report: Mapping[str, Any]) -> None:
    text = json.dumps(report, ensure_ascii=False)
    if SECRET_RE.search(text.lower()) or LONG_ID_RE.search(text):
        raise ValueError("Phase 40W synthetic replay contains sensitive values.")
    for key in ("raw_content_logged", "raw_discord_ids_logged", "secret_values_logged", "discord_api_send_called", "discord_message_sent", "llm_called", "rag_called", "embedding_api_called", "external_execution"):
        if report.get(key):
            raise ValueError(f"Phase 40W unsafe flag is true: {key}")
    if int(report.get("message_sent_count", 0) or 0) != 0:
        raise ValueError("Phase 40W message_sent_count must remain 0.")


def render_phase40w_synthetic_private_test_replay_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# STOXL Phase 40W Synthetic Private-test Replay",
            "",
            "- Synthetic fixture available: true",
            "- Raw content/IDs/secrets logged: false",
            "- Discord message sent: false",
            f"- Fixture count: {len(report.get('fixtures', {}))}",
        ]
    ) + "\n"

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_readonly_preflight_snapshot import (
    assert_phase40t_readonly_preflight_snapshot_safe,
    build_phase40t_readonly_preflight_snapshot,
    render_phase40t_readonly_preflight_snapshot_markdown,
    snapshot_has_login_prerequisites,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")
APPROVAL_PHRASE = "I_APPROVE_PHASE40J_PRIVATE_TEST_READONLY_RUNTIME"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def preflight(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "preflight_passed": True,
        "discord_token_present": True,
        "private_test_channel_id_present": True,
        "approval_actualized": True,
        "approval_phrase_present": True,
        "approval_phrase_exact_match": True,
        "send_messages_enabled": False,
        "private_test_reply_enabled": False,
        "reply_mode_readonly_private_test_only": True,
        "llm_called": False,
        "llm_api_call_attempted": False,
        "llm_api_called": False,
        "rag_called": False,
        "embedding_api_called": False,
        "vector_index_created": False,
        "external_execution": False,
    }
    report.update(overrides)
    return report


def test_snapshot_contains_booleans_only_and_login_prerequisites() -> None:
    snapshot = build_phase40t_readonly_preflight_snapshot(preflight())
    assert_true(snapshot["discord_token_present"] is True, "Token present")
    assert_true(snapshot["private_test_channel_id_present"] is True, "Channel present")
    assert_true(snapshot["approval_phrase_exact_match"] is True, "Approval exact")
    assert_true(snapshot["reply_mode_readonly_private_test_only"] is True, "Reply mode")
    assert_true(snapshot["llm_disabled"] is True, "LLM disabled")
    assert_true(snapshot["rag_disabled"] is True, "RAG disabled")
    assert_true(snapshot["embedding_disabled"] is True, "Embedding disabled")
    assert_true(snapshot_has_login_prerequisites(snapshot) is True, "Login prerequisites")


def test_snapshot_missing_prerequisites() -> None:
    missing_token = build_phase40t_readonly_preflight_snapshot(preflight(discord_token_present=False))
    missing_channel = build_phase40t_readonly_preflight_snapshot(preflight(private_test_channel_id_present=False))
    assert_true(snapshot_has_login_prerequisites(missing_token) is False, "Missing token")
    assert_true(snapshot_has_login_prerequisites(missing_channel) is False, "Missing channel")


def test_snapshot_no_sensitive_values() -> None:
    snapshot = build_phase40t_readonly_preflight_snapshot(
        preflight(
            raw_token_value="xoxb-secret-value",
            raw_channel_id="123456789012345678",
            approval_phrase_value=APPROVAL_PHRASE,
        )
    )
    text = json.dumps(snapshot, ensure_ascii=False)
    assert_phase40t_readonly_preflight_snapshot_safe(snapshot)
    assert_true("xoxb-secret-value" not in text, "Token value hidden")
    assert_true(APPROVAL_PHRASE not in text, "Approval phrase hidden")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw ID hidden")


def test_snapshot_markdown() -> None:
    markdown = render_phase40t_readonly_preflight_snapshot_markdown(build_phase40t_readonly_preflight_snapshot(preflight()))
    assert_true("Read-only Preflight Snapshot" in markdown, "Markdown")
    assert_true("Token/channel/approval values logged: false" in markdown, "No values")


def main() -> int:
    for test in (
        test_snapshot_contains_booleans_only_and_login_prerequisites,
        test_snapshot_missing_prerequisites,
        test_snapshot_no_sensitive_values,
        test_snapshot_markdown,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T read-only preflight snapshot tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

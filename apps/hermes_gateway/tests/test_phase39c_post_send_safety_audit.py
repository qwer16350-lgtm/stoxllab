from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39c_post_send_safety_audit import build_phase39c_post_send_safety_audit, render_phase39c_post_send_safety_audit_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def gate_off_env(**overrides: str) -> dict[str, str]:
    env = {
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED": "false",
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE": "",
        "HERMES_DISCORD_SEND_MESSAGES": "false",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "false",
        "HERMES_DISCORD_REPLY_MODE": "",
        "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION": "false",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_DISCORD_LLM_ENABLED": "false",
    }
    env.update(overrides)
    return env


def test_post_send_audit_gate_off_verified() -> None:
    report = build_phase39c_post_send_safety_audit(env=gate_off_env())
    assert_true(report["gate_off_verified"] is True, "Gate off")
    assert_true(report["approval_gate_off"] is True, "Approval off")
    assert_true(report["discord_send_messages_off"] is True, "Send off")
    assert_true(report["private_test_reply_off"] is True, "Reply off")
    assert_true(report["reply_mode_empty"] is True, "Reply mode empty")
    assert_true(report["real_discord_send_execution_off"] is True, "Real env off")


def test_post_send_audit_counts_and_no_additional_send() -> None:
    report = build_phase39c_post_send_safety_audit(env=gate_off_env())
    assert_true(report["phase39b_actual_send_count"] == 1, "Phase39B count")
    assert_true(report["phase39c_additional_send_count"] == 0, "Phase39C additional 0")
    assert_true(report["total_actual_discord_send_count_this_sequence"] == 1, "Total count")
    assert_true(report["additional_discord_send_called_in_phase39c"] is False, "No extra API")
    assert_true(report["additional_discord_message_sent_in_phase39c"] is False, "No extra message")


def test_post_send_audit_blocks_gates_on() -> None:
    for key, value in (
        ("HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED", "true"),
        ("HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE", "present"),
        ("HERMES_DISCORD_SEND_MESSAGES", "true"),
        ("HERMES_DISCORD_PRIVATE_TEST_REPLY", "true"),
        ("HERMES_DISCORD_REPLY_MODE", "private_test_only"),
        ("HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION", "true"),
        ("HERMES_LLM_DISCORD_SEND_ENABLED", "true"),
        ("HERMES_DISCORD_RAG_ENABLED", "true"),
        ("HERMES_DISCORD_EXTERNAL_EXECUTION", "true"),
    ):
        assert_raises(lambda selected=key, selected_value=value: build_phase39c_post_send_safety_audit(env=gate_off_env(**{selected: selected_value})), f"{key} should fail")


def test_post_send_audit_no_sensitive_values_and_markdown() -> None:
    report = build_phase39c_post_send_safety_audit(env=gate_off_env())
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 39C Post-send Safety Audit" in render_phase39c_post_send_safety_audit_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_post_send_audit_gate_off_verified,
        test_post_send_audit_counts_and_no_additional_send,
        test_post_send_audit_blocks_gates_on,
        test_post_send_audit_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39C post-send safety audit tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

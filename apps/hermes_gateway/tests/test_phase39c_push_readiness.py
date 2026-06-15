from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase39c_post_send_safety_audit import build_phase39c_post_send_safety_audit
from phase39c_push_readiness import build_phase39c_push_readiness, render_phase39c_push_readiness_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def gate_off_env() -> dict[str, str]:
    return {
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
    }


def test_push_readiness_report() -> None:
    audit = build_phase39c_post_send_safety_audit(env=gate_off_env())
    report = build_phase39c_push_readiness(safety_audit=audit)
    assert_true(report["report_type"] == "phase39c_push_readiness", "Report type")
    assert_true(report["working_tree_expected_clean_after_commit"] is True, "Clean expected")
    assert_true(report["branch"] == "feature/stoxl-hermes-agent-org", "Branch")
    assert_true(report["remote_push_required"] is True, "Push required")
    assert_true(report["push_executed_by_codex"] is False, "Codex no push")
    assert_true(report["push_command"] == "git push origin feature/stoxl-hermes-agent-org", "Push command")


def test_push_readiness_requires_closeout_lock_and_gate_off() -> None:
    audit = build_phase39c_post_send_safety_audit(env=gate_off_env())
    report = build_phase39c_push_readiness(safety_audit=audit)
    assert_true(report["actual_discord_send_count_locked"] == 1, "Locked count")
    assert_true(report["phase39c_closeout_completed"] is True, "Closeout complete")
    assert_true(report["phase39c_no_repeat_lock_active"] is True, "No-repeat")
    assert_true(report["phase39c_gate_off_verified"] is True, "Gate off")


def test_push_readiness_no_send_or_external() -> None:
    audit = build_phase39c_post_send_safety_audit(env=gate_off_env())
    report = build_phase39c_push_readiness(safety_audit=audit)
    for key in ("discord_api_send_called_in_phase39c", "discord_message_sent_in_phase39c", "repeat_send_allowed", "automatic_retry_allowed", "manual_retry_allowed", "ready_for_repeat_send", "unattended_auto_reply_allowed", "new_llm_api_call_attempted", "new_llm_api_called", "llm_api_call_attempted", "llm_api_called", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count_in_phase39c"] == 0, "No Phase39C message")


def test_push_readiness_no_sensitive_values_and_markdown() -> None:
    audit = build_phase39c_post_send_safety_audit(env=gate_off_env())
    report = build_phase39c_push_readiness(safety_audit=audit)
    text = json.dumps(report, ensure_ascii=False).lower().replace(report["push_command"].lower(), "")
    assert_true("sk-" not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 39C Push Readiness" in render_phase39c_push_readiness_markdown(report), "Markdown")


def main() -> int:
    tests = [
        test_push_readiness_report,
        test_push_readiness_requires_closeout_lock_and_gate_off,
        test_push_readiness_no_send_or_external,
        test_push_readiness_no_sensitive_values_and_markdown,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39C push readiness tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

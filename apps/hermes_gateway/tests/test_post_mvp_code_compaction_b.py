from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from manual_gate_helpers import (
    approval_gate_report,
    assert_disabled_flags,
    assert_reply_mode,
    build_blocked_reasons,
    env_int,
    env_present,
    env_true,
    redacted_presence_report,
)
from mvp_state_registry import (
    build_hermes_manual_gate_inventory,
    build_hermes_mvp_state_report,
    build_hermes_post_mvp_compaction_plan,
    build_post_mvp_compaction_b_report,
)
from phase60_65_team_canary_autonomy_stage import build_actual_phase60_team_canary
from phase67_72_supervised_team_auto_ops import build_actual_phase67_team_auto_ops
from phase74_limited_auto_mode_prep import build_actual_phase74_limited_auto_mode
from safety_report_builders import (
    base_no_external_action_report,
    build_blocked_report,
    build_consumed_lock_report,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_sensitive_values(report: dict[str, object]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("secret-token-value" not in text, "No token value")
    assert_true("channel-value" not in text, "No channel value")
    assert_true("approval-value" not in text, "No approval value")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def test_manual_gate_helpers_return_booleans_only() -> None:
    env = {
        "APPROVED": "true",
        "PHRASE": "approval-value",
        "TOKEN": "secret-token-value",
        "CHANNEL": "channel-value",
        "COUNT": "7",
        "HERMES_DISCORD_REPLY_MODE": "expected_mode",
        "DISABLED_FLAG": "false",
    }
    assert_true(env_present(env, "TOKEN") is True, "Token presence")
    assert_true(env_present(env, "CHANNEL") is True, "Channel presence")
    assert_true(env_true(env, "APPROVED") is True, "Approval bool")
    assert_true(env_int(env, "COUNT") == 7, "Integer parse")
    presence = redacted_presence_report(env, ("TOKEN", "CHANNEL"))
    gate = approval_gate_report(env, "APPROVED", "PHRASE", "approval-value")
    assert_true(presence == {"token_present": True, "channel_present": True}, "Presence only")
    assert_true(gate["manual_approval_true"] is True, "Manual approval")
    assert_true(gate["approval_phrase_present"] is True, "Phrase present")
    assert_true(gate["approval_phrase_exact_match"] is True, "Phrase match")
    assert_true(gate["approval_phrase_value_logged"] is False, "No phrase value")
    assert_true(assert_reply_mode(env, "expected_mode") is True, "Reply mode")
    assert_true(assert_disabled_flags(env, ("DISABLED_FLAG",)) is True, "Disabled flag")
    assert_true(build_blocked_reasons({"a": True, "b": False}) == ["b"], "Blocked reasons")
    assert_no_sensitive_values({**presence, **gate})


def test_safety_report_builders() -> None:
    base = base_no_external_action_report()
    for key in (
        "actual_discord_runtime_executed",
        "discord_gateway_live_connection_executed",
        "discord_api_send_called",
        "discord_message_sent",
        "llm_api_call_attempted",
        "llm_api_called",
        "rag_called",
        "embedding_api_called",
        "vector_index_created",
        "external_execution",
        "scheduler_live_execution",
        "cron_started",
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        assert_true(base[key] is False, key)
    assert_true(base["message_sent_count"] == 0, "No send count")
    blocked = build_blocked_report("sample_blocked", ["reason"])
    assert_true(blocked["blocked"] is True, "Blocked")
    assert_true(blocked["blocked_reasons"] == ["reason"], "Reason")
    assert_true(blocked["message_sent_count"] == 0, "Blocked no send")
    consumed = build_consumed_lock_report("phase74_limited_auto_mode", "phase74_limited_auto_mode_already_consumed")
    assert_true(consumed["blocked"] is True, "Consumed blocked")
    assert_true(consumed["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Consumed reason")


def test_repeat_locks_preserved() -> None:
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    assert_true(phase60["blocked"] is True, "Phase60 blocked")
    assert_true(phase60["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Phase60 consumed")
    assert_true(phase67["blocked"] is True, "Phase67 blocked")
    assert_true(phase67["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Phase67 consumed")
    assert_true(phase74["blocked"] is True, "Phase74 blocked")
    assert_true(phase74["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Phase74 consumed")
    for report in (phase60, phase67, phase74):
        assert_true(report["discord_api_send_called"] is False, "No API")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No send count")


def test_mvp_registry_reports_still_pass() -> None:
    state = build_hermes_mvp_state_report()
    inventory = build_hermes_manual_gate_inventory()
    plan = build_hermes_post_mvp_compaction_plan()
    compaction_b = build_post_mvp_compaction_b_report()
    assert_true(state["mvp_supervised_discord_agent_os_complete"] is True, "MVP complete")
    assert_true(inventory["manual_gates"], "Manual gates present")
    assert_true(plan["delete_files_now"] is False, "No delete")
    assert_true(plan["move_files_now"] is False, "No move")
    assert_true(compaction_b["manual_gate_helpers_available"] is True, "Manual helpers")
    assert_true(compaction_b["safety_report_builders_available"] is True, "Safety builders")
    assert_true(compaction_b["manual_gate_behavior_weakened"] is False, "Gate not weakened")
    assert_true(compaction_b["consumed_locks_weakened"] is False, "Locks not weakened")
    assert_true(compaction_b["ready_for_next_compaction_stage"] is True, "Next ready")


def main() -> int:
    tests = [
        test_manual_gate_helpers_return_booleans_only,
        test_safety_report_builders,
        test_repeat_locks_preserved,
        test_mvp_registry_reports_still_pass,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Post-MVP Code Compaction B tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mvp_state_registry import (
    build_hermes_mvp_state_report,
    build_post_mvp_compaction_b_report,
    build_post_mvp_compaction_d_report,
)
from phase60_65_team_canary_autonomy_stage import (
    build_actual_phase60_team_canary,
    build_phase60_65_team_canary_autonomy_stage,
)
from phase67_72_supervised_team_auto_ops import (
    build_actual_phase67_team_auto_ops,
    build_phase67_72_supervised_team_auto_ops,
)
from phase74_limited_auto_mode_prep import (
    build_actual_phase74_limited_auto_mode,
    build_phase74_limited_auto_mode_prep,
)
from phase_archive_index import build_hermes_phase_archive_index
from phase_policy_builders import (
    build_allowed_scope,
    build_blocked_scope,
    build_known_team_low_risk_policy_report,
    build_limited_bounds_report,
    build_phase_progression_report,
    build_policy_capsule_report,
    build_queue_review_packet_report,
)


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_sensitive_values(report: dict[str, object]) -> None:
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No token-like values")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def assert_no_runtime_send_or_external(report: dict[str, object]) -> None:
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
        "raw_content_logged",
        "raw_discord_ids_logged",
        "secret_values_logged",
        "approval_phrase_value_logged",
        "team_channel_id_value_logged",
    ):
        assert_true(report[key] is False, key)
    assert_true(report["message_sent_count"] == 0, "No send count")


def test_phase_policy_builders_exist_and_are_redacted() -> None:
    allowed = build_allowed_scope("known_team_channel_only", "low_risk_intent_only")
    blocked = build_blocked_scope("public_channel", "unknown_channel")
    capsule = build_policy_capsule_report(allowed, blocked)
    policy = build_known_team_low_risk_policy_report()
    queue = build_queue_review_packet_report()
    bounds = build_limited_bounds_report(60, 1, 1, 30)
    progression = build_phase_progression_report("current", "next")
    assert_true(capsule["policy_capsule_available"] is True, "Capsule")
    assert_true(capsule["allowed_scope"] == allowed, "Allowed labels")
    assert_true(capsule["blocked_scope"] == blocked, "Blocked labels")
    assert_true(policy["known_team_channel_required"] is True, "Known team")
    assert_true(policy["low_risk_intent_required"] is True, "Low risk")
    assert_true(policy["deterministic_template_only"] is True, "Template")
    assert_true(queue["review_packet_raw_content_included"] is False, "No raw content")
    assert_true(bounds["session_seconds_bounded"] is True, "Bounds")
    assert_true(progression["ready_for_production_unattended"] is False, "Production false")
    assert_no_sensitive_values({**capsule, **policy, **queue, **bounds, **progression})


def test_phase_reports_keep_existing_keys() -> None:
    phase60 = build_phase60_65_team_canary_autonomy_stage()
    phase67 = build_phase67_72_supervised_team_auto_ops()
    phase74 = build_phase74_limited_auto_mode_prep()
    for report in (phase60, phase67, phase74):
        assert_true(report["known_team_channel_required"] is True, "Known key")
        assert_true(report["low_risk_intent_required"] is True, "Low-risk key")
        assert_true(report["deterministic_template_only"] is True, "Template key")
        assert_true(report["ready_for_production_unattended"] is False, "Production false")
        assert_true(report["current_verified_level"], "Current level key")
        assert_true(report["next_target_level"], "Next level key")
    assert_true(phase67["ops_queue_required"] is True, "Phase67 queue")
    assert_true(phase67["review_packet_required"] is True, "Phase67 packet")
    assert_true(phase74["ops_queue_required"] is True, "Phase74 queue")
    assert_true(phase74["review_packet_required"] is True, "Phase74 packet")
    assert_true(phase74["policy_capsule_available"] is True, "Phase74 capsule")


def test_repeat_locks_still_blocked_send_zero() -> None:
    phase60 = build_actual_phase60_team_canary(allow_flag_present=True)
    phase67 = build_actual_phase67_team_auto_ops(allow_flag_present=True)
    phase74 = build_actual_phase74_limited_auto_mode(allow_flag_present=True)
    assert_true(phase60["blocked_reasons"] == ["phase60_team_canary_already_consumed"], "Phase60 consumed")
    assert_true(phase67["blocked_reasons"] == ["phase67_team_auto_ops_already_consumed"], "Phase67 consumed")
    assert_true(phase74["blocked_reasons"] == ["phase74_limited_auto_mode_already_consumed"], "Phase74 consumed")
    for report in (phase60, phase67, phase74):
        assert_true(report["blocked"] is True, "Blocked")
        assert_true(report["discord_api_send_called"] is False, "No API")
        assert_true(report["discord_message_sent"] is False, "No message")
        assert_true(report["message_sent_count"] == 0, "No send")


def test_registry_archive_and_compaction_d_reports() -> None:
    mvp = build_hermes_mvp_state_report()
    compaction_b = build_post_mvp_compaction_b_report()
    archive = build_hermes_phase_archive_index()
    compaction_d = build_post_mvp_compaction_d_report()
    assert_true(mvp["mvp_supervised_discord_agent_os_complete"] is True, "MVP")
    assert_true(compaction_b["ready_for_next_compaction_stage"] is True, "Compaction B")
    assert_true(archive["delete_files_now"] is False, "Archive no delete")
    assert_true(archive["move_files_now"] is False, "Archive no move")
    assert_true(compaction_d["phase_policy_builders_available"] is True, "Policy builders")
    assert_true(compaction_d["phase60_policy_helpers_integrated"] is True, "Phase60 integrated")
    assert_true(compaction_d["phase67_policy_helpers_integrated"] is True, "Phase67 integrated")
    assert_true(compaction_d["phase74_policy_helpers_integrated"] is True, "Phase74 integrated")
    assert_true(compaction_d["delete_files_now"] is False, "No delete")
    assert_true(compaction_d["move_files_now"] is False, "No move")
    assert_true(compaction_d["manual_gate_behavior_weakened"] is False, "Gate not weakened")
    assert_true(compaction_d["consumed_locks_weakened"] is False, "Locks not weakened")
    assert_true(compaction_d["secret_redaction_weakened"] is False, "Redaction not weakened")
    assert_no_runtime_send_or_external(compaction_d)


def main() -> int:
    tests = [
        test_phase_policy_builders_exist_and_are_redacted,
        test_phase_reports_keep_existing_keys,
        test_repeat_locks_still_blocked_send_zero,
        test_registry_archive_and_compaction_d_reports,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Post-MVP Code Compaction D tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

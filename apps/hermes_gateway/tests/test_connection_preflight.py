"""Read-only Discord connection preflight tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_connection_preflight.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from connection_preflight import build_connection_preflight_report, build_dependency_plan


ROOT = APP_DIR.parents[1]
REPORT = ROOT / "apps" / "hermes_gateway" / "examples" / "connection_preflight_report.example.json"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def report() -> dict:
    return build_connection_preflight_report(ROOT)


def test_dependency_plan_created() -> None:
    plan = build_dependency_plan()
    assert_true(plan["recommended_runtime"] == "python", "Dependency plan should recommend python runtime")


def test_recommended_library_discord_py() -> None:
    assert_true(build_dependency_plan()["recommended_library"] == "discord.py", "Recommended library should be discord.py")


def test_install_now_false() -> None:
    assert_true(build_dependency_plan()["install_now"] is False, "Dependency should not be installed in Phase 23")


def test_phase23_dependency_declared_still_fails() -> None:
    check = [item for item in report()["checks"] if item["check_id"] == "readonly_safety_flags"][0]
    assert_true(check["details"]["discord_dependency_declared_now"] is True, "Test fixture should include declared Discord dependency")
    assert_true(check["status"] == "fail", "Phase 23 no-connection preflight should still fail when Discord dependency is declared")


def test_local_mapping_validation_reflected() -> None:
    check = [item for item in report()["checks"] if item["check_id"] == "local_mapping_strict_validation"][0]
    assert_true(check["status"] == "pass", "Local mapping strict validation should be reflected as pass")
    assert_true(check["details"]["ready_for_readonly_connection"] is True, "Local mapping should be ready before Phase 23 proceeds")


def test_token_value_not_read() -> None:
    safety = report()["safety_assertions"]
    assert_true(safety["bot_token_value_read"] is False, "Bot token value must not be read")


def test_env_file_not_read() -> None:
    safety = report()["safety_assertions"]
    assert_true(safety["env_file_read"] is False, ".env file must not be read")


def test_discord_api_not_called() -> None:
    assert_true(report()["safety_assertions"]["discord_api_called"] is False, "Discord API must not be called")


def test_gateway_not_connected() -> None:
    assert_true(report()["safety_assertions"]["gateway_connected"] is False, "Gateway must not connect")


def test_message_not_sent() -> None:
    assert_true(report()["safety_assertions"]["message_sent"] is False, "Message must not be sent")


def test_external_execution_disabled() -> None:
    assert_true(report()["safety_assertions"]["external_execution_enabled"] is False, "External execution must be disabled")


def test_human_only_preserved() -> None:
    assert_true(report()["safety_assertions"]["human_only_execution_preserved"] is True, "Human-only execution must be preserved")


def test_gitignore_protections() -> None:
    check = [item for item in report()["checks"] if item["check_id"] == "gitignore_runtime_artifact_protection"][0]
    assert_true(check["status"] == "pass", "Runtime artifacts should be gitignored")
    assert_true(check["details"]["local_mapping_gitignored"] is True, "Local mapping should be gitignored")
    assert_true(check["details"]["logs_gitignored"] is True, "Logs should be gitignored")
    assert_true(check["details"]["exports_gitignored"] is True, "Exports should be gitignored")


def test_report_does_not_print_raw_discord_ids() -> None:
    text = json.dumps(report(), ensure_ascii=False)
    assert_true(not LONG_NUMBER_RE.search(text), "Report should not print long Discord-like numeric IDs")


def test_example_report_parseable_and_safe() -> None:
    data = json.loads(REPORT.read_text(encoding="utf-8-sig"))
    text = json.dumps(data, ensure_ascii=False).lower()
    assert_true(data["report_type"] == "readonly_discord_connection_preflight", "Example report should parse")
    assert_true("xoxb-" not in text and "sk-" not in text and "mfa." not in text, "Example report should not contain secret-like raw values")


def main() -> int:
    tests = [
        test_dependency_plan_created,
        test_recommended_library_discord_py,
        test_install_now_false,
        test_phase23_dependency_declared_still_fails,
        test_local_mapping_validation_reflected,
        test_token_value_not_read,
        test_env_file_not_read,
        test_discord_api_not_called,
        test_gateway_not_connected,
        test_message_not_sent,
        test_external_execution_disabled,
        test_human_only_preserved,
        test_gitignore_protections,
        test_report_does_not_print_raw_discord_ids,
        test_example_report_parseable_and_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All connection preflight tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

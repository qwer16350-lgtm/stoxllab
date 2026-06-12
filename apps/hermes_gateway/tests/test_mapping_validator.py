"""Local Discord mapping validator tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_mapping_validator.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from mapping_validator import build_mapping_validation_report, find_secret_like_values, load_mapping, load_registry, validate_mapping


ROOT = APP_DIR.parents[1]
TEMPLATE = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_runtime_mapping.template.json"
PARTIAL = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_runtime_mapping.partial.example.json"
REPORT = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_mapping_validation_report.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def template_report(strict: bool = False) -> dict:
    return build_mapping_validation_report(TEMPLATE, root=ROOT, strict=strict)


def partial_report() -> dict:
    return build_mapping_validation_report(PARTIAL, root=ROOT)


def test_template_mapping_parses() -> None:
    mapping = load_mapping(TEMPLATE)
    assert_true(mapping["mapping_type"] == "discord_runtime_mapping_template", "Template mapping should parse")


def test_non_strict_template_manual_required() -> None:
    report = template_report()
    assert_true(report["overall_valid"] is True, "Non-strict template should be structurally valid")
    assert_true(len(report["manual_required"]) > 0, "Non-strict template should contain manual_required placeholders")


def test_non_strict_template_not_ready() -> None:
    report = template_report()
    assert_true(report["ready_for_readonly_connection"] is False, "Template TODO placeholders should not be ready for read-only connection")


def test_strict_template_fails_on_todo() -> None:
    report = template_report(strict=True)
    assert_true(report["overall_valid"] is False, "Strict template should fail on TODO placeholders")
    assert_true(any(check["status"] == "fail" for check in report["checks"]), "Strict report should include failing checks")


def test_partial_mapping_detects_missing_items() -> None:
    report = partial_report()
    missing = set(report["missing_mappings"])
    assert_true("owner:OWNER_LEE_DISCORD_ID" in missing, "Partial mapping should miss one owner")
    assert_true("role:Human Operator" in missing, "Partial mapping should miss one role")
    assert_true("channel:보류된-안건" in missing, "Partial mapping should miss archive hold channel")
    assert_true("channel:폐기된-안건" in missing, "Partial mapping should miss archive discarded channel")


def test_approval_channel_mapping_present() -> None:
    report = template_report()
    approval = [check for check in report["checks"] if check["check_id"] == "approval_mapping"][0]
    assert_true(approval["status"] == "pass", "Approval channel mapping should pass")


def test_audit_channel_placeholder_detected() -> None:
    report = partial_report()
    audit = [check for check in report["checks"] if check["check_id"] == "audit_mapping"][0]
    assert_true(audit["status"] == "manual_required", "Partial audit placeholder should require manual completion")


def test_secret_like_value_invalid_and_redacted() -> None:
    mapping = load_mapping(TEMPLATE)
    registry = load_registry(ROOT)
    mutated = copy.deepcopy(mapping)
    mutated["bot_token"] = "xoxb-this-value-must-not-appear"
    findings = find_secret_like_values(mutated)
    report = validate_mapping(mutated, registry)
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(len(findings) >= 1, "Secret-like value should be detected")
    assert_true(report["overall_valid"] is False, "Secret-like value should invalidate mapping")
    assert_true("xoxb-this-value-must-not-appear" not in text, "Secret value must not appear in report")
    assert_true("[redacted]" in text, "Secret finding should be redacted")


def test_registry_channels_covered_by_template() -> None:
    registry = load_registry(ROOT)
    mapping = load_mapping(TEMPLATE)
    missing = set(registry.get("channels", {}).keys()) - set(mapping.get("channels", {}).keys())
    assert_true(not missing, f"Template should cover registry channels: {missing}")


def test_safety_assertions_are_local_only() -> None:
    safety = template_report()["safety_assertions"]
    assert_true(safety["discord_api_called"] is False, "Discord API must not be called")
    assert_true(safety["gateway_connected"] is False, "Gateway must not connect")
    assert_true(safety["message_sent"] is False, "Message must not be sent")
    assert_true(safety["external_execution_enabled"] is False, "External execution must not be enabled")
    assert_true(safety["human_only_execution_preserved"] is True, "Human-only execution must be preserved")


def test_example_report_is_parseable_and_safe() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8-sig"))
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true(report["report_type"] == "discord_mapping_validation", "Example report should be parseable")
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Example report should contain no secret-like raw value")


def main() -> int:
    tests = [
        test_template_mapping_parses,
        test_non_strict_template_manual_required,
        test_non_strict_template_not_ready,
        test_strict_template_fails_on_todo,
        test_partial_mapping_detects_missing_items,
        test_approval_channel_mapping_present,
        test_audit_channel_placeholder_detected,
        test_secret_like_value_invalid_and_redacted,
        test_registry_channels_covered_by_template,
        test_safety_assertions_are_local_only,
        test_example_report_is_parseable_and_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord mapping validator tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

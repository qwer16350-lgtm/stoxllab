"""Local Discord readiness tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_discord_readiness.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_readiness import build_readiness_report, load_mapping_template
from registry_loader import load_registry
from config import load_config


ROOT = APP_DIR.parents[1]
MAPPING = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_runtime_mapping.template.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def report() -> dict:
    return build_readiness_report(ROOT, MAPPING)


def test_mapping_template_parses() -> None:
    mapping = load_mapping_template(MAPPING)
    assert_true(mapping["mapping_type"] == "discord_runtime_mapping_template", "Mapping template should parse")


def test_readiness_report_created() -> None:
    output = report()
    assert_true(output["report_type"] == "discord_readiness_check", "Readiness report should be created")


def test_safety_flags_false_for_real_connections() -> None:
    safety = report()["safety_assertions"]
    assert_true(safety["discord_api_called"] is False, "Discord API must not be called")
    assert_true(safety["gateway_connected"] is False, "Gateway must not connect")
    assert_true(safety["external_execution_enabled"] is False, "External execution must remain disabled")
    assert_true(safety["human_only_execution_preserved"] is True, "Human-only execution should be preserved")


def test_owner_placeholders_present() -> None:
    mapping = load_mapping_template(MAPPING)
    placeholders = {owner["user_id_placeholder"] for owner in mapping["owners"]}
    assert_true("TODO_OWNER_KIM_DISCORD_ID" in placeholders, "Kim owner placeholder should exist")
    assert_true("TODO_OWNER_LEE_DISCORD_ID" in placeholders, "Lee owner placeholder should exist")


def test_approval_channel_mapping_present() -> None:
    mapping = load_mapping_template(MAPPING)
    assert_true("최종-승인요청" in mapping["channels"], "Approval channel should be mapped")


def test_all_registry_channels_mapped() -> None:
    cfg = load_config(APP_DIR)
    registry = load_registry(cfg)
    mapping = load_mapping_template(MAPPING)
    missing = set(registry.get("channels", {}).keys()) - set(mapping.get("channels", {}).keys())
    assert_true(not missing, f"All registry channels should be mapped: {missing}")


def test_no_secret_like_values_in_report() -> None:
    text = json.dumps(report(), ensure_ascii=False)
    for marker in ["sk-", "xoxb-", "mfa.", "Bot ", "Bearer "]:
        assert_true(marker not in text, f"Report should not contain secret-like marker {marker}")


def main() -> int:
    tests = [
        test_mapping_template_parses,
        test_readiness_report_created,
        test_safety_flags_false_for_real_connections,
        test_owner_placeholders_present,
        test_approval_channel_mapping_present,
        test_all_registry_channels_mapped,
        test_no_secret_like_values_in_report,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord readiness tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

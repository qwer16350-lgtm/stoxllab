"""Local mapping manager tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_local_mapping_manager.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from local_mapping_manager import (
    build_local_mapping_manager_report,
    copy_template_to_local,
    ensure_local_dir,
    get_default_local_mapping_path,
    get_default_template_path,
    get_local_dir,
    validate_local_mapping,
)


ROOT = APP_DIR.parents[1]
TEMPLATE = ROOT / "apps" / "hermes_gateway" / "examples" / "discord_runtime_mapping.template.json"
GITIGNORE = ROOT / ".gitignore"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_local_dir_path() -> None:
    assert_true(get_local_dir(ROOT).as_posix().endswith("apps/hermes_gateway/local"), "Local dir path should be stable")


def test_template_path_exists() -> None:
    assert_true(get_default_template_path(ROOT).exists(), "Default template path should exist")


def test_temp_template_copy_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        report = copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target)
        assert_true(report["created"] is True, "Template copy should create local mapping")
        assert_true(target.exists(), "Copied local mapping should exist")


def test_existing_mapping_overwrite_forbidden() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target)
        report = copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target)
        assert_true(report["created"] is False, "Existing local mapping should not be overwritten")
        assert_true(report["blocked_reasons"], "Overwrite refusal should be reported")


def test_force_overwrite_allowed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        target.write_text('{"old": true}\n', encoding="utf-8")
        report = copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target, force=True)
        data = json.loads(target.read_text(encoding="utf-8"))
        assert_true(report["created"] is True, "Force should overwrite local mapping")
        assert_true(data.get("mapping_type") == "discord_runtime_mapping_template", "Force copy should write template content")


def test_validate_local_mapping_call_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target)
        report = validate_local_mapping(ROOT, local_path=target)
        assert_true(report["report_type"] == "discord_mapping_validation", "Validation report should be returned")
        assert_true(report["overall_valid"] is True, "Template structure should be valid in non-strict mode")


def test_strict_validation_ready_false_for_todo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        copy_template_to_local(ROOT, template_path=TEMPLATE, local_path=target)
        report = build_local_mapping_manager_report(ROOT, local_path=target, strict=True)
        assert_true(report["validated"] is True, "Strict validation should run")
        assert_true(report["ready_for_readonly_connection"] is False, "TODO placeholders should keep ready false")
        assert_true(report["blocked_reasons"], "Strict TODO placeholders should create blocked reasons")


def test_secret_like_value_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "discord_runtime_mapping.local.json"
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        data["runtime_secret"] = "xoxb-do-not-commit-this"
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        report = build_local_mapping_manager_report(ROOT, local_path=target)
        text = json.dumps(report, ensure_ascii=False).lower()
        assert_true(report["ready_for_readonly_connection"] is False, "Secret-like value should block readiness")
        assert_true("xoxb-do-not-commit-this" not in text, "Secret-like raw value should not appear in report")


def test_safety_assertions_preserved() -> None:
    report = build_local_mapping_manager_report(ROOT, local_path=Path(tempfile.gettempdir()) / "missing_stoxl_mapping.json")
    safety = report["safety_assertions"]
    assert_true(safety["discord_api_called"] is False, "Discord API must not be called")
    assert_true(safety["gateway_connected"] is False, "Gateway must not connect")
    assert_true(safety["bot_token_required"] is False, "Bot Token must not be required")
    assert_true(safety["env_file_read"] is False, ".env must not be read")
    assert_true(safety["message_sent"] is False, "Message must not be sent")
    assert_true(safety["external_execution_enabled"] is False, "External execution must not be enabled")
    assert_true(safety["human_only_execution_preserved"] is True, "Human-only execution must be preserved")


def test_gitignore_protects_local_mapping() -> None:
    text = GITIGNORE.read_text(encoding="utf-8")
    assert_true("apps/hermes_gateway/local/*" in text, "Local mapping files should be ignored")
    assert_true("!apps/hermes_gateway/local/.gitkeep" in text, ".gitkeep should remain trackable")
    assert_true("!apps/hermes_gateway/local/README.md" in text, "Local README should remain trackable")


def test_default_local_mapping_path() -> None:
    path = get_default_local_mapping_path(ROOT)
    assert_true(path.name == "discord_runtime_mapping.local.json", "Default local mapping file name should be stable")


def test_ensure_local_dir() -> None:
    local_dir = ensure_local_dir(ROOT)
    assert_true(local_dir.exists(), "Local dir should exist after ensure")


def main() -> int:
    tests = [
        test_local_dir_path,
        test_template_path_exists,
        test_temp_template_copy_success,
        test_existing_mapping_overwrite_forbidden,
        test_force_overwrite_allowed,
        test_validate_local_mapping_call_success,
        test_strict_validation_ready_false_for_todo,
        test_secret_like_value_blocked,
        test_safety_assertions_preserved,
        test_gitignore_protects_local_mapping,
        test_default_local_mapping_path,
        test_ensure_local_dir,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All local mapping manager tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

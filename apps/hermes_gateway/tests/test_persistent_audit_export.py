"""Local persistent audit export tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_persistent_audit_export.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from log_exporter import export_replay_result
from replay import run_replay


ROOT = APP_DIR.parents[1]
EVENTS = ROOT / "apps" / "hermes_gateway" / "examples" / "export_replay_events.example.json"
ACTIONS = ROOT / "apps" / "hermes_gateway" / "examples" / "approval_actions.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_replay_result_export_creates_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        summary = export_replay_result(output, Path(tmp) / "logs")
        replay_path = Path(summary["replay_run_path"])
        approval_path = Path(summary["approval_decisions_path"])
        audit_path = Path(summary["audit_events_path"])
        assert_true(summary["exported"] is True, "Export summary should mark exported=true")
        assert_true(replay_path.exists(), "Replay run JSON should be created")
        assert_true(approval_path.exists(), "Approval decisions JSONL should be created")
        assert_true(audit_path.exists(), "Audit events JSONL should be created")


def test_redaction_applied_to_sensitive_values() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        summary = export_replay_result(output, Path(tmp) / "logs")
        replay_text = Path(summary["replay_run_path"]).read_text(encoding="utf-8")
        audit_text = Path(summary["audit_events_path"]).read_text(encoding="utf-8")
        assert_true("sk-test-secret-value" not in replay_text, "Secret value should not appear in replay JSON")
        assert_true("sk-test-secret-value" not in audit_text, "Secret value should not appear in audit JSONL")
        assert_true("[REDACTED]" in replay_text or "[REDACTED]" in audit_text, "Redaction marker should be present")


def test_external_execution_zero_allows_export() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        summary = export_replay_result(output, Path(tmp) / "logs")
        assert_true(summary["external_execution_count"] == 0, "External execution count should be zero")


def test_external_execution_nonzero_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        output["summary"]["external_execution_count"] = 1
        try:
            export_replay_result(output, Path(tmp) / "logs")
        except ValueError as exc:
            assert_true("external_execution_count" in str(exc), "Error should mention external_execution_count")
            return
        raise AssertionError("Exporter should reject external_execution_count > 0")


def test_dry_run_export_creates_no_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        log_root = Path(tmp) / "logs"
        summary = export_replay_result(output, log_root, dry_run=True)
        assert_true(summary["exported"] is False, "Dry-run export should not mark exported=true")
        assert_true(not log_root.exists(), "Dry-run export should not create log root")


def test_jsonl_record_counts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = run_replay(EVENTS, ACTIONS)
        summary = export_replay_result(output, Path(tmp) / "logs")
        approval_records = read_jsonl(Path(summary["approval_decisions_path"]))
        audit_records = read_jsonl(Path(summary["audit_events_path"]))
        assert_true(len(approval_records) == summary["records"]["approval_decisions"], "Approval JSONL count should match summary")
        assert_true(len(audit_records) == summary["records"]["audit_events"], "Audit JSONL count should match summary")


def main() -> int:
    tests = [
        test_replay_result_export_creates_files,
        test_redaction_applied_to_sensitive_values,
        test_external_execution_zero_allows_export,
        test_external_execution_nonzero_rejected,
        test_dry_run_export_creates_no_files,
        test_jsonl_record_counts,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All persistent audit export tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

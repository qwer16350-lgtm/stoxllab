from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase42_supervised_private_test_session import build_phase42_supervised_private_test_session_preflight


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase42_default_blocked_no_runtime() -> None:
    report = build_phase42_supervised_private_test_session_preflight()
    assert_true(report["default_blocked"] is True, "Default blocked")
    assert_true("max_reply_count_required" in report["blocked_reasons"], "Max count required")
    assert_true("timeout_required" in report["blocked_reasons"], "Timeout required")
    assert_true("cooldown_required" in report["blocked_reasons"], "Cooldown required")
    assert_true(report["llm_called"] is False, "No LLM")
    assert_true(report["rag_called"] is False, "No RAG")
    assert_true(report["external_execution"] is False, "No external")
    assert_true(report["actual_runtime_executed"] is False, "No runtime")


def main() -> int:
    test_phase42_default_blocked_no_runtime()
    print("PASS test_phase42_default_blocked_no_runtime")
    print("All Phase 42 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

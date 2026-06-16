from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40_private_test_runtime_plan import build_phase40_private_test_runtime_plan, render_phase40_private_test_runtime_plan_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40b_runtime_plan_is_no_live_execution() -> None:
    report = build_phase40_private_test_runtime_plan()
    assert_true(report["runtime_scope"] == "private_test_only", "Private-test only")
    assert_true(report["live_runtime_started"] is False, "No runtime")
    assert_true(report["discord_gateway_connected"] is False, "No gateway")
    assert_true(report["discord_api_send_called"] is False, "No send API")
    assert_true(report["discord_message_sent"] is False, "No message sent")
    assert_true(report["ready_for_runtime_dry_replay"] is True, "Ready for dry replay")
    assert_true(report["ready_for_live_runtime_execution"] is False, "No live execution")


def test_phase40b_planned_guards_include_core_runtime_guards() -> None:
    guards = set(build_phase40_private_test_runtime_plan()["planned_runtime_guards"])
    for guard in ("private_test_channel_id_only", "self_message_guard", "bot_message_guard", "duplicate_message_id_guard", "one_reply_per_human_message", "no_public_team_send", "no_unattended_auto_reply", "no_llm_by_default", "no_rag_by_default"):
        assert_true(guard in guards, f"{guard} present")


def test_phase40b_no_sensitive_values_and_markdown() -> None:
    report = build_phase40_private_test_runtime_plan()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "i_approve_" not in text, "No secrets")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Phase 40B" in render_phase40_private_test_runtime_plan_markdown(report), "Markdown")


def main() -> int:
    for test in (test_phase40b_runtime_plan_is_no_live_execution, test_phase40b_planned_guards_include_core_runtime_guards, test_phase40b_no_sensitive_values_and_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40B private-test runtime plan tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase50_automation_roadmap import build_phase50_automation_roadmap


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase50_roadmap_contract() -> None:
    report = build_phase50_automation_roadmap()
    assert_true(report["report_type"] == "phase50_automation_roadmap", "Report type")
    assert_true(report["remaining_safe_mega_bundles"] == 7, "Bundles")
    assert_true(report["remaining_manual_gates"] == 5, "Gates")
    assert_true(report["next_phase"] == "phase51_52_continuous_readonly_runtime_foundation", "Next")
    assert_true(report["final_manual_gate"] == "limited_production_unattended_launch", "Final")
    assert_true(report["automatic_retry_allowed_now"] is False, "No retry")
    assert_true(report["automatic_discord_send_allowed_now"] is False, "No Discord")
    assert_true(report["production_unattended_allowed_now"] is False, "No production")


def test_phase50_roadmap_steps_and_no_execution() -> None:
    report = build_phase50_automation_roadmap()
    assert_true(len(report["roadmap"]) == 11, "Roadmap entries")
    assert_true(report["roadmap"][0] == "Phase51/52: Continuous read-only runtime + review packet base", "First")
    assert_true(report["roadmap"][-1] == "Final Manual Gate: limited production unattended launch", "Last")
    for key in ("scheduler_cron_live_execution", "llm_api_call_attempted", "llm_api_called", "discord_api_send_called", "discord_message_sent", "rag_called", "embedding_api_called", "vector_index_created", "external_execution"):
        assert_true(report[key] is False, key)


def test_phase50_roadmap_no_sensitive_values() -> None:
    text = json.dumps(build_phase50_automation_roadmap(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase50_roadmap_contract, test_phase50_roadmap_steps_and_no_execution, test_phase50_roadmap_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase50 automation roadmap tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase51_readonly_event_schema import build_phase51_readonly_event_schema, normalize_readonly_event


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase51_schema_contract() -> None:
    report = build_phase51_readonly_event_schema()
    assert_true(report["report_type"] == "phase51_readonly_event_schema", "Report type")
    assert_true(report["event_id_present"] is True, "Event id presence")
    assert_true(report["source"] == "discord", "Source")
    assert_true(report["channel_scope"] == "private_test", "Scope")
    assert_true(report["channel_risk"] == "private_test", "Risk")
    assert_true(report["author_kind"] == "human", "Author")
    assert_true(report["message_kind"] == "normal", "Kind")
    assert_true(report["content_present"] is True, "Content presence")
    assert_true(report["raw_content_logged"] is False, "No raw content")
    assert_true(report["raw_discord_ids_logged"] is False, "No raw IDs")


def test_phase51_schema_classification() -> None:
    event = normalize_readonly_event(
        {
            "event_ref": "evt_public_synthetic",
            "source": "discord",
            "channel_scope": "public",
            "author_kind": "bot",
            "content": "/status",
        }
    )
    assert_true(event["channel_risk"] == "public_high", "Public high")
    assert_true(event["author_kind"] == "bot", "Bot")
    assert_true(event["message_kind"] == "operator_command", "Command")
    assert_true(event["raw_content_logged"] is False, "No raw")


def test_phase51_schema_no_sensitive_values() -> None:
    text = json.dumps(build_phase51_readonly_event_schema(), ensure_ascii=False).lower()
    assert_true("please review" not in text, "No raw content")
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [test_phase51_schema_contract, test_phase51_schema_classification, test_phase51_schema_no_sensitive_values]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase51 read-only event schema tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

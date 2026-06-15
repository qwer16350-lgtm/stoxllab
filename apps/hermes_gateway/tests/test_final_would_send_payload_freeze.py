from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from final_would_send_payload_freeze import build_final_would_send_payload_freeze, render_final_would_send_payload_freeze_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def test_payload_freeze_success_fixture() -> None:
    report = build_final_would_send_payload_freeze()
    assert_true(report["payload_freeze_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase38a_contract_available"] is True, "38A source")
    assert_true(report["source_phase37a_review_packet_available"] is True, "37A source")
    assert_true(report["would_send_payload_frozen"] is True, "Frozen")
    assert_true(report["safe_disclaimer_present"] is True, "Disclaimer")


def test_payload_freeze_no_full_content_or_send() -> None:
    report = build_final_would_send_payload_freeze()
    for key in ("would_send_external_action_claim", "would_send_full_content_included", "payload_contains_api_key", "payload_contains_token", "payload_contains_raw_discord_id", "payload_contains_private_channel_id_value", "payload_contains_approval_phrase_value", "discord_api_send_called", "discord_message_sent", "ready_for_actual_private_test_send", "ready_for_discord_send"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message count")
    assert_true("No external action has been taken." in report["payload_preview"], "Safe disclaimer text")


def test_payload_freeze_blocks_bad_sources() -> None:
    assert_raises(lambda: build_final_would_send_payload_freeze(contract={"contract_available": False}), "Missing contract should fail")
    assert_raises(lambda: build_final_would_send_payload_freeze(review_packet={"review_packet_available": False}), "Missing review should fail")


def test_payload_freeze_no_sensitive_values_and_markdown() -> None:
    report = build_final_would_send_payload_freeze()
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "bearer " not in text and "token=" not in text, "No secrets")
    assert_true("i_approve_" not in text, "No approval")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Final Would-send Payload Freeze" in render_final_would_send_payload_freeze_markdown(report), "Markdown")


def main() -> int:
    tests = [test_payload_freeze_success_fixture, test_payload_freeze_no_full_content_or_send, test_payload_freeze_blocks_bad_sources, test_payload_freeze_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All final would-send payload freeze tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

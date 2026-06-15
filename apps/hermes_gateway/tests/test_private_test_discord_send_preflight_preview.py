from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from private_test_discord_send_preflight_preview import build_private_test_discord_send_preflight_preview, render_private_test_discord_send_preflight_preview_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_send_preflight_success_fixture() -> None:
    report = build_private_test_discord_send_preflight_preview(env={})
    assert_true(report["send_preflight_preview_available"] is True, "Available")
    assert_true(report["report_only"] is True, "Report only")
    assert_true(report["source_phase37a_review_packet_available"] is True, "37A source")
    assert_true(report["private_test_scope_only"] is True, "Private test only")
    assert_true(report["would_send_preview_created"] is True, "Preview created")


def test_send_preflight_presence_booleans_and_blocking() -> None:
    report = build_private_test_discord_send_preflight_preview(env={"DISCORD_BOT_TOKEN": "secret-token", "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678"})
    assert_true(report["discord_token_present"] is True, "Token present boolean")
    assert_true(report["private_test_channel_id_present"] is True, "Channel present boolean")
    assert_true(report["discord_token_value_logged"] is False, "Token not logged")
    assert_true(report["private_test_channel_id_value_logged"] is False, "Channel not logged")
    assert_true(report["public_channel_send_allowed"] is False, "No public send")
    assert_true(report["team_channel_send_allowed"] is False, "No team send")
    assert_true(report["discord_api_send_allowed"] is False, "Send not allowed")
    assert_true(report["discord_api_send_called"] is False, "No send call")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["ready_for_actual_private_test_send"] is False, "No actual readiness")
    assert_true(report["ready_for_discord_send"] is False, "No send readiness")


def test_send_preflight_no_sensitive_values_and_markdown() -> None:
    report = build_private_test_discord_send_preflight_preview(env={"DISCORD_BOT_TOKEN": "secret-token", "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "123456789012345678"})
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("secret-token" not in text, "Token value not logged")
    assert_true("123456789012345678" not in text, "Channel id not logged")
    assert_true("i_approve_" not in text, "No approval phrase")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")
    assert_true("Discord Send Preflight Preview" in render_private_test_discord_send_preflight_preview_markdown(report), "Markdown")


def main() -> int:
    tests = [test_send_preflight_success_fixture, test_send_preflight_presence_booleans_and_blocking, test_send_preflight_no_sensitive_values_and_markdown]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private-test Discord send preflight preview tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

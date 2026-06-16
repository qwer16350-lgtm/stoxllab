from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40v_capture_review_closeout import build_phase40v_capture_review_closeout, classify_capture_review


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_valid_no_event_timeout_capture_accepted() -> None:
    report = build_phase40v_capture_review_closeout()
    assert_true(report["capture_classification"] == "valid_no_event_timeout_capture", "No-event timeout valid")
    assert_true(report["capture_valid"] is True, "Capture valid")


def test_valid_private_test_human_capture_accepted() -> None:
    classification = classify_capture_review({"channel_scope": "private_test_only", "author_type": "human"})
    assert_true(classification == "valid_private_test_human_message_capture", "Human capture valid")


def test_invalid_capture_classifications() -> None:
    assert_true(classify_capture_review({"raw_content_logged": True}) == "invalid_raw_content_capture", "Raw content blocked")
    assert_true(classify_capture_review({"raw_discord_ids_logged": True}) == "invalid_raw_discord_id_capture", "Raw IDs blocked")
    assert_true(classify_capture_review({"secret_values_logged": True}) == "invalid_secret_capture", "Secrets blocked")
    assert_true(classify_capture_review({"channel_scope": "public"}) == "invalid_public_team_capture", "Public blocked")
    assert_true(classify_capture_review({"channel_scope": "team"}) == "invalid_public_team_capture", "Team blocked")


def test_no_send_or_external() -> None:
    report = build_phase40v_capture_review_closeout()
    for key in ("discord_api_send_called", "discord_message_sent", "llm_called", "rag_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No messages")


def main() -> int:
    for test in (
        test_valid_no_event_timeout_capture_accepted,
        test_valid_private_test_human_capture_accepted,
        test_invalid_capture_classifications,
        test_no_send_or_external,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40V capture review tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

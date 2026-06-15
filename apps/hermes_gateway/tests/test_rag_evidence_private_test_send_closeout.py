"""Phase 34J-2 private-test send closeout tests."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from rag_evidence_private_test_send_closeout import EMBEDDED_SANITIZED_SEND_FIXTURE, build_rag_evidence_private_test_send_closeout, render_rag_evidence_private_test_send_closeout_markdown


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_raises(func, message: str) -> None:
    try:
        func()
    except ValueError:
        return
    raise AssertionError(message)


def fixture() -> dict:
    return copy.deepcopy(EMBEDDED_SANITIZED_SEND_FIXTURE)


def test_send_closeout_observes_exactly_one_prior_send() -> None:
    report = build_rag_evidence_private_test_send_closeout()
    assert_true(report["actual_private_test_send_observed"] is True, "Prior send should be observed")
    assert_true(report["discord_api_send_called_count"] == 1, "Send call count should be one")
    assert_true(report["discord_message_sent_count"] == 1, "Message sent count should be one")


def test_send_closeout_does_not_call_discord_api_again() -> None:
    report = build_rag_evidence_private_test_send_closeout()
    assert_true(report["additional_discord_send"] is False, "No additional send")


def test_send_closeout_fails_if_message_sent_count_not_one() -> None:
    bad = fixture()
    bad["message_sent_count"] = 2
    assert_raises(lambda: build_rag_evidence_private_test_send_closeout(bad), "Count not one should fail")


def test_send_closeout_fails_if_channel_scope_wrong() -> None:
    bad = fixture()
    bad["sent_channel_scope"] = "marketing"
    assert_raises(lambda: build_rag_evidence_private_test_send_closeout(bad), "Wrong channel scope should fail")


def test_send_closeout_fails_if_additional_send_true() -> None:
    report = build_rag_evidence_private_test_send_closeout()
    bad = dict(report)
    bad["additional_discord_send"] = True
    assert_raises(lambda: build_rag_evidence_private_test_send_closeout_safe_proxy(bad), "Additional send should fail")


def build_rag_evidence_private_test_send_closeout_safe_proxy(report: dict) -> None:
    from rag_evidence_private_test_send_closeout import assert_rag_evidence_private_test_send_closeout_safe

    assert_rag_evidence_private_test_send_closeout_safe(report)


def test_self_loop_and_duplicate_audit_pass() -> None:
    audit = build_rag_evidence_private_test_send_closeout()["self_loop_audit"]
    assert_true(audit["self_message_reply_attempted"] is False, "Self message should not reply")
    assert_true(audit["bot_message_reply_attempted"] is False, "Bot message should not reply")
    assert_true(audit["duplicate_send_blocked"] is True, "Duplicate should be blocked")


def test_no_sensitive_values() -> None:
    text = json.dumps(build_rag_evidence_private_test_send_closeout(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "bearer " not in text, "Secret markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_markdown_render() -> None:
    markdown = render_rag_evidence_private_test_send_closeout_markdown(build_rag_evidence_private_test_send_closeout())
    assert_true("Private-test Send Closeout" in markdown, "Markdown should render")


def main() -> int:
    tests = [
        test_send_closeout_observes_exactly_one_prior_send,
        test_send_closeout_does_not_call_discord_api_again,
        test_send_closeout_fails_if_message_sent_count_not_one,
        test_send_closeout_fails_if_channel_scope_wrong,
        test_send_closeout_fails_if_additional_send_true,
        test_self_loop_and_duplicate_audit_pass,
        test_no_sensitive_values,
        test_markdown_render,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG evidence private-test send closeout tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

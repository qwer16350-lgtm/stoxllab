from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40w_synthetic_private_test_replay import build_phase40w_synthetic_private_test_replay


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_synthetic_fixtures_exist_and_are_redacted() -> None:
    report = build_phase40w_synthetic_private_test_replay()
    fixtures = report["fixtures"]
    for name in ("private_test_human", "self_message", "bot_message", "duplicate_message", "public_channel", "team_channel"):
        assert_true(name in fixtures, f"{name} exists")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("raw_content_logged" in text, "Flags present")
    assert_true("sk-" not in text and "xoxb-" not in text and not LONG_ID_RE.search(text), "No sensitive values")


def test_no_send_llm_rag_external() -> None:
    report = build_phase40w_synthetic_private_test_replay()
    for key in ("discord_api_send_called", "discord_message_sent", "llm_called", "rag_called", "embedding_api_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No messages")


def main() -> int:
    for test in (test_synthetic_fixtures_exist_and_are_redacted, test_no_send_llm_rag_external):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40W synthetic replay tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

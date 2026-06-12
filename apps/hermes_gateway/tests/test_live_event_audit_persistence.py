"""Phase 30 live event audit persistence tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_live_event_audit_persistence.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_audit_persistence import (
    append_live_event_audit_record,
    assert_audit_record_safe,
    build_daily_live_event_manifest,
    build_live_event_audit_record,
    build_sample_visibility_event,
    redact_content_preview,
)


ROOT = APP_DIR.parents[1]
TEST_ROOT = ROOT / "logs" / "hermes_gateway_test" / "phase30_audit"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def record() -> dict:
    return build_live_event_audit_record(
        build_sample_visibility_event(),
        content="Line one\napi_key=abc123 123456789012345678 " + "x" * 200,
    )


def test_accepted_visibility_event_to_audit_record() -> None:
    item = record()
    assert_true(item["record_type"] == "live_event_audit_record", "Audit record type should match")
    assert_true(item["decision"] == "accepted_mapped_channel", "Decision should be preserved")


def test_guild_and_channel_flags_preserved() -> None:
    item = record()
    assert_true(item["guild_configured"] is True, "guild_configured should remain true")
    assert_true(item["channel_mapped"] is True, "channel_mapped should remain true")


def test_content_preview_max_120() -> None:
    assert_true(len(record()["content_preview"]) <= 120, "Content preview should be capped at 120 chars")


def test_secret_like_value_redacted() -> None:
    assert_true("abc123" not in record()["content_preview"], "Secret-like values should be redacted")


def test_discord_like_id_redacted() -> None:
    text = json.dumps(record(), ensure_ascii=False)
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be redacted")


def test_jsonl_append() -> None:
    item = record()
    path = append_live_event_audit_record(item, root=TEST_ROOT)
    assert_true(path.exists(), "Audit jsonl should be created")
    data = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert_true(data["message_sent"] is False, "Audit jsonl should preserve message_sent=false")


def test_daily_manifest_created() -> None:
    item = record()
    append_live_event_audit_record(item, root=TEST_ROOT)
    manifest = build_daily_live_event_manifest(root=TEST_ROOT, date=item["created_at"])
    assert_true(manifest["manifest_type"] == "live_event_daily_manifest", "Manifest should be created")
    assert_true(manifest["record_count"] >= 1, "Manifest should count records")


def test_execution_flags_false() -> None:
    item = record()
    assert_true(item["message_sent"] is False, "message_sent should be false")
    assert_true(item["external_execution"] is False, "external_execution should be false")
    assert_true(item["llm_called"] is False, "llm_called should be false")
    assert_true(item["rag_called"] is False, "rag_called should be false")


def test_raw_token_and_id_not_logged() -> None:
    item = record()
    assert_audit_record_safe(item)
    text = json.dumps(item, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")


def test_empty_preview() -> None:
    assert_true(redact_content_preview(None) == "", "Missing content should produce empty preview")


def main() -> int:
    tests = [
        test_accepted_visibility_event_to_audit_record,
        test_guild_and_channel_flags_preserved,
        test_content_preview_max_120,
        test_secret_like_value_redacted,
        test_discord_like_id_redacted,
        test_jsonl_append,
        test_daily_manifest_created,
        test_execution_flags_false,
        test_raw_token_and_id_not_logged,
        test_empty_preview,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All live event audit persistence tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

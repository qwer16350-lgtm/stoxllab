from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40t_readonly_capture_writer import (
    CAPTURE_SCHEMA_VERSION,
    build_redacted_capture_payload,
    sanitize_capture_event,
    validate_capture_root,
    write_redacted_capture_file,
)


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


def test_capture_writer_redacts_to_hashes_only() -> None:
    payload = build_redacted_capture_payload(
        [
            {
                "event_id": "123456789012345678",
                "message_id": "234567890123456789",
                "channel_scope": "private_test",
                "author_kind": "human",
                "decision": "capture_only",
            }
        ]
    )
    text = json.dumps(payload, ensure_ascii=False)
    assert_true(payload["capture_schema_version"] == CAPTURE_SCHEMA_VERSION, "Schema version")
    assert_true(payload["events"][0]["event_id_hash"], "Event hash")
    assert_true("123456789012345678" not in text, "Raw event id absent")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw long IDs")
    assert_true(payload["safety"]["message_sent_count"] == 0, "No send count")


def test_capture_writer_rejects_forbidden_fields() -> None:
    for field in ("raw_message_content", "content", "author_id", "channel_id", "guild_id", "discord_token", "api_key", "approval_phrase"):
        assert_raises(lambda selected=field: sanitize_capture_event({selected: "secret"}), f"{field} rejected")


def test_capture_root_must_be_local_ignored_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ok, _, _ = validate_capture_root(None, root=tmp)
        bad, reason, _ = validate_capture_root(Path(tmp) / "exports", root=tmp)
        assert_true(ok is True, "Default root ok")
        assert_true(bad is False, "Exports root blocked")
        assert_true(reason == "capture_root_not_local_ignored_path", "Reason")


def test_write_redacted_capture_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = write_redacted_capture_file(
            [{"event_id": "event-a", "message_id": "message-a", "channel_scope": "private_test", "author_kind": "human"}],
            root=tmp,
        )
        assert_true(result["capture_file_written"] is True, "Written")
        path = Path(result["capture_file_path"])
        assert_true(path.exists(), "Path exists")
        text = path.read_text(encoding="utf-8")
        assert_true("event-a" not in text and "message-a" not in text, "Raw ids absent")
        assert_true("raw_message_content" not in text, "Raw content absent")


def main() -> int:
    for test in (
        test_capture_writer_redacts_to_hashes_only,
        test_capture_writer_rejects_forbidden_fields,
        test_capture_root_must_be_local_ignored_path,
        test_write_redacted_capture_file,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40T capture writer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

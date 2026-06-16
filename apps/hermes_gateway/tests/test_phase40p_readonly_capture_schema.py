from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40p_readonly_capture_schema import build_phase40p_readonly_capture_schema, render_phase40p_readonly_capture_schema_markdown


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40p_schema_excludes_raw_values() -> None:
    report = build_phase40p_readonly_capture_schema()
    allowed = set(report["allowed_capture_fields"])
    forbidden = set(report["forbidden_capture_fields"])
    assert_true(report["capture_schema_available"] is True, "Schema available")
    assert_true(report["capture_file_required_for_closeout"] is True, "File required")
    assert_true(report["capture_file_written_by_codex"] is False, "Codex does not write")
    assert_true(allowed.isdisjoint(forbidden), "Allowed excludes forbidden")
    for field in ("raw_message_content", "raw_author_id", "raw_channel_id", "discord_token", "api_key", "approval_phrase"):
        assert_true(field in forbidden, f"{field} forbidden")


def test_phase40p_no_logging_or_send() -> None:
    report = build_phase40p_readonly_capture_schema()
    for key in ("raw_content_logged", "raw_discord_ids_logged", "secret_values_logged", "live_runtime_started", "discord_gateway_connected", "discord_api_send_called", "discord_message_sent", "llm_api_call_attempted", "rag_called", "external_execution"):
        assert_true(report[key] is False, f"{key} false")
    assert_true(report["message_sent_count"] == 0, "No message")


def test_phase40p_markdown() -> None:
    assert_true("Phase 40P" in render_phase40p_readonly_capture_schema_markdown(build_phase40p_readonly_capture_schema()), "Markdown")


def main() -> int:
    for test in (test_phase40p_schema_excludes_raw_values, test_phase40p_no_logging_or_send, test_phase40p_markdown):
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 40P capture schema tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

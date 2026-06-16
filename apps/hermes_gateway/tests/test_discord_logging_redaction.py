from __future__ import annotations

import io
import logging
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from discord_logging_redaction import DiscordLogRedactionFilter, install_discord_logging_redaction, redact_discord_log_text


SESSION_VALUE = "abc123SESSION.secret-value"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_redact_discord_gateway_session_id_text() -> None:
    text = f"discord.gateway INFO Session ID: {SESSION_VALUE} connected"
    redacted = redact_discord_log_text(text)
    assert_true(SESSION_VALUE not in redacted, "Session value removed")
    assert_true("[REDACTED_SESSION_ID]" in redacted, "Session placeholder present")


def test_redact_token_id_and_raw_content_text() -> None:
    text = "token=secret 123456789012345678 raw_content: hello world"
    redacted = redact_discord_log_text(text)
    assert_true("secret" not in redacted, "Token removed")
    assert_true(not LONG_NUMBER_RE.search(redacted), "Raw ID removed")
    assert_true("hello world" not in redacted, "Raw content removed")


def test_logging_filter_does_not_preserve_session_id() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(DiscordLogRedactionFilter())
    logger = logging.getLogger("phase41c_redaction_test")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("discord.gateway Session ID: %s connected", SESSION_VALUE)
    output = stream.getvalue()
    assert_true(SESSION_VALUE not in output, "Session value absent")
    assert_true("[REDACTED_SESSION_ID]" in output, "Session placeholder output")


def test_install_suppresses_discord_gateway_info() -> None:
    install_discord_logging_redaction()
    gateway_logger = logging.getLogger("discord.gateway")
    assert_true(gateway_logger.level >= logging.WARNING, "Gateway INFO suppressed")


def main() -> int:
    tests = [
        test_redact_discord_gateway_session_id_text,
        test_redact_token_id_and_raw_content_text,
        test_logging_filter_does_not_preserve_session_id,
        test_install_suppresses_discord_gateway_info,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Discord logging redaction tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_discord_outbound_guard import HARD_LIMIT, prepare_discord_outbound_messages, send_discord_messages_safely, split_discord_message


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_short_response_single_chunk() -> None:
    result = split_discord_message("짧은 응답", "kasumi")
    assert_true(result["outbound_chunking_used"] is False, "short no chunk")
    assert_true(result["messages"] == ["짧은 응답"], "unchanged")


def test_long_response_chunks_under_hard_limit() -> None:
    result = split_discord_message(("긴 줄입니다.\n" * 500), "meiko")
    assert_true(result["outbound_chunking_used"] is True, "chunked")
    assert_true(1 < result["outbound_chunk_count"] <= 4, "bounded chunks")
    assert_true(all(len(message) <= HARD_LIMIT for message in result["messages"]), "hard limit")
    assert_true(result["messages"][0].startswith("[MEIKO_STOXL] 1/"), "headers")


def test_max_chunk_truncation_is_explicit() -> None:
    result = split_discord_message("x" * 20000, "reze", max_chunk_count=2)
    assert_true(result["outbound_truncated_for_discord"] is True, "truncated")
    assert_true(result["outbound_chunk_count"] == 2, "max chunks")
    assert_true("memory/context" in result["messages"][-1], "explicit notice")


def test_send_discord_messages_safely_reports_partial_failure() -> None:
    sent: list[str] = []

    async def send_one(message: str) -> None:
        if sent:
            raise RuntimeError("message_too_long")
        sent.append(message)

    async def fallback(message: str) -> None:
        sent.append(message)

    result = asyncio.run(send_discord_messages_safely(send_one, ["a", "b"], fallback_send_one=fallback))
    assert_true(result["discord_send_failure_reason"] == "discord_message_too_long", "reason")
    assert_true(result["fallback_short_notice_attempted"] is True, "fallback attempted")
    assert_true(result["fallback_short_notice_sent"] is True, "fallback sent")
    assert_true(result["message_sent_count"] == 1, "partial count")


def main() -> int:
    for test in (
        test_short_response_single_chunk,
        test_long_response_chunks_under_hard_limit,
        test_max_chunk_truncation_is_explicit,
        test_send_discord_messages_safely_reports_partial_failure,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All company agent Discord chunking tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

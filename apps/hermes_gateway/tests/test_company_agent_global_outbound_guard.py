from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import build_company_agent_message_result
from company_discord_outbound_guard import prepare_discord_outbound_messages


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_all_agents_pass_global_outbound_guard_preview() -> None:
    cases = {
        "lucy": ("lucy-검토", "!lucy 문구 검토해줘"),
        "marin": ("marketing-brief", "!marin 인스타 문구 3개"),
        "meiko": ("meiko-검토", "!meiko 일정 리스크 판단"),
        "kasumi": ("kasumi-리서치", "!kasumi 지원사업 후보 찾아줘"),
        "reze": ("reze-전략기획", "!reze 제품 방향 비평"),
    }
    for agent, (channel, message) in cases.items():
        result = build_company_agent_message_result(channel, message, env={"HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED": "false"})
        assert_true(result["selected_agent"] == agent, f"{agent} selected")
        assert_true(result["outbound_guard_applied"] is True, f"{agent} guard")
        assert_true(result["outbound_chunk_count"] >= 1, f"{agent} chunk count")
        assert_true(result["discord_message_sent"] is False, f"{agent} dry no send")


def test_help_agents_short_commands_not_overchunked() -> None:
    for command in ("!agents", "!help"):
        result = build_company_agent_message_result("operation-brief", command)
        assert_true(result["outbound_guard_applied"] is True, f"{command} guard")
        assert_true(result["outbound_chunking_used"] is False, f"{command} short")
        assert_true(result["outbound_chunk_count"] == 1, f"{command} one chunk")


def test_prepare_guard_safety_flags() -> None:
    prepared = prepare_discord_outbound_messages("x" * 3000, "kasumi")
    assert_true(prepared["outbound_guard_applied"] is True, "guard applied")
    assert_true(prepared["discord_api_send_called"] is False, "no send in prepare")
    assert_true(prepared["llm_api_called"] is False, "no LLM")
    assert_true(prepared["rag_called"] is False, "no RAG")
    assert_true(prepared["embedding_called"] is False, "no embedding")
    assert_true(prepared["external_execution"] is False, "no external")


def main() -> int:
    for test in (
        test_all_agents_pass_global_outbound_guard_preview,
        test_help_agents_short_commands_not_overchunked,
        test_prepare_guard_safety_flags,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("All company agent global outbound guard tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

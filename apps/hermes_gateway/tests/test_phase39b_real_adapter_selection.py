from __future__ import annotations

import json
import re
import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from actual_private_test_one_shot_send import SendResult, build_actual_private_test_one_shot_send
from actual_private_test_send_safety_gate import EXPECTED_APPROVAL_PHRASE


LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


class FakeRealAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def send_message(self, channel_id: str, content: str) -> SendResult:
        self.calls.append((channel_id, content))
        return SendResult(api_send_called=False, message_sent=False, message_sent_count=0)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _ready_env(**overrides: str) -> dict[str, str]:
    env = {
        "DISCORD_BOT_TOKEN": "token-value",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private-channel-present",
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED": "true",
        "HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE": EXPECTED_APPROVAL_PHRASE,
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION": "true",
        "HERMES_LLM_DISCORD_SEND_ENABLED": "false",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
        "HERMES_LLM_RAG_ENABLED": "false",
        "HERMES_RAG_LLM_REPLY_ENABLED": "false",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_DISCORD_LLM_ENABLED": "false",
    }
    env.update(overrides)
    return env


def test_real_env_false_selects_mock() -> None:
    adapter = FakeRealAdapter()
    report = build_actual_private_test_one_shot_send(
        allow_flag_present=True,
        execute_flag_present=True,
        send_adapter=adapter,
        env=_ready_env(HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION="false"),
    )
    assert_true(report["actual_execution_adapter"] == "mock", "Real env false selects mock")
    assert_true(report["real_adapter_selected"] is False, "Real adapter not selected")
    assert_true(report["real_adapter_called"] is False, "Adapter not called")
    assert_true(len(adapter.calls) == 0, "No fake adapter call")
    assert_true(report["message_sent_count"] == 0, "No message count")


def test_real_env_true_selects_injected_real_adapter_without_discord_send() -> None:
    adapter = FakeRealAdapter()
    report = build_actual_private_test_one_shot_send(
        allow_flag_present=True,
        execute_flag_present=True,
        send_adapter=adapter,
        env=_ready_env(),
    )
    assert_true(report["version"] == "phase39b_manual_actual_private_test_one_shot_send", "Real version")
    assert_true(report["mode"] == "phase39b_actual_send_execution", "Execution mode")
    assert_true(report["actual_execution_adapter"] == "real", "Real adapter selected")
    assert_true(report["real_discord_send_execution_env_enabled"] is True, "Real env reflected")
    assert_true(report["real_adapter_selected"] is True, "Real selected")
    assert_true(report["real_adapter_injected_for_test"] is True, "Injected for test")
    assert_true(report["real_adapter_called"] is True, "Fake real adapter called")
    assert_true(len(adapter.calls) == 1, "One fake call")
    assert_true(report["discord_api_send_called"] is False, "No actual Discord API send")
    assert_true(report["discord_message_sent"] is False, "No Discord message sent")
    assert_true(report["message_sent_count"] == 0, "Message count 0")
    assert_true(report["actual_private_test_send_executed"] is False, "No actual send")
    assert_true(report["ready_for_phase39c_send_closeout"] is False, "No closeout without send")


def test_real_adapter_requires_exact_approval_phrase() -> None:
    adapter = FakeRealAdapter()
    report = build_actual_private_test_one_shot_send(
        allow_flag_present=True,
        execute_flag_present=True,
        send_adapter=adapter,
        env=_ready_env(HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE="wrong"),
    )
    assert_true(report["approval_phrase_exact_match"] is False, "Wrong phrase false")
    assert_true(report["real_adapter_selected"] is False, "No real adapter")
    assert_true(report["real_adapter_called"] is False, "No adapter call")
    assert_true(report["blocked"] is True, "Blocked")


def test_real_adapter_requires_token_channel_and_private_reply_mode() -> None:
    for key, reason in (
        ("DISCORD_BOT_TOKEN", "discord_token_missing"),
        ("HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID", "private_test_channel_id_missing"),
        ("HERMES_DISCORD_REPLY_MODE", "reply_mode_not_private_test_only"),
    ):
        adapter = FakeRealAdapter()
        value = "" if key != "HERMES_DISCORD_REPLY_MODE" else "public"
        report = build_actual_private_test_one_shot_send(
            allow_flag_present=True,
            execute_flag_present=True,
            send_adapter=adapter,
            env=_ready_env(**{key: value}),
        )
        assert_true(reason in report["blocked_reasons"], f"{reason} should block")
        assert_true(report["real_adapter_selected"] is False, f"{key} should not select real")
        assert_true(report["real_adapter_called"] is False, f"{key} should not call adapter")


def test_real_adapter_blocks_llm_rag_embedding_external_flags() -> None:
    for key in (
        "HERMES_LLM_DISCORD_SEND_ENABLED",
        "HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED",
        "HERMES_DISCORD_RAG_ENABLED",
        "HERMES_LLM_RAG_ENABLED",
        "HERMES_RAG_LLM_REPLY_ENABLED",
        "HERMES_DISCORD_EXTERNAL_EXECUTION",
        "HERMES_DISCORD_LLM_ENABLED",
    ):
        adapter = FakeRealAdapter()
        report = build_actual_private_test_one_shot_send(
            allow_flag_present=True,
            execute_flag_present=True,
            send_adapter=adapter,
            env=_ready_env(**{key: "true"}),
        )
        assert_true(report["runtime_safety_flags_disabled"] is False, f"{key} should disable runtime safety")
        assert_true(f"unsafe_runtime_flag_enabled:{key}" in report["blocked_reasons"], f"{key} blocked reason")
        assert_true(report["real_adapter_selected"] is False, f"{key} should not select real")
        assert_true(report["real_adapter_called"] is False, f"{key} should not call adapter")


def test_real_adapter_selection_no_sensitive_values() -> None:
    report = build_actual_private_test_one_shot_send(
        allow_flag_present=True,
        execute_flag_present=True,
        send_adapter=FakeRealAdapter(),
        env=_ready_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID="123456789012345678"),
    )
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("token-value" not in text, "Token value hidden")
    assert_true("123456789012345678" not in text, "Channel value hidden")
    assert_true(EXPECTED_APPROVAL_PHRASE.lower() not in text, "Approval phrase hidden")
    assert_true("sk-" not in text, "No API key")
    assert_true(not LONG_NUMBER_RE.search(text), "No raw IDs")


def main() -> int:
    tests = [
        test_real_env_false_selects_mock,
        test_real_env_true_selects_injected_real_adapter_without_discord_send,
        test_real_adapter_requires_exact_approval_phrase,
        test_real_adapter_requires_token_channel_and_private_reply_mode,
        test_real_adapter_blocks_llm_rag_embedding_external_flags,
        test_real_adapter_selection_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All Phase 39B real adapter selection tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

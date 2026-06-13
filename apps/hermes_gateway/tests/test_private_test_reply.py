"""Phase 31B private test channel reply tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_private_test_reply.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from agent_placeholder_response import build_agent_placeholder_response
from discord_readonly_runtime import build_private_test_reply_runtime_preflight, build_ready_visibility, should_skip_private_test_reply_event
from discord_safety_wrapper import is_outgoing_action_allowed
from live_event_audit_persistence import build_live_event_audit_record, build_sample_visibility_event
from live_event_routing_report import build_live_event_routing_report
from private_test_reply import (
    assert_private_test_reply_payload_safe,
    build_private_test_reply_audit,
    build_private_test_reply_payload,
    build_private_test_reply_policy,
    build_private_test_reply_report,
    render_private_test_reply_message,
    send_private_test_reply_only,
)


ROOT = APP_DIR.parents[1]
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")
FORBIDDEN_RUNTIME_SNIPPETS = [".reply(", "add_reaction", "create_channel", "create_role"]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def allowed_env(**overrides: object) -> dict[str, object]:
    env: dict[str, object] = {
        "HERMES_DISCORD_SEND_MESSAGES": "true",
        "HERMES_DISCORD_PRIVATE_TEST_REPLY": "true",
        "HERMES_DISCORD_REPLY_MODE": "private_test_only",
        "HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID": "private_test_channel",
        "HERMES_DISCORD_EXTERNAL_EXECUTION": "false",
        "HERMES_DISCORD_LLM_ENABLED": "false",
        "HERMES_DISCORD_RAG_ENABLED": "false",
    }
    env.update(overrides)
    return env


def private_event(channel_id: str = "private_test_channel") -> dict[str, object]:
    return {
        "event_id": "event_redacted_0000",
        "channel_id": channel_id,
        "channel_name": "private-test",
    }


def private_bot_event(channel_id: str = "private_test_channel") -> dict[str, object]:
    event = private_event(channel_id)
    event["author"] = {"id": "bot_user", "bot": True}
    event["author_is_bot"] = True
    return event


def public_mapped_event() -> dict[str, object]:
    return {
        "event_id": "event_redacted_0000",
        "channel_id": "marketing_channel",
        "channel_name": "marketing-brief",
    }


def placeholder_response() -> dict:
    visibility = build_sample_visibility_event()
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="private test message")
    routing = build_live_event_routing_report(audit)
    return build_agent_placeholder_response(audit, routing)


def decision_reason(env: dict[str, object], channel_id: str = "private_test_channel", response: dict | None = None) -> str:
    payload = build_private_test_reply_payload(private_event(channel_id), response or placeholder_response(), build_private_test_reply_policy(env))
    return payload["decision"]["reason"]


def test_default_policy_disabled() -> None:
    policy = build_private_test_reply_policy({})
    payload = build_private_test_reply_payload(private_event(), placeholder_response(), policy)
    assert_true(payload["will_send"] is False, "Default private test reply policy should be disabled")
    assert_true(payload["decision"]["reason"] == "send_messages_disabled", "Default block should be send disabled")


def test_send_messages_false_blocked() -> None:
    assert_true(decision_reason(allowed_env(HERMES_DISCORD_SEND_MESSAGES="false")) == "send_messages_disabled", "send_messages=false should block")


def test_private_flag_false_blocked() -> None:
    assert_true(
        decision_reason(allowed_env(HERMES_DISCORD_PRIVATE_TEST_REPLY="false")) == "private_test_reply_disabled",
        "private flag false should block",
    )


def test_reply_mode_not_private_test_only_blocked() -> None:
    assert_true(
        decision_reason(allowed_env(HERMES_DISCORD_REPLY_MODE="disabled")) == "reply_mode_not_private_test_only",
        "reply mode mismatch should block",
    )


def test_no_channel_id_blocked() -> None:
    assert_true(
        decision_reason(allowed_env(HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID="")) == "private_test_channel_id_missing",
        "missing private channel id should block",
    )


def test_channel_mismatch_blocked() -> None:
    assert_true(decision_reason(allowed_env(), channel_id="other_channel") == "channel_not_private_test", "channel mismatch should block")


def test_self_message_policy_blocked() -> None:
    payload = build_private_test_reply_payload(private_bot_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_true(payload["will_send"] is False, "Self/bot message should never be allowed")
    assert_true(payload["decision"]["reason"] == "self_message", "Self/bot message should use self_message reason")


def test_private_test_channel_name_match_but_id_mismatch_blocked() -> None:
    event = {"event_id": "event_redacted_0000", "channel_id": "other_channel", "channel_name": "hermes-private-test"}
    payload = build_private_test_reply_payload(event, placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_true(payload["decision"]["reason"] == "channel_not_private_test", "Channel name must not override ID mismatch")
    assert_true(payload["decision"]["channel_is_private_test"] is False, "ID mismatch should not be private test")


def test_llm_rag_external_true_blocked() -> None:
    assert_true(decision_reason(allowed_env(HERMES_DISCORD_LLM_ENABLED="true")) == "llm_enabled_blocked", "LLM true should block")
    assert_true(decision_reason(allowed_env(HERMES_DISCORD_RAG_ENABLED="true")) == "rag_enabled_blocked", "RAG true should block")
    assert_true(
        decision_reason(allowed_env(HERMES_DISCORD_EXTERNAL_EXECUTION="true")) == "external_execution_blocked",
        "external true should block",
    )


def test_non_placeholder_source_blocked() -> None:
    bad_response = {"response_type": "freeform_llm_response"}
    assert_true(
        decision_reason(allowed_env(), response=bad_response) == "message_source_not_agent_placeholder_response",
        "Only agent placeholder response source should be allowed",
    )


def test_all_conditions_true_allowed() -> None:
    payload = build_private_test_reply_payload(private_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_true(payload["will_send"] is True, "All private test reply gates should allow would-send")
    assert_true(payload["decision"]["reason"] == "private_test_reply_allowed", "Allowed reason should be explicit")


def test_private_test_runtime_preflight_all_flags_true_passes() -> None:
    env = allowed_env(token_present=True)
    preflight = build_private_test_reply_runtime_preflight(ROOT, env)
    assert_true(preflight["ready"] is True, "Private test runtime preflight should pass when all gates are true")
    assert_true(preflight["blocked"] is False, "Private test runtime preflight should not be blocked")


def test_private_test_runtime_preflight_requires_channel_id() -> None:
    env = allowed_env(token_present=True, HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID="")
    preflight = build_private_test_reply_runtime_preflight(ROOT, env)
    assert_true(preflight["ready"] is False, "Missing private channel id should block")
    assert_true(preflight["reason"] == "private_test_reply_preflight_failed:private_test_channel_id_present", "Missing channel reason should be explicit")


def test_private_test_runtime_preflight_requires_reply_mode() -> None:
    env = allowed_env(token_present=True, HERMES_DISCORD_REPLY_MODE="disabled")
    preflight = build_private_test_reply_runtime_preflight(ROOT, env)
    assert_true(preflight["ready"] is False, "Wrong reply mode should block")
    assert_true(preflight["reason"] == "private_test_reply_preflight_failed:reply_mode_private_test_only", "Reply mode reason should be explicit")


def test_private_test_runtime_preflight_blocks_llm_rag_external() -> None:
    assert_true(
        build_private_test_reply_runtime_preflight(ROOT, allowed_env(token_present=True, HERMES_DISCORD_LLM_ENABLED="true"))["reason"]
        == "private_test_reply_preflight_failed:llm_disabled",
        "LLM true should block private runtime preflight",
    )
    assert_true(
        build_private_test_reply_runtime_preflight(ROOT, allowed_env(token_present=True, HERMES_DISCORD_RAG_ENABLED="true"))["reason"]
        == "private_test_reply_preflight_failed:rag_disabled",
        "RAG true should block private runtime preflight",
    )
    assert_true(
        build_private_test_reply_runtime_preflight(ROOT, allowed_env(token_present=True, HERMES_DISCORD_EXTERNAL_EXECUTION="true"))["reason"]
        == "private_test_reply_preflight_failed:external_execution_disabled",
        "External execution true should block private runtime preflight",
    )


def test_runtime_skip_self_message_before_private_reply_decision() -> None:
    message = {"id": "msg-1", "channel_id": "private_test_channel", "author": {"id": "bot_user", "bot": True}}
    result = {"visibility_event": {"decision": "ignored_self_message", "author_is_bot": True, "channel_is_private_test": True}}
    assert_true(
        should_skip_private_test_reply_event(message, result, bot_user_id="bot_user") == "self_message",
        "Runtime should skip self messages before private reply decision",
    )


def test_runtime_skip_author_id_matching_bot_user() -> None:
    message = {"id": "msg-2", "channel_id": "private_test_channel", "author": {"id": "bot_user", "bot": False}}
    result = {"visibility_event": {"decision": "accepted_private_test_channel", "author_is_bot": False, "channel_is_private_test": True}}
    assert_true(
        should_skip_private_test_reply_event(message, result, bot_user_id="bot_user") == "self_message",
        "Runtime should skip author id matching the bot user id",
    )


def test_runtime_allows_human_private_test_message_to_reach_payload() -> None:
    message = {"id": "msg-3", "channel_id": "private_test_channel", "author": {"id": "human_user", "bot": False}}
    result = {"visibility_event": {"decision": "accepted_private_test_channel", "author_is_bot": False, "channel_is_private_test": True}}
    assert_true(
        should_skip_private_test_reply_event(message, result, bot_user_id="bot_user") == "",
        "Human private test message should reach payload decision",
    )


def test_duplicate_message_id_skipped() -> None:
    processed = {"msg-4"}
    message = {"id": "msg-4", "channel_id": "private_test_channel", "author": {"id": "human_user", "bot": False}}
    result = {"visibility_event": {"decision": "accepted_private_test_channel", "author_is_bot": False, "channel_is_private_test": True}}
    assert_true(
        should_skip_private_test_reply_event(message, result, bot_user_id="bot_user", processed_message_ids=processed) == "skipped_duplicate_message",
        "Duplicate message id should be skipped",
    )


def test_public_mapped_channel_reply_blocked() -> None:
    payload = build_private_test_reply_payload(public_mapped_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_true(payload["will_send"] is False, "Mapped public work channel must not allow private test reply")
    assert_true(payload["decision"]["reason"] == "channel_not_private_test", "Public mapped channel should fail private channel ID gate")


def test_runtime_ready_visibility_marks_private_test_flags() -> None:
    class Client:
        user = None
        guilds: list[object] = []

    visibility = build_ready_visibility(
        Client(),
        {
            "runtime_mode": "readonly",
            "send_messages": True,
            "private_test_reply_enabled": True,
            "reply_mode": "private_test_only",
            "_private_test_channel_id": "private_test_channel",
            "external_execution": False,
            "llm_enabled": False,
            "rag_enabled": False,
        },
    )
    assert_true(visibility["general_send_disabled"] is True, "General send should still be disabled")
    assert_true(visibility["private_test_reply_enabled"] is True, "Ready visibility should mark private test reply enabled")
    assert_true(visibility["private_test_channel_configured"] is True, "Ready visibility should mark private channel configured")


def test_allowed_decision_message_sent_false_until_runtime_send() -> None:
    payload = build_private_test_reply_payload(private_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_true(payload["message_sent"] is False, "Payload should not mark message_sent before runtime send")
    assert_true(payload["decision"]["message_sent"] is False, "Decision should not mark message_sent before runtime send")


def test_rendered_message_includes_llm_disabled() -> None:
    text = render_private_test_reply_message(placeholder_response())
    assert_true("LLM: disabled" in text, "Rendered private test reply should state LLM disabled")
    assert_true("RAG: disabled" in text, "Rendered private test reply should state RAG disabled")


def test_rendered_message_has_no_raw_token_or_id() -> None:
    response = placeholder_response()
    response["placeholder"]["summary"] = "token=secret 123456789012345678"
    text = render_private_test_reply_message(response)
    assert_true("token=secret" not in text.lower(), "Secret-like values should be redacted")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be redacted")


def test_rendered_message_is_deterministic_placeholder_based() -> None:
    response = placeholder_response()
    assert_true(render_private_test_reply_message(response) == render_private_test_reply_message(response), "Rendered message should be deterministic")
    assert_true("deterministic placeholder / no LLM" in render_private_test_reply_message(response), "Message should declare placeholder mode")


def test_safety_wrapper_only_allows_private_test_reply_send() -> None:
    policy = build_private_test_reply_policy(allowed_env())
    assert_true(is_outgoing_action_allowed("private_test_reply_send", policy) is True, "Private test send should be conditionally allowed")
    assert_true(is_outgoing_action_allowed("message_create", policy) is False, "Regular message_create must remain blocked")


def test_regular_message_create_always_blocked() -> None:
    assert_true(is_outgoing_action_allowed("message_create", build_private_test_reply_policy({})) is False, "message_create should block by default")
    assert_true(is_outgoing_action_allowed("message_create", build_private_test_reply_policy(allowed_env())) is False, "message_create should block even in private mode")


def test_runtime_source_has_no_unrestricted_send_path() -> None:
    runtime_source = (APP_DIR / "discord_readonly_runtime.py").read_text(encoding="utf-8")
    private_source = (APP_DIR / "private_test_reply.py").read_text(encoding="utf-8")
    assert_true(".send(" not in runtime_source, "Runtime source should not contain direct send calls")
    for snippet in FORBIDDEN_RUNTIME_SNIPPETS:
        assert_true(snippet not in runtime_source, f"Runtime source should not contain {snippet}")
        assert_true(snippet not in private_source, f"Private reply source should not contain {snippet}")


def test_blocked_audit_and_sent_audit_possible() -> None:
    blocked_payload = build_private_test_reply_payload(private_event(), placeholder_response(), build_private_test_reply_policy({}))
    blocked_audit = build_private_test_reply_audit(blocked_payload["decision"], sent=False)
    assert_true(blocked_audit["event_type"] == "private_test_reply_blocked", "Blocked audit should be possible")

    allowed_payload = build_private_test_reply_payload(private_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    sent_audit = build_private_test_reply_audit(allowed_payload["decision"], sent=True)
    assert_true(sent_audit["event_type"] == "private_test_reply_sent", "Sent audit should be possible after runtime send")
    assert_true(sent_audit["llm_called"] is False and sent_audit["rag_called"] is False, "Sent audit should keep LLM/RAG false")


class MockChannel:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, content: str) -> None:
        self.sent.append(content)


def test_mock_runtime_send_only_after_allowed_payload() -> None:
    channel = MockChannel()
    policy = build_private_test_reply_policy(allowed_env())
    payload = build_private_test_reply_payload(private_event(), placeholder_response(), policy)
    audit = asyncio.run(send_private_test_reply_only(channel, payload, policy))
    assert_true(audit["message_sent"] is True, "Mock private test channel should receive one send")
    assert_true(len(channel.sent) == 1, "Mock channel should record one sent message")
    assert_true("LLM: disabled" in channel.sent[0], "Sent mock content should be deterministic placeholder text")


def test_report_has_no_raw_token_or_id() -> None:
    report = build_private_test_reply_report(ROOT)
    text = json.dumps(report, ensure_ascii=False)
    assert_true("sk-" not in text.lower() and "xoxb-" not in text.lower() and "mfa." not in text.lower(), "Report should not contain token markers")
    assert_true(not LONG_NUMBER_RE.search(text), "Report should not contain raw Discord-like IDs")
    assert_true(report["message_sent"] is False, "Report should not mark message sent")


def test_payload_safe_assertions() -> None:
    payload = build_private_test_reply_payload(private_event(), placeholder_response(), build_private_test_reply_policy(allowed_env()))
    assert_private_test_reply_payload_safe(payload)
    assert_true(payload["safety_assertions"]["llm_called"] is False, "LLM should remain false")
    assert_true(payload["safety_assertions"]["rag_called"] is False, "RAG should remain false")
    assert_true(payload["safety_assertions"]["external_execution"] is False, "External execution should remain false")


def main() -> int:
    tests = [
        test_default_policy_disabled,
        test_send_messages_false_blocked,
        test_private_flag_false_blocked,
        test_reply_mode_not_private_test_only_blocked,
        test_no_channel_id_blocked,
        test_channel_mismatch_blocked,
        test_self_message_policy_blocked,
        test_private_test_channel_name_match_but_id_mismatch_blocked,
        test_llm_rag_external_true_blocked,
        test_non_placeholder_source_blocked,
        test_all_conditions_true_allowed,
        test_private_test_runtime_preflight_all_flags_true_passes,
        test_private_test_runtime_preflight_requires_channel_id,
        test_private_test_runtime_preflight_requires_reply_mode,
        test_private_test_runtime_preflight_blocks_llm_rag_external,
        test_runtime_skip_self_message_before_private_reply_decision,
        test_runtime_skip_author_id_matching_bot_user,
        test_runtime_allows_human_private_test_message_to_reach_payload,
        test_duplicate_message_id_skipped,
        test_public_mapped_channel_reply_blocked,
        test_runtime_ready_visibility_marks_private_test_flags,
        test_allowed_decision_message_sent_false_until_runtime_send,
        test_rendered_message_includes_llm_disabled,
        test_rendered_message_has_no_raw_token_or_id,
        test_rendered_message_is_deterministic_placeholder_based,
        test_safety_wrapper_only_allows_private_test_reply_send,
        test_regular_message_create_always_blocked,
        test_runtime_source_has_no_unrestricted_send_path,
        test_blocked_audit_and_sent_audit_possible,
        test_mock_runtime_send_only_after_allowed_payload,
        test_report_has_no_raw_token_or_id,
        test_payload_safe_assertions,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All private test reply tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

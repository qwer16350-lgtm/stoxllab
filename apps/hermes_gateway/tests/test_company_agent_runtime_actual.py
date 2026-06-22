from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import (
    build_company_agent_message_result,
    build_company_agent_runtime_report,
    build_company_agent_runtime_start_report,
    should_ignore_message,
)


class FakeAuthor:
    def __init__(self, *, bot: bool = False, author_id: int = 1) -> None:
        self.bot = bot
        self.id = author_id


class FakeChannel:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeMessage:
    def __init__(self, content: str, channel: str, *, bot: bool = False, author_id: int = 1) -> None:
        self.content = content
        self.channel = FakeChannel(channel)
        self.author = FakeAuthor(bot=bot, author_id=author_id)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_runtime_without_allow_flag_blocked() -> None:
    report = build_company_agent_runtime_report(allow_flag_present=False)
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["blocked_reasons"] == ["allow_flag_missing"], "allow flag missing")
    assert_true(report["discord_gateway_live_connection_executed"] is False, "no gateway")


def test_runtime_start_report_when_allowed_and_token_present() -> None:
    report = build_company_agent_runtime_start_report(
        True,
        {
            "DISCORD_BOT_TOKEN": "super-secret-token-value",
            "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
            "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
        },
        discord_dependency_available=True,
    )
    assert_true(report["report_type"] == "company_agent_runtime_started", "started report")
    assert_true(report["started"] is True, "started")
    assert_true(report["blocked"] is False, "not blocked")
    assert_true(report["allow_flag_present"] is True, "allow")
    assert_true(report["discord_gateway_live_connection_executed"] is True, "gateway branch")
    assert_true(report["runtime_loop_active"] is True, "loop active")
    assert_true(report["llm_enabled"] is False, "llm false")
    assert_true(report["reply_mode"] == "deterministic_fallback", "fallback")
    assert_true(report["agent_count"] == 5, "agents")
    text = json.dumps(report, ensure_ascii=False)
    assert_true("super-secret-token-value" not in text, "token value not logged")


def test_commands_route_to_correct_agents() -> None:
    assert_true(build_company_agent_message_result("marketing-brief", "!marin draft")["selected_agent"] == "marin", "marin")
    assert_true(build_company_agent_message_result("marketing-brief", "!lucy review")["selected_agent"] == "lucy", "lucy")
    assert_true(build_company_agent_message_result("operation-brief", "!kasumi search")["selected_agent"] == "kasumi", "kasumi")
    assert_true(build_company_agent_message_result("operation-brief", "!meiko decide")["selected_agent"] == "meiko", "meiko")
    assert_true(build_company_agent_message_result("reze-전략기획", "!reze strategy")["selected_agent"] == "reze", "reze")
    assert_true(build_company_agent_message_result("marketing-brief", "!agent marin copy")["selected_agent"] == "marin", "agent")
    assert_true(build_company_agent_message_result("marketing-brief", "!route SNS draft")["selected_agent"] == "marin", "route")
    assert_true(build_company_agent_message_result("marketing-brief", "!handoff lucy review")["selected_agent"] == "lucy", "handoff")


def test_explicit_command_priority_over_channel_and_keywords() -> None:
    meiko = build_company_agent_message_result("meiko-검토", "!meiko 이 지원사업 넣을만한지 판단해줘")
    assert_true(meiko["selected_agent"] == "meiko", "explicit meiko selected")
    assert_true(meiko["agent_display_name"] == "메이코", "explicit meiko display")
    assert_true(meiko["reason"] == "explicit_command", "explicit reason")
    content = meiko["response"]["content"]
    assert_true(content.startswith("[MEIKO_STOXL / 메이코]"), "meiko prefix")
    assert_true("[KASUMI_STOXL / 카스미]" not in content, "not kasumi")
    for marker in ("소속: 운영팀 선임", "업무: 실행 판단 / 일정 / 리스크", "판단:", "이유:", "실행 조건:", "리스크:", "next:"):
        assert_true(marker in content, f"meiko marker {marker}")
    assert_true(build_company_agent_message_result("operation-brief", "!meiko 지원사업 판단")["selected_agent"] == "meiko", "keyword does not override meiko")
    assert_true(build_company_agent_message_result("operation-brief", "!kasumi 지원사업 찾아줘")["selected_agent"] == "kasumi", "explicit kasumi")
    assert_true(build_company_agent_message_result("operation-brief", "지원사업 찾아줘")["selected_agent"] == "kasumi", "plain support route")
    default_meiko = build_company_agent_message_result("meiko-검토", "이 지원사업 넣을만한지 판단해줘")
    assert_true(default_meiko["selected_agent"] == "meiko", "meiko channel default")
    assert_true(default_meiko["reason"] == "exact_channel_default", "channel default reason")
    assert_true(build_company_agent_message_result("marketing-brief", "!lucy 브랜드톤 검토")["selected_agent"] == "lucy", "explicit lucy")
    marin = build_company_agent_message_result("lucy-검토", "!marin 콘텐츠 초안")
    assert_true(marin["selected_agent"] == "marin", "explicit marin overrides lucy channel")
    assert_true(marin["reason"] == "explicit_command", "explicit marin reason")
    route_keyword = build_company_agent_message_result("operation-brief", "!route 지원사업 찾아줘")
    assert_true(route_keyword["selected_agent"] == "kasumi", "route keyword kasumi")
    assert_true("keyword" in route_keyword["reason"], "keyword reason on route")


def test_deterministic_fallback_agent_prefix_and_handoff() -> None:
    marin = build_company_agent_message_result("marketing-brief", "!marin MML 테스트 문구 3개")
    kasumi = build_company_agent_message_result("operation-brief", "!kasumi 지원사업 후보")
    reze = build_company_agent_message_result("reze-전략기획", "!reze 신제품 방향")
    assert_true("[MARIN_STOXL / 마린]" in marin["response"]["content"], "marin prefix")
    assert_true("handoff:" in marin["response"]["content"], "marin handoff block")
    assert_true("to: lucy-" in marin["response"]["content"], "marin handoff target")
    assert_true("[KASUMI_STOXL / 카스미]" in kasumi["response"]["content"], "kasumi prefix")
    assert_true("handoff:" in kasumi["response"]["content"], "kasumi handoff block")
    assert_true("to: meiko-" in kasumi["response"]["content"], "kasumi handoff target")
    assert_true("[REZE_STOXL / 레제]" in reze["response"]["content"], "reze prefix")
    assert_true("대표-회의실" in reze["response"]["content"], "reze decision channel")


def test_unknown_bot_self_external_and_webhook_fallback() -> None:
    unknown = build_company_agent_message_result("unknown-channel", "!marin draft")
    assert_true(unknown["blocked"] is True, "unknown channel blocked")
    bot_ignored = should_ignore_message(FakeMessage("!marin draft", "marketing-brief", bot=True))
    assert_true(bot_ignored == (True, "bot_message"), "bot ignored")
    self_ignored = should_ignore_message(FakeMessage("!marin draft", "marketing-brief", author_id=7), bot_user=FakeAuthor(author_id=7))
    assert_true(self_ignored == (True, "self_message"), "self ignored")
    external = build_company_agent_message_result("marketing-brief", "publish this SNS now")
    assert_true(external["blocked"] is True, "external blocked")
    assert_true(external["external_execution_allowed"] is False, "external false")
    fallback = build_company_agent_message_result("marketing-brief", "!marin draft")
    assert_true(fallback["bot_message_fallback_used"] is True, "bot fallback")
    assert_true(fallback["send_strategy"] == "bot_message_fallback", "fallback strategy")
    text = json.dumps(fallback, ensure_ascii=False)
    assert_true("webhook_url" in text and "https://" not in text, "no webhook URL value")


def main() -> int:
    tests = [
        test_runtime_without_allow_flag_blocked,
        test_runtime_start_report_when_allowed_and_token_present,
        test_commands_route_to_correct_agents,
        test_explicit_command_priority_over_channel_and_keywords,
        test_deterministic_fallback_agent_prefix_and_handoff,
        test_unknown_bot_self_external_and_webhook_fallback,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent actual runtime tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

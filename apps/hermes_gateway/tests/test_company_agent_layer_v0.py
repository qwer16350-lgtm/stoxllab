from __future__ import annotations

import io
import os
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
SCRIPT_DIR = APP_DIR.parents[1] / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from company_agent_registry import CHANNEL_STRUCTURE, load_company_registry
from company_agent_router import build_company_agent_org_report, extract_first_command_line, normalize_discord_message_content, route_company_agent_message
from company_agent_runtime import build_company_agent_router_dry_run, build_company_agent_runtime_report
from company_handoff import build_handoff_message
from company_webhook_sender import send_as_agent
import setup_discord_company_os


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_registry_agents_prompts_and_channels() -> None:
    registry = load_company_registry()
    assert_true(len(registry["agents"]) == 5, "registry has 5 agents")
    for agent_id in ("lucy", "marin", "meiko", "kasumi", "reze"):
        assert_true(agent_id in registry["agents"], agent_id)
        assert_true(registry["agents"][agent_id]["prompt_present"] is True, f"{agent_id} prompt")
    for category, channels in CHANNEL_STRUCTURE.items():
        assert_true(category in registry["channel_structure"], category)
        for channel in channels:
            assert_true(channel in registry["channel_structure"][category], channel)


def test_router_default_and_keyword_routes() -> None:
    marin = route_company_agent_message("marketing-brief", "SNS draft copy for MML")
    assert_true(marin["selected_agent"] == "marin", "marin SNS draft")
    lucy = route_company_agent_message("marketing-brief", "SNS final review please")
    assert_true(lucy["selected_agent"] == "lucy", "lucy marketing review")
    kasumi = route_company_agent_message("operation-brief", "지원사업 후보 찾아줘")
    assert_true(kasumi["selected_agent"] == "kasumi", "kasumi support search")
    meiko = route_company_agent_message("operation-brief", "지원사업 최종 판단과 일정 검토")
    assert_true(meiko["selected_agent"] == "meiko", "meiko support decision")
    reze = route_company_agent_message("reze-전략기획", "신제품 방향 아이디어 제안")
    assert_true(reze["selected_agent"] == "reze", "reze strategy idea")


def test_router_commands_and_blocks() -> None:
    direct = route_company_agent_message("marketing-brief", "!agent marin SNS draft")
    assert_true(direct["selected_agent"] == "marin", "agent command")
    assert_true(direct["reason"] == "explicit_command", "agent command reason")
    explicit_meiko = route_company_agent_message("meiko-검토", "!meiko 이 지원사업 넣을만한지 판단해줘")
    assert_true(explicit_meiko["selected_agent"] == "meiko", "explicit meiko")
    assert_true(explicit_meiko["reason"] == "explicit_command", "explicit command reason")
    default_meiko = route_company_agent_message("meiko-검토", "이 지원사업 넣을만한지 판단해줘")
    assert_true(default_meiko["selected_agent"] == "meiko", "meiko channel default")
    assert_true(default_meiko["reason"] == "exact_channel_default", "exact channel default reason")
    keyword = route_company_agent_message("operation-brief", "!route 지원사업 찾아줘")
    assert_true(keyword["selected_agent"] == "kasumi", "keyword route")
    assert_true("keyword" in keyword["reason"], "keyword reason")
    handoff = route_company_agent_message("marketing-brief", "!handoff lucy review this")
    assert_true(handoff["selected_agent"] == "lucy", "handoff command")
    unknown = route_company_agent_message("unknown-channel", "SNS draft")
    assert_true(unknown["blocked"] is True, "unknown channel blocked")
    external = route_company_agent_message("marketing-brief", "publish this SNS post now")
    assert_true(external["blocked"] is True, "external execution request blocked")
    assert_true(external["external_execution_allowed"] is False, "external execution false")


def test_message_normalization_and_command_extraction() -> None:
    assert_true(normalize_discord_message_content("   !meiko 판단해줘").startswith("!meiko"), "strip whitespace")
    examples = [
        "   !meiko 판단해줘",
        "\n\n!meiko 판단해줘",
        "<#123456789012345678>\n!meiko 판단해줘",
        "#operation-brief\n!meiko 판단해줘",
        "# operation-brief\n!meiko 판단해줘",
        "> quoted\n!meiko 판단해줘",
    ]
    for example in examples:
        assert_true(extract_first_command_line(example).startswith("!meiko"), "extract meiko command")
    prefixed = route_company_agent_message("operation-brief", "#operation-brief\n!meiko 이 지원사업 넣을만한지 판단해줘")
    assert_true(prefixed["selected_agent"] == "meiko", "prefixed command route")
    assert_true(prefixed["reason"] == "explicit_command", "prefixed explicit reason")


def test_handoff_flow() -> None:
    marin = build_handoff_message("marin", "draft ready", "marin-초안")
    kasumi = build_handoff_message("kasumi", "candidate ready", "kasumi-리서치")
    reze = build_handoff_message("reze", "strategy opinion", "reze-전략기획")
    assert_true(marin["to"] == "lucy", "marin handoff")
    assert_true(kasumi["to"] == "meiko", "kasumi handoff")
    assert_true(reze["to"] == "decision-meeting", "reze decision meeting")
    assert_true(reze["target_channel"] == "대표-회의실", "reze reports to representative meeting")


def test_webhook_sender_redacts_and_blocks() -> None:
    blocked = send_as_agent("marin", "marketing-brief", "hello")
    assert_true(blocked["blocked"] is True, "webhook default blocked")
    assert_true(blocked["webhook_url_value_logged"] is False, "webhook URL hidden")
    assert_true(blocked["raw_discord_ids_logged"] is False, "raw IDs hidden")
    assert_true(blocked["message_sent_count"] == 0, "no send")
    unknown = send_as_agent("marin", "unknown-channel", "hello", allow_send=True, sender_adapter=lambda *_: {})
    assert_true(unknown["blocked"] is True, "unknown channel blocked")


def test_org_report_router_dry_run_and_runtime_default_blocked() -> None:
    org = build_company_agent_org_report()
    assert_true(org["agent_count"] == 5, "org report agents")
    assert_true(org["discord_message_sent"] is False, "org no send")
    assert_true(org["permissions"]["external_execution_allowed"] is False, "org external false")
    dry_run = build_company_agent_router_dry_run("marketing-brief", "SNS draft")
    assert_true(dry_run["discord_message_sent"] is False, "router no send")
    assert_true(dry_run["message_sent_count"] == 0, "router send count")
    runtime = build_company_agent_runtime_report(allow_flag_present=False)
    assert_true(runtime["blocked"] is True, "runtime blocked")
    assert_true(runtime["actual_discord_runtime_executed"] is False, "runtime not executed")
    assert_true(runtime["discord_gateway_live_connection_executed"] is False, "no gateway")
    assert_true(runtime["message_sent_count"] == 0, "runtime no send")


def test_discord_setup_request_headers_and_http_error_report() -> None:
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return b"{}"

    def fake_opener(request, timeout):
        captured["user_agent"] = request.get_header("User-agent")
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse()

    setup_discord_company_os._request("token-value", "GET", "/users/@me", opener=fake_opener)
    assert_true(captured["user_agent"] == "STOXL-Hermes-Gateway (local setup)", "User-Agent")
    assert_true(captured["authorization"] == "Bot token-value", "Authorization")
    error = urllib.error.HTTPError(
        "https://discord.example",
        403,
        "Forbidden",
        hdrs=None,
        fp=io.BytesIO(b'{"message":"Missing Access"}'),
    )
    with patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "present", "DISCORD_GUILD_ID": "123456789012345678"}, clear=False):
        with patch("setup_discord_company_os._request", side_effect=error):
            report = setup_discord_company_os.build_execute_report(True)
    assert_true(report["blocked"] is True, "blocked")
    assert_true(report["http_status"] == 403, "HTTP status")
    assert_true(report["blocked_reasons"] == ["discord_api_forbidden"], "status reason")
    assert_true(report["blocked_reason_detail"] == "discord_api_forbidden_or_request_rejected", "detail")
    assert_true(report["discord_error_code"] is None, "Discord code redacted")
    assert_true(report["discord_error_message_present"] is True, "Discord message present")
    assert_true(report["discord_token_value_logged"] is False, "token hidden")
    assert_true(report["discord_guild_id_value_logged"] is False, "guild hidden")


def main() -> int:
    tests = [
        test_registry_agents_prompts_and_channels,
        test_router_default_and_keyword_routes,
        test_router_commands_and_blocks,
        test_message_normalization_and_command_extraction,
        test_handoff_flow,
        test_webhook_sender_redacts_and_blocks,
        test_org_report_router_dry_run_and_runtime_default_blocked,
        test_discord_setup_request_headers_and_http_error_report,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent layer v0 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

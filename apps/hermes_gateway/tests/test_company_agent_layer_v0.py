from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_registry import CHANNEL_STRUCTURE, load_company_registry
from company_agent_router import build_company_agent_org_report, route_company_agent_message
from company_agent_runtime import build_company_agent_router_dry_run, build_company_agent_runtime_report
from company_handoff import build_handoff_message
from company_webhook_sender import send_as_agent


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
    handoff = route_company_agent_message("marketing-brief", "!handoff lucy review this")
    assert_true(handoff["selected_agent"] == "lucy", "handoff command")
    unknown = route_company_agent_message("unknown-channel", "SNS draft")
    assert_true(unknown["blocked"] is True, "unknown channel blocked")
    external = route_company_agent_message("marketing-brief", "publish this SNS post now")
    assert_true(external["blocked"] is True, "external execution request blocked")
    assert_true(external["external_execution_allowed"] is False, "external execution false")


def test_handoff_flow() -> None:
    marin = build_handoff_message("marin", "draft ready", "marin-초안")
    kasumi = build_handoff_message("kasumi", "candidate ready", "kasumi-리서치")
    reze = build_handoff_message("reze", "strategy opinion", "reze-전략기획")
    assert_true(marin["to"] == "lucy", "marin handoff")
    assert_true(kasumi["to"] == "meiko", "kasumi handoff")
    assert_true(reze["to"] == "decision-meeting", "reze decision meeting")
    assert_true(reze["target_channel"] == "대주주회의실", "reze reports to decision meeting")


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


def main() -> int:
    tests = [
        test_registry_agents_prompts_and_channels,
        test_router_default_and_keyword_routes,
        test_router_commands_and_blocks,
        test_handoff_flow,
        test_webhook_sender_redacts_and_blocks,
        test_org_report_router_dry_run_and_runtime_default_blocked,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent layer v0 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

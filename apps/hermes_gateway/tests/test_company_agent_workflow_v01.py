from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_responder import build_approval_draft, build_company_agent_response
from company_agent_router import route_company_agent_message
from company_agent_runtime import (
    build_company_agent_runtime_start_report,
    build_company_agent_workflow_dry_run,
    build_company_agent_workflow_v01_report,
)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def response_for(agent_id: str, channel: str, message: str) -> str:
    route = route_company_agent_message(channel, f"!{agent_id} {message}")
    return str(build_company_agent_response(agent_id, message, route)["content"])


def test_agent_templates_upgraded() -> None:
    marin = response_for("marin", "marketing-brief", "MML 테스트 문구 3개")
    assert_true("초안:" in marin, "marin draft")
    assert_true("체크 필요:" in marin, "marin check")
    assert_true("to: lucy-검토" in marin, "marin handoff")
    lucy = response_for("lucy", "lucy-검토", "검토해줘")
    assert_true("판정:" in lucy, "lucy decision")
    assert_true("수정 제안:" in lucy, "lucy revision")
    assert_true("최종승인 필요 여부:" in lucy, "lucy approval")
    kasumi = response_for("kasumi", "operation-brief", "지원사업 찾아줘")
    assert_true("리서치 후보:" in kasumi, "kasumi candidates")
    assert_true("마감:" in kasumi, "kasumi deadline")
    assert_true("필요자료:" in kasumi, "kasumi materials")
    assert_true("리스크:" in kasumi, "kasumi risk")
    assert_true("to: meiko-검토" in kasumi, "kasumi handoff")
    meiko = response_for("meiko", "meiko-검토", "판단해줘")
    assert_true("추천 / 보류 / 비추천" in meiko, "meiko judgment")
    assert_true("실행 조건:" in meiko, "meiko conditions")
    assert_true("리스크:" in meiko, "meiko risk")
    reze = response_for("reze", "reze-전략기획", "신제품 방향")
    assert_true("전략 판단:" in reze, "reze strategy")
    assert_true("스톡스 적합성:" in reze, "reze fit")
    assert_true("대표-회의실" in reze, "reze meeting")


def test_approval_draft_and_external_blocking() -> None:
    route = route_company_agent_message("marketing-brief", "publish this SNS now")
    draft = build_approval_draft("lucy", "publish this SNS now", route)
    assert_true("[APPROVAL_REQUEST]" in draft["content"], "approval request")
    assert_true("external_execution_requested=true" in draft["content"], "external requested")
    assert_true("external_execution_performed=false" in draft["content"], "external not performed")
    dry_run = build_company_agent_workflow_dry_run("marketing-brief", "publish this SNS now")
    assert_true(dry_run["blocked"] is True, "external request blocked")
    assert_true(dry_run["external_execution_performed"] is False, "external not performed")


def test_handoff_posting_and_workflow_dry_run() -> None:
    default = build_company_agent_workflow_dry_run("marketing-brief", "MML 테스트 문구 3개")
    assert_true(default["selected_agent"] == "marin", "selected marin")
    assert_true(default["response_preview_present"] is True, "preview present")
    assert_true(default["handoff_target"] == "lucy-검토", "handoff target")
    assert_true(default["handoff_post"]["handoff_posting_enabled"] is False, "handoff disabled default")
    direct_handoff = build_company_agent_workflow_dry_run("marketing-brief", "!handoff lucy MML 검토 요청")
    assert_true(direct_handoff["selected_agent"] == "lucy", "direct handoff selected lucy")
    assert_true(direct_handoff["handoff_target"] == "lucy-검토", "direct handoff target")
    reze_handoff = build_company_agent_workflow_dry_run("marketing-brief", "!handoff reze 신제품 방향 검토")
    assert_true(reze_handoff["selected_agent"] == "reze", "direct handoff selected reze")
    assert_true(reze_handoff["handoff_target"] == "대표-회의실", "direct handoff meeting")
    enabled = build_company_agent_workflow_dry_run(
        "operation-brief",
        "지원사업 찾아줘",
        env={"HERMES_COMPANY_AGENT_HANDOFF_ENABLED": "true"},
    )
    assert_true(enabled["handoff_post"]["handoff_posting_enabled"] is True, "handoff enabled")
    assert_true(enabled["handoff_post"]["handoff_target_channel"] == "meiko-검토", "handoff channel")
    assert_true(enabled["discord_api_send_called"] is False, "dry-run no send")


def test_explicit_command_priority_workflow_dry_run() -> None:
    meiko = build_company_agent_workflow_dry_run("meiko-검토", "!meiko 이 지원사업 넣을만한지 판단해줘")
    assert_true(meiko["selected_agent"] == "meiko", "workflow explicit meiko")
    assert_true(meiko["agent_display_name"] == "메이코", "workflow meiko display")
    assert_true(meiko["response_preview_present"] is True, "workflow preview")
    assert_true(meiko["target_channel"] == "meiko-검토", "workflow meiko target")
    assert_true(meiko["discord_api_send_called"] is False, "workflow no send")
    assert_true(meiko["external_execution_performed"] is False, "workflow no external")
    plain_operation = build_company_agent_workflow_dry_run("operation-brief", "지원사업 찾아줘")
    assert_true(plain_operation["selected_agent"] == "kasumi", "plain support can route kasumi")
    plain_meiko = build_company_agent_workflow_dry_run("meiko-검토", "이 지원사업 넣을만한지 판단해줘")
    assert_true(plain_meiko["selected_agent"] == "meiko", "plain meiko channel default")


def test_commands_agents_help_and_report() -> None:
    report = build_company_agent_workflow_v01_report()
    assert_true(report["workflow_v01_available"] is True, "workflow report")
    assert_true(report["agent_templates_upgraded"] is True, "templates")
    assert_true(report["handoff_posting_supported"] is True, "handoff supported")
    assert_true(report["handoff_posting_default_enabled"] is False, "handoff default")
    assert_true(report["approval_draft_supported"] is True, "approval draft")
    assert_true(report["senior_junior_hierarchy"]["marin"] == "lucy", "marin hierarchy")
    assert_true(report["senior_junior_hierarchy"]["kasumi"] == "meiko", "kasumi hierarchy")
    assert_true(report["senior_junior_hierarchy"]["reze"] == "대표-회의실", "reze hierarchy")
    agents = build_company_agent_workflow_dry_run("marketing-brief", "!agents")
    assert_true(len(agents["handoff_post"]) > 0, "agents response")
    assert_true(agents["response_preview_present"] is True, "agents preview")
    help_report = build_company_agent_workflow_dry_run("marketing-brief", "!help")
    assert_true(help_report["response_preview_present"] is True, "help preview")


def test_runtime_path_preserved_and_no_sensitive_values() -> None:
    runtime = build_company_agent_runtime_start_report(
        True,
        {
            "DISCORD_BOT_TOKEN": "secret-token",
            "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
            "HERMES_COMPANY_AGENT_HANDOFF_ENABLED": "false",
        },
        discord_dependency_available=True,
    )
    assert_true(runtime["report_type"] == "company_agent_runtime_started", "runtime start")
    assert_true(runtime["discord_gateway_live_connection_executed"] is True, "gateway branch")
    text = json.dumps(runtime, ensure_ascii=False)
    assert_true("secret-token" not in text, "token redacted")
    assert_true("http://" not in text and "https://" not in text, "no webhook URL")


def main() -> int:
    tests = [
        test_agent_templates_upgraded,
        test_approval_draft_and_external_blocking,
        test_handoff_posting_and_workflow_dry_run,
        test_explicit_command_priority_workflow_dry_run,
        test_commands_agents_help_and_report,
        test_runtime_path_preserved_and_no_sensitive_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent workflow v0.1 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

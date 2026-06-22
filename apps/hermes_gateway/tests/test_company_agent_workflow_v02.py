from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_runtime import (
    build_company_agent_approval_dry_run,
    build_company_agent_handoff_dry_run,
    resolve_target_channel_by_name,
)
from company_handoff import build_handoff_post_payload


class FakeChannel:
    def __init__(self, name: str, channel_id: str = "123456789012345678") -> None:
        self.name = name
        self.id = channel_id


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_safe(report: dict) -> None:
    text = json.dumps(report, ensure_ascii=False)
    assert_true("123456789012345678" not in text, "raw channel id hidden")
    assert_true("secret-token" not in text, "secret hidden")
    assert_true("https://" not in text and "http://" not in text, "webhook URL hidden")
    assert_true(report["discord_api_send_called"] is False, "dry-run no send")
    assert_true(report["external_execution_performed"] is False, "no external execution")


def test_handoff_disabled_by_default_and_targets() -> None:
    marin = build_company_agent_handoff_dry_run("marketing-brief", "!marin MML 인스타 문구 3개 뽑아줘")
    assert_true(marin["selected_agent"] == "marin", "marin selected")
    assert_true(marin["handoff_enabled"] is False, "handoff disabled")
    assert_true(marin["handoff_supported"] is True, "handoff supported")
    assert_true(marin["handoff_target_channel"] == "lucy-검토", "marin target")
    assert_true(marin["handoff_message_preview_present"] is True, "marin preview")
    assert_true("[HANDOFF]" in marin["handoff_message_preview"], "handoff marker")
    assert_safe(marin)
    kasumi = build_company_agent_handoff_dry_run("kasumi-리서치", "!kasumi 올해 12월까지 디자인 지원사업 찾아줘")
    assert_true(kasumi["handoff_target_channel"] == "meiko-검토", "kasumi target")
    reze = build_company_agent_handoff_dry_run("reze-전략기획", "!reze 스톡슬 신규 제품 방향 제안해줘")
    assert_true(reze["handoff_target_channel"] == "대표-회의실", "reze target")


def test_approval_dry_run() -> None:
    approval = build_company_agent_approval_dry_run("lucy-검토", "!approve-draft 이 문구 발행 승인 요청서 만들어줘")
    assert_true(approval["selected_agent"] == "lucy", "lucy selected")
    assert_true(approval["approval_draft_supported"] is True, "approval supported")
    assert_true(approval["approval_target_channel"] == "최종-승인요청", "approval target")
    assert_true(approval["approval_message_preview_present"] is True, "approval preview")
    assert_true("[APPROVAL_REQUEST]" in approval["approval_message_preview"], "approval marker")
    assert_true("external_execution_performed: false" in approval["approval_message_preview"], "external false")
    assert_safe(approval)


def test_external_request_never_executes() -> None:
    approval = build_company_agent_approval_dry_run("lucy-검토", "!approve-draft publish this SNS now")
    assert_true(approval["external_execution_requested"] is True, "external requested")
    assert_true(approval["external_execution_performed"] is False, "external not performed")
    assert_true("external_execution_requested: true" in approval["approval_message_preview"], "external requested marker")
    assert_safe(approval)


def test_target_channel_resolution_and_missing_target() -> None:
    found = resolve_target_channel_by_name([FakeChannel("lucy-검토")], "lucy-검토")
    assert_true(found["target_channel_found"] is True, "target found")
    assert_true("123456789012345678" not in json.dumps(found, ensure_ascii=False), "target id hidden")
    missing = resolve_target_channel_by_name([FakeChannel("marketing-brief")], "lucy-검토")
    assert_true(missing["target_channel_found"] is False, "target missing")
    blocked = build_handoff_post_payload({"selected_agent": "marin", "source_channel": "marketing-brief", "response": {"content": "draft"}})
    assert_true(blocked["blocked"] is True, "missing handoff target blocked")
    assert_true(blocked["blocked_reasons"] == ["handoff_target_missing"], "missing target reason")
    assert_true(blocked["discord_api_send_called"] is False, "missing target no send")


def main() -> int:
    tests = [
        test_handoff_disabled_by_default_and_targets,
        test_approval_dry_run,
        test_external_request_never_executes,
        test_target_channel_resolution_and_missing_target,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All company agent workflow v0.2 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

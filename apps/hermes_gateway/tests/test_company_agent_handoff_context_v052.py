from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

TEST_MEMORY_DIR = tempfile.TemporaryDirectory()
os.environ["HERMES_COMPANY_MEMORY_DIR"] = TEST_MEMORY_DIR.name

from company_agent_llm import build_agent_llm_messages
from company_agent_runtime import (
    build_company_agent_context_dry_run,
    build_company_agent_context_handoff_simulation,
    build_company_agent_message_result,
)
from company_context_store import (
    HandoffContext,
    build_contextual_user_message,
    clear_handoff_context_store,
    detect_context_reference_terms,
    get_latest_context_by_agent_pair,
    get_latest_context_for_channel,
    store_handoff_context,
)
from company_handoff import build_handoff_post_payload


SAFE_ENV = {
    "HERMES_COMPANY_AGENT_LLM_ENABLED": "false",
    "HERMES_COMPANY_AGENT_LLM_MODE": "off",
    "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def clear_test_persistent_memory() -> None:
    for path in Path(TEST_MEMORY_DIR.name).glob("*.jsonl"):
        path.write_text("", encoding="utf-8")


def kasumi_context(content: str = "시제품/PoC/사업화 지원 후보. 마감과 자격은 최신 확인 필요.") -> HandoffContext:
    return HandoffContext(
        context_type="handoff",
        source_agent="kasumi",
        target_agent="meiko",
        source_channel="kasumi-리서치",
        target_channel="meiko-검토",
        status="리서치 정리 완료",
        request_summary="이번 달 지원사업 후보",
        handoff_content=content,
        next_action="메이코 검토 필요",
    )


def test_handoff_context_store_and_reference_detection() -> None:
    clear_handoff_context_store()
    stored = store_handoff_context("meiko-검토", kasumi_context())
    latest = get_latest_context_for_channel("meiko-검토")
    pair = get_latest_context_by_agent_pair("kasumi", "meiko")
    assert_true(stored["created_at_present"] is True, "created timestamp presence")
    assert_true(latest is not None and latest["source_agent"] == "kasumi", "latest by channel")
    assert_true(pair is not None and pair["target_agent"] == "meiko", "latest by pair")
    assert_true(detect_context_reference_terms("!meiko 이 지원사업 넣을만한지 판단해줘"), "support reference")
    assert_true(detect_context_reference_terms("!lucy 방금 마린 초안 검토해줘"), "Marin reference")


def test_handoff_payload_saves_context() -> None:
    clear_handoff_context_store()
    result = {
        "selected_agent": "kasumi",
        "source_channel": "kasumi-리서치",
        "handoff_channel": "meiko-검토",
        "response": {"content": "지원사업 후보와 최신성 확인 항목"},
    }
    payload = build_handoff_post_payload(result, "이번 달 지원사업 후보")
    latest = get_latest_context_for_channel("meiko-검토")
    assert_true(payload["handoff_context_saved"] is True, "payload saves context")
    assert_true(latest is not None and latest["source_agent"] == "kasumi", "Kasumi stored")


def test_meiko_and_lucy_use_latest_handoff_context() -> None:
    clear_handoff_context_store()
    store_handoff_context("meiko-검토", kasumi_context())
    meiko = build_company_agent_message_result(
        "meiko-검토",
        "!meiko 이 지원사업 넣을만한지 판단해줘",
        env=SAFE_ENV,
    )
    meiko_text = str(meiko["response"]["content"])
    assert_true(meiko["handoff_context_used"] is True, "Meiko context used")
    assert_true("카스미가 넘긴 내용 기준" in meiko_text, "Meiko cites Kasumi")
    assert_true("시제품/PoC/사업화 지원 후보" in meiko_text, "Meiko uses provided content")
    assert_true("공고문을 달라" not in meiko_text, "Meiko does not repeat missing-content request")

    store_handoff_context(
        "lucy-검토",
        HandoffContext(
            context_type="handoff",
            source_agent="marin",
            target_agent="lucy",
            source_channel="marketing-brief",
            target_channel="lucy-검토",
            status="초안 생성 완료",
            request_summary="MML 인스타 문구",
            handoff_content="작은 구조가 만드는 큰 변화, MML.",
            next_action="루시 검토 필요",
        ),
    )
    lucy = build_company_agent_message_result(
        "lucy-검토",
        "!lucy 방금 마린 초안 검토해줘",
        env=SAFE_ENV,
    )
    lucy_text = str(lucy["response"]["content"])
    assert_true(lucy["handoff_context_used"] is True, "Lucy context used")
    assert_true("마린이 넘긴 초안 기준" in lucy_text, "Lucy cites Marin")
    assert_true("작은 구조가 만드는 큰 변화" in lucy_text, "Lucy uses draft")


def test_reply_context_has_priority_over_latest_channel_context() -> None:
    clear_handoff_context_store()
    store_handoff_context("lucy-검토", kasumi_context("older channel context"))
    replied = (
        "[HANDOFF]\n"
        "from_agent: MARIN_STOXL / 마린\n"
        "to: LUCY_STOXL / 루시\n\n"
        "전달 내용:\nreply-specific Marin draft"
    )
    result = build_company_agent_message_result(
        "lucy-검토",
        "!lucy 이 문구 발행 가능해?",
        replied,
        SAFE_ENV,
    )
    text = str(result["response"]["content"])
    assert_true(result["handoff_context_priority"] == "reply", "reply priority")
    assert_true(result["handoff_context_source_agent"] == "marin", "reply source")
    assert_true("reply-specific Marin draft" in text, "reply content used")
    assert_true("older channel context" not in text, "latest context not selected")


def test_no_context_preserves_existing_insufficient_information_behavior() -> None:
    clear_handoff_context_store()
    clear_test_persistent_memory()
    result = build_company_agent_message_result(
        "meiko-검토",
        "!meiko 이 지원사업 넣을만한지 판단해줘",
        env=SAFE_ENV,
    )
    text = str(result["response"]["content"])
    assert_true(result["handoff_context_used"] is False, "no context")
    assert_true("현재 공고명/마감/지원조건이 확정되지 않았습니다" in text, "existing hold behavior")


def test_context_is_injected_into_llm_messages() -> None:
    context = store_handoff_context("meiko-검토", kasumi_context())
    envelope = build_agent_llm_messages(
        "meiko",
        "!meiko 이 지원사업 판단해줘",
        {"command": "meiko", "source_channel": "meiko-검토", "handoff_context": context},
    )
    text = json.dumps(envelope["messages_preview"], ensure_ascii=False)
    contextual = build_contextual_user_message("meiko", "이 지원사업 판단", "meiko-검토")
    assert_true(envelope["handoff_context_used"] is True, "LLM context used")
    assert_true("[CONTEXT_FROM_RECENT_HANDOFF]" in text, "context block")
    assert_true("KASUMI_STOXL / 카스미" in text, "source label")
    assert_true("[CONTEXT_FROM_RECENT_HANDOFF]" in contextual, "contextual user message")
    assert_true(envelope["rag_called"] is False, "no RAG")
    assert_true(envelope["embedding_called"] is False, "no embedding")
    assert_true(envelope["external_execution"] is False, "no external")


def test_cli_builders_and_redaction_are_safe() -> None:
    clear_handoff_context_store()
    sensitive = "candidate token=secret-token 123456789012345678"
    simulation = build_company_agent_context_handoff_simulation(
        "kasumi", "meiko", "meiko-검토", sensitive
    )
    dry = build_company_agent_context_dry_run(
        "meiko-검토", "!meiko 이 지원사업 넣을만한지 판단해줘"
    )
    stored = get_latest_context_for_channel("meiko-검토") or {}
    combined = json.dumps({"simulation": simulation, "dry": dry, "stored": stored}, ensure_ascii=False)
    assert_true(simulation["handoff_context_saved"] is True, "simulation saved")
    assert_true(dry["context_used"] is True, "dry-run context used")
    assert_true("secret-token" not in combined, "secret redacted")
    assert_true("123456789012345678" not in combined, "raw ID redacted")
    for report in (simulation, dry):
        assert_true(report["raw_discord_ids_logged"] is False, "raw IDs flag")
        assert_true(report["secret_values_logged"] is False, "secret flag")
        assert_true(report["rag_called"] is False, "no RAG")
        assert_true(report["embedding_called"] is False, "no embedding")
        assert_true(report["external_execution"] is False, "no external")


def main() -> int:
    tests = [
        test_handoff_context_store_and_reference_detection,
        test_handoff_payload_saves_context,
        test_meiko_and_lucy_use_latest_handoff_context,
        test_reply_context_has_priority_over_latest_channel_context,
        test_no_context_preserves_existing_insufficient_information_behavior,
        test_context_is_injected_into_llm_messages,
        test_cli_builders_and_redaction_are_safe,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    clear_handoff_context_store()
    TEST_MEMORY_DIR.cleanup()
    print("All company agent handoff context v0.5.2 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

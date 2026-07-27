from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_intent import (
    AGENT_INTENT_CAPABILITIES,
    assess_rag_sufficiency,
    build_agent_rag_query,
    build_intent_aware_deterministic_fallback,
    build_intent_prompt_context,
    classify_agent_intent,
    extract_source_text,
    intent_metadata_boost,
    resolve_agent_response_mode,
)
from company_agent_llm import build_agent_llm_messages
from company_agent_responder import build_deterministic_company_agent_reply
from company_agent_runtime import build_company_agent_message_result


CASES = {
    "write": ("홈페이지 소개문을 써줘", "write"),
    "rewrite": ('다음 원문을 자연스럽게 고쳐줘: "공간을 완벽하게 해결합니다."', "rewrite"),
    "summarize": ("내부 운영 자료를 핵심만 요약해줘", "summarize"),
    "extract_facts": ("내부 자료에서 확인되는 사실만 뽑아줘", "extract_facts"),
    "review": ('다음 문구를 검토해줘: "과장된 문구입니다."', "review"),
    "evaluate": ("이 사업의 가능성을 평가해줘", "evaluate"),
    "recommend": ("공간 방향 세 가지를 추천해줘", "recommend"),
    "compare": ("내부 자료와 경쟁사 자료를 비교해줘", "compare"),
    "plan": ("프로젝트 실행 절차를 단계별로 정리해줘", "plan"),
    "research": ("관련 지원사업을 조사해줘", "research"),
    "status": ("홈페이지 프로젝트 현재 상태 알려줘", "status"),
    "approve_publish": ('이 문구를 홈페이지에 올려도 되는지 판단해줘: "소개문"', "approve_or_publish"),
    "execute": ("이 소개문을 홈페이지에 게시해줘", "execute"),
}


def _decision(message: str, agent: str = "lucy", reply: str = ""):
    return classify_agent_intent(
        user_message=message, selected_agent=agent, replied_message_content=reply
    )


def run_named_case(name: str) -> None:
    stem = Path(name).stem
    key = stem.removeprefix("test_agent_intent_")
    if key == stem:
        key = stem.removeprefix("test_agent_")
    if key in CASES:
        message, expected = CASES[key]
        decision = _decision(message)
        assert decision.intent == expected, (decision, expected)
        if expected == "execute":
            assert decision.approval_required is True
        print(f"PASS {key}")
        return
    if key == "priority":
        assert _decision("문구를 검토해서 게시해도 되는지 판단해줘").intent == "approve_or_publish"
        assert _decision("자료를 비교해서 소개문을 써줘").intent == "write"
    elif key == "source_text_extraction":
        assert extract_source_text('검토해줘: "충분히 긴 원문 문장입니다."', replied_message_content=None)[0]
        assert extract_source_text("고쳐줘", replied_message_content="답장으로 전달된 충분한 원문")[0]
    elif key == "instruction_not_source_text":
        decision = _decision("내부 회사소개에서 확인되는 사실을 기반으로 홈페이지 소개문을 써줘")
        assert decision.intent == "write" and not decision.source_text_present
    elif key == "response_mode_matrix":
        assert resolve_agent_response_mode(agent_name="lucy", intent="write").mode == "copywriting"
        assert resolve_agent_response_mode(agent_name="meiko", intent="plan").mode == "execution_checklist"
        assert all(agent in AGENT_INTENT_CAPABILITIES for agent in ("hermes", "kasumi", "meiko", "marin", "lucy", "reze"))
    elif key == "role_not_fixed_template":
        mode = resolve_agent_response_mode(agent_name="reze", intent="write")
        assert mode.mode == "strategy_document_draft" and not mode.fixed_role_template_used
    elif key == "prompt_context":
        decision = _decision("소개문을 써줘")
        mode = resolve_agent_response_mode(agent_name="lucy", intent=decision.intent)
        block = build_intent_prompt_context(agent_name="lucy", decision=decision, response_mode=mode)
        assert "user_intent: write" in block and "not as a fixed output template" in block
        envelope = build_agent_llm_messages("lucy", "소개문을 써줘", {"agent_intent_prompt_context": block})
        assert envelope["intent_context_used"] is True
    elif key == "rag_query_expansion":
        query = build_agent_rag_query(agent_name="lucy", intent="write", user_message="회사 소개")
        assert "홈페이지" in query and len(query) <= 900
    elif key == "metadata_boost":
        assert intent_metadata_boost("write", {"relative_path": "homepage/copy.md"}) > 0
        assert intent_metadata_boost("status", {"relative_path": "unrelated.bin"}) == 0
    elif key == "second_pass_retrieval":
        low = assess_rag_sufficiency([{"media_type": "image", "snippet": "x"}], "write")
        assert low["rag_sufficiency"] == "low"
    elif key == "rag_sufficiency":
        medium = assess_rag_sufficiency(
            [{"media_type": "document", "relative_path": "homepage/intro.md", "snippet": "a" * 300}],
            "write",
        )
        assert medium["rag_sufficiency"] == "medium"
    elif key == "deterministic_fallback":
        result = build_intent_aware_deterministic_fallback(
            agent_name="lucy", intent="write", user_message="소개문을 써줘"
        )
        assert result["deterministic_fallback_intent_aware"] and "보류" not in result["content"]
    elif key == "approval_boundary":
        assert not _decision("소개문을 써줘").approval_required
        assert _decision("소개문을 홈페이지에 게시해줘").approval_required
    elif key == "citation_behavior":
        result = build_intent_aware_deterministic_fallback(
            agent_name="lucy", intent="write", user_message="소개문을 써줘"
        )
        assert "[S1]" not in result["content"]
    elif key == "internal_web_separation":
        envelope = build_agent_llm_messages(
            "reze", "비교해줘",
            {"internal_rag_prompt_context": "[INTERNAL_RAG_CONTEXT]\nA\n[/INTERNAL_RAG_CONTEXT]",
             "web_reference_results_block": "[WEB_REFERENCE_CONTEXT]\nB\n[/WEB_REFERENCE_CONTEXT]"},
        )
        content = envelope["messages_preview"][1]["content"]
        assert content.index("[INTERNAL_RAG_CONTEXT]") < content.index("[WEB_REFERENCE_CONTEXT]")
    elif key == "no_fixture_leak":
        for agent in ("hermes", "kasumi", "meiko", "marin", "lucy", "reze"):
            result = build_intent_aware_deterministic_fallback(
                agent_name=agent, intent="write", user_message="새 문서를 써줘"
            )
            assert "MML" not in result["content"]
    else:
        raise AssertionError(f"unknown intent test: {key}")
    print(f"PASS {key}")


def run_agent_mode(agent: str, intent: str) -> None:
    messages = {
        "status": "현재 상태 알려줘",
        "write": "업무 문서 초안을 써줘",
        "research": "자료를 조사해줘",
        "summarize": "자료를 요약해줘",
        "review": '문구를 검토해줘: "충분히 긴 검토 원문입니다."',
        "plan": "실행 절차를 단계별로 정리해줘",
        "recommend": "공간 방향을 추천해줘",
        "approve_or_publish": '이 문구를 올려도 되는지 판단해줘: "소개 문구"',
        "evaluate": "사업성을 평가해줘",
    }
    decision = _decision(messages[intent], agent)
    assert decision.intent == intent
    route = {
        "agent_intent": intent,
        "agent_response_mode": resolve_agent_response_mode(agent_name=agent, intent=intent).mode,
        "source_text_present": decision.source_text_present,
        "source_text": decision.source_text,
        "approval_required": decision.approval_required,
    }
    response = build_deterministic_company_agent_reply(agent, messages[intent], route)
    assert response["fixed_role_template_used"] is False
    if intent == "write":
        assert "보류" not in response["content"] and "최종승인" not in response["content"]
    if agent == "lucy" and intent == "write":
        runtime = build_company_agent_message_result(
            "marketing-brief",
            "!lucy 내부 회사소개에서 확인되는 사실을 기반으로 홈페이지 소개문을 써줘",
            env={
                "HERMES_COMPANY_AGENT_REPLY_MODE": "deterministic_fallback",
                "HERMES_AGENT_RAG_ENABLED": "false",
            },
        )
        assert runtime["selected_agent"] == "lucy"
        assert runtime["agent_intent"] == "write"
        assert runtime["agent_response_mode"] == "copywriting"
        assert runtime["source_text_present"] is False
        assert runtime["approval_required"] is False
        assert runtime["discord_api_send_called"] is False
        assert runtime["discord_message_sent"] is False
        assert runtime["external_execution"] is False
    print(f"PASS {agent}_{intent}_mode")

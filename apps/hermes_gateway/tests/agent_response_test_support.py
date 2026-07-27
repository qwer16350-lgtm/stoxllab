from __future__ import annotations

import asyncio
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import company_agent_runtime as runtime
from company_agent_citations import apply_grounded_answer_citations
from company_agent_output import (
    OMISSION_NOTICE,
    assemble_agent_response,
    split_discord_response,
)
from company_agent_responder import build_deterministic_company_agent_reply
from company_agent_llm import generate_agent_reply
from company_discord_outbound_guard import (
    prepare_discord_outbound_messages,
    send_discord_messages_safely,
)


BODY = "\n\n".join(
    f"{index}. 스톡슬의 공간 전략은 사용 조건과 운영 근거를 함께 검토합니다."
    for index in range(1, 70)
)
FOOTER = "참고한 내부 자료\n[S1] 회사소개 - docs/company.md\n[S2] 사업계획 - docs/plan.md"


def _chunks(body: str = BODY, footer: str = FOOTER, max_chars: int = 420, max_chunks: int = 8):
    return split_discord_response(
        body=body,
        source_footer=footer,
        max_chunk_chars=max_chars,
        max_chunks=max_chunks,
    )


def _joined_without_footer(chunks: list[str]) -> str:
    return "\n".join(chunks)


def _mock_grounded(text: str) -> dict:
    return apply_grounded_answer_citations(
        text,
        [
            {"source_id": "S1", "source_label": "회사소개", "relative_path": "docs/company.md"},
            {"source_id": "S2", "source_label": "사업계획", "relative_path": "docs/plan.md"},
        ],
        {
            "HERMES_AGENT_GROUNDED_ANSWERS_ENABLED": "true",
            "HERMES_AGENT_SOURCE_CITATIONS_ENABLED": "true",
        },
    )


def run_named_case(filename: str) -> None:
    key = Path(filename).stem.removeprefix("test_agent_response_")
    if key == "no_mid_sentence_truncation":
        chunks = _chunks(max_chars=800, max_chunks=8)
        assert all(not chunk.endswith(("실제", "확")) for chunk in chunks)
        assert all(len(chunk) <= 800 for chunk in chunks)
        generated = "완결된 장문 응답입니다. " * 250
        llm = generate_agent_reply(
            "reze",
            "!reze 장문을 작성해줘",
            {"command": "reze"},
            {
                "HERMES_COMPANY_AGENT_LLM_ENABLED": "true",
                "HERMES_COMPANY_AGENT_LLM_MODE": "manual_command_only",
                "HERMES_LLM_API_KEY": "test-only",
                "HERMES_LLM_MODEL": "mock",
            },
            llm_caller=lambda _prompt, _config: {
                "api_call_attempted": True,
                "api_call_succeeded": True,
                "response_text": generated,
            },
        )
        assert llm["response_text"] == generated.strip()
    elif key == "body_preserved_before_footer":
        chunks = _chunks(max_chars=500, max_chunks=8)
        joined = _joined_without_footer(chunks)
        assert joined.index("공간 전략") < joined.index("참고한 내부 자료")
    elif key == "semantic_chunking":
        chunks = _chunks(max_chars=500, max_chunks=8)
        assert len(chunks) > 1 and all(len(chunk) <= 500 for chunk in chunks)
    elif key == "paragraph_boundary":
        chunks = _chunks(body=("첫 문단입니다.\n\n" * 80), footer="", max_chars=300)
        assert all(chunk.endswith(".") for chunk in chunks)
    elif key == "sentence_boundary":
        chunks = _chunks(body=("완결된 문장입니다. " * 100), footer="", max_chars=300)
        assert all(chunk.endswith(".") for chunk in chunks)
    elif key == "footer_last_chunk":
        chunks = _chunks(max_chars=600)
        assert "참고한 내부 자료" in chunks[-1]
        assert all("참고한 내부 자료" not in chunk for chunk in chunks[:-1])
    elif key == "footer_separate_chunk":
        chunks = _chunks(body=("가" * 150) + ".", max_chars=180)
        assert chunks[-1].startswith("참고한 내부 자료")
    elif key == "citation_before_chunking":
        grounded = _mock_grounded("확인된 사실입니다. [S1]")
        rendered = assemble_agent_response(body=grounded["body"], source_footer=grounded["source_footer"])
        assert rendered.metadata["citation_validation_before_chunking"] is True
        assert grounded["citation_ids_valid"] == ["S1"]
    elif key == "valid_citations_across_chunks":
        grounded = _mock_grounded(("확인된 사실입니다. [S1]\n\n" * 100) + "추가 사실입니다. [S2]")
        chunks = _chunks(grounded["body"], grounded["source_footer"], 500, 8)
        assert "[S1]" in "\n".join(chunks) and "[S2]" in "\n".join(chunks)
        assert "회사소개" in chunks[-1] and "사업계획" in chunks[-1]
    elif key == "max_chunks":
        chunks = _chunks(body="긴 설명입니다. " * 5000, footer="", max_chars=300, max_chunks=3)
        assert len(chunks) == 3 and OMISSION_NOTICE in chunks[-1]
    elif key == "explicit_omission_notice":
        rendered = assemble_agent_response(
            body="완결된 설명입니다. " * 5000,
            env={"HERMES_AGENT_MAX_RESPONSE_CHARS": "1200"},
        )
        assert rendered.metadata["body_truncated"] is True
        assert rendered.body.endswith(OMISSION_NOTICE)
    elif key == "code_block_chunking":
        code = "설명입니다.\n\n```python\n" + ("print('safe')\n" * 120) + "```\n\n끝입니다."
        chunks = _chunks(code, "", 350, 8)
        assert all(chunk.count("```") % 2 == 0 for chunk in chunks)
        assert all(len(chunk) <= 350 for chunk in chunks)
    elif key == "list_chunking":
        chunks = _chunks("\n".join(f"{i}. 완결된 목록 항목입니다." for i in range(100)), "", 300, 8)
        assert all(not chunk.startswith("완결된 목록") for chunk in chunks[1:])
    elif key == "real_bot_all_chunks_sent":
        sent: list[str] = []
        original_env = runtime._runtime_env
        original_send = runtime.send_as_real_agent_bot

        async def fake_send(_fleet, _agent, _channel, content):
            sent.append(content)
            return {"blocked": False, "message_sent_count": 1, "discord_message_sent": True}

        class Client:
            _agent_bot_fleet = object()

        class Channel:
            name = "marketing-brief"

            async def send(self, content):
                sent.append(content)

        runtime._runtime_env = lambda: {
            "sender_mode": "real_bot",
            "real_bots_enabled": True,
            "webhook_enabled": False,
            "webhook_persona_enabled": False,
            "webhook_create_enabled": False,
        }
        runtime.send_as_real_agent_bot = fake_send
        try:
            result = asyncio.run(runtime._send_agent_content(Client(), "lucy", Channel(), BODY))
        finally:
            runtime._runtime_env = original_env
            runtime.send_as_real_agent_bot = original_send
        assert result["message_sent_count"] == len(result["messages"]) == len(sent)
    elif key == "bot_fallback_all_chunks_sent":
        sent: list[str] = []

        async def send_one(content):
            sent.append(content)

        messages = _chunks(max_chars=500)
        result = asyncio.run(send_discord_messages_safely(send_one, messages))
        assert result["message_sent_count"] == len(messages) == len(sent)
    elif key == "partial_send_report":
        sent: list[str] = []

        async def send_one(content):
            if len(sent) == 2:
                raise RuntimeError("send failed")
            sent.append(content)

        result = asyncio.run(send_discord_messages_safely(send_one, ["a", "b", "c"]))
        assert result["message_sent_count"] == 2
        assert result["discord_message_sent"] is True
    elif key == "outbound_guard_each_chunk":
        prepared = prepare_discord_outbound_messages(
            ("안전한 문장입니다. token=secret-value\n\n" * 200),
            "lucy",
            compact_web_reference=False,
        )
        assert len(prepared["messages"]) > 1
        assert all("secret-value" not in chunk for chunk in prepared["messages"])
    elif key == "no_header_repetition":
        chunks = _chunks(body="[REZE_STOXL / 레제]\n" + BODY, footer="", max_chars=450)
        assert chunks[0].startswith("[REZE_STOXL / 레제]")
        assert all("[REZE_STOXL / 레제]" not in chunk for chunk in chunks[1:])
    elif key == "deterministic_fallback_chunking":
        response = build_deterministic_company_agent_reply(
            "lucy",
            "소개문을 써줘",
            {"agent_intent": "write", "agent_response_mode": "copywriting"},
        )
        assert response["semantic_chunking_enabled"] is True
        assert response["response_chunk_count"] >= 1
    elif key == "all_agents_shared_pipeline":
        for agent in ("hermes", "kasumi", "meiko", "marin", "lucy", "reze"):
            response = build_deterministic_company_agent_reply(
                agent,
                "업무 문서 초안을 써줘",
                {"agent_intent": "write", "agent_response_mode": "general_business_draft"},
            )
            assert response["discord_chunking_enabled"] is True
            assert response["sentence_midpoint_truncation"] is False
    else:
        raise AssertionError(f"unknown response test: {key}")
    print(f"PASS {key}")

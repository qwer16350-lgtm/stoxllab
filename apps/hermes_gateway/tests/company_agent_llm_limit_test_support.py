from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from company_agent_llm import _llm_config, generate_agent_reply
from company_agent_output import assemble_agent_response
from llm_client import build_llm_client_config, call_llm_once
from llm_safety_policy import PROVIDER_LENGTH_NOTICE


def _env(**overrides: str) -> dict[str, str]:
    return {
        "HERMES_COMPANY_AGENT_LLM_ENABLED": "true",
        "HERMES_COMPANY_AGENT_LLM_MODE": "manual_command_only",
        "HERMES_LLM_API_KEY": "test-only",
        "HERMES_LLM_MODEL": "mock-model",
        **overrides,
    }


def _generate(text: str, finish_reason: str = "stop", **env_overrides: str):
    calls = {"count": 0, "config": {}}

    def caller(_prompt, config):
        calls["count"] += 1
        calls["config"] = config
        return {
            "api_call_attempted": True,
            "api_call_succeeded": True,
            "response_text": text,
            "provider_finish_reason": finish_reason,
        }

    result = generate_agent_reply(
        "lucy",
        "!lucy 회사 소개문을 작성해줘",
        {"command": "lucy"},
        _env(**env_overrides),
        llm_caller=caller,
    )
    return result, calls


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {"content": "정상 응답입니다."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {},
            }
        ).encode("utf-8")


def run_named_case(filename: str) -> None:
    key = Path(filename).stem.removeprefix("test_company_agent_llm_")
    if key == "default_output_chars_8000":
        assert _llm_config(_env())["max_output_chars"] == 8000
        assert build_llm_client_config({})["max_output_chars"] == 1200
    elif key == "provider_max_tokens":
        captured: dict = {}

        def opener(request, timeout=0):
            del timeout
            captured.update(json.loads(request.data.decode("utf-8")))
            return _Response()

        config = _llm_config(_env())
        result = call_llm_once(
            {"messages_preview": [{"role": "user", "content": "test"}]},
            config,
            opener=opener,
        )
        assert captured["max_tokens"] >= 2000
        assert result["provider_finish_reason"] == "stop"
    elif key == "finish_reason_stop":
        result, calls = _generate("첫 문장입니다. 두 번째 문장입니다.", "stop")
        assert result["provider_finish_reason"] == "stop"
        assert result["provider_output_incomplete"] is False
        assert result["llm_complete"] is True
        assert calls["count"] == 1
    elif key == "finish_reason_length":
        result, calls = _generate("완결된 문장입니다. 이어지는 문장은 중간에서 종", "length")
        assert result["provider_output_incomplete"] is True
        assert result["llm_complete"] is False
        assert result["response_text"].startswith("완결된 문장입니다.")
        assert "중간에서 종" not in result["response_text"]
        assert result["response_text"].endswith(PROVIDER_LENGTH_NOTICE)
        assert calls["count"] == 1
    elif key == "no_1200_char_truncation":
        text = "완결된 상세 설명입니다. " * 140
        assert len(text) > 1200 and len(text) < 8000
        result, _calls = _generate(text, "stop")
        assert result["response_text"] == text.strip()
        assert result["generation_output_chars"] == len(text)
    elif key == "sentence_safe_limit":
        text = ("보존할 완결 문장입니다. " * 30) + "마지막 불완전 단"
        result, _calls = _generate(
            text,
            "stop",
            HERMES_COMPANY_AGENT_LLM_MAX_OUTPUT_CHARS="400",
        )
        assert result["generation_output_shortened"] is True
        assert result["generation_sentence_midpoint_truncation"] is False
        assert "마지막 불완전 단" not in result["response_text"]
        assert result["response_text"].endswith("응답이 길어 일부 부가 설명을 생략했습니다.")
    elif key == "generation_and_discord_limits_separated":
        text = "완결된 회사 소개 문장입니다. " * 180
        result, calls = _generate(text, "stop")
        rendered = assemble_agent_response(body=result["response_text"], env=_env())
        assert calls["config"]["max_output_chars"] == 8000
        assert rendered.metadata["agent_max_response_chars"] == 12000
        assert rendered.metadata["discord_chunk_max_chars"] == 1800
        assert len(rendered.chunks) > 1
        assert all(len(chunk) <= 1800 for chunk in rendered.chunks)
    elif key == "single_call_preserved":
        result, calls = _generate("완결된 문장입니다. 잘린 후속", "length")
        assert calls["count"] == 1
        assert result["provider_output_incomplete"] is True
    else:
        raise AssertionError(f"unknown company agent LLM limit test: {key}")
    print(f"PASS {key}")

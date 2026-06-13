"""Private-test-only LLM dry call orchestration for Phase 32B."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_client import (
    assert_llm_client_result_safe,
    build_llm_client_config,
    build_mock_llm_response,
    call_llm_once,
    public_llm_client_config,
    validate_llm_client_config,
)
from llm_preflight import build_llm_preflight_report
from llm_prompt_envelope import build_llm_prompt_envelope, redact_llm_prompt_content
from llm_safety_policy import build_llm_safety_policy, check_llm_output_allowed


VERSION = "phase32b_private_test_only_no_discord_send"
SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_filename_part(value: Any, fallback: str = "unknown") -> str:
    text = str(value or fallback).strip().replace("/", "-")
    text = SAFE_FILENAME_RE.sub("-", text).strip("-._").lower()
    return text or fallback


def _artifact_stem(report: dict[str, Any]) -> str:
    created = str(report.get("created_at", utc_now()))
    stamp = created[:19].replace("-", "").replace(":", "").replace("T", "_")
    result = report.get("client_result", {}) if isinstance(report.get("client_result"), dict) else {}
    provider = _safe_filename_part(result.get("provider"), "provider")
    model = _safe_filename_part(result.get("model"), "model")
    return f"llm_dry_call_{stamp}_{provider}_{model}"


def build_llm_dry_call_request(
    agent_route_candidate: str = "marin",
    user_content_preview: str | None = None,
    env: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = build_llm_client_config(env)
    return {
        "request_type": "llm_dry_call_request",
        "version": VERSION,
        "agent_route_candidate": agent_route_candidate,
        "channel_scope": "private_test_only",
        "user_content_preview": redact_llm_prompt_content(
            user_content_preview or "Private test LLM dry call preview. Prepare a review-only draft."
        ),
        "allow_api_call": False,
        "discord_send_enabled": bool(config.get("discord_send_enabled") or config.get("discord_runtime_send_messages")),
        "rag_enabled": bool(config.get("rag_enabled")),
        "external_execution": bool(config.get("external_execution")),
    }


def _blocked_result(config: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "result_type": "llm_client_result",
        "version": "phase32b_private_test_dry_call",
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "api_call_attempted": False,
        "api_call_succeeded": False,
        "api_call_failed": True,
        "error_type": reason,
        "response_text": "",
        "usage": {
            "input_chars": 0,
            "output_chars": 0,
            "estimated_cost_krw": None,
        },
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }


def run_llm_dry_call(
    request: dict[str, Any],
    env: dict[str, Any] | None = None,
    allow_api_call: bool = False,
) -> dict[str, Any]:
    selected_request = dict(request)
    selected_request["allow_api_call"] = bool(allow_api_call)
    config = build_llm_client_config(env)
    safety_policy = build_llm_safety_policy(env)
    safety_policy["max_output_chars"] = int(config.get("max_output_chars", 1200))
    envelope = build_llm_prompt_envelope(
        str(request.get("agent_route_candidate", "marin")),
        str(request.get("user_content_preview", "")),
        policy={"max_input_chars": 4000},
    )
    _apply_phase32b_prompt_safety_instruction(envelope)
    validation = validate_llm_client_config(config)
    block_reasons: list[str] = []
    if selected_request.get("channel_scope") != "private_test_only":
        block_reasons.append("not_private_test_context")
    if selected_request.get("discord_send_enabled") or config.get("discord_send_enabled") or config.get("discord_runtime_send_messages"):
        block_reasons.append("discord_send_enabled")
    if selected_request.get("rag_enabled") or config.get("rag_enabled"):
        block_reasons.append("rag_enabled")
    if selected_request.get("external_execution") or config.get("external_execution"):
        block_reasons.append("external_execution_enabled")

    if allow_api_call:
        if validation["blocked"]:
            block_reasons.extend([reason for reason in validation["blocked_reasons"] if reason not in block_reasons])
        result = _blocked_result(config, "api_call_gate_blocked") if block_reasons else call_llm_once(envelope, config)
    else:
        result = build_mock_llm_response(envelope, config)

    output_check = check_llm_output_allowed(result.get("response_text", ""), safety_policy)
    return build_llm_dry_call_report(selected_request, result, output_check, envelope=envelope, preflight=build_llm_preflight_report(env), config=config)


def _apply_phase32b_prompt_safety_instruction(envelope: dict[str, Any]) -> None:
    messages = envelope.get("messages_preview", [])
    if not messages:
        return
    instruction = (
        " Use review-only wording. Do not say that anything was published, submitted, sent, "
        "uploaded, approved, confirmed, or externally delivered. You may say that no such "
        "action has been taken."
    )
    messages[0]["content"] = str(messages[0].get("content", "")) + instruction


def build_llm_dry_call_report(
    request: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    output_check: dict[str, Any] | None = None,
    *,
    envelope: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_request = request or build_llm_dry_call_request()
    selected_envelope = envelope or build_llm_prompt_envelope(
        str(selected_request.get("agent_route_candidate", "marin")),
        str(selected_request.get("user_content_preview", "")),
    )
    selected_result = result or build_mock_llm_response(selected_envelope)
    selected_output = output_check or check_llm_output_allowed(selected_result.get("response_text", ""), build_llm_safety_policy({}))
    report = {
        "report_type": "llm_dry_call_report",
        "version": VERSION,
        "created_at": utc_now(),
        "request": selected_request,
        "preflight": preflight or build_llm_preflight_report({}),
        "client_config": public_llm_client_config(config or build_llm_client_config({})),
        "prompt_envelope": selected_envelope,
        "client_result": selected_result,
        "output_safety": {
            "allowed": bool(selected_output.get("allowed")),
            "blocked": bool(selected_output.get("blocked")),
            "blocked_reasons": selected_output.get("blocked_reasons", []),
            "safe_disclaimer_detected": bool(selected_output.get("safe_disclaimer_detected")),
            "safe_disclaimer_reasons": selected_output.get("safe_disclaimer_reasons", []),
            "reason": selected_output.get("reason", ""),
        },
        "artifact_paths": [],
        "ready_for_phase32c_private_test_reply": bool(selected_output.get("allowed")) and bool(selected_result.get("response_text")),
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "safety_assertions": {
            "llm_api_called_only_when_explicitly_enabled": True,
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_llm_dry_call_report_safe(report)
    return report


def write_llm_dry_call_artifact(report: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root) if root else Path.cwd()
    day = str(report.get("created_at", utc_now()))[:10].replace("-", "")
    target_dir = base / "exports" / "hermes_gateway" / "llm_dry_calls" / day
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = _artifact_stem(report)
    json_path = target_dir / f"{stem}.json"
    markdown_path = target_dir / f"{stem}.md"
    report_with_paths = dict(report)
    report_with_paths["artifact_paths"] = [str(json_path), str(markdown_path)]
    json_path.write_text(json.dumps(report_with_paths, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(render_llm_dry_call_markdown(report_with_paths), encoding="utf-8")
    return {"artifact_paths": report_with_paths["artifact_paths"], "message_sent": False, "discord_send_attempted": False}


def render_llm_dry_call_markdown(report: dict[str, Any]) -> str:
    result = report.get("client_result", {})
    output = report.get("output_safety", {})
    return "\n".join(
        [
            "# LLM Dry Call Report",
            "",
            f"- version: {report.get('version', '')}",
            f"- provider: {result.get('provider', '')}",
            f"- model: {result.get('model', '')}",
            f"- api_call_attempted: {str(result.get('api_call_attempted')).lower()}",
            f"- api_call_succeeded: {str(result.get('api_call_succeeded')).lower()}",
            f"- output_allowed: {str(output.get('allowed')).lower()}",
            f"- output_blocked: {str(output.get('blocked')).lower()}",
            "- message_sent: false",
            "- discord_send_attempted: false",
            "- rag_called: false",
            "- external_execution: false",
            "",
            "## Response Preview",
            str(result.get("response_text", "")),
        ]
    ) + "\n"


def assert_llm_dry_call_report_safe(report: dict[str, Any]) -> None:
    assert_llm_client_result_safe(report.get("client_result", {}))
    text = json.dumps(report, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or "bearer " in text:
        raise ValueError("LLM dry call report contains secret-like text.")
    if any(str(report.get(key)).lower() == "true" for key in ("message_sent", "discord_send_attempted", "rag_called", "external_execution")):
        raise ValueError("LLM dry call report has unsafe top-level execution flag.")
    assertions = report.get("safety_assertions", {})
    for key in ("api_key_value_logged", "discord_message_sent", "rag_called", "external_execution", "raw_discord_ids_logged"):
        if assertions.get(key):
            raise ValueError(f"LLM dry call report unsafe assertion is true: {key}")

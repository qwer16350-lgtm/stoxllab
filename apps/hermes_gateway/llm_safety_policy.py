"""Phase 32A local-only LLM request and output safety policy."""

from __future__ import annotations

import json
import os
import re
from typing import Any


VERSION = "phase32a_no_api_call"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+)")
EXECUTION_CLAIM_RE = re.compile(r"(?i)(posted|published|submitted|sent|uploaded|confirmed|approved|executed|completed|발행|게시|제출|발송|업로드|확정|실행|완료)")
EXTERNAL_ACTION_RE = re.compile(r"(?i)(will post|will publish|will submit|will send|will upload|send the email|submit the application|external action|외부 실행|이메일 발송|지원사업 제출)")
APPROVAL_CLAIM_RE = re.compile(r"(?i)(approved|final approval|approval complete|승인했습니다|최종 승인|승인 완료)")
PRICE_CONFIRM_RE = re.compile(r"(?i)(price confirmed|confirmed price|가격 확정|견적 확정)")
CONTRACT_CONFIRM_RE = re.compile(r"(?i)(contract confirmed|contract approved|계약 확정|계약 승인|계약 체결)")
DELIVERY_CONFIRM_RE = re.compile(r"(?i)(delivery confirmed|delivery date confirmed|납기 확정|배송 확정)")
PUBLIC_PUBLISH_RE = re.compile(r"(?i)(published publicly|posted publicly|sns published|homepage updated|공개 게시|SNS 발행|홈페이지 반영)")
BLOCKED_OUTPUT_PATTERNS = {
    "sns_publish": re.compile(r"(?i)(sns|instagram|인스타|게시|발행).*(완료|진행|하겠습니다|확정)"),
    "homepage_upload": re.compile(r"(?i)(homepage|홈페이지|업로드|반영).*(완료|진행|하겠습니다|확정)"),
    "competition_submit": re.compile(r"(?i)(공모전|competition).*(제출|접수|신청).*(완료|진행|하겠습니다|확정)?"),
    "grant_submit": re.compile(r"(?i)(지원사업|grant).*(제출|접수|신청).*(완료|진행|하겠습니다|확정)?"),
    "external_email_send": re.compile(r"(?i)(이메일|email|메일).*(발송|보내겠습니다|전송)"),
    "contract_confirm": re.compile(r"(?i)(계약|contract).*(확정|승인|체결)"),
    "price_confirm": re.compile(r"(?i)(가격|price|견적).*(확정|승인)"),
    "delivery_schedule_confirm": re.compile(r"(?i)(납기|delivery|일정).*(확정|승인)"),
}


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _env_value(env: dict[str, Any] | None, key: str, default: str = "") -> str:
    if env is not None:
        return str(env.get(key, default) or "")
    return os.environ.get(key, default)


def build_llm_safety_policy(env: dict[str, Any] | None = None) -> dict[str, Any]:
    private_test_only = _flag(_env_value(env, "HERMES_LLM_PRIVATE_TEST_ONLY", "true"), True)
    allow_discord_send = _flag(_env_value(env, "HERMES_LLM_ALLOW_DISCORD_SEND", "false"))
    return {
        "policy_type": "llm_safety_policy",
        "version": VERSION,
        "private_test_only": private_test_only,
        "allow_public_channel": False,
        "allow_external_execution": False,
        "allow_rag": False,
        "allow_discord_send": allow_discord_send,
        "require_human_review_for_external_actions": True,
        "blocked_output_intents": list(BLOCKED_OUTPUT_PATTERNS.keys()),
        "allowed_response_sources": [
            "agent_placeholder_response",
            "future_llm_private_test_response",
        ],
        "safety_assertions": {
            "llm_api_called": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
        },
    }


def check_llm_request_allowed(context: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    channel_scope = str(context.get("channel_scope", "private_test_only") or "")
    if policy.get("private_test_only") and channel_scope != "private_test_only":
        reasons.append("public_or_team_channel_blocked")
    if context.get("request_external_execution"):
        reasons.append("external_execution_blocked")
    if context.get("request_rag"):
        reasons.append("rag_blocked")
    if context.get("request_discord_send") or policy.get("allow_discord_send"):
        reasons.append("discord_send_blocked")
    return {
        "decision_type": "llm_request_safety_decision",
        "allowed": not reasons,
        "blocked": bool(reasons),
        "blocked_reasons": reasons,
        "message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def check_llm_output_allowed(output_text: str, policy: dict[str, Any]) -> dict[str, Any]:
    text = output_text or ""
    matched = [intent for intent, pattern in BLOCKED_OUTPUT_PATTERNS.items() if pattern.search(text)]
    blocked_reasons: list[str] = []
    max_output_chars = int(policy.get("max_output_chars", 1200) or 1200)
    if not text.strip():
        blocked_reasons.append("empty_output")
    if len(text) > max_output_chars:
        blocked_reasons.append("output_too_long")
    if EXECUTION_CLAIM_RE.search(text) or EXTERNAL_ACTION_RE.search(text):
        blocked_reasons.append("external_action_claim")
    if APPROVAL_CLAIM_RE.search(text):
        blocked_reasons.append("approval_claim")
    if PRICE_CONFIRM_RE.search(text):
        blocked_reasons.append("price_confirmation_claim")
    if CONTRACT_CONFIRM_RE.search(text):
        blocked_reasons.append("contract_confirmation_claim")
    if DELIVERY_CONFIRM_RE.search(text):
        blocked_reasons.append("delivery_confirmation_claim")
    if PUBLIC_PUBLISH_RE.search(text):
        blocked_reasons.append("public_publish_claim")
    if policy.get("allow_discord_send"):
        blocked_reasons.append("discord_send_not_allowed")
    for intent in matched:
        if intent not in blocked_reasons:
            blocked_reasons.append(intent)
    return {
        "decision_type": "llm_output_safety_decision",
        "allowed": not blocked_reasons,
        "blocked": bool(blocked_reasons),
        "review_required": True,
        "matched_blocked_intents": matched,
        "blocked_reasons": blocked_reasons,
        "reason": "blocked_output_intent_detected" if blocked_reasons else "review_only_output_allowed",
        "message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
    }


def build_llm_safety_policy_report(env: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = build_llm_safety_policy(env)
    sample_request = check_llm_request_allowed({"channel_scope": "private_test_only"}, policy)
    sample_output = check_llm_output_allowed("검토용 초안입니다. 승인 후 진행해 주세요.", policy)
    report = {
        "report_type": "llm_safety_policy_report",
        "version": VERSION,
        "policy": policy,
        "sample_private_test_request": sample_request,
        "sample_review_only_output": sample_output,
        "message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
    }
    assert_llm_safety_policy_safe(report)
    return report


def assert_llm_safety_policy_safe(policy_or_report: dict[str, Any]) -> None:
    text = json.dumps(policy_or_report, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM safety policy contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM safety policy contains raw Discord-like IDs.")
    for key in ("message_sent", "llm_api_called", "rag_called", "external_execution"):
        if policy_or_report.get(key):
            raise ValueError(f"LLM safety policy unsafe flag is true: {key}")
    assertions = policy_or_report.get("safety_assertions") or policy_or_report.get("policy", {}).get("safety_assertions", {})
    for key in ("llm_api_called", "discord_message_sent", "rag_called", "external_execution"):
        if assertions.get(key):
            raise ValueError(f"LLM safety policy assertion is unsafe: {key}")

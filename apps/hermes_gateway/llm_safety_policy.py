"""Phase 32A local-only LLM request and output safety policy."""

from __future__ import annotations

import json
import os
import re
from typing import Any


VERSION = "phase32a_no_api_call"
OUTPUT_LIMIT_NOTICE = "응답이 길어 일부 부가 설명을 생략했습니다."
PROVIDER_LENGTH_NOTICE = "응답 생성 한도에 도달해 일부 설명이 생략되었습니다."
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+)")
EXECUTION_CLAIM_RE = re.compile(r"(?i)(posted|published|submitted|sent|uploaded|confirmed|approved|executed|completed|발행|게시|제출|발송|업로드|확정|실행|완료)")
EXTERNAL_ACTION_RE = re.compile(r"(?i)(will post|will publish|will submit|will send|will upload|send the email|submit the application|external action|외부 실행|이메일 발송|지원사업 제출)")
APPROVAL_CLAIM_RE = re.compile(r"(?i)(approved|final approval|approval complete|승인했습니다|최종 승인|승인 완료)")
PRICE_CONFIRM_RE = re.compile(r"(?i)(price confirmed|confirmed price|가격 확정|견적 확정)")
CONTRACT_CONFIRM_RE = re.compile(r"(?i)(contract confirmed|contract approved|계약 확정|계약 승인|계약 체결)")
DELIVERY_CONFIRM_RE = re.compile(r"(?i)(delivery confirmed|delivery date confirmed|납기 확정|배송 확정)")
PUBLIC_PUBLISH_RE = re.compile(r"(?i)(published publicly|posted publicly|sns published|homepage updated|공개 게시|SNS 발행|홈페이지 반영)")
NEGATED_ACTION_MADE_RE = re.compile(r"(?i)\bno\b.{0,100}\b(publishing|published|posted|posting|uploaded|upload|external delivery|delivery|delivered)\b.{0,60}\b(has|have)\s+been\s+made\b")
NEGATED_PUBLICATION_RE = re.compile(r"(?i)\b(no|not|never|has not|have not|was not|were not)\b.{0,40}\b(publishing|published|posted|posting|uploaded|upload)\b|\b(publishing|published|posted|uploaded)\b.{0,40}\b(not|no|never)\b")
NEGATED_DELIVERY_RE = re.compile(r"(?i)\b(no|not|never|has not|have not|was not|were not)\b.{0,50}\b(external delivery|delivery|delivered)\b|\b(external delivery|delivery|delivered)\b.{0,50}\b(not|no|never)\b")
NEGATED_EXTERNAL_ACTION_RE = re.compile(
    r"(?i)\b("
    r"no\s+external\s+actions?\s+(has|have)\s+been\s+taken|"
    r"i\s+have\s+not\s+taken\s+any\s+external\s+action|"
    r"no\s+action\s+has\s+been\s+taken|"
    r"no\s+external\s+execution\s+(occurred|has\s+occurred)|"
    r"nothing\s+has\s+been\s+.{0,120}\b(externally\s+delivered|published|submitted|sent|uploaded|approved|confirmed)\b"
    r")\b"
)
NEGATED_SUBMISSION_RE = re.compile(r"(?i)\b(not|no|never|has not|have not)\b.{0,40}\b(submitted|submission|submit)\b|\b(submitted|submission)\b.{0,40}\b(not|no|never)\b")
NEGATED_EMAIL_RE = re.compile(r"(?i)\b(no|not|never|has not|have not)\b.{0,40}\b(email|sent|send)\b|\b(email|sent)\b.{0,40}\b(not|no|never)\b")
NEGATED_APPROVAL_RE = re.compile(r"(?i)\b(no|not|never|has not|have not)\b.{0,40}\b(approval|approved|granted)\b|\b(approval|approved|granted)\b.{0,40}\b(not|no|never)\b")
NEGATED_CONTRACT_RE = re.compile(r"(?i)\b(no|not|never|has not|have not)\b.{0,40}\b(contract|confirmed)\b|\b(contract|confirmed)\b.{0,40}\b(not|no|never)\b")
NEGATED_DELIVERY_CONFIRM_RE = re.compile(r"(?i)\b(no|not|never|has not|have not)\b.{0,50}\b(delivery date|delivery|confirmed)\b|\b(delivery date|delivery confirmed)\b.{0,50}\b(not|no|never)\b")
REVIEW_ONLY_RE = re.compile(r"(?i)\b(internal review only|review-only|for review only|draft only|review draft|검토용)\b")
PUBLIC_PUBLISH_CLAIM_RE = re.compile(r"(?i)\b(i|we|this|it)?\s*(published|posted|uploaded)\b|published publicly|posted on sns|uploaded it to the homepage|homepage updated")
SUBMISSION_CLAIM_RE = re.compile(r"(?i)\b(i|we|this|it)?\s*submitted\b|submitted the application|application submitted")
EMAIL_SEND_CLAIM_RE = re.compile(r"(?i)\b(i|we)?\s*sent\s+(the\s+)?email\b|email has been sent|email sent")
APPROVAL_POSITIVE_RE = re.compile(r"(?i)\b(this is approved|approved\.|final approval is complete|approval is complete|approval complete)\b")
EXTERNAL_ACTION_CLAIM_RE = re.compile(r"(?i)\b(executed|completed|external action completed|external delivery has been made)\b")
PRICE_CONFIRM_CLAIM_RE = re.compile(r"(?i)\b(price is confirmed|the price is confirmed|price confirmed|confirmed price)\b")
CONTRACT_CONFIRM_CLAIM_RE = re.compile(r"(?i)\b(contract is confirmed|the contract is confirmed|contract confirmed|contract approved)\b")
DELIVERY_CONFIRM_CLAIM_RE = re.compile(r"(?i)\b(delivery date is confirmed|the delivery date is confirmed|delivery confirmed|delivery date confirmed)\b")
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
        "max_output_chars": int(_env_value(env, "HERMES_LLM_MAX_OUTPUT_CHARS", "1200") or 1200),
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


def _sentence_safe_prefix(text: str, limit: int) -> str:
    candidate = str(text or "")[: max(limit, 0)].rstrip()
    matches = list(re.finditer(r"(?:[.!?。！？](?=\s|$)|(?:다|한다|입니다|됩니다|있습니다|없습니다)\.?(?=\s|$))", candidate))
    if matches:
        return candidate[: matches[-1].end()].rstrip()
    paragraph = candidate.rfind("\n\n")
    if paragraph > 0:
        return candidate[:paragraph].rstrip()
    return ""


def enforce_llm_output_limit(
    output_text: str,
    max_output_chars: int,
    *,
    provider_output_incomplete: bool = False,
) -> dict[str, Any]:
    text = str(output_text or "").strip()
    notice = PROVIDER_LENGTH_NOTICE if provider_output_incomplete else OUTPUT_LIMIT_NOTICE
    needs_shortening = provider_output_incomplete or len(text) > max_output_chars
    if not needs_shortening:
        return {
            "safe_output_text": text,
            "output_was_shortened": False,
            "sentence_midpoint_truncation": False,
        }
    budget = max(1, max_output_chars - len(notice) - 2)
    safe_prefix = _sentence_safe_prefix(text, budget)
    return {
        "safe_output_text": f"{safe_prefix}\n\n{notice}".strip(),
        "output_was_shortened": True,
        "sentence_midpoint_truncation": False,
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
    safe_disclaimer_reasons = _safe_disclaimer_reasons(text)
    safe_disclaimer_detected = bool(safe_disclaimer_reasons)
    max_output_chars = int(policy.get("max_output_chars", 1200) or 1200)
    bounded = enforce_llm_output_limit(text, max_output_chars)
    if not text.strip():
        blocked_reasons.append("empty_output")
    if len(text) > max_output_chars:
        blocked_reasons.append("output_too_long")
    if EXTERNAL_ACTION_CLAIM_RE.search(text) or EXTERNAL_ACTION_RE.search(text):
        blocked_reasons.append("external_action_claim")
    if PUBLIC_PUBLISH_CLAIM_RE.search(text) or PUBLIC_PUBLISH_RE.search(text):
        blocked_reasons.append("public_publish_claim")
    if SUBMISSION_CLAIM_RE.search(text):
        blocked_reasons.append("submission_claim")
    if EMAIL_SEND_CLAIM_RE.search(text):
        blocked_reasons.append("email_send_claim")
    if APPROVAL_POSITIVE_RE.search(text) or APPROVAL_CLAIM_RE.search(text):
        blocked_reasons.append("approval_claim")
    if PRICE_CONFIRM_CLAIM_RE.search(text) or PRICE_CONFIRM_RE.search(text):
        blocked_reasons.append("price_confirmation_claim")
    if CONTRACT_CONFIRM_CLAIM_RE.search(text) or CONTRACT_CONFIRM_RE.search(text):
        blocked_reasons.append("contract_confirmation_claim")
    if DELIVERY_CONFIRM_CLAIM_RE.search(text) or DELIVERY_CONFIRM_RE.search(text):
        blocked_reasons.append("delivery_confirmation_claim")
    if policy.get("allow_discord_send"):
        blocked_reasons.append("discord_send_not_allowed")
    for intent in matched:
        if intent not in blocked_reasons:
            blocked_reasons.append(intent)
    if safe_disclaimer_detected and not _has_non_negated_claim(text):
        blocked_reasons = [
            reason
            for reason in blocked_reasons
            if reason in {"empty_output", "output_too_long", "discord_send_not_allowed"}
        ]
    return {
        "decision_type": "llm_output_safety_decision",
        "allowed": not blocked_reasons,
        "blocked": bool(blocked_reasons),
        "review_required": True,
        "matched_blocked_intents": matched,
        "blocked_reasons": blocked_reasons,
        "safe_disclaimer_detected": safe_disclaimer_detected,
        "safe_disclaimer_reasons": safe_disclaimer_reasons,
        "reason": "blocked_output_intent_detected" if blocked_reasons else "review_only_output_allowed",
        "message_sent": False,
        "llm_api_called": False,
        "rag_called": False,
        "external_execution": False,
        **bounded,
    }


def _safe_disclaimer_reasons(text: str) -> list[str]:
    reasons: list[str] = []
    checks = [
        ("negated_action_made", NEGATED_ACTION_MADE_RE),
        ("negated_publication", NEGATED_PUBLICATION_RE),
        ("negated_external_delivery", NEGATED_DELIVERY_RE),
        ("negated_external_action", NEGATED_EXTERNAL_ACTION_RE),
        ("negated_submission", NEGATED_SUBMISSION_RE),
        ("negated_email_send", NEGATED_EMAIL_RE),
        ("negated_approval", NEGATED_APPROVAL_RE),
        ("negated_contract_confirmation", NEGATED_CONTRACT_RE),
        ("negated_delivery_confirmation", NEGATED_DELIVERY_CONFIRM_RE),
        ("review_only", REVIEW_ONLY_RE),
    ]
    for reason, pattern in checks:
        if pattern.search(text):
            reasons.append(reason)
    return reasons


def _has_non_negated_claim(text: str) -> bool:
    remaining = text
    for pattern in (
        NEGATED_ACTION_MADE_RE,
        NEGATED_PUBLICATION_RE,
        NEGATED_DELIVERY_RE,
        NEGATED_EXTERNAL_ACTION_RE,
        NEGATED_SUBMISSION_RE,
        NEGATED_EMAIL_RE,
        NEGATED_APPROVAL_RE,
        NEGATED_CONTRACT_RE,
        NEGATED_DELIVERY_CONFIRM_RE,
        REVIEW_ONLY_RE,
    ):
        remaining = pattern.sub("", remaining)
    return any(
        pattern.search(remaining)
        for pattern in (
            PUBLIC_PUBLISH_CLAIM_RE,
            SUBMISSION_CLAIM_RE,
            EMAIL_SEND_CLAIM_RE,
            APPROVAL_POSITIVE_RE,
            PRICE_CONFIRM_RE,
            PRICE_CONFIRM_CLAIM_RE,
            CONTRACT_CONFIRM_RE,
            CONTRACT_CONFIRM_CLAIM_RE,
            DELIVERY_CONFIRM_RE,
            DELIVERY_CONFIRM_CLAIM_RE,
            EXTERNAL_ACTION_CLAIM_RE,
            EXTERNAL_ACTION_RE,
        )
    )


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

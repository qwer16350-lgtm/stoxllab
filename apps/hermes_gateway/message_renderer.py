"""Render would-send payloads without sending Discord messages."""

from __future__ import annotations

from typing import Any


SECRET_MARKERS = ("api key", "apikey", "token", "secret", "password", "sk-", "bearer")


def _redact_text(text: str) -> str:
    lower = text.lower()
    if any(marker in lower for marker in SECRET_MARKERS):
        return "[REDACTED]"
    return text


def build_would_send_payload(
    message_kind: str,
    channel_name: str | None,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "would_send": True,
        "message_kind": message_kind,
        "target_channel": channel_name,
        "content": _redact_text(content),
        "metadata": metadata or {},
        "safety": {
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
            "human_only_execution": True,
        },
    }


def render_agent_dispatch_message(evaluation_result: dict[str, Any], dispatch_plan: dict[str, Any]) -> str:
    agent = dispatch_plan.get("dispatch_to_agent") or "담당 에이전트"
    reviewer = dispatch_plan.get("reviewer_agent")
    if reviewer:
        return f"이 요청은 {agent}에게 배정되고, {reviewer} 검토 흐름으로 이어집니다. 실제 외부 실행은 하지 않습니다."
    return f"이 요청은 {agent}에게 배정됩니다. 실제 외부 실행은 하지 않습니다."


def render_blocked_message(evaluation_result: dict[str, Any]) -> str:
    reasons = evaluation_result.get("block_reasons") or ["safety rule"]
    reason_text = "; ".join(str(reason) for reason in reasons)
    return f"이 요청은 현재 안전 규칙에 의해 차단되었습니다. 사유: {reason_text}"


def render_approval_required_message(evaluation_result: dict[str, Any], dispatch_plan: dict[str, Any]) -> str:
    channel = dispatch_plan.get("final_report_channel") or "최종-승인요청"
    return (
        f"이 요청은 결정권자 승인 대상입니다. 검토 채널: {channel}. "
        "승인 이후에도 실제 외부 실행은 사람이 별도로 수행해야 합니다."
    )


def render_review_packet_hint(evaluation_result: dict[str, Any]) -> str:
    return "필요하면 이 요청은 approval review packet에 포함해 결정권자 검토용으로 정리할 수 있습니다."


def render_audit_notice(evaluation_result: dict[str, Any]) -> str:
    return "이 dry-run 결과는 감사 로그 payload로만 기록될 수 있으며 Discord 메시지는 전송되지 않았습니다."

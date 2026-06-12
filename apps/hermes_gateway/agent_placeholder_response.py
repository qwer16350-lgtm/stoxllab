"""Deterministic agent placeholder responses with no LLM or RAG calls."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "phase31c_deterministic_no_llm"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.[a-z0-9_-]+|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


TEMPLATES = {
    "marin": {
        "title": "Marin placeholder draft intake",
        "summary": "Marketing draft or idea intake was received. Draft generation is disabled in this phase; only the draft direction is recorded.",
        "next_step": "Request purpose, target channel, and Lucy review requirements should be checked before any public wording is considered.",
        "review_note": "SNS or homepage publishing is not executed without Decision Maker approval.",
    },
    "lucy": {
        "title": "Lucy placeholder review",
        "summary": "Marketing senior review was requested. This phase records brand fit, expression, and public-risk review points only.",
        "next_step": "If Marin draft material exists, it should be reviewed as a local packet before any approval request.",
        "review_note": "Public release requires Decision Maker approval.",
    },
    "kasumi": {
        "title": "Kasumi placeholder research intake",
        "summary": "Operations research intake was received. This phase records conditions, deadlines, and source checks only.",
        "next_step": "Source links, deadlines, and eligibility conditions should be verified for Meiko review.",
        "review_note": "Application submission or external inquiry is not automated.",
    },
    "meiko": {
        "title": "Meiko placeholder operation review",
        "summary": "Operations senior review was requested. Recommendation, hold, or reject decisions are not finalized in this phase.",
        "next_step": "Review Kasumi research for schedule, risk, and execution feasibility.",
        "review_note": "External submission or schedule commitment remains human-only after Decision Maker approval.",
    },
    "reze": {
        "title": "Reze placeholder strategy note",
        "summary": "Strategy review was requested. This phase records directional fit, tension, and risk without issuing team orders.",
        "next_step": "Check brand, product, and business alignment before drafting a strategy note.",
        "review_note": "Reze can provide strategic opinion, not operational commands to other teams.",
    },
    "decision_maker_review": {
        "title": "Decision maker placeholder review",
        "summary": "Approval or executive review appears necessary. This phase records the need for review without processing approval automatically.",
        "next_step": "Kim Taeho_STOXL or Lee Juho_STOXL should review directly.",
        "review_note": "Approval does not trigger automated external execution.",
    },
    "unrouted": {
        "title": "Unrouted placeholder",
        "summary": "The request was received, but a clear agent route could not be determined.",
        "next_step": "Channel, workflow role, and request intent should be checked.",
        "review_note": "No automated reply or external execution is allowed until routing is resolved.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(value: str | None = None) -> str:
    return (value or utc_now())[:10].replace("-", "")


def redact_preview(text: str | None, max_chars: int = 120) -> str:
    if not text:
        return ""
    normalized = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
    redacted = SECRET_RE.sub("[REDACTED_SECRET]", normalized)
    redacted = LONG_ID_RE.sub(lambda match: f"discord_id_redacted:{match.group(0)[-4:]}", redacted)
    return redacted[:max_chars]


def resolve_placeholder_template(agent_route_candidate: str, workflow_role: str | None = None) -> dict[str, str]:
    return dict(TEMPLATES.get(agent_route_candidate or "", TEMPLATES["unrouted"]))


def build_agent_placeholder_response(
    audit_record: dict[str, Any],
    routing_report: dict[str, Any],
    content_preview: str | None = None,
) -> dict[str, Any]:
    agent = routing_report.get("agent_route_candidate") or audit_record.get("agent_route_candidate") or "unrouted"
    workflow_role = routing_report.get("workflow_role") or audit_record.get("workflow_role", "")
    template = resolve_placeholder_template(agent, workflow_role)
    safe_preview = redact_preview(content_preview if content_preview is not None else audit_record.get("content_preview", ""))
    response = {
        "response_type": "agent_placeholder_response",
        "version": VERSION,
        "created_at": utc_now(),
        "event_id": audit_record.get("event_id", ""),
        "agent_route_candidate": agent if agent in TEMPLATES else "unrouted",
        "workflow_role": workflow_role,
        "channel_name": audit_record.get("channel_name", ""),
        "response_generated": True,
        "deterministic": True,
        "llm_enabled": False,
        "rag_enabled": False,
        "will_send": False,
        "message_sent": False,
        "content_basis": {
            "uses_content_preview": bool(safe_preview),
            "content_preview_max_chars": 120,
            "raw_content_included": False,
            "content_preview": safe_preview,
        },
        "placeholder": template,
        "safety_assertions": {
            "discord_api_called": False,
            "message_sent": False,
            "llm_called": False,
            "rag_called": False,
            "external_execution": False,
            "raw_token_logged": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_agent_placeholder_response_safe(response)
    return response


def assert_agent_placeholder_response_safe(response: dict[str, Any]) -> None:
    if response.get("llm_enabled") or response.get("rag_enabled") or response.get("will_send") or response.get("message_sent"):
        raise ValueError("Agent placeholder response has unsafe send/generation flags.")
    safety = response.get("safety_assertions", {})
    if safety.get("discord_api_called") or safety.get("message_sent") or safety.get("llm_called") or safety.get("rag_called") or safety.get("external_execution"):
        raise ValueError("Agent placeholder response safety assertions are unsafe.")
    text = json.dumps(response, ensure_ascii=False).lower()
    if "sk-" in text or "xoxb-" in text or "mfa." in text or LONG_ID_RE.search(text):
        raise ValueError("Agent placeholder response contains unsafe raw values.")


def write_agent_placeholder_response(response: dict[str, Any], root: str | Path | None = None) -> Path:
    assert_agent_placeholder_response_safe(response)
    repo_root = Path(root or Path.cwd()).resolve()
    out_dir = repo_root / "exports" / "hermes_gateway" / "agent_placeholder_responses" / _date_stamp(response.get("created_at"))
    out_dir.mkdir(parents=True, exist_ok=True)
    event_id = str(response.get("event_id") or "event").replace(":", "_")
    path = out_dir / f"{event_id}.json"
    path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def render_agent_placeholder_response_markdown(response: dict[str, Any]) -> str:
    placeholder = response.get("placeholder", {})
    text = "\n".join(
        [
            "# Agent Placeholder Response",
            "",
            f"- Agent: {response.get('agent_route_candidate', '')}",
            f"- Workflow: {response.get('workflow_role', '')}",
            f"- Channel: {response.get('channel_name', '')}",
            f"- Title: {placeholder.get('title', '')}",
            f"- Summary: {placeholder.get('summary', '')}",
            f"- Next Step: {placeholder.get('next_step', '')}",
            f"- Will Send: {str(response.get('will_send')).lower()}",
            f"- LLM Enabled: {str(response.get('llm_enabled')).lower()}",
            f"- RAG Enabled: {str(response.get('rag_enabled')).lower()}",
        ]
    ) + "\n"
    assert_agent_placeholder_response_safe(response)
    return text

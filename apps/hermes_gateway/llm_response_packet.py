"""Phase 32C LLM response packets for local human review only."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_client import redact_text


VERSION = "phase32c_no_discord_send"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_RE = re.compile(r"(?i)(sk-[a-z0-9_-]+|xoxb-[a-z0-9_-]+|mfa\.|bearer\s+\S+|api[_ -]?key\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+)")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(value: str | None = None) -> str:
    return (value or utc_now())[:10].replace("-", "")


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _llm_dry_call_files(root: str | Path | None = None) -> list[Path]:
    repo_root = Path(root or Path.cwd()).resolve()
    base = repo_root / "exports" / "hermes_gateway" / "llm_dry_calls"
    if not base.exists():
        return []
    return [path for path in base.glob("*/*.json") if path.is_file()]


def _sort_artifact_files(files: list[Path]) -> list[Path]:
    def key(path: Path) -> tuple[str, float]:
        report = _safe_json_load(path) or {}
        return (str(report.get("created_at", "")), path.stat().st_mtime)

    return sorted(files, key=key, reverse=True)


def find_latest_llm_dry_call_artifact(root: str | Path | None = None) -> dict[str, Any]:
    for path in _sort_artifact_files(_llm_dry_call_files(root)):
        report = _safe_json_load(path)
        if report and report.get("report_type") == "llm_dry_call_report":
            safe = {
                "found": True,
                "path": str(path),
                "created_at": report.get("created_at", ""),
                "provider": report.get("client_result", {}).get("provider", ""),
                "model": report.get("client_result", {}).get("model", ""),
                "api_call_succeeded": bool(report.get("client_result", {}).get("api_call_succeeded")),
                "output_safety_allowed": bool(report.get("output_safety", {}).get("allowed")),
                "message_sent": False,
                "discord_send_attempted": False,
                "rag_called": False,
                "external_execution": False,
                "report": report,
            }
            assert_llm_response_packet_safe({"message_sent": False, "discord_send_attempted": False, "rag_called": False, "external_execution": False, "safety_assertions": {}})
            return safe
    return {
        "found": False,
        "path": "",
        "created_at": "",
        "provider": "",
        "model": "",
        "api_call_succeeded": False,
        "output_safety_allowed": False,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "report": {},
    }


def build_latest_llm_response_packet_report(root: str | Path | None = None, write_artifact: bool = True) -> dict[str, Any]:
    latest = find_latest_llm_dry_call_artifact(root)
    if not latest.get("found"):
        return {
            "report_type": "llm_response_packet_latest_report",
            "version": VERSION,
            "created_at": utc_now(),
            "latest_dry_call_found": False,
            "source_dry_call_path": "",
            "packet_created": False,
            "packet": {},
            "packet_paths": {},
            "message_sent": False,
            "discord_send_attempted": False,
            "rag_called": False,
            "external_execution": False,
            "safety_assertions": _safe_assertions(),
        }
    packet = build_llm_response_packet(latest["report"])
    paths = write_llm_response_packet(packet, root=root) if write_artifact else {}
    report = {
        "report_type": "llm_response_packet_latest_report",
        "version": VERSION,
        "created_at": utc_now(),
        "latest_dry_call_found": True,
        "source_dry_call_path": latest.get("path", ""),
        "packet_created": True,
        "packet": packet,
        "packet_paths": paths,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "safety_assertions": _safe_assertions(),
    }
    assert_llm_response_packet_safe(report)
    return report


def build_llm_response_summary(llm_dry_call_report: dict[str, Any]) -> dict[str, Any]:
    result = llm_dry_call_report.get("client_result", {})
    output = llm_dry_call_report.get("output_safety", {})
    response_text = redact_text(str(result.get("response_text", "") or ""), 1600)
    usage = result.get("usage", {}) if isinstance(result.get("usage"), dict) else {}
    provider_usage = usage.get("provider_usage", {}) if isinstance(usage.get("provider_usage"), dict) else {}
    return {
        "available": bool(response_text) and bool(output.get("allowed")),
        "summary": response_text[:240],
        "char_count": len(response_text),
        "review_only": True,
        "safe_disclaimer_detected": bool(output.get("safe_disclaimer_detected")),
        "safe_disclaimer_reasons": output.get("safe_disclaimer_reasons", []),
        "output_safety_allowed": bool(output.get("allowed")),
        "output_safety_blocked": bool(output.get("blocked")),
        "prompt_tokens": int(provider_usage.get("prompt_tokens", usage.get("input_chars", 0)) or 0),
        "completion_tokens": int(provider_usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(provider_usage.get("total_tokens", 0) or 0),
        "cost": usage.get("estimated_cost_krw"),
        "message_sent": False,
        "will_send": False,
    }


def build_llm_response_packet(llm_dry_call_report: dict[str, Any]) -> dict[str, Any]:
    result = llm_dry_call_report.get("client_result", {})
    request = llm_dry_call_report.get("request", {})
    output = llm_dry_call_report.get("output_safety", {})
    summary = build_llm_response_summary(llm_dry_call_report)
    usage = result.get("usage", {}) if isinstance(result.get("usage"), dict) else {}
    provider_usage = usage.get("provider_usage", {}) if isinstance(usage.get("provider_usage"), dict) else {}
    response_text = redact_text(str(result.get("response_text", "") or ""), 1600)
    packet = {
        "packet_type": "llm_response_packet",
        "version": VERSION,
        "created_at": utc_now(),
        "source_report_type": llm_dry_call_report.get("report_type", "llm_dry_call_report"),
        "agent_route_candidate": request.get("agent_route_candidate", ""),
        "provider": result.get("provider", ""),
        "model": result.get("model", ""),
        "response_available": bool(response_text) and bool(output.get("allowed")),
        "response_text": response_text,
        "response_summary": summary,
        "output_safety": {
            "allowed": bool(output.get("allowed")),
            "blocked": bool(output.get("blocked")),
            "blocked_reasons": output.get("blocked_reasons", []),
            "safe_disclaimer_detected": bool(output.get("safe_disclaimer_detected")),
            "safe_disclaimer_reasons": output.get("safe_disclaimer_reasons", []),
        },
        "usage": {
            "prompt_tokens": int(provider_usage.get("prompt_tokens", usage.get("input_chars", 0)) or 0),
            "completion_tokens": int(provider_usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(provider_usage.get("total_tokens", 0) or 0),
            "cost": usage.get("estimated_cost_krw"),
        },
        "human_review": {
            "required": True,
            "reason": "LLM response is not sent automatically in Phase 32C.",
            "allowed_actions": ["review_only", "manual_edit", "manual_followup_outside_bot"],
            "disallowed_actions": ["auto_reply", "external_execution", "rag_call", "public_publish"],
        },
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "safety_assertions": {
            "api_key_value_logged": False,
            "discord_message_sent": False,
            "rag_called": False,
            "external_execution": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_llm_response_packet_safe(packet)
    return packet


def _safe_assertions() -> dict[str, bool]:
    return {
        "api_key_value_logged": False,
        "discord_message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "raw_discord_ids_logged": False,
    }


def build_llm_response_packet_live_closeout(root: str | Path | None = None) -> dict[str, Any]:
    latest_report = build_latest_llm_response_packet_report(root=root, write_artifact=True)
    packet = latest_report.get("packet", {}) if isinstance(latest_report.get("packet"), dict) else {}
    summary = llm_response_packet_preview(packet, packet_path=latest_report.get("packet_paths", {}).get("json_path", ""))
    operations_viewer_available = bool(summary.get("available")) or bool(latest_report.get("packet_created"))
    closeout = {
        "report_type": "llm_response_packet_live_closeout",
        "version": "phase32c_live_closeout",
        "created_at": utc_now(),
        "latest_dry_call_found": bool(latest_report.get("latest_dry_call_found")),
        "source_dry_call_path": latest_report.get("source_dry_call_path", ""),
        "llm_response_packet_created": bool(latest_report.get("packet_created")),
        "packet_paths": latest_report.get("packet_paths", {}),
        "operations_viewer_summary_available": operations_viewer_available,
        "provider": packet.get("provider", ""),
        "model": packet.get("model", ""),
        "output_safety_allowed": bool(packet.get("output_safety", {}).get("allowed")),
        "response_available": bool(packet.get("response_available")),
        "usage": packet.get("usage", {}),
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
        "ready_for_phase32d_guarded_private_test_llm_reply": (
            bool(latest_report.get("latest_dry_call_found"))
            and bool(packet.get("response_available"))
            and bool(packet.get("output_safety", {}).get("allowed"))
        ),
        "safety_assertions": _safe_assertions(),
    }
    assert_llm_response_packet_safe(closeout)
    return closeout


def render_llm_response_packet_live_closeout_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# LLM Response Packet Live Closeout",
            "",
            f"- Latest dry call found: {str(report.get('latest_dry_call_found')).lower()}",
            f"- Packet created: {str(report.get('llm_response_packet_created')).lower()}",
            f"- Operations viewer summary available: {str(report.get('operations_viewer_summary_available')).lower()}",
            f"- Provider: {report.get('provider', '')}",
            f"- Model: {report.get('model', '')}",
            f"- Output safety allowed: {str(report.get('output_safety_allowed')).lower()}",
            f"- Ready for Phase 32D guarded private-test LLM reply: {str(report.get('ready_for_phase32d_guarded_private_test_llm_reply')).lower()}",
            "- Sent to Discord: false",
            "- RAG called: false",
            "- External execution: false",
        ]
    ) + "\n"


def llm_response_packet_preview(packet: dict[str, Any] | None = None, packet_path: str = "") -> dict[str, Any]:
    if not packet:
        return {
            "available": False,
            "packet_path": "",
            "provider": "",
            "model": "",
            "summary": "",
            "output_safety_allowed": False,
            "blocked": False,
            "cost": None,
            "will_send": False,
            "message_sent": False,
        }
    summary = packet.get("response_summary", {})
    return {
        "available": bool(packet.get("response_available")) and bool(packet.get("output_safety", {}).get("allowed")),
        "packet_path": packet_path or packet.get("packet_path", ""),
        "provider": packet.get("provider", ""),
        "model": packet.get("model", ""),
        "summary": summary.get("summary", ""),
        "output_safety_allowed": bool(packet.get("output_safety", {}).get("allowed")),
        "blocked": bool(packet.get("output_safety", {}).get("blocked")),
        "cost": packet.get("usage", {}).get("cost"),
        "will_send": False,
        "message_sent": False,
    }


def write_llm_response_packet(packet: dict[str, Any], root: str | Path | None = None) -> dict[str, str]:
    assert_llm_response_packet_safe(packet)
    repo_root = Path(root or Path.cwd()).resolve()
    out_dir = repo_root / "exports" / "hermes_gateway" / "llm_response_packets" / _date_stamp(packet.get("created_at"))
    out_dir.mkdir(parents=True, exist_ok=True)
    agent = str(packet.get("agent_route_candidate") or "agent")
    json_path = out_dir / f"{agent}_llm_response_packet.json"
    md_path = out_dir / f"{agent}_llm_response_packet.md"
    packet_with_path = dict(packet)
    packet_with_path["packet_path"] = str(json_path)
    json_path.write_text(json.dumps(packet_with_path, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_llm_response_packet_markdown(packet_with_path), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(md_path)}


def render_llm_response_packet_markdown(packet: dict[str, Any]) -> str:
    output = packet.get("output_safety", {})
    usage = packet.get("usage", {})
    return "\n".join(
        [
            "# LLM Response Packet",
            "",
            f"- Agent: {packet.get('agent_route_candidate', '')}",
            f"- Provider: {packet.get('provider', '')}",
            f"- Model: {packet.get('model', '')}",
            f"- Response available: {str(packet.get('response_available')).lower()}",
            f"- Output safety allowed: {str(output.get('allowed')).lower()}",
            f"- Output safety blocked: {str(output.get('blocked')).lower()}",
            f"- Prompt tokens: {usage.get('prompt_tokens', 0)}",
            f"- Completion tokens: {usage.get('completion_tokens', 0)}",
            f"- Total tokens: {usage.get('total_tokens', 0)}",
            f"- Cost: {usage.get('cost')}",
            "- Human review required: true",
            "- Sent to Discord: false",
            "- RAG called: false",
            "- External execution: false",
            "",
            "## Response Summary",
            str(packet.get("response_summary", {}).get("summary", "")),
        ]
    ) + "\n"


def assert_llm_response_packet_safe(packet: dict[str, Any]) -> None:
    text = json.dumps(packet, ensure_ascii=False).lower()
    if SECRET_RE.search(text):
        raise ValueError("LLM response packet contains secret-like text.")
    if LONG_ID_RE.search(text):
        raise ValueError("LLM response packet contains raw Discord-like IDs.")
    for key in ("message_sent", "discord_send_attempted", "rag_called", "external_execution"):
        if packet.get(key):
            raise ValueError(f"LLM response packet has unsafe flag: {key}")
    assertions = packet.get("safety_assertions", {})
    for key in ("api_key_value_logged", "discord_message_sent", "rag_called", "external_execution", "raw_discord_ids_logged"):
        if assertions.get(key):
            raise ValueError(f"LLM response packet unsafe assertion is true: {key}")

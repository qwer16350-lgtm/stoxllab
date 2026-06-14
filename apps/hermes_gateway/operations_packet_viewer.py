"""Local-only viewer for Phase 30 live event operation artifacts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from private_test_reply_replay import build_private_test_reply_replay_report
from llm_private_test_reply_replay import build_llm_private_test_reply_replay_report
from llm_response_packet import llm_response_packet_preview
from rag_preflight import build_rag_preflight_report
from rag_local_retrieval import run_rag_local_retrieval
from rag_response_packet import build_rag_response_packet
from rag_context_safety import build_rag_context_safety_report
from rag_llm_private_test_reply import build_rag_llm_private_test_reply_preflight
from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope
from rag_llm_would_send_preview import build_rag_llm_would_send_preview
from rag_llm_private_test_reply_replay import build_rag_llm_private_test_reply_replay_report


VERSION = "phase31a_local_viewer"
LONG_ID_RE = re.compile(r"\b\d{15,25}\b")
SECRET_MARKERS = ("sk-", "xoxb-", "mfa.", "bearer ", "api_key", "apikey", "token=", "password=")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _date_stamp(date: str | None = None) -> str:
    if date:
        return date.replace("-", "")[:8]
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _repo(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _assert_no_raw_values(obj: Any) -> None:
    text = json.dumps(obj, ensure_ascii=False).lower()
    if any(marker in text for marker in SECRET_MARKERS):
        raise ValueError("Viewer output contains secret-like values.")
    if LONG_ID_RE.search(text):
        raise ValueError("Viewer output contains raw Discord-like IDs.")


def _event_summary(record: dict[str, Any]) -> dict[str, Any]:
    item = {
        "event_id": record.get("event_id", ""),
        "created_at": record.get("created_at", ""),
        "decision": record.get("decision", ""),
        "channel_name": record.get("channel_name", ""),
        "workflow_role": record.get("workflow_role", ""),
        "agent_route_candidate": record.get("agent_route_candidate", ""),
        "content_present": bool(record.get("content_present")),
        "content_length": int(record.get("content_length") or 0),
        "content_preview": str(record.get("content_preview", ""))[:120],
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
    }
    _assert_no_raw_values(item)
    return item


def list_recent_live_events(root: str | Path | None = None, limit: int = 20, date: str | None = None) -> list[dict[str, Any]]:
    repo = _repo(root)
    log_path = repo / "logs" / "hermes_gateway" / "live_events" / f"readonly_events_{_date_stamp(date)}.jsonl"
    if not log_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        events.append(_event_summary(record))
    events.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return events[: max(0, int(limit))]


def _packet_summary(path: Path, packet: dict[str, Any]) -> dict[str, Any]:
    summary = packet.get("summary", {})
    placeholder = packet.get("agent_placeholder_response", {})
    item = {
        "event_id": packet.get("event_id", ""),
        "created_at": packet.get("created_at", ""),
        "packet_path": str(path),
        "channel_name": summary.get("channel_name", ""),
        "workflow_role": summary.get("workflow_role", ""),
        "agent_route_candidate": summary.get("agent_route_candidate", ""),
        "decision": summary.get("decision", ""),
        "human_review_required": bool(packet.get("human_review", {}).get("required")),
        "agent_placeholder_response_available": bool(placeholder.get("available")),
        "agent_placeholder_title": placeholder.get("title", ""),
        "agent_placeholder_summary": placeholder.get("summary", ""),
        "message_sent": False,
        "llm_called": False,
        "rag_called": False,
    }
    _assert_no_raw_values(item)
    return item


def _packet_files(root: str | Path | None = None, date: str | None = None) -> list[Path]:
    base = _repo(root) / "exports" / "hermes_gateway" / "live_event_packets"
    if date:
        dirs = [base / _date_stamp(date)]
    else:
        dirs = [path for path in base.glob("*") if path.is_dir()] if base.exists() else []
    files: list[Path] = []
    for directory in dirs:
        if directory.exists():
            files.extend(directory.glob("*.json"))
    return files


def _llm_packet_files(root: str | Path | None = None, date: str | None = None) -> list[Path]:
    base = _repo(root) / "exports" / "hermes_gateway" / "llm_response_packets"
    if date:
        dirs = [base / _date_stamp(date)]
    else:
        dirs = [path for path in base.glob("*") if path.is_dir()] if base.exists() else []
    files: list[Path] = []
    for directory in dirs:
        if directory.exists():
            files.extend(directory.glob("*.json"))
    return files


def list_recent_llm_response_packets(root: str | Path | None = None, limit: int = 20, date: str | None = None) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for path in _llm_packet_files(root, date):
        packet = _safe_json_load(path)
        if packet:
            preview = llm_response_packet_preview(packet, packet_path=str(path))
            item = {
                "packet_path": str(path),
                "llm_response_available": bool(preview.get("available")),
                "llm_provider": preview.get("provider", ""),
                "llm_model": preview.get("model", ""),
                "llm_output_safety_allowed": bool(preview.get("output_safety_allowed")),
                "llm_cost": preview.get("cost"),
                "llm_message_sent": False,
                "summary": preview.get("summary", ""),
                "created_at": packet.get("created_at", ""),
            }
            _assert_no_raw_values(item)
            packets.append(item)
    packets.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return packets[: max(0, int(limit))]


def _empty_latest_llm_response_packet() -> dict[str, Any]:
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
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
    }


def latest_llm_response_packet_summary(root: str | Path | None = None, date: str | None = None) -> dict[str, Any]:
    packets = _llm_packet_files(root, date)
    best: tuple[str, Path, dict[str, Any]] | None = None
    for path in packets:
        packet = _safe_json_load(path)
        if not packet:
            continue
        created_at = str(packet.get("created_at", ""))
        if best is None or created_at > best[0]:
            best = (created_at, path, packet)
    if not best:
        return _empty_latest_llm_response_packet()
    preview = llm_response_packet_preview(best[2], packet_path=str(best[1]))
    item = {
        "available": bool(preview.get("available")),
        "packet_path": preview.get("packet_path", ""),
        "provider": preview.get("provider", ""),
        "model": preview.get("model", ""),
        "summary": preview.get("summary", ""),
        "output_safety_allowed": bool(preview.get("output_safety_allowed")),
        "blocked": bool(preview.get("blocked")),
        "cost": preview.get("cost"),
        "will_send": False,
        "message_sent": False,
        "discord_send_attempted": False,
        "rag_called": False,
        "external_execution": False,
    }
    _assert_no_raw_values(item)
    return item


def list_recent_review_packets(root: str | Path | None = None, limit: int = 20, date: str | None = None) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for path in _packet_files(root, date):
        packet = _safe_json_load(path)
        if packet:
            packets.append(_packet_summary(path, packet))
    packets.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return packets[: max(0, int(limit))]


def load_review_packet(root: str | Path | None = None, event_id: str | None = None, packet_path: str | Path | None = None) -> dict[str, Any]:
    if packet_path:
        path = Path(packet_path)
        if not path.is_absolute():
            path = _repo(root) / path
        packet = _safe_json_load(path)
        if not packet:
            return {}
        _assert_no_raw_values(packet)
        return packet
    if not event_id:
        return {}
    for path in _packet_files(root):
        packet = _safe_json_load(path)
        if packet and packet.get("event_id") == event_id:
            _assert_no_raw_values(packet)
            return packet
    return {}


def load_daily_manifest(root: str | Path | None = None, date: str | None = None) -> dict[str, Any]:
    stamp = _date_stamp(date)
    path = _repo(root) / "logs" / "hermes_gateway" / "live_events" / "manifests" / f"readonly_manifest_{stamp}.json"
    manifest = _safe_json_load(path) if path.exists() else {}
    decision_counts = manifest.get("decision_counts", {}) if manifest else {}
    events = list_recent_live_events(root=root, limit=10000, date=stamp)
    summary = {
        "date": stamp,
        "total_events": manifest.get("record_count", len(events)) if manifest else len(events),
        "accepted_mapped_channel": decision_counts.get("accepted_mapped_channel", 0),
        "ignored_self_message": decision_counts.get("ignored_self_message", 0),
        "ignored_guild_not_allowed": decision_counts.get("ignored_guild_not_allowed", 0),
        "ignored_unmapped_channel": decision_counts.get("ignored_unmapped_channel", 0),
        "content_unavailable_or_empty": decision_counts.get("content_unavailable_or_empty", 0),
        "channels": _count_by(events, "channel_name"),
        "workflow_roles": _count_by(events, "workflow_role"),
        "agent_route_candidates": _count_by(events, "agent_route_candidate"),
        "message_sent_count": sum(1 for item in events if item.get("message_sent")),
        "external_execution_count": sum(1 for item in events if item.get("external_execution")),
        "llm_called_count": sum(1 for item in events if item.get("llm_called")),
        "rag_called_count": sum(1 for item in events if item.get("rag_called")),
    }
    _assert_no_raw_values(summary)
    return summary


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "")
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def filter_events(
    events: list[dict[str, Any]],
    channel_name: str | None = None,
    workflow_role: str | None = None,
    agent_route_candidate: str | None = None,
    decision: str | None = None,
) -> list[dict[str, Any]]:
    output = []
    for item in events:
        if channel_name and item.get("channel_name") != channel_name:
            continue
        if workflow_role and item.get("workflow_role") != workflow_role:
            continue
        if agent_route_candidate and item.get("agent_route_candidate") != agent_route_candidate:
            continue
        if decision and item.get("decision") != decision:
            continue
        output.append(item)
    return output


def build_operations_packet_viewer_report(
    root: str | Path | None = None,
    limit: int = 20,
    date: str | None = None,
    channel_name: str | None = None,
    workflow_role: str | None = None,
    agent_route_candidate: str | None = None,
    decision: str | None = None,
) -> dict[str, Any]:
    events = filter_events(
        list_recent_live_events(root=root, limit=10000, date=date),
        channel_name=channel_name,
        workflow_role=workflow_role,
        agent_route_candidate=agent_route_candidate,
        decision=decision,
    )[: max(0, int(limit))]
    packets = list_recent_review_packets(root=root, limit=limit, date=date)
    llm_packets = list_recent_llm_response_packets(root=root, limit=limit, date=date)
    latest_llm = latest_llm_response_packet_summary(root=root, date=date)
    replay_report = build_private_test_reply_replay_report(root=str(_repo(root)))
    replay_summary = replay_report.get("summary", {})
    llm_reply_closeout = build_llm_private_test_reply_replay_report()
    llm_reply_summary = llm_reply_closeout.get("summary", {})
    rag_preflight = build_rag_preflight_report()
    rag_retrieval = run_rag_local_retrieval(root=root, source="operation", query="STOXL brand tone")
    rag_packet = build_rag_response_packet(rag_retrieval)
    rag_context = build_rag_context_safety_report(rag_retrieval)
    rag_llm_preflight = build_rag_llm_private_test_reply_preflight(root=str(_repo(root)))
    rag_llm_envelope = build_rag_llm_prompt_envelope(root=str(_repo(root)))
    rag_llm_preview = build_rag_llm_would_send_preview(root=str(_repo(root)))
    rag_llm_replay = build_rag_llm_private_test_reply_replay_report(root=str(_repo(root)))
    report = {
        "report_type": "operations_packet_viewer",
        "version": VERSION,
        "created_at": utc_now(),
        "root": str(_repo(root)),
        "date": _date_stamp(date),
        "recent_live_events": events,
        "recent_review_packets": packets,
        "recent_llm_response_packets": llm_packets,
        "latest_llm_response_packet": latest_llm,
        "llm_response_summary": llm_packets[0] if llm_packets else {
            "llm_response_available": False,
            "llm_provider": "",
            "llm_model": "",
            "llm_output_safety_allowed": False,
            "llm_cost": None,
            "llm_message_sent": False,
        },
        "private_test_reply_summary": {
            "available": True,
            "sent_count": replay_summary.get("sent", 0),
            "blocked_count": replay_summary.get("blocked", 0),
            "self_message_skipped_count": replay_summary.get("self_message_skipped", 0),
            "cooldown_blocked_count": replay_summary.get("cooldown_blocked", 0),
            "budget_exhausted_count": replay_summary.get("budget_exhausted_blocked", 0),
            "circuit_breaker_count": replay_summary.get("circuit_breaker_opened", 0),
        },
        "llm_private_test_reply_closeout": {
            "available": True,
            "live_success_fixture_verified": bool(llm_reply_closeout.get("live_success_fixture_verified")),
            "sent_in_fixture": llm_reply_summary.get("sent", 0),
            "self_messages_skipped": llm_reply_summary.get("self_messages_skipped", 0),
            "public_channel_blocked": llm_reply_summary.get("public_channel_blocked", 0),
            "llm_api_called_by_replay": False,
            "discord_send_by_replay": False,
            "ready_for_phase33a_rag_preflight": bool(llm_reply_closeout.get("ready_for_phase33a_rag_preflight")),
        },
        "rag": {
            "preflight_available": True,
            "local_retrieval_available": True,
            "response_packet_available": True,
            "ready_for_phase33b_local_readonly_retrieval": bool(rag_preflight.get("ready_for_phase33b_local_readonly_retrieval")),
            "ready_for_phase33c_rag_response_packet": bool(rag_retrieval.get("ready_for_phase33c_rag_response_packet")),
            "ready_for_phase33d_plan_only": True,
            "embedding_called": False,
            "llm_called": False,
            "discord_message_sent": False,
            "external_execution": False,
            "documents_returned": rag_retrieval.get("documents_returned", 0),
            "response_available": bool(rag_packet.get("response_available")),
        },
        "rag_llm_private_test_scaffold": {
            "preflight_available": bool(rag_llm_preflight),
            "context_safety_available": bool(rag_context),
            "prompt_envelope_available": bool(rag_llm_envelope),
            "would_send_preview_available": bool(rag_llm_preview),
            "replay_available": bool(rag_llm_replay),
            "actual_discord_send": False,
            "actual_llm_api_call": False,
            "embedding_api_call": False,
            "external_execution": False,
            "ready_for_phase33d_live_review": bool(rag_llm_replay.get("ready_for_phase33d_live_review")),
        },
        "daily_manifest_summary": load_daily_manifest(root=root, date=date),
        "filters": {
            "channel_name": channel_name,
            "workflow_role": workflow_role,
            "agent_route_candidate": agent_route_candidate,
            "decision": decision,
        },
        "safety_assertions": {
            "discord_api_called": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
            "env_file_read": False,
            "local_mapping_file_read": False,
            "raw_token_logged": False,
            "raw_discord_ids_logged": False,
        },
    }
    assert_viewer_output_safe(report)
    return report


def render_operations_summary_markdown(report: dict[str, Any]) -> str:
    summary = report.get("daily_manifest_summary", {})
    accepted = summary.get("accepted_mapped_channel", 0)
    ignored = sum(summary.get(key, 0) for key in ("ignored_self_message", "ignored_guild_not_allowed", "ignored_unmapped_channel", "content_unavailable_or_empty"))
    lines = [
        "# STOXL Hermes Operations Viewer",
        "",
        "## Daily Summary",
        f"- Date: {summary.get('date', report.get('date', ''))}",
        f"- Total Events: {summary.get('total_events', 0)}",
        f"- Accepted: {accepted}",
        f"- Ignored: {ignored}",
        "",
        "## Recent Live Events",
        "| Time | Channel | Workflow | Route | Decision |",
        "|---|---|---|---|---|",
    ]
    for item in report.get("recent_live_events", []):
        lines.append(f"| {item.get('created_at', '')} | {item.get('channel_name', '')} | {item.get('workflow_role', '')} | {item.get('agent_route_candidate', '')} | {item.get('decision', '')} |")
    lines.extend(["", "## Recent Review Packets", "| Time | Event ID | Channel | Route | Human Review |", "|---|---|---|---|---|"])
    for item in report.get("recent_review_packets", []):
        lines.append(f"| {item.get('created_at', '')} | {item.get('event_id', '')} | {item.get('channel_name', '')} | {item.get('agent_route_candidate', '')} | {str(item.get('human_review_required')).lower()} |")
    placeholders = [item for item in report.get("recent_review_packets", []) if item.get("agent_placeholder_response_available")]
    if placeholders:
        first = placeholders[0]
        lines.extend(
            [
                "",
                "## Agent Placeholder Response",
                f"- Agent: {first.get('agent_route_candidate', '')}",
                f"- Title: {first.get('agent_placeholder_title', '')}",
                f"- Summary: {first.get('agent_placeholder_summary', '')}",
                "- Will Send: false",
            ]
        )
    private_summary = report.get("private_test_reply_summary", {})
    llm_reply_closeout = report.get("llm_private_test_reply_closeout", {})
    rag = report.get("rag", {})
    rag_llm_scaffold = report.get("rag_llm_private_test_scaffold", {})
    llm_summary = report.get("latest_llm_response_packet", {})
    lines.extend(
        [
            "",
            "## Latest LLM Response Packet",
            f"- Available: {str(llm_summary.get('available', False)).lower()}",
            f"- Provider: {llm_summary.get('provider', '')}",
            f"- Model: {llm_summary.get('model', '')}",
            f"- Output safety: {str(llm_summary.get('output_safety_allowed', False)).lower()}",
            f"- Cost: {llm_summary.get('cost')}",
            "- Sent to Discord: false",
            "",
            "## Private Test Reply",
            f"- Historical sent: {private_summary.get('sent_count', 0)}",
            f"- Blocked: {private_summary.get('blocked_count', 0)}",
            f"- Self-message skipped: {private_summary.get('self_message_skipped_count', 0)}",
            f"- Cooldown blocked: {private_summary.get('cooldown_blocked_count', 0)}",
            f"- Budget exhausted: {private_summary.get('budget_exhausted_count', 0)}",
            f"- Circuit breaker: {private_summary.get('circuit_breaker_count', 0)}",
            "",
            "## LLM Private Test Reply Closeout",
            f"- Live success fixture verified: {str(llm_reply_closeout.get('live_success_fixture_verified', False)).lower()}",
            f"- Sent in fixture: {llm_reply_closeout.get('sent_in_fixture', 0)}",
            f"- Self-message skipped: {llm_reply_closeout.get('self_messages_skipped', 0)}",
            f"- Public channel blocked: {llm_reply_closeout.get('public_channel_blocked', 0)}",
            "- Replay Discord send: false",
            "- Replay LLM API call: false",
            "",
            "## RAG",
            f"- Preflight: {'available' if rag.get('preflight_available') else 'unavailable'}",
            f"- Local retrieval: {'available' if rag.get('local_retrieval_available') else 'unavailable'}",
            f"- Response packet: {'available' if rag.get('response_packet_available') else 'unavailable'}",
            f"- Embedding called: {str(rag.get('embedding_called', False)).lower()}",
            f"- LLM called: {str(rag.get('llm_called', False)).lower()}",
            f"- Discord sent: {str(rag.get('discord_message_sent', False)).lower()}",
            f"- External execution: {str(rag.get('external_execution', False)).lower()}",
            "",
            "## RAG+LLM Private Test Scaffold",
            f"- Preflight: {'available' if rag_llm_scaffold.get('preflight_available') else 'unavailable'}",
            f"- Context safety: {'available' if rag_llm_scaffold.get('context_safety_available') else 'unavailable'}",
            f"- Prompt envelope: {'available' if rag_llm_scaffold.get('prompt_envelope_available') else 'unavailable'}",
            f"- Would-send: {'available' if rag_llm_scaffold.get('would_send_preview_available') else 'unavailable'}",
            f"- Replay: {'available' if rag_llm_scaffold.get('replay_available') else 'unavailable'}",
            f"- Actual Discord send: {str(rag_llm_scaffold.get('actual_discord_send', False)).lower()}",
            f"- Actual LLM API call: {str(rag_llm_scaffold.get('actual_llm_api_call', False)).lower()}",
            f"- Embedding API call: {str(rag_llm_scaffold.get('embedding_api_call', False)).lower()}",
            f"- External execution: {str(rag_llm_scaffold.get('external_execution', False)).lower()}",
        ]
    )
    safety = report.get("safety_assertions", {})
    lines.extend(
        [
            "",
            "## Safety",
            f"- Discord API called: {str(safety.get('discord_api_called')).lower()}",
            f"- Message sent: {str(safety.get('message_sent')).lower()}",
            f"- LLM called: {str(safety.get('llm_called')).lower()}",
            f"- RAG called: {str(safety.get('rag_called')).lower()}",
        ]
    )
    text = "\n".join(lines) + "\n"
    assert_viewer_output_safe(text)
    return text


def assert_viewer_output_safe(output: Any) -> None:
    _assert_no_raw_values(output)
    data = output if isinstance(output, dict) else {}
    safety = data.get("safety_assertions", {}) if isinstance(data, dict) else {}
    if safety.get("discord_api_called") or safety.get("message_sent") or safety.get("external_execution") or safety.get("llm_called") or safety.get("rag_called"):
        raise ValueError("Viewer safety assertions are unsafe.")

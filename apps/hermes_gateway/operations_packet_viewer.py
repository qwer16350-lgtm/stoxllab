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
from rag_llm_live_readiness_review import build_rag_llm_live_readiness_review
from rag_llm_private_test_runtime import build_rag_llm_private_test_runtime_report
from rag_llm_live_preflight_closeout import build_rag_llm_live_preflight_closeout
from rag_llm_live_success_closeout import build_rag_llm_live_success_closeout
from knowledge_ingestion_boundary import build_knowledge_ingestion_boundary_report
from knowledge_manifest import build_knowledge_manifest
from knowledge_source_routing import build_knowledge_source_routing_report
from knowledge_evidence_packet import build_knowledge_evidence_packet
from knowledge_dry_chain import build_knowledge_dry_chain_report
from rag_evidence_integration import build_rag_evidence_integration_report
from rag_evidence_llm_dry_call_closeout import build_rag_evidence_llm_dry_call_closeout
from rag_evidence_llm_dry_call import build_rag_evidence_llm_dry_call_report
from rag_evidence_llm_dry_readiness import build_rag_evidence_llm_dry_readiness_report
from rag_evidence_private_test_send import build_rag_evidence_private_test_send_report
from rag_evidence_private_test_send_closeout import build_rag_evidence_private_test_send_closeout
from rag_evidence_private_test_e2e_preflight import build_rag_evidence_private_test_e2e_preflight
from rag_evidence_private_test_e2e_replay import build_rag_evidence_private_test_e2e_replay
from rag_evidence_private_test_e2e_live_reply import build_rag_evidence_private_test_e2e_live_reply_report
from rag_evidence_private_test_e2e_send_retry import build_rag_evidence_private_test_e2e_send_retry_report
from rag_evidence_private_test_e2e_live_closeout import build_rag_evidence_private_test_e2e_live_closeout
from rag_evidence_private_test_phase34_final_lock import build_rag_evidence_private_test_phase34_final_lock
from phase35a_post_mvp_safety_audit import build_phase35a_post_mvp_safety_audit
from rag_evidence_private_test_send_preflight import build_rag_evidence_private_test_send_preflight
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope
from rag_evidence_review_packet import build_rag_evidence_review_packet
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview


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
    for safe_label in (
        "openrouter_api_key",
        "hermes_openrouter_api_key",
        "api_key_value_logged",
        "openrouter api key present",
        "openrouter api key value logged",
    ):
        text = text.replace(safe_label, "")
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
    rag_llm_readiness = build_rag_llm_live_readiness_review(root=str(_repo(root)))
    rag_llm_runtime = build_rag_llm_private_test_runtime_report(root=str(_repo(root)))
    rag_llm_closeout = build_rag_llm_live_preflight_closeout(root=str(_repo(root)))
    rag_llm_success_closeout = build_rag_llm_live_success_closeout()
    knowledge_boundary = build_knowledge_ingestion_boundary_report(root=str(_repo(root)))
    knowledge_manifest = build_knowledge_manifest(root=str(_repo(root)))
    knowledge_routing = build_knowledge_source_routing_report()
    knowledge_evidence = build_knowledge_evidence_packet(root=str(_repo(root)))
    rag_evidence_integration = build_rag_evidence_integration_report(root=str(_repo(root)))
    rag_evidence_review = build_rag_evidence_review_packet(root=str(_repo(root)))
    knowledge_dry_chain = build_knowledge_dry_chain_report(root=str(_repo(root)))
    rag_evidence_prompt = build_rag_evidence_prompt_envelope(root=str(_repo(root)))
    rag_evidence_llm_readiness = build_rag_evidence_llm_dry_readiness_report(root=str(_repo(root)))
    rag_evidence_llm_dry_call = build_rag_evidence_llm_dry_call_report(root=str(_repo(root)), allow_api_call=False)
    rag_evidence_llm_closeout = build_rag_evidence_llm_dry_call_closeout()
    rag_evidence_would_send = build_rag_evidence_would_send_preview(rag_evidence_llm_closeout)
    rag_evidence_send_preflight = build_rag_evidence_private_test_send_preflight(rag_evidence_would_send)
    rag_evidence_send = build_rag_evidence_private_test_send_report(
        allow_send=False,
        preview=rag_evidence_would_send,
        preflight=rag_evidence_send_preflight,
    )
    rag_evidence_send_closeout = build_rag_evidence_private_test_send_closeout()
    rag_evidence_e2e_preflight = build_rag_evidence_private_test_e2e_preflight(root=str(_repo(root)), send_closeout=rag_evidence_send_closeout)
    rag_evidence_e2e_replay = build_rag_evidence_private_test_e2e_replay(root=str(_repo(root)), preflight=rag_evidence_e2e_preflight)
    rag_evidence_e2e_live_reply = build_rag_evidence_private_test_e2e_live_reply_report(
        root=str(_repo(root)),
        allow_live_reply=False,
        preflight=rag_evidence_e2e_preflight,
    )
    rag_evidence_e2e_partial_success = rag_evidence_e2e_live_reply.get("partial_success_artifact", {})
    if not rag_evidence_e2e_partial_success:
        rag_evidence_e2e_partial_success = {
            "report_type": "rag_evidence_private_test_e2e_partial_success",
            "available": False,
            "llm_api_called": False,
            "llm_api_call_count": 0,
            "output_safety_allowed": False,
            "discord_message_sent": False,
            "ready_for_manual_send_retry_without_llm": False,
        }
    rag_evidence_e2e_send_retry = build_rag_evidence_private_test_e2e_send_retry_report(
        partial_success=rag_evidence_e2e_partial_success,
        allow_send_retry=False,
    )
    rag_evidence_e2e_live_closeout = build_rag_evidence_private_test_e2e_live_closeout()
    rag_evidence_phase34_final_lock = build_rag_evidence_private_test_phase34_final_lock(
        root=str(_repo(root)),
        closeout=rag_evidence_e2e_live_closeout,
    )
    phase35a_audit = build_phase35a_post_mvp_safety_audit(
        root=str(_repo(root)),
        final_lock=rag_evidence_phase34_final_lock,
    )
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
        "rag_llm_live_readiness_review": {
            "available": True,
            "go": bool(rag_llm_readiness.get("go")),
            "ready_for_manual_phase33d_implementation_request": bool(rag_llm_readiness.get("ready_for_manual_phase33d_implementation_request")),
            "actual_discord_send": False,
            "actual_llm_api_call": False,
            "embedding_api_called": False,
            "external_execution": False,
        },
        "rag_llm_private_test_runtime": {
            "available": True,
            "ready": bool(rag_llm_runtime.get("ready")),
            "blocked": bool(rag_llm_runtime.get("blocked")),
            "runtime_option_added": bool(rag_llm_runtime.get("runtime_option_added")),
            "runtime_executed_by_report": False,
            "actual_discord_send": False,
            "actual_llm_api_call": False,
            "embedding_api_called": False,
            "external_execution": False,
        },
        "rag_llm_live_preflight_closeout": {
            "available": True,
            "runtime_executed": False,
            "ready_for_single_live_private_test": bool(rag_llm_closeout.get("ready_for_single_live_private_test")),
            "actual_discord_send": False,
            "actual_llm_api_call": False,
            "embedding_api_called": False,
            "external_execution": False,
        },
        "rag_llm_single_live_test_closeout": {
            "available": True,
            "closeout_passed": bool(rag_llm_success_closeout.get("closeout_passed")),
            "sent_exactly_once": bool(rag_llm_success_closeout.get("sent_exactly_once")),
            "self_loop_prevented": bool(rag_llm_success_closeout.get("safety_assertions", {}).get("self_loop_prevented")),
            "private_test_channel_only": bool(rag_llm_success_closeout.get("private_test_channel_only")),
            "llm_api_called_once": bool(rag_llm_success_closeout.get("safety_assertions", {}).get("llm_api_called_once")),
            "discord_message_sent_once": bool(rag_llm_success_closeout.get("safety_assertions", {}).get("discord_message_sent_once")),
            "embedding_api_called": bool(rag_llm_success_closeout.get("embedding_api_called")),
            "external_execution": bool(rag_llm_success_closeout.get("external_execution")),
            "ready_for_phase34_knowledge_ingestion": bool(rag_llm_success_closeout.get("ready_for_phase34_knowledge_ingestion")),
        },
        "knowledge_foundation": {
            "available": True,
            "ready_for_local_text_ingestion": bool(knowledge_boundary.get("ready_for_local_text_ingestion")),
            "ready_for_embedding": bool(knowledge_boundary.get("ready_for_embedding")),
            "ready_for_external_sources": bool(knowledge_boundary.get("ready_for_external_sources")),
            "source_routing_available": bool(knowledge_routing),
            "evidence_packet_available": bool(knowledge_evidence),
            "canonical_sources": knowledge_boundary.get("canonical_sources", []),
            "operations_source_present": bool(knowledge_manifest.get("operations_source_present")),
            "embedding_api_called": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
        "rag_evidence_integration": {
            "available": True,
            "evidence_packet_available": bool(rag_evidence_integration.get("evidence_packet_available")),
            "rag_response_packet_created": bool(rag_evidence_integration.get("rag_response_packet_created")),
            "citations_included": bool(rag_evidence_integration.get("citations_included")),
            "ready_for_private_test_review": bool(rag_evidence_integration.get("ready_for_private_test_review")),
            "ready_for_llm_prompt": bool(rag_evidence_integration.get("ready_for_llm_prompt")),
            "ready_for_embedding": bool(rag_evidence_integration.get("ready_for_embedding")),
            "ready_for_external_sources": bool(rag_evidence_integration.get("ready_for_external_sources")),
            "embedding_api_called": False,
            "llm_api_called": False,
            "discord_message_sent": False,
            "external_execution": False,
        },
        "rag_evidence_review_packet": {
            "available": True,
            "review_only": bool(rag_evidence_review.get("review_only")),
            "human_review_required": bool(rag_evidence_review.get("human_review_required")),
            "ready_for_private_test_review": bool(rag_evidence_review.get("ready_for_private_test_review")),
            "ready_for_llm_prompt": bool(rag_evidence_review.get("ready_for_llm_prompt")),
            "ready_for_discord_send": bool(rag_evidence_review.get("ready_for_discord_send")),
            "ready_for_embedding": bool(rag_evidence_review.get("ready_for_embedding")),
            "ready_for_external_sources": bool(rag_evidence_review.get("ready_for_external_sources")),
        },
        "knowledge_dry_chain": {
            "available": True,
            "sample_files_present": bool(knowledge_dry_chain.get("sample_files_present")),
            "manifest_available": bool(knowledge_dry_chain.get("manifest_available")),
            "evidence_packet_available": bool(knowledge_dry_chain.get("evidence_packet_available")),
            "rag_response_packet_available": bool(knowledge_dry_chain.get("rag_response_packet_available")),
            "review_packet_available": bool(knowledge_dry_chain.get("review_packet_available")),
            "ready_for_private_test_review": bool(knowledge_dry_chain.get("ready_for_private_test_review")),
            "ready_for_llm_prompt": bool(knowledge_dry_chain.get("ready_for_llm_prompt")),
            "ready_for_discord_send": bool(knowledge_dry_chain.get("ready_for_discord_send")),
            "ready_for_embedding": bool(knowledge_dry_chain.get("ready_for_embedding")),
            "ready_for_external_sources": bool(knowledge_dry_chain.get("ready_for_external_sources")),
        },
        "rag_evidence_prompt_envelope": {
            "available": True,
            "review_only": bool(rag_evidence_prompt.get("review_only")),
            "human_review_required": bool(rag_evidence_prompt.get("human_review_required")),
            "ready_for_prompt_preview": bool(rag_evidence_prompt.get("ready_for_prompt_preview")),
            "ready_for_llm_api_call": bool(rag_evidence_prompt.get("ready_for_llm_api_call")),
            "ready_for_discord_send": bool(rag_evidence_prompt.get("ready_for_discord_send")),
            "ready_for_embedding": bool(rag_evidence_prompt.get("ready_for_embedding")),
            "ready_for_external_sources": bool(rag_evidence_prompt.get("ready_for_external_sources")),
        },
        "rag_evidence_llm_dry_readiness": {
            "available": True,
            "prompt_envelope_available": bool(rag_evidence_llm_readiness.get("prompt_envelope_available")),
            "prompt_safety_allowed": bool(rag_evidence_llm_readiness.get("prompt_safety_allowed")),
            "mock_response_created": bool(rag_evidence_llm_readiness.get("mock_response_created")),
            "mock_response_safety_allowed": bool(rag_evidence_llm_readiness.get("mock_response_safety_allowed")),
            "llm_response_packet_created": bool(rag_evidence_llm_readiness.get("llm_response_packet_created")),
            "ready_for_actual_llm_dry_call": bool(rag_evidence_llm_readiness.get("ready_for_actual_llm_dry_call")),
            "actual_llm_api_call": bool(rag_evidence_llm_readiness.get("actual_llm_api_call")),
            "ready_for_discord_send": bool(rag_evidence_llm_readiness.get("ready_for_discord_send")),
            "embedding_api_called": bool(rag_evidence_llm_readiness.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_llm_readiness.get("external_execution")),
        },
        "rag_evidence_llm_dry_call": {
            "available": True,
            "manual_approval_required": bool(rag_evidence_llm_dry_call.get("manual_approval", {}).get("required")),
            "manual_approval_approved": bool(rag_evidence_llm_dry_call.get("manual_approval", {}).get("approved")),
            "ready": bool(rag_evidence_llm_dry_call.get("ready")),
            "blocked": bool(rag_evidence_llm_dry_call.get("blocked")),
            "actual_llm_api_call": bool(rag_evidence_llm_dry_call.get("actual_llm_api_call")),
            "api_call_attempted": bool(rag_evidence_llm_dry_call.get("api_call_attempted")),
            "api_call_succeeded": bool(rag_evidence_llm_dry_call.get("api_call_succeeded")),
            "llm_response_packet_created": bool(rag_evidence_llm_dry_call.get("llm_response_packet_created")),
            "output_safety_allowed": bool(rag_evidence_llm_dry_call.get("output_safety_allowed")),
            "ready_for_discord_send": bool(rag_evidence_llm_dry_call.get("ready_for_discord_send")),
            "discord_message_sent": bool(rag_evidence_llm_dry_call.get("discord_message_sent")),
            "embedding_api_called": bool(rag_evidence_llm_dry_call.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_llm_dry_call.get("external_execution")),
        },
        "rag_evidence_llm_dry_call_closeout": {
            "available": True,
            "actual_dry_call_observed": bool(rag_evidence_llm_closeout.get("actual_dry_call_observed")),
            "api_call_succeeded_count": int(rag_evidence_llm_closeout.get("api_call_succeeded_count", 0) or 0),
            "llm_response_packet_created": bool(rag_evidence_llm_closeout.get("llm_response_packet_created")),
            "output_safety_allowed": bool(rag_evidence_llm_closeout.get("output_safety_allowed")),
            "ready_for_discord_send": bool(rag_evidence_llm_closeout.get("ready_for_discord_send")),
            "discord_message_sent": bool(rag_evidence_llm_closeout.get("discord_message_sent")),
            "embedding_api_called": bool(rag_evidence_llm_closeout.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_llm_closeout.get("external_execution")),
            "additional_llm_api_call": bool(rag_evidence_llm_closeout.get("additional_llm_api_call")),
            "ready_for_phase34i_private_test_would_send_preview": bool(rag_evidence_llm_closeout.get("ready_for_phase34i_private_test_would_send_preview")),
        },
        "rag_evidence_would_send_preview": {
            "available": True,
            "would_send_preview_created": bool(rag_evidence_would_send.get("would_send_preview_created")),
            "private_test_channel_only": bool(rag_evidence_would_send.get("private_test_channel_only")),
            "public_channel_send_allowed": bool(rag_evidence_would_send.get("public_channel_send_allowed")),
            "team_channel_send_allowed": bool(rag_evidence_would_send.get("team_channel_send_allowed")),
            "discord_api_send_allowed": bool(rag_evidence_would_send.get("discord_api_send_allowed")),
            "discord_api_send_called": bool(rag_evidence_would_send.get("discord_api_send_called")),
            "discord_message_sent": bool(rag_evidence_would_send.get("discord_message_sent")),
            "ready_for_actual_discord_send": bool(rag_evidence_would_send.get("ready_for_actual_discord_send")),
            "ready_for_phase34j_private_test_send_preflight": bool(rag_evidence_would_send.get("ready_for_phase34j_private_test_send_preflight")),
        },
        "rag_evidence_private_test_send_preflight": {
            "available": True,
            "would_send_preview_available": bool(rag_evidence_send_preflight.get("would_send_preview_available")),
            "manual_approval_required": bool(rag_evidence_send_preflight.get("manual_approval_required")),
            "private_test_channel_only": bool(rag_evidence_send_preflight.get("private_test_channel_only")),
            "public_channel_send_allowed": bool(rag_evidence_send_preflight.get("public_channel_send_allowed")),
            "team_channel_send_allowed": bool(rag_evidence_send_preflight.get("team_channel_send_allowed")),
            "discord_api_send_allowed": bool(rag_evidence_send_preflight.get("discord_api_send_allowed")),
            "discord_api_send_called": bool(rag_evidence_send_preflight.get("discord_api_send_called")),
            "discord_message_sent": bool(rag_evidence_send_preflight.get("discord_message_sent")),
            "ready_for_actual_private_test_send": bool(rag_evidence_send_preflight.get("ready_for_actual_private_test_send")),
            "ready_for_phase34j1_manual_live_send": bool(rag_evidence_send_preflight.get("ready_for_phase34j1_manual_live_send")),
        },
        "rag_evidence_private_test_send": {
            "available": True,
            "manual_approval_required": True,
            "private_test_channel_only": bool(rag_evidence_send.get("private_test_channel_only")),
            "public_channel_send_allowed": bool(rag_evidence_send.get("public_channel_send_allowed")),
            "team_channel_send_allowed": bool(rag_evidence_send.get("team_channel_send_allowed")),
            "discord_api_send_called": bool(rag_evidence_send.get("discord_api_send_called")),
            "discord_message_sent": bool(rag_evidence_send.get("discord_message_sent")),
            "message_sent_count": int(rag_evidence_send.get("message_sent_count", 0) or 0),
            "ready_for_phase34j2_send_closeout": bool(rag_evidence_send.get("ready_for_phase34j2_send_closeout")),
            "llm_api_called": bool(rag_evidence_send.get("llm_api_called")),
            "embedding_api_called": bool(rag_evidence_send.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_send.get("external_execution")),
        },
        "rag_evidence_private_test_send_closeout": {
            "available": True,
            "actual_private_test_send_observed": bool(rag_evidence_send_closeout.get("actual_private_test_send_observed")),
            "discord_api_send_called_count": int(rag_evidence_send_closeout.get("discord_api_send_called_count", 0) or 0),
            "discord_message_sent_count": int(rag_evidence_send_closeout.get("discord_message_sent_count", 0) or 0),
            "sent_channel_scope": rag_evidence_send_closeout.get("sent_channel_scope", ""),
            "additional_discord_send": bool(rag_evidence_send_closeout.get("additional_discord_send")),
            "llm_api_called": bool(rag_evidence_send_closeout.get("llm_api_called")),
            "embedding_api_called": bool(rag_evidence_send_closeout.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_send_closeout.get("external_execution")),
            "closeout_passed": bool(rag_evidence_send_closeout.get("closeout_passed")),
            "ready_for_phase34k_private_test_e2e_preflight": bool(rag_evidence_send_closeout.get("ready_for_phase34k_private_test_e2e_preflight")),
        },
        "rag_evidence_private_test_e2e_preflight": {
            "available": True,
            "private_test_channel_only": bool(rag_evidence_e2e_preflight.get("private_test_channel_only")),
            "public_channel_reply_allowed": bool(rag_evidence_e2e_preflight.get("public_channel_reply_allowed")),
            "team_channel_reply_allowed": bool(rag_evidence_e2e_preflight.get("team_channel_reply_allowed")),
            "discord_live_runtime_executed": bool(rag_evidence_e2e_preflight.get("discord_live_runtime_executed")),
            "discord_api_send_called": bool(rag_evidence_e2e_preflight.get("discord_api_send_called")),
            "discord_message_sent": bool(rag_evidence_e2e_preflight.get("discord_message_sent")),
            "llm_api_called": bool(rag_evidence_e2e_preflight.get("llm_api_called")),
            "embedding_api_called": bool(rag_evidence_e2e_preflight.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_e2e_preflight.get("external_execution")),
            "ready_for_phase34l1_manual_e2e_live_reply": bool(rag_evidence_e2e_preflight.get("ready_for_phase34l1_manual_e2e_live_reply")),
            "ready_for_unattended_auto_reply": bool(rag_evidence_e2e_preflight.get("ready_for_unattended_auto_reply")),
        },
        "rag_evidence_private_test_e2e_replay": {
            "available": True,
            "e2e_replay_passed": bool(rag_evidence_e2e_replay.get("e2e_replay_passed")),
            "discord_live_runtime_executed": bool(rag_evidence_e2e_replay.get("discord_live_runtime_executed")),
            "discord_api_send_called": bool(rag_evidence_e2e_replay.get("discord_api_send_called")),
            "discord_message_sent": bool(rag_evidence_e2e_replay.get("discord_message_sent")),
            "llm_api_called": bool(rag_evidence_e2e_replay.get("llm_api_called")),
            "embedding_api_called": bool(rag_evidence_e2e_replay.get("embedding_api_called")),
            "external_execution": bool(rag_evidence_e2e_replay.get("external_execution")),
            "ready_for_phase34l1_manual_e2e_live_reply": bool(rag_evidence_e2e_replay.get("ready_for_phase34l1_manual_e2e_live_reply")),
            "ready_for_unattended_auto_reply": bool(rag_evidence_e2e_replay.get("ready_for_unattended_auto_reply")),
        },
        "rag_evidence_private_test_e2e_live_reply": {
            "available": True,
            "manual_approval_required": bool(rag_evidence_e2e_live_reply.get("manual_approval", {}).get("required")),
            "manual_approval_approved": bool(rag_evidence_e2e_live_reply.get("manual_approval", {}).get("approved")),
            "private_test_channel_only": bool(rag_evidence_e2e_live_reply.get("private_test_channel_only")),
            "public_channel_reply_allowed": bool(rag_evidence_e2e_live_reply.get("public_channel_reply_allowed")),
            "team_channel_reply_allowed": bool(rag_evidence_e2e_live_reply.get("team_channel_reply_allowed")),
            "openrouter_api_key_present": bool(rag_evidence_e2e_live_reply.get("openrouter_api_key_present")),
            "openrouter_api_key_aliases_checked": rag_evidence_e2e_live_reply.get("openrouter_api_key_aliases_checked", []),
            "openrouter_api_key_value_logged": bool(rag_evidence_e2e_live_reply.get("openrouter_api_key_value_logged")),
            "ready": bool(rag_evidence_e2e_live_reply.get("ready")),
            "blocked": bool(rag_evidence_e2e_live_reply.get("blocked")),
            "discord_live_runtime_executed": bool(rag_evidence_e2e_live_reply.get("discord_live_runtime_executed")),
            "discord_event_received": bool(rag_evidence_e2e_live_reply.get("discord_event_received")),
            "accepted_private_test_channel": bool(rag_evidence_e2e_live_reply.get("accepted_private_test_channel")),
            "prompt_safety_checked": bool(rag_evidence_e2e_live_reply.get("prompt_safety_checked")),
            "prompt_safety_allowed": bool(rag_evidence_e2e_live_reply.get("prompt_safety_allowed")),
            "prompt_safety_blocked": bool(rag_evidence_e2e_live_reply.get("prompt_safety_blocked")),
            "llm_stage_reached": bool(rag_evidence_e2e_live_reply.get("llm_stage_reached")),
            "llm_call_allowed": bool(rag_evidence_e2e_live_reply.get("llm_call_allowed")),
            "llm_dispatch_invoked": bool(rag_evidence_e2e_live_reply.get("llm_dispatch_invoked")),
            "llm_dispatch_mode": rag_evidence_e2e_live_reply.get("llm_dispatch_mode", ""),
            "llm_dispatch_blocked_reason": rag_evidence_e2e_live_reply.get("llm_dispatch_blocked_reason", ""),
            "llm_api_call_attempted": bool(rag_evidence_e2e_live_reply.get("llm_api_call_attempted")),
            "llm_api_called": bool(rag_evidence_e2e_live_reply.get("llm_api_called")),
            "llm_api_call_count": int(rag_evidence_e2e_live_reply.get("llm_api_call_count", 0) or 0),
            "llm_response_packet_created": bool(rag_evidence_e2e_live_reply.get("llm_response_packet_created")),
            "output_safety_checked": bool(rag_evidence_e2e_live_reply.get("output_safety_checked")),
            "output_safety_allowed": bool(rag_evidence_e2e_live_reply.get("output_safety_allowed")),
            "output_safety_blocked": bool(rag_evidence_e2e_live_reply.get("output_safety_blocked")),
            "discord_message_sent": bool(rag_evidence_e2e_live_reply.get("discord_message_sent")),
            "message_sent_count": int(rag_evidence_e2e_live_reply.get("message_sent_count", 0) or 0),
            "ready_for_phase34l2_e2e_live_reply_closeout": bool(rag_evidence_e2e_live_reply.get("ready_for_phase34l2_e2e_live_reply_closeout")),
            "ready_for_unattended_auto_reply": bool(rag_evidence_e2e_live_reply.get("ready_for_unattended_auto_reply")),
        },
        "rag_evidence_private_test_e2e_partial_success": {
            "available": bool(rag_evidence_e2e_partial_success.get("ready_for_manual_send_retry_without_llm")),
            "llm_api_called": bool(rag_evidence_e2e_partial_success.get("llm_api_called")),
            "llm_api_call_count": int(rag_evidence_e2e_partial_success.get("llm_api_call_count", 0) or 0),
            "output_safety_allowed": bool(rag_evidence_e2e_partial_success.get("output_safety_allowed")),
            "discord_message_sent": bool(rag_evidence_e2e_partial_success.get("discord_message_sent")),
            "ready_for_manual_send_retry_without_llm": bool(rag_evidence_e2e_partial_success.get("ready_for_manual_send_retry_without_llm")),
        },
        "rag_evidence_private_test_e2e_send_retry": {
            "available": bool(rag_evidence_e2e_send_retry),
            "llm_recall_allowed": bool(rag_evidence_e2e_send_retry.get("llm_recall_allowed")),
            "manual_approval_required": bool(rag_evidence_e2e_send_retry.get("manual_approval_required")),
            "actual_send_retry_sender_available": bool(rag_evidence_e2e_send_retry.get("actual_send_retry_sender_available")),
            "actual_send_retry_sender_not_provided": bool(rag_evidence_e2e_send_retry.get("actual_send_retry_sender_not_provided")),
            "ready_for_actual_send_retry": bool(rag_evidence_e2e_send_retry.get("ready_for_actual_send_retry")),
            "ready_for_phase34l2_e2e_live_reply_closeout": bool(rag_evidence_e2e_send_retry.get("ready_for_phase34l2_e2e_live_reply_closeout")),
            "discord_message_sent": bool(rag_evidence_e2e_send_retry.get("discord_message_sent")),
            "message_sent_count": int(rag_evidence_e2e_send_retry.get("message_sent_count", 0) or 0),
        },
        "rag_evidence_private_test_e2e_live_closeout": {
            "available": True,
            "e2e_live_reply_observed": bool(rag_evidence_e2e_live_closeout.get("e2e_live_reply_observed")),
            "llm_api_call_count": int(rag_evidence_e2e_live_closeout.get("llm_api_call_count", 0) or 0),
            "send_retry_llm_call_count": int(rag_evidence_e2e_live_closeout.get("no_llm_send_retry", {}).get("llm_api_call_count", 0) or 0),
            "final_discord_message_sent_count": int(rag_evidence_e2e_live_closeout.get("final_result", {}).get("message_sent_count", 0) or 0),
            "sent_channel_scope": rag_evidence_e2e_live_closeout.get("final_result", {}).get("sent_channel_scope", ""),
            "closeout_passed": bool(rag_evidence_e2e_live_closeout.get("closeout_passed")),
            "ready_for_phase34m_final_lock": bool(rag_evidence_e2e_live_closeout.get("final_result", {}).get("ready_for_phase34m_final_lock")),
            "ready_for_unattended_auto_reply": bool(rag_evidence_e2e_live_closeout.get("final_result", {}).get("ready_for_unattended_auto_reply")),
        },
        "rag_evidence_private_test_phase34_final_lock": {
            "available": True,
            "phase34_private_test_mvp_complete": bool(rag_evidence_phase34_final_lock.get("phase34_private_test_mvp_complete")),
            "llm_api_call_count": int(rag_evidence_phase34_final_lock.get("e2e_live_reply_closeout", {}).get("llm_api_call_count", 0) or 0),
            "send_retry_llm_call_count": int(rag_evidence_phase34_final_lock.get("no_llm_send_retry_closeout", {}).get("llm_api_call_count", 0) or 0),
            "final_discord_message_sent_count": int(rag_evidence_phase34_final_lock.get("no_llm_send_retry_closeout", {}).get("message_sent_count", 0) or 0),
            "sent_channel_scope": rag_evidence_phase34_final_lock.get("no_llm_send_retry_closeout", {}).get("sent_channel_scope", ""),
            "ready_for_unattended_auto_reply": bool(rag_evidence_phase34_final_lock.get("final_safety_state", {}).get("ready_for_unattended_auto_reply")),
            "phase34m_final_lock_passed": bool(rag_evidence_phase34_final_lock.get("phase34m_final_lock_passed")),
        },
        "phase35a_post_mvp_safety_audit": {
            "available": True,
            "phase34_private_test_mvp_complete": bool(phase35a_audit.get("phase34_private_test_mvp_complete")),
            "phase34m_final_lock_passed": bool(phase35a_audit.get("phase34m_final_lock_passed")),
            "total_llm_call_count": int(phase35a_audit.get("final_e2e_counts", {}).get("total_llm_call_count", 0) or 0),
            "send_retry_llm_call_count": int(phase35a_audit.get("final_e2e_counts", {}).get("send_retry_llm_call_count", 0) or 0),
            "final_discord_message_sent_count": int(phase35a_audit.get("final_e2e_counts", {}).get("final_discord_message_sent_count", 0) or 0),
            "sent_channel_scope": phase35a_audit.get("final_e2e_counts", {}).get("sent_channel_scope", ""),
            "public_team_blocked": not any(
                bool(phase35a_audit.get("blocked_scopes", {}).get(key))
                for key in ("public_channel_reply_allowed", "team_channel_reply_allowed", "public_channel_send_allowed", "team_channel_send_allowed")
            ),
            "unattended_auto_reply_allowed": bool(phase35a_audit.get("blocked_scopes", {}).get("unattended_auto_reply_allowed")),
            "embedding_external_disabled": not any(bool(value) for value in phase35a_audit.get("disabled_capabilities", {}).values()),
            "phase35a_audit_passed": bool(phase35a_audit.get("phase35a_audit_passed")),
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
    rag_llm_readiness = report.get("rag_llm_live_readiness_review", {})
    rag_llm_runtime = report.get("rag_llm_private_test_runtime", {})
    rag_llm_closeout = report.get("rag_llm_live_preflight_closeout", {})
    rag_llm_success_closeout = report.get("rag_llm_single_live_test_closeout", {})
    knowledge = report.get("knowledge_foundation", {})
    rag_evidence = report.get("rag_evidence_integration", {})
    rag_evidence_review = report.get("rag_evidence_review_packet", {})
    knowledge_dry_chain = report.get("knowledge_dry_chain", {})
    rag_evidence_prompt = report.get("rag_evidence_prompt_envelope", {})
    rag_evidence_llm = report.get("rag_evidence_llm_dry_readiness", {})
    rag_evidence_llm_dry_call = report.get("rag_evidence_llm_dry_call", {})
    rag_evidence_llm_closeout = report.get("rag_evidence_llm_dry_call_closeout", {})
    rag_evidence_would_send = report.get("rag_evidence_would_send_preview", {})
    rag_evidence_send_preflight = report.get("rag_evidence_private_test_send_preflight", {})
    rag_evidence_send = report.get("rag_evidence_private_test_send", {})
    rag_evidence_send_closeout = report.get("rag_evidence_private_test_send_closeout", {})
    rag_evidence_e2e_preflight = report.get("rag_evidence_private_test_e2e_preflight", {})
    rag_evidence_e2e_replay = report.get("rag_evidence_private_test_e2e_replay", {})
    rag_evidence_e2e_live_reply = report.get("rag_evidence_private_test_e2e_live_reply", {})
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
            "",
            "## RAG+LLM Live Readiness",
            f"- Go: {str(rag_llm_readiness.get('go', False)).lower()}",
            f"- Manual implementation request ready: {str(rag_llm_readiness.get('ready_for_manual_phase33d_implementation_request', False)).lower()}",
            f"- Actual Discord send: {str(rag_llm_readiness.get('actual_discord_send', False)).lower()}",
            f"- Actual LLM API call: {str(rag_llm_readiness.get('actual_llm_api_call', False)).lower()}",
            f"- Embedding API: {str(rag_llm_readiness.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_llm_readiness.get('external_execution', False)).lower()}",
            "",
            "## RAG+LLM Private Test Runtime",
            f"- Available: {str(rag_llm_runtime.get('available', False)).lower()}",
            f"- Ready: {str(rag_llm_runtime.get('ready', False)).lower()}",
            f"- Blocked: {str(rag_llm_runtime.get('blocked', True)).lower()}",
            f"- Runtime option added: {str(rag_llm_runtime.get('runtime_option_added', False)).lower()}",
            "- Runtime executed by report: false",
            f"- Actual Discord send: {str(rag_llm_runtime.get('actual_discord_send', False)).lower()}",
            f"- Actual LLM API call: {str(rag_llm_runtime.get('actual_llm_api_call', False)).lower()}",
            f"- Embedding API: {str(rag_llm_runtime.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_llm_runtime.get('external_execution', False)).lower()}",
            "",
            "## RAG+LLM Live Preflight Closeout",
            f"- Runtime executed: {str(rag_llm_closeout.get('runtime_executed', False)).lower()}",
            f"- Ready for single live private test: {str(rag_llm_closeout.get('ready_for_single_live_private_test', False)).lower()}",
            f"- Actual Discord send: {str(rag_llm_closeout.get('actual_discord_send', False)).lower()}",
            f"- Actual LLM API call: {str(rag_llm_closeout.get('actual_llm_api_call', False)).lower()}",
            f"- Embedding API: {str(rag_llm_closeout.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_llm_closeout.get('external_execution', False)).lower()}",
            "",
            "## RAG+LLM Single Live Test Closeout",
            f"- Available: {str(rag_llm_success_closeout.get('available', False)).lower()}",
            f"- Closeout passed: {str(rag_llm_success_closeout.get('closeout_passed', False)).lower()}",
            f"- Sent exactly once: {str(rag_llm_success_closeout.get('sent_exactly_once', False)).lower()}",
            f"- Self-loop prevented: {str(rag_llm_success_closeout.get('self_loop_prevented', False)).lower()}",
            f"- Private test channel only: {str(rag_llm_success_closeout.get('private_test_channel_only', False)).lower()}",
            f"- LLM API called once: {str(rag_llm_success_closeout.get('llm_api_called_once', False)).lower()}",
            f"- Discord message sent once: {str(rag_llm_success_closeout.get('discord_message_sent_once', False)).lower()}",
            f"- Embedding API called: {str(rag_llm_success_closeout.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_llm_success_closeout.get('external_execution', False)).lower()}",
            f"- Ready for Phase 34 knowledge ingestion: {str(rag_llm_success_closeout.get('ready_for_phase34_knowledge_ingestion', False)).lower()}",
            "",
            "## Knowledge Foundation",
            f"- Available: {str(knowledge.get('available', False)).lower()}",
            f"- Ready for local text ingestion: {str(knowledge.get('ready_for_local_text_ingestion', False)).lower()}",
            f"- Ready for embedding: {str(knowledge.get('ready_for_embedding', False)).lower()}",
            f"- Ready for external sources: {str(knowledge.get('ready_for_external_sources', False)).lower()}",
            f"- Source routing available: {str(knowledge.get('source_routing_available', False)).lower()}",
            f"- Evidence packet available: {str(knowledge.get('evidence_packet_available', False)).lower()}",
            f"- Canonical sources: {', '.join(knowledge.get('canonical_sources', []))}",
            f"- Operations source present: {str(knowledge.get('operations_source_present', False)).lower()}",
            f"- Embedding API called: {str(knowledge.get('embedding_api_called', False)).lower()}",
            f"- LLM API called: {str(knowledge.get('llm_api_called', False)).lower()}",
            f"- Discord message sent: {str(knowledge.get('discord_message_sent', False)).lower()}",
            f"- External execution: {str(knowledge.get('external_execution', False)).lower()}",
            "",
            "## RAG Evidence Integration",
            f"- Available: {str(rag_evidence.get('available', False)).lower()}",
            f"- Evidence packet available: {str(rag_evidence.get('evidence_packet_available', False)).lower()}",
            f"- RAG response packet created: {str(rag_evidence.get('rag_response_packet_created', False)).lower()}",
            f"- Citations included: {str(rag_evidence.get('citations_included', False)).lower()}",
            f"- Ready for private test review: {str(rag_evidence.get('ready_for_private_test_review', False)).lower()}",
            f"- Ready for LLM prompt: {str(rag_evidence.get('ready_for_llm_prompt', False)).lower()}",
            f"- Ready for embedding: {str(rag_evidence.get('ready_for_embedding', False)).lower()}",
            f"- Ready for external sources: {str(rag_evidence.get('ready_for_external_sources', False)).lower()}",
            f"- Embedding API called: {str(rag_evidence.get('embedding_api_called', False)).lower()}",
            f"- LLM API called: {str(rag_evidence.get('llm_api_called', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence.get('discord_message_sent', False)).lower()}",
            f"- External execution: {str(rag_evidence.get('external_execution', False)).lower()}",
            "",
            "## RAG Evidence Review Packet",
            f"- Available: {str(rag_evidence_review.get('available', False)).lower()}",
            f"- Review only: {str(rag_evidence_review.get('review_only', False)).lower()}",
            f"- Human review required: {str(rag_evidence_review.get('human_review_required', False)).lower()}",
            f"- Ready for private test review: {str(rag_evidence_review.get('ready_for_private_test_review', False)).lower()}",
            f"- Ready for LLM prompt: {str(rag_evidence_review.get('ready_for_llm_prompt', False)).lower()}",
            f"- Ready for Discord send: {str(rag_evidence_review.get('ready_for_discord_send', False)).lower()}",
            f"- Ready for embedding: {str(rag_evidence_review.get('ready_for_embedding', False)).lower()}",
            f"- Ready for external sources: {str(rag_evidence_review.get('ready_for_external_sources', False)).lower()}",
            "",
            "## Knowledge Dry Chain",
            f"- Available: {str(knowledge_dry_chain.get('available', False)).lower()}",
            f"- Sample files present: {str(knowledge_dry_chain.get('sample_files_present', False)).lower()}",
            f"- Manifest available: {str(knowledge_dry_chain.get('manifest_available', False)).lower()}",
            f"- Evidence packet available: {str(knowledge_dry_chain.get('evidence_packet_available', False)).lower()}",
            f"- RAG response packet available: {str(knowledge_dry_chain.get('rag_response_packet_available', False)).lower()}",
            f"- Review packet available: {str(knowledge_dry_chain.get('review_packet_available', False)).lower()}",
            f"- Ready for private test review: {str(knowledge_dry_chain.get('ready_for_private_test_review', False)).lower()}",
            f"- Ready for LLM prompt: {str(knowledge_dry_chain.get('ready_for_llm_prompt', False)).lower()}",
            f"- Ready for Discord send: {str(knowledge_dry_chain.get('ready_for_discord_send', False)).lower()}",
            f"- Ready for embedding: {str(knowledge_dry_chain.get('ready_for_embedding', False)).lower()}",
            f"- Ready for external sources: {str(knowledge_dry_chain.get('ready_for_external_sources', False)).lower()}",
            "",
            "## RAG Evidence Prompt Envelope",
            f"- Available: {str(rag_evidence_prompt.get('available', False)).lower()}",
            f"- Review only: {str(rag_evidence_prompt.get('review_only', False)).lower()}",
            f"- Human review required: {str(rag_evidence_prompt.get('human_review_required', False)).lower()}",
            f"- Ready for prompt preview: {str(rag_evidence_prompt.get('ready_for_prompt_preview', False)).lower()}",
            f"- Ready for LLM API call: {str(rag_evidence_prompt.get('ready_for_llm_api_call', False)).lower()}",
            f"- Ready for Discord send: {str(rag_evidence_prompt.get('ready_for_discord_send', False)).lower()}",
            f"- Ready for embedding: {str(rag_evidence_prompt.get('ready_for_embedding', False)).lower()}",
            f"- Ready for external sources: {str(rag_evidence_prompt.get('ready_for_external_sources', False)).lower()}",
            "",
            "## RAG Evidence LLM Dry Readiness",
            f"- Available: {str(rag_evidence_llm.get('available', False)).lower()}",
            f"- Prompt envelope available: {str(rag_evidence_llm.get('prompt_envelope_available', False)).lower()}",
            f"- Prompt safety allowed: {str(rag_evidence_llm.get('prompt_safety_allowed', False)).lower()}",
            f"- Mock response created: {str(rag_evidence_llm.get('mock_response_created', False)).lower()}",
            f"- Mock response safety allowed: {str(rag_evidence_llm.get('mock_response_safety_allowed', False)).lower()}",
            f"- LLM response packet created: {str(rag_evidence_llm.get('llm_response_packet_created', False)).lower()}",
            f"- Ready for actual LLM dry call: {str(rag_evidence_llm.get('ready_for_actual_llm_dry_call', False)).lower()}",
            f"- Actual LLM API call: {str(rag_evidence_llm.get('actual_llm_api_call', False)).lower()}",
            f"- Ready for Discord send: {str(rag_evidence_llm.get('ready_for_discord_send', False)).lower()}",
            f"- Embedding API called: {str(rag_evidence_llm.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_evidence_llm.get('external_execution', False)).lower()}",
            "",
            "## RAG Evidence LLM Dry Call",
            f"- Available: {str(rag_evidence_llm_dry_call.get('available', False)).lower()}",
            f"- Manual approval required: {str(rag_evidence_llm_dry_call.get('manual_approval_required', False)).lower()}",
            f"- Manual approval approved: {str(rag_evidence_llm_dry_call.get('manual_approval_approved', False)).lower()}",
            f"- Ready: {str(rag_evidence_llm_dry_call.get('ready', False)).lower()}",
            f"- Blocked: {str(rag_evidence_llm_dry_call.get('blocked', True)).lower()}",
            f"- Actual LLM API call: {str(rag_evidence_llm_dry_call.get('actual_llm_api_call', False)).lower()}",
            f"- API call attempted: {str(rag_evidence_llm_dry_call.get('api_call_attempted', False)).lower()}",
            f"- API call succeeded: {str(rag_evidence_llm_dry_call.get('api_call_succeeded', False)).lower()}",
            f"- LLM response packet created: {str(rag_evidence_llm_dry_call.get('llm_response_packet_created', False)).lower()}",
            f"- Output safety allowed: {str(rag_evidence_llm_dry_call.get('output_safety_allowed', False)).lower()}",
            f"- Ready for Discord send: {str(rag_evidence_llm_dry_call.get('ready_for_discord_send', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_llm_dry_call.get('discord_message_sent', False)).lower()}",
            f"- Embedding API called: {str(rag_evidence_llm_dry_call.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_evidence_llm_dry_call.get('external_execution', False)).lower()}",
            "",
            "## RAG Evidence LLM Dry Call Closeout",
            f"- Available: {str(rag_evidence_llm_closeout.get('available', False)).lower()}",
            f"- Actual dry call observed: {str(rag_evidence_llm_closeout.get('actual_dry_call_observed', False)).lower()}",
            f"- API call succeeded count: {rag_evidence_llm_closeout.get('api_call_succeeded_count', 0)}",
            f"- LLM response packet created: {str(rag_evidence_llm_closeout.get('llm_response_packet_created', False)).lower()}",
            f"- Output safety allowed: {str(rag_evidence_llm_closeout.get('output_safety_allowed', False)).lower()}",
            f"- Ready for Discord send: {str(rag_evidence_llm_closeout.get('ready_for_discord_send', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_llm_closeout.get('discord_message_sent', False)).lower()}",
            f"- Embedding API called: {str(rag_evidence_llm_closeout.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_evidence_llm_closeout.get('external_execution', False)).lower()}",
            f"- Additional LLM API call: {str(rag_evidence_llm_closeout.get('additional_llm_api_call', False)).lower()}",
            f"- Ready for Phase 34I private-test would-send preview: {str(rag_evidence_llm_closeout.get('ready_for_phase34i_private_test_would_send_preview', False)).lower()}",
            "",
            "## RAG Evidence Would-send Preview",
            f"- Available: {str(rag_evidence_would_send.get('available', False)).lower()}",
            f"- Preview created: {str(rag_evidence_would_send.get('would_send_preview_created', False)).lower()}",
            f"- Private test channel only: {str(rag_evidence_would_send.get('private_test_channel_only', False)).lower()}",
            f"- Public channel send allowed: {str(rag_evidence_would_send.get('public_channel_send_allowed', False)).lower()}",
            f"- Team channel send allowed: {str(rag_evidence_would_send.get('team_channel_send_allowed', False)).lower()}",
            f"- Discord API send allowed: {str(rag_evidence_would_send.get('discord_api_send_allowed', False)).lower()}",
            f"- Discord API send called: {str(rag_evidence_would_send.get('discord_api_send_called', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_would_send.get('discord_message_sent', False)).lower()}",
            f"- Ready for actual Discord send: {str(rag_evidence_would_send.get('ready_for_actual_discord_send', False)).lower()}",
            f"- Ready for Phase 34J preflight: {str(rag_evidence_would_send.get('ready_for_phase34j_private_test_send_preflight', False)).lower()}",
            "",
            "## RAG Evidence Private-test Send Preflight",
            f"- Available: {str(rag_evidence_send_preflight.get('available', False)).lower()}",
            f"- Would-send preview available: {str(rag_evidence_send_preflight.get('would_send_preview_available', False)).lower()}",
            f"- Manual approval required: {str(rag_evidence_send_preflight.get('manual_approval_required', False)).lower()}",
            f"- Private test channel only: {str(rag_evidence_send_preflight.get('private_test_channel_only', False)).lower()}",
            f"- Public channel send allowed: {str(rag_evidence_send_preflight.get('public_channel_send_allowed', False)).lower()}",
            f"- Team channel send allowed: {str(rag_evidence_send_preflight.get('team_channel_send_allowed', False)).lower()}",
            f"- Discord API send allowed: {str(rag_evidence_send_preflight.get('discord_api_send_allowed', False)).lower()}",
            f"- Discord API send called: {str(rag_evidence_send_preflight.get('discord_api_send_called', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_send_preflight.get('discord_message_sent', False)).lower()}",
            f"- Ready for actual private-test send: {str(rag_evidence_send_preflight.get('ready_for_actual_private_test_send', False)).lower()}",
            f"- Ready for Phase 34J-1 manual live send: {str(rag_evidence_send_preflight.get('ready_for_phase34j1_manual_live_send', False)).lower()}",
            "",
            "## RAG Evidence Private-test Send",
            f"- Available: {str(rag_evidence_send.get('available', False)).lower()}",
            f"- Manual approval required: {str(rag_evidence_send.get('manual_approval_required', False)).lower()}",
            f"- Private test channel only: {str(rag_evidence_send.get('private_test_channel_only', False)).lower()}",
            f"- Public channel send allowed: {str(rag_evidence_send.get('public_channel_send_allowed', False)).lower()}",
            f"- Team channel send allowed: {str(rag_evidence_send.get('team_channel_send_allowed', False)).lower()}",
            f"- Discord API send called: {str(rag_evidence_send.get('discord_api_send_called', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_send.get('discord_message_sent', False)).lower()}",
            f"- Message sent count: {rag_evidence_send.get('message_sent_count', 0)}",
            f"- Ready for Phase 34J-2 send closeout: {str(rag_evidence_send.get('ready_for_phase34j2_send_closeout', False)).lower()}",
            f"- LLM API called: {str(rag_evidence_send.get('llm_api_called', False)).lower()}",
            f"- Embedding API called: {str(rag_evidence_send.get('embedding_api_called', False)).lower()}",
            f"- External execution: {str(rag_evidence_send.get('external_execution', False)).lower()}",
            "",
            "## RAG Evidence Private-test Send Closeout",
            f"- Available: {str(rag_evidence_send_closeout.get('available', False)).lower()}",
            f"- Actual private-test send observed: {str(rag_evidence_send_closeout.get('actual_private_test_send_observed', False)).lower()}",
            f"- Discord API send called count: {rag_evidence_send_closeout.get('discord_api_send_called_count', 0)}",
            f"- Discord message sent count: {rag_evidence_send_closeout.get('discord_message_sent_count', 0)}",
            f"- Sent channel scope: {rag_evidence_send_closeout.get('sent_channel_scope', '')}",
            f"- Additional Discord send: {str(rag_evidence_send_closeout.get('additional_discord_send', False)).lower()}",
            f"- Closeout passed: {str(rag_evidence_send_closeout.get('closeout_passed', False)).lower()}",
            f"- Ready for Phase 34K E2E preflight: {str(rag_evidence_send_closeout.get('ready_for_phase34k_private_test_e2e_preflight', False)).lower()}",
            "",
            "## RAG Evidence Private-test E2E Preflight",
            f"- Available: {str(rag_evidence_e2e_preflight.get('available', False)).lower()}",
            f"- Private test channel only: {str(rag_evidence_e2e_preflight.get('private_test_channel_only', False)).lower()}",
            f"- Public channel reply allowed: {str(rag_evidence_e2e_preflight.get('public_channel_reply_allowed', False)).lower()}",
            f"- Team channel reply allowed: {str(rag_evidence_e2e_preflight.get('team_channel_reply_allowed', False)).lower()}",
            f"- Discord live runtime executed: {str(rag_evidence_e2e_preflight.get('discord_live_runtime_executed', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_e2e_preflight.get('discord_message_sent', False)).lower()}",
            f"- LLM API called: {str(rag_evidence_e2e_preflight.get('llm_api_called', False)).lower()}",
            f"- Ready for Phase 34L-1 manual E2E live reply: {str(rag_evidence_e2e_preflight.get('ready_for_phase34l1_manual_e2e_live_reply', False)).lower()}",
            f"- Ready for unattended auto reply: {str(rag_evidence_e2e_preflight.get('ready_for_unattended_auto_reply', False)).lower()}",
            "",
            "## RAG Evidence Private-test E2E Replay",
            f"- Available: {str(rag_evidence_e2e_replay.get('available', False)).lower()}",
            f"- E2E replay passed: {str(rag_evidence_e2e_replay.get('e2e_replay_passed', False)).lower()}",
            f"- Discord live runtime executed: {str(rag_evidence_e2e_replay.get('discord_live_runtime_executed', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_e2e_replay.get('discord_message_sent', False)).lower()}",
            f"- LLM API called: {str(rag_evidence_e2e_replay.get('llm_api_called', False)).lower()}",
            f"- Ready for Phase 34L-1 manual E2E live reply: {str(rag_evidence_e2e_replay.get('ready_for_phase34l1_manual_e2e_live_reply', False)).lower()}",
            f"- Ready for unattended auto reply: {str(rag_evidence_e2e_replay.get('ready_for_unattended_auto_reply', False)).lower()}",
            "",
            "## RAG Evidence Private-test E2E Live Reply",
            f"- Available: {str(rag_evidence_e2e_live_reply.get('available', False)).lower()}",
            f"- Manual approval required: {str(rag_evidence_e2e_live_reply.get('manual_approval_required', False)).lower()}",
            f"- Manual approval approved: {str(rag_evidence_e2e_live_reply.get('manual_approval_approved', False)).lower()}",
            f"- Private test channel only: {str(rag_evidence_e2e_live_reply.get('private_test_channel_only', False)).lower()}",
            f"- Public channel reply allowed: {str(rag_evidence_e2e_live_reply.get('public_channel_reply_allowed', False)).lower()}",
            f"- Team channel reply allowed: {str(rag_evidence_e2e_live_reply.get('team_channel_reply_allowed', False)).lower()}",
            f"- OpenRouter API key present: {str(rag_evidence_e2e_live_reply.get('openrouter_api_key_present', False)).lower()}",
            "- OpenRouter API key value logged: false",
            f"- Ready: {str(rag_evidence_e2e_live_reply.get('ready', False)).lower()}",
            f"- Blocked: {str(rag_evidence_e2e_live_reply.get('blocked', True)).lower()}",
            f"- Discord live runtime executed: {str(rag_evidence_e2e_live_reply.get('discord_live_runtime_executed', False)).lower()}",
            f"- Discord event received: {str(rag_evidence_e2e_live_reply.get('discord_event_received', False)).lower()}",
            f"- Accepted private-test channel: {str(rag_evidence_e2e_live_reply.get('accepted_private_test_channel', False)).lower()}",
            f"- Prompt safety checked: {str(rag_evidence_e2e_live_reply.get('prompt_safety_checked', False)).lower()}",
            f"- Prompt safety allowed: {str(rag_evidence_e2e_live_reply.get('prompt_safety_allowed', False)).lower()}",
            f"- Prompt safety blocked: {str(rag_evidence_e2e_live_reply.get('prompt_safety_blocked', False)).lower()}",
            f"- LLM stage reached: {str(rag_evidence_e2e_live_reply.get('llm_stage_reached', False)).lower()}",
            f"- LLM call allowed: {str(rag_evidence_e2e_live_reply.get('llm_call_allowed', False)).lower()}",
            f"- LLM dispatch invoked: {str(rag_evidence_e2e_live_reply.get('llm_dispatch_invoked', False)).lower()}",
            f"- LLM dispatch mode: {rag_evidence_e2e_live_reply.get('llm_dispatch_mode', '')}",
            f"- LLM dispatch blocked reason: {rag_evidence_e2e_live_reply.get('llm_dispatch_blocked_reason', '')}",
            f"- LLM API call attempted: {str(rag_evidence_e2e_live_reply.get('llm_api_call_attempted', False)).lower()}",
            f"- LLM API called: {str(rag_evidence_e2e_live_reply.get('llm_api_called', False)).lower()}",
            f"- LLM API call count: {rag_evidence_e2e_live_reply.get('llm_api_call_count', 0)}",
            f"- LLM response packet created: {str(rag_evidence_e2e_live_reply.get('llm_response_packet_created', False)).lower()}",
            f"- Output safety checked: {str(rag_evidence_e2e_live_reply.get('output_safety_checked', False)).lower()}",
            f"- Output safety allowed: {str(rag_evidence_e2e_live_reply.get('output_safety_allowed', False)).lower()}",
            f"- Output safety blocked: {str(rag_evidence_e2e_live_reply.get('output_safety_blocked', False)).lower()}",
            f"- Discord message sent: {str(rag_evidence_e2e_live_reply.get('discord_message_sent', False)).lower()}",
            f"- Message sent count: {rag_evidence_e2e_live_reply.get('message_sent_count', 0)}",
            f"- Ready for Phase 34L-2 closeout: {str(rag_evidence_e2e_live_reply.get('ready_for_phase34l2_e2e_live_reply_closeout', False)).lower()}",
            f"- Ready for unattended auto reply: {str(rag_evidence_e2e_live_reply.get('ready_for_unattended_auto_reply', False)).lower()}",
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

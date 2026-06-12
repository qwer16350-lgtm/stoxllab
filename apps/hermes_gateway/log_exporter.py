"""Export local replay results to JSON and JSONL dry-run logs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from persistence import append_jsonl, ensure_log_dirs, make_timestamped_filename, redact_sensitive_values, write_json


def _assert_export_safe(replay_result: dict[str, Any]) -> None:
    summary = replay_result.get("summary", {})
    if summary.get("external_execution_count", 0) != 0:
        raise ValueError("Refusing export: external_execution_count must be 0")
    for item in replay_result.get("approval_queue", []):
        if item.get("status") == "approved" and item.get("human_only_execution") is not True:
            raise ValueError("Refusing export: approved approval item must remain human_only_execution=true")
        if item.get("external_execution_allowed") is not False:
            raise ValueError("Refusing export: approval item must keep external_execution_allowed=false")


def export_replay_result(
    replay_result: dict[str, Any],
    log_root: str | Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    _assert_export_safe(replay_result)
    root = Path(log_root)
    replay_filename = make_timestamped_filename("replay_run", ".json")
    approval_filename = make_timestamped_filename("approval_decisions", ".jsonl")
    audit_filename = make_timestamped_filename("audit_events", ".jsonl")
    replay_path = root / "replay_runs" / replay_filename
    approval_path = root / "approval_decisions" / approval_filename
    audit_path = root / "audit_events" / audit_filename

    approval_records = list(replay_result.get("approval_actions", []))
    if not approval_records:
        approval_records = [
            {
                "approval_id": item.get("approval_id"),
                "source_event_id": item.get("source_event_id"),
                "status": item.get("status"),
                "human_only_execution": item.get("human_only_execution"),
                "external_execution_allowed": item.get("external_execution_allowed"),
                "decision_by": item.get("decision_by"),
                "decision_note": item.get("decision_note"),
            }
            for item in replay_result.get("approval_queue", [])
        ]

    audit_records = list(replay_result.get("audit_trail", []))
    summary = replay_result.get("summary", {})
    export_summary = {
        "exported": not dry_run,
        "dry_run": dry_run,
        "log_root": str(root),
        "replay_run_path": str(replay_path),
        "approval_decisions_path": str(approval_path),
        "audit_events_path": str(audit_path),
        "records": {
            "approval_decisions": len(approval_records),
            "audit_events": len(audit_records),
        },
        "redaction_applied": True,
        "external_execution_count": summary.get("external_execution_count", 0),
        "human_only_execution_preserved": all(
            item.get("human_only_execution") is True
            for item in replay_result.get("approval_queue", [])
            if item.get("status") == "approved"
        ),
    }
    if dry_run:
        return export_summary

    ensure_log_dirs(root)
    replay_payload = dict(replay_result)
    replay_payload["export_summary"] = export_summary
    write_json(replay_path, replay_payload, overwrite=False)
    for record in approval_records:
        append_jsonl(approval_path, record)
    for record in audit_records:
        append_jsonl(audit_path, record)
    return redact_sensitive_values(export_summary)

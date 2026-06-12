"""Local CLI for the fresh STOXL Hermes Gateway skeleton."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from audit_log import build_audit_payload
from config import load_config
from discord_event_adapter import event_from_text, normalize_event
from dispatcher import build_dispatch_plan
from evaluator_bridge import evaluate_request
from registry_loader import load_registry
from replay import run_replay


def load_event_file(path: str) -> dict[str, Any]:
    event_path = Path(path)
    if not event_path.is_absolute():
        event_path = Path.cwd() / event_path
    return json.loads(event_path.read_text(encoding="utf-8"))


def run_pipeline(event: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config(Path(__file__).resolve())
    registry = load_registry(cfg)
    normalized = normalize_event(event)
    evaluator_result = evaluate_request(registry, normalized, cfg)
    dispatch_plan = build_dispatch_plan(normalized, evaluator_result)
    audit_payload = build_audit_payload(event.get("event_type", "manual_cli_event"), normalized, evaluator_result, dispatch_plan)
    return {
        "normalized_request": normalized,
        "evaluator_result": evaluator_result,
        "dispatch_plan": dispatch_plan,
        "audit_log_payload": audit_payload,
    }


def print_human(output: dict[str, Any]) -> None:
    plan = output["dispatch_plan"]
    result = output["evaluator_result"]
    print("STOXL local dry-run result")
    print(f"- dispatch_to_agent: {plan.get('dispatch_to_agent')}")
    print(f"- reviewer_agent: {plan.get('reviewer_agent')}")
    print(f"- dispatch_channel: {plan.get('dispatch_channel')}")
    print(f"- approval_required: {plan.get('approval_required')}")
    print(f"- human_only_execution: {plan.get('human_only_execution')}")
    print(f"- blocked: {plan.get('blocked')}")
    if plan.get("block_reasons"):
        print("- block_reasons:")
        for reason in plan["block_reasons"]:
            print(f"  - {reason}")
    print(f"- next_action: {result.get('recommended_next_action')}")


def print_replay_human(output: dict[str, Any]) -> None:
    summary = output["summary"]
    print("STOXL local replay result")
    print(f"- events_processed: {output.get('events_processed')}")
    print(f"- blocked_count: {summary.get('blocked_count')}")
    print(f"- dispatch_count: {summary.get('dispatch_count')}")
    print(f"- approval_required_count: {summary.get('approval_required_count')}")
    print(f"- approved_count: {summary.get('approved_count')}")
    print(f"- rejected_count: {summary.get('rejected_count')}")
    print(f"- human_only_execution_count: {summary.get('human_only_execution_count')}")
    print(f"- external_execution_count: {summary.get('external_execution_count')}")
    if output.get("warnings"):
        print("- warnings:")
        for warning in output["warnings"]:
            print(f"  - {warning}")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run a local STOXL Hermes Gateway dry-run pipeline.")
    parser.add_argument("--text", help="Local request text.")
    parser.add_argument("--channel", default="대표-회의실", help="Source channel name for --text input.")
    parser.add_argument("--author-role", default="Decision Maker", help="Author role for --text input.")
    parser.add_argument("--event", help="Path to a local JSON event.")
    parser.add_argument("--replay", help="Path to a local replay events JSON file.")
    parser.add_argument("--approval-actions", help="Path to mock approval actions JSON for --replay.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    if args.replay:
        output = run_replay(args.replay, args.approval_actions)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print_replay_human(output)
        return 0

    if args.approval_actions:
        parser.error("--approval-actions can only be used with --replay.")
    if args.event:
        event = load_event_file(args.event)
    elif args.text:
        event = event_from_text(args.text, args.channel, args.author_role)
    else:
        parser.error("Provide --text, --event, or --replay.")

    output = run_pipeline(event)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_human(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

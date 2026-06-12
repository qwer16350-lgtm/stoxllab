#!/usr/bin/env python
"""Evaluate Discord-shaped mock events against the STOXL mock evaluator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evaluate_stoxl_mock_request import evaluate_one, find_root, load_registry


REGISTRY_PATH = "registry/stoxl_agent_registry.example.json"
ARCHIVE_CHANNELS = {"완료된-안건", "보류된-안건", "폐기된-안건"}
JUNIOR_AGENTS = {"marin", "kasumi"}
ROLE_TO_AGENT = {
    "Marketing Senior": "lucy",
    "Marketing Junior": "marin",
    "Operation Senior": "meiko",
    "Operation Junior": "kasumi",
    "Strategy Office": "reze",
}


def load_events(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("events", [])
    if isinstance(data, list):
        return data
    raise ValueError("Event file must contain a list or an object with events")


def channel_lookup(registry: dict[str, Any], channel_name: str | None) -> dict[str, Any] | None:
    if not channel_name:
        return None
    return registry.get("channels", {}).get(channel_name)


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    author_role = event.get("author_role")
    actor_agent = event.get("actor_agent")
    if event.get("author_is_agent") and not actor_agent:
        actor_agent = ROLE_TO_AGENT.get(author_role)
    requested_action = event.get("requested_action")
    requested_source = event.get("requested_source")
    text = event.get("message_text", "")
    lower = text.lower()
    if not requested_source:
        for source in ["brand", "marketing", "operation", "strategy", "shared"]:
            if source in lower:
                requested_source = source
                break
    return {
        "text": text,
        "actor_role": author_role,
        "actor_agent": actor_agent,
        "source_channel": event.get("channel_name"),
        "source_category": event.get("channel_category"),
        "mentioned_agents": event.get("mentioned_agents", []),
        "requested_action": requested_action,
        "requested_source": requested_source,
        "current_status": event.get("current_status"),
        "requested_next_status": event.get("requested_next_status"),
    }


def default_result(event: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id", ""),
        "input_event": event,
        "normalized_request": normalized,
        "channel_check": {},
        "author_check": {},
        "mention_check": {},
        "evaluator_result": {},
        "dispatch_plan": {},
        "blocked": False,
        "block_reasons": [],
        "recommended_next_action": "",
        "notes": [],
    }


def add_block(result: dict[str, Any], reason: str) -> None:
    result["blocked"] = True
    result["block_reasons"].append(reason)


def check_channel(registry: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    channel_name = event.get("channel_name")
    channel = channel_lookup(registry, channel_name)
    check = {
        "channel_name": channel_name,
        "exists": channel is not None,
        "category_matches": None,
        "blocked": False,
        "reason": "",
    }
    if not channel:
        check.update({"blocked": True, "reason": f"Unknown channel: {channel_name}"})
        return check
    provided_category = event.get("channel_category")
    actual_category = channel.get("category_name")
    check["actual_category"] = actual_category
    if provided_category:
        check["category_matches"] = provided_category == actual_category
        if not check["category_matches"]:
            check.update({"blocked": True, "reason": f"Channel category mismatch: {provided_category} != {actual_category}"})
    if channel_name in ARCHIVE_CHANNELS and (event.get("author_role") in {"Marketing Junior", "Operation Junior"} or event.get("author_is_agent")):
        text = event.get("message_text", "")
        if any(word in text for word in ["새", "신규", "시작", "작성", "찾아줘", "만들어줘"]):
            check.update({"blocked": True, "reason": "Junior/agent cannot start new work from archive channels"})
    if channel_name == "최종-승인요청" and any(agent in JUNIOR_AGENTS for agent in event.get("mentioned_agents", [])):
        check.update({"blocked": True, "reason": "Junior agents cannot be directly invoked in 최종-승인요청"})
    return check


def check_author(registry: dict[str, Any], event: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    role = event.get("author_role")
    actor_agent = normalized.get("actor_agent")
    known_roles = {"Decision Maker", "Marketing Senior", "Marketing Junior", "Operation Senior", "Operation Junior", "Strategy Office", "Agent", "Archive Viewer"}
    check = {
        "author_role": role,
        "author_is_agent": event.get("author_is_agent", False),
        "actor_agent": actor_agent,
        "known_role": role in known_roles,
        "blocked": False,
        "warnings": [],
        "reason": "",
    }
    if role not in known_roles:
        check["warnings"].append(f"Unknown role: {role}")
    if event.get("author_is_agent"):
        if actor_agent not in registry.get("agents", {}):
            check.update({"blocked": True, "reason": f"Unknown agent author: {actor_agent}"})
        elif normalized.get("requested_action") in {"sns_publish", "homepage_upload", "grant_submit", "competition_submit", "external_email_send"}:
            check.update({"blocked": True, "reason": "Agent author cannot initiate direct external execution"})
    return check


def check_mentions(registry: dict[str, Any], event: dict[str, Any], channel: dict[str, Any] | None) -> dict[str, Any]:
    mentioned = event.get("mentioned_agents", [])
    check = {"mentioned_agents": mentioned, "unknown_agents": [], "blocked": False, "reason": "", "notes": []}
    agents = registry.get("agents", {})
    for agent in mentioned:
        if agent not in agents:
            check["unknown_agents"].append(agent)
    if check["unknown_agents"]:
        check.update({"blocked": True, "reason": "Unknown mentioned agent(s): " + ", ".join(check["unknown_agents"])})
        return check
    channel_name = event.get("channel_name")
    if channel_name == "최종-승인요청" and any(agent in JUNIOR_AGENTS for agent in mentioned):
        check.update({"blocked": True, "reason": "Junior agent mention shortcut in 최종-승인요청 is forbidden"})
    if "reze" in mentioned and channel_name in {"marketing-brief", "operation-brief", "lucy-검토", "meiko-검토"}:
        check["notes"].append("Reze mention is allowed only as opinion_only; no direct order.")
    if channel:
        readable = set(channel.get("allowed_agents") or [])
        if channel.get("workflow_role") == "rag_summary":
            readable.update(registry.get("agents", {}).keys())
        for agent in mentioned:
            if readable and agent not in readable and agent != "reze":
                check["notes"].append(f"Review channel access for mentioned agent: {agent}")
    return check


def build_dispatch_plan(evaluator_result: dict[str, Any]) -> dict[str, Any]:
    route = evaluator_result.get("routing", {})
    handoff = evaluator_result.get("handoff", {})
    gate = evaluator_result.get("approval_gate", {})
    return {
        "should_dispatch": not evaluator_result.get("blocked", False),
        "dispatch_to_agent": route.get("primary_agent"),
        "reviewer_agent": route.get("reviewer_agent"),
        "dispatch_channel": handoff.get("target_channel") or route.get("source_channel_candidates", [None])[0],
        "final_report_channel": route.get("final_report_channel"),
        "approval_required": gate.get("approval_required", route.get("approval_required")),
        "human_only_execution": gate.get("human_only_execution", True if gate else False),
        "message_kind": evaluator_result.get("classification", {}).get("request_type"),
        "required_handoff": handoff.get("handoff_id"),
        "forbidden_shortcuts": route.get("forbidden_shortcuts", []),
    }


def evaluate_event(registry: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_event(event)
    result = default_result(event, normalized)
    channel = channel_lookup(registry, event.get("channel_name"))

    result["channel_check"] = check_channel(registry, event)
    result["author_check"] = check_author(registry, event, normalized)
    result["mention_check"] = check_mentions(registry, event, channel)
    for key in ["channel_check", "author_check", "mention_check"]:
        if result[key].get("blocked"):
            add_block(result, result[key].get("reason", f"{key} blocked"))

    evaluator_input = {
        "text": normalized.get("text", ""),
        "actor_agent": normalized.get("actor_agent"),
        "requested_action": normalized.get("requested_action"),
        "requested_source": normalized.get("requested_source"),
        "current_status": normalized.get("current_status"),
        "requested_next_status": normalized.get("requested_next_status"),
    }
    evaluator_result = evaluate_one(registry, evaluator_input)
    result["evaluator_result"] = evaluator_result
    if evaluator_result.get("blocked"):
        for reason in evaluator_result.get("block_reasons", []):
            add_block(result, reason)

    result["dispatch_plan"] = build_dispatch_plan(evaluator_result)
    if result["blocked"]:
        result["dispatch_plan"]["should_dispatch"] = False
    result["recommended_next_action"] = (
        "Do not dispatch; review block reasons."
        if result["blocked"]
        else evaluator_result.get("recommended_next_action", "Dispatch according to plan.")
    )
    return result


def load_events_from_cli(args: argparse.Namespace, root: Path) -> list[dict[str, Any]]:
    if args.event:
        path = Path(args.event)
        if not path.is_absolute():
            path = root / path
        return load_events(path)
    return [
        {
            "event_id": "cli_event",
            "guild_id": "TODO_DISCORD_GUILD_ID",
            "channel_name": args.channel,
            "channel_category": args.channel_category,
            "author_display_name": args.author_display_name,
            "author_role": args.author_role,
            "author_is_agent": args.author_is_agent,
            "mentioned_agents": args.mention or [],
            "message_text": args.text or "",
            "attachments": [],
            "timestamp": None,
            "expected_primary_agent": None,
            "expected_blocked": None,
            "notes": "CLI-generated mock event",
        }
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Discord-shaped mock events without Discord API calls.")
    parser.add_argument("--root", help="Repository root. Defaults to auto-detection.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. JSON is the default output format.")
    parser.add_argument("--text", help="Mock Discord message text.")
    parser.add_argument("--channel", default="marketing-brief", help="Mock Discord channel name.")
    parser.add_argument("--channel-category", help="Mock Discord channel category.")
    parser.add_argument("--author-display-name", default="김태호_STOXL", help="Mock author display name.")
    parser.add_argument("--author-role", default="Decision Maker", help="Mock author role.")
    parser.add_argument("--author-is-agent", action="store_true", help="Treat author as an agent.")
    parser.add_argument("--mention", action="append", help="Mentioned agent id. Can be repeated.")
    parser.add_argument("--event", help="Mock event JSON file.")
    parser.add_argument("--out", help="Write result JSON to this path. Relative paths resolve from repo root.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else find_root(Path.cwd())
    try:
        registry = load_registry(root)
        events = load_events_from_cli(args, root)
        results = [evaluate_event(registry, event) for event in events]
        output: Any = results[0] if not args.event and len(results) == 1 else {"meta": {"event_count": len(events)}, "results": results}
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote Discord mock results: {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Local CLI for the fresh STOXL Hermes Gateway skeleton."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from agent_response_interface import build_agent_response_interface_report
from approval_interaction_spec import build_approval_interaction_spec
from audit_log import build_audit_payload
from config import load_config
from connection_preflight import build_connection_preflight_report
from discord_readiness import build_readiness_report
from discord_adapter_stub import load_raw_events, run_discord_adapter_stub
from discord_replay import load_discord_raw_events, run_discord_raw_event_replay
from discord_event_adapter import event_from_text, normalize_event
from dispatcher import build_dispatch_plan
from evaluator_bridge import evaluate_request
from log_exporter import export_replay_result
from local_mapping_manager import build_local_mapping_manager_report, copy_template_to_local
from mapping_validator import build_mapping_validation_report
from persistence import get_default_log_root
from readonly_runtime_stub import build_readonly_runtime_stub_report
from live_capture_stub import build_live_capture_stub_report
from registry_loader import load_registry
from replay import run_replay
from reply_planner import build_reply_planner_report
from review_packet import build_review_packet, export_review_packet


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
    audit_payload = build_audit_payload(event.get("event_type", "manual_cli_event"), normalized, evaluator_result, dispatch_plan, event.get("event_id"))
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
    if output.get("review_packet"):
        print(f"- review_packet_items: {len(output['review_packet'].get('items', []))}")
    if output.get("review_packet_export"):
        print(f"- review_packet_export: {output['review_packet_export']}")
    if output.get("export_summary"):
        print(f"- export_summary: {output['export_summary']}")
    if output.get("warnings"):
        print("- warnings:")
        for warning in output["warnings"]:
            print(f"  - {warning}")


def build_safety_scaffold_report(root: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    reports = {
        "phase23_connection_preflight": build_connection_preflight_report(root_path),
        "phase24_readonly_runtime_stub": build_readonly_runtime_stub_report(root_path),
        "phase25_live_capture_stub": build_live_capture_stub_report(root_path),
        "phase26_reply_planner": build_reply_planner_report(root_path),
        "phase27_approval_interaction_spec": build_approval_interaction_spec(),
        "phase28_agent_response_interface": build_agent_response_interface_report(root_path),
    }
    return {
        "report_type": "phase23_28_safety_scaffold",
        "version": "consolidated_no_connection",
        "reports": reports,
        "safety_assertions": {
            "discord_api_called": False,
            "gateway_connected": False,
            "message_sent": False,
            "llm_called": False,
            "rag_called": False,
            "external_execution_enabled": False,
            "human_only_execution_preserved": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run a local STOXL Hermes Gateway dry-run pipeline.")
    parser.add_argument("--text", help="Local request text.")
    parser.add_argument("--channel", default="대표-회의실", help="Source channel name for --text input.")
    parser.add_argument("--author-role", default="Decision Maker", help="Author role for --text input.")
    parser.add_argument("--event", help="Path to a local JSON event.")
    parser.add_argument("--discord-readiness", action="store_true", help="Run Phase 17 read-only Discord readiness checks.")
    parser.add_argument("--discord-raw-event", help="Run Phase 18 local Discord raw event adapter stub.")
    parser.add_argument("--discord-replay", help="Run Phase 19 local Discord raw event replay.")
    parser.add_argument("--validate-mapping", help="Run Phase 20 local Discord runtime mapping validation.")
    parser.add_argument("--init-local-mapping", action="store_true", help="Copy runtime mapping template to local ignored mapping path.")
    parser.add_argument("--validate-local-mapping", action="store_true", help="Validate local ignored Discord runtime mapping.")
    parser.add_argument("--connection-preflight", action="store_true", help="Run Phase 23 local read-only Discord connection preflight.")
    parser.add_argument("--readonly-runtime-stub", action="store_true", help="Run Phase 24 no-Gateway readonly runtime stub report.")
    parser.add_argument("--live-capture-stub", action="store_true", help="Run Phase 25 audit-only live capture stub report.")
    parser.add_argument("--reply-planner-report", action="store_true", help="Run Phase 26 disabled reply planner report.")
    parser.add_argument("--approval-interaction-spec", action="store_true", help="Print Phase 27 approval interaction spec.")
    parser.add_argument("--agent-response-interface", action="store_true", help="Print Phase 28 agent response interface report.")
    parser.add_argument("--safety-scaffold-report", action="store_true", help="Print consolidated Phase 23-28 safety scaffold report.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting local mapping with --init-local-mapping.")
    parser.add_argument("--strict", action="store_true", help="Treat TODO placeholders as validation failures for --validate-mapping.")
    parser.add_argument("--mapping", help="Discord runtime mapping template for --discord-readiness.")
    parser.add_argument("--replay", help="Path to a local replay events JSON file.")
    parser.add_argument("--approval-actions", help="Path to mock approval actions JSON for --replay.")
    parser.add_argument("--export-log", action="store_true", help="Export replay results to local JSON/JSONL logs.")
    parser.add_argument("--log-root", help="Log root for --export-log. Defaults to logs/hermes_gateway.")
    parser.add_argument("--review-packet", action="store_true", help="Build an approval review packet from replay results.")
    parser.add_argument("--export-review-packet", action="store_true", help="Export review packet JSON and Markdown.")
    parser.add_argument("--review-export-root", help="Export root for review packets. Defaults to exports/hermes_gateway/review_packets.")
    parser.add_argument("--dry-run-export", action="store_true", help="Build export plan without writing files.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)

    if args.discord_readiness:
        cfg = load_config(Path(__file__).resolve())
        output = build_readiness_report(cfg.repo_root, args.mapping)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord readiness result")
            print(f"- overall_ready: {output.get('overall_ready')}")
            print(f"- missing_required_values: {len(output.get('missing_required_values', []))}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
            print(f"- discord_api_called: {output.get('safety_assertions', {}).get('discord_api_called')}")
            print(f"- gateway_connected: {output.get('safety_assertions', {}).get('gateway_connected')}")
        return 0

    if args.validate_mapping:
        cfg = load_config(Path(__file__).resolve())
        output = build_mapping_validation_report(args.validate_mapping, root=cfg.repo_root, strict=args.strict)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord mapping validation result")
            print(f"- overall_valid: {output.get('overall_valid')}")
            print(f"- ready_for_readonly_connection: {output.get('ready_for_readonly_connection')}")
            print(f"- missing_mappings: {len(output.get('missing_mappings', []))}")
            print(f"- manual_required: {len(output.get('manual_required', []))}")
            print(f"- warnings: {len(output.get('warnings', []))}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
            print(f"- secret_like_values: {output.get('summary', {}).get('secret_like_values')}")
        return 0

    if args.init_local_mapping:
        cfg = load_config(Path(__file__).resolve())
        output = copy_template_to_local(cfg.repo_root, force=args.force)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL local mapping init result")
            print(f"- local_mapping_exists: {output.get('local_mapping_exists')}")
            print(f"- created: {output.get('created')}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
        return 0

    if args.connection_preflight:
        cfg = load_config(Path(__file__).resolve())
        output = build_connection_preflight_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL read-only Discord connection preflight")
            print(f"- ready_for_phase24_readonly_connection: {output.get('ready_for_phase24_readonly_connection')}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
            print(f"- warnings: {len(output.get('warnings', []))}")
            print(f"- recommended_library: {output.get('dependency_plan', {}).get('recommended_library')}")
            print(f"- install_now: {output.get('dependency_plan', {}).get('install_now')}")
        return 0

    if args.readonly_runtime_stub:
        cfg = load_config(Path(__file__).resolve())
        output = build_readonly_runtime_stub_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL readonly runtime stub")
            print(f"- runtime_mode: {output.get('runtime_mode')}")
            print(f"- can_connect_gateway: {output.get('can_connect_gateway')}")
            print(f"- can_send_messages: {output.get('can_send_messages')}")
        return 0

    if args.live_capture_stub:
        cfg = load_config(Path(__file__).resolve())
        output = build_live_capture_stub_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL live capture audit-only stub")
            print(f"- capture_mode: {output.get('capture_mode')}")
            print(f"- live_event_received: {output.get('live_event_received')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.reply_planner_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_reply_planner_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL reply planner report")
            print(f"- default_reply_enabled: {output.get('default_reply_enabled')}")
            print(f"- public_channel_reply_allowed: {output.get('public_channel_reply_allowed')}")
        return 0

    if args.approval_interaction_spec:
        output = build_approval_interaction_spec()
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL approval interaction spec")
            print(f"- current_mode: {output.get('current_mode')}")
            print(f"- enabled_in_runtime: {output.get('enabled_in_runtime')}")
        return 0

    if args.agent_response_interface:
        cfg = load_config(Path(__file__).resolve())
        output = build_agent_response_interface_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent response interface")
            print(f"- llm_enabled: {output.get('llm_enabled')}")
            print(f"- rag_enabled: {output.get('rag_enabled')}")
        return 0

    if args.safety_scaffold_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_safety_scaffold_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 23-28 safety scaffold")
            print(f"- phases: {len(output.get('reports', {}))}")
            print(f"- discord_api_called: {output.get('safety_assertions', {}).get('discord_api_called')}")
        return 0

    if args.validate_local_mapping:
        cfg = load_config(Path(__file__).resolve())
        output = build_local_mapping_manager_report(cfg.repo_root, strict=args.strict)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL local mapping validation result")
            print(f"- local_mapping_exists: {output.get('local_mapping_exists')}")
            print(f"- validated: {output.get('validated')}")
            print(f"- ready_for_readonly_connection: {output.get('ready_for_readonly_connection')}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
        return 0

    if args.discord_raw_event:
        path = Path(args.discord_raw_event)
        if not path.is_absolute():
            path = Path.cwd() / path
        events = load_raw_events(path)
        cfg = load_config(Path(__file__).resolve())
        results = [run_discord_adapter_stub(event, root=cfg.repo_root) for event in events]
        output = {"adapter_type": "discord_adapter_stub_batch", "event_count": len(results), "results": results}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord adapter stub result")
            print(f"- event_count: {len(results)}")
            for index, result in enumerate(results, start=1):
                payload = result.get("would_send_payload", {})
                print(f"- {index}: {payload.get('message_kind')} -> {payload.get('target_channel')}")
        return 0

    if args.discord_replay:
        path = Path(args.discord_replay)
        if not path.is_absolute():
            path = Path.cwd() / path
        cfg = load_config(Path(__file__).resolve())
        events = load_discord_raw_events(path)
        approval_actions = None
        if args.approval_actions:
            actions_path = Path(args.approval_actions)
            if not actions_path.is_absolute():
                actions_path = Path.cwd() / actions_path
            actions_data = json.loads(actions_path.read_text(encoding="utf-8"))
            approval_actions = actions_data if isinstance(actions_data, list) else actions_data.get("actions", [])
        output = run_discord_raw_event_replay(
            events,
            root=cfg.repo_root,
            approval_actions=approval_actions,
            include_review_packet=args.review_packet or args.export_review_packet,
        )
        output["source_event_file"] = str(path)
        if args.export_log:
            log_root = Path(args.log_root) if args.log_root else get_default_log_root(cfg.repo_root)
            if not log_root.is_absolute():
                log_root = cfg.repo_root / log_root
            output["export_summary"] = export_replay_result(output, log_root, dry_run=args.dry_run_export)
        elif args.log_root:
            parser.error("--log-root can only be used with --export-log.")
        if args.export_review_packet:
            if not output.get("review_packet"):
                output["review_packet"] = build_review_packet(output)
            export_root = Path(args.review_export_root) if args.review_export_root else cfg.repo_root / "exports" / "hermes_gateway" / "review_packets"
            if not export_root.is_absolute():
                export_root = cfg.repo_root / export_root
            output["review_packet_export"] = export_review_packet(output["review_packet"], export_root, dry_run=args.dry_run_export)
        elif args.review_export_root:
            parser.error("--review-export-root can only be used with --export-review-packet.")
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print_replay_human(output)
        return 0

    if args.replay:
        output = run_replay(args.replay, args.approval_actions)
        cfg = load_config(Path(__file__).resolve())
        if args.export_log:
            log_root = Path(args.log_root) if args.log_root else get_default_log_root(cfg.repo_root)
            if not log_root.is_absolute():
                log_root = cfg.repo_root / log_root
            output["export_summary"] = export_replay_result(output, log_root, dry_run=args.dry_run_export)
        elif args.log_root:
            parser.error("--log-root can only be used with --export-log.")

        if args.review_packet or args.export_review_packet:
            packet = build_review_packet(output)
            output["review_packet"] = packet
            if args.export_review_packet:
                export_root = Path(args.review_export_root) if args.review_export_root else cfg.repo_root / "exports" / "hermes_gateway" / "review_packets"
                if not export_root.is_absolute():
                    export_root = cfg.repo_root / export_root
                output["review_packet_export"] = export_review_packet(packet, export_root, dry_run=args.dry_run_export)
        elif args.review_export_root:
            parser.error("--review-export-root can only be used with --export-review-packet.")

        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print_replay_human(output)
        return 0

    if (
        args.approval_actions
        or args.mapping
        or args.discord_raw_event
        or args.discord_replay
        or args.validate_mapping
        or args.init_local_mapping
        or args.validate_local_mapping
        or args.connection_preflight
        or args.readonly_runtime_stub
        or args.live_capture_stub
        or args.reply_planner_report
        or args.approval_interaction_spec
        or args.agent_response_interface
        or args.safety_scaffold_report
        or args.force
        or args.strict
        or args.export_log
        or args.log_root
        or args.review_packet
        or args.export_review_packet
        or args.review_export_root
        or args.dry_run_export
    ):
        parser.error("Replay/export/readiness options require the matching mode option.")
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

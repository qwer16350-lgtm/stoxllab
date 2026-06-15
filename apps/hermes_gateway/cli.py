"""Local CLI for the fresh STOXL Hermes Gateway skeleton."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from agent_response_interface import build_agent_response_interface_report
from agent_placeholder_response import (
    build_agent_placeholder_response,
    render_agent_placeholder_response_markdown,
)
from approval_interaction_spec import build_approval_interaction_spec
from audit_log import build_audit_payload
from config import load_config
from connection_preflight import build_connection_preflight_report
from discord_readiness import build_readiness_report
from discord_adapter_stub import load_raw_events, run_discord_adapter_stub
from discord_replay import load_discord_raw_events, run_discord_raw_event_replay
from discord_readonly_runtime import build_readonly_runtime_report, run_discord_private_test_llm_reply_bot, run_discord_private_test_reply_bot, run_readonly_discord_bot
from discord_safety_wrapper import build_send_block_report
from discord_token_loader import build_token_loader_report
from discord_event_adapter import event_from_text, normalize_event
from dispatcher import build_dispatch_plan
from evaluator_bridge import evaluate_request
from live_event_audit_persistence import (
    build_daily_live_event_manifest,
    build_live_event_audit_record,
    build_sample_visibility_event,
)
from live_event_pipeline import build_live_event_pipeline_report
from live_event_review_packet import build_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from knowledge_evidence_packet import build_knowledge_evidence_packet, render_knowledge_evidence_packet_markdown
from knowledge_dry_chain import build_knowledge_dry_chain_report, render_knowledge_dry_chain_markdown
from knowledge_ingestion_boundary import build_knowledge_ingestion_boundary_report, render_knowledge_ingestion_boundary_markdown
from knowledge_manifest import build_knowledge_manifest, render_knowledge_manifest_markdown
from knowledge_source_routing import build_knowledge_source_routing_report, render_knowledge_source_routing_markdown
from llm_preflight import build_llm_preflight_report, render_llm_preflight_markdown
from llm_dry_call import build_llm_dry_call_request, render_llm_dry_call_markdown, run_llm_dry_call, write_llm_dry_call_artifact
from llm_private_test_reply import build_llm_private_test_reply_preflight, render_llm_private_test_reply_report_markdown
from llm_private_test_reply_replay import build_llm_private_test_reply_replay_report, render_llm_private_test_reply_replay_markdown
from llm_prompt_envelope import build_llm_prompt_envelope, render_llm_prompt_envelope_preview
from llm_response_packet import (
    build_latest_llm_response_packet_report,
    build_llm_response_packet,
    build_llm_response_packet_live_closeout,
    render_llm_response_packet_live_closeout_markdown,
    render_llm_response_packet_markdown,
)
from llm_safety_policy import build_llm_safety_policy_report
from log_exporter import export_replay_result
from local_mapping_manager import build_local_mapping_manager_report, copy_template_to_local
from mapping_validator import build_mapping_validation_report
from operations_packet_viewer import (
    build_operations_packet_viewer_report,
    load_review_packet,
    render_operations_summary_markdown,
)
from private_test_reply import build_private_test_reply_report, render_private_test_reply_report_markdown
from private_test_reply_replay import build_private_test_reply_replay_report, render_private_test_reply_replay_markdown
from private_test_reply_safety import build_private_test_reply_safety_report, render_private_test_reply_safety_report_markdown
from rag_local_retrieval import render_rag_local_retrieval_markdown, run_rag_local_retrieval
from rag_preflight import build_rag_preflight_report, render_rag_preflight_markdown
from rag_response_packet import build_rag_response_packet_report, render_rag_response_packet_markdown
from rag_evidence_integration import build_rag_evidence_integration_report, render_rag_evidence_integration_markdown
from rag_evidence_llm_dry_call_closeout import build_rag_evidence_llm_dry_call_closeout, render_rag_evidence_llm_dry_call_closeout_markdown
from rag_evidence_llm_dry_call import build_rag_evidence_llm_dry_call_report, render_rag_evidence_llm_dry_call_markdown
from rag_evidence_llm_dry_readiness import build_rag_evidence_llm_dry_readiness_report, render_rag_evidence_llm_dry_readiness_markdown
from rag_evidence_private_test_send import build_rag_evidence_private_test_send_report, render_rag_evidence_private_test_send_markdown
from rag_evidence_private_test_send_closeout import build_rag_evidence_private_test_send_closeout, render_rag_evidence_private_test_send_closeout_markdown
from rag_evidence_private_test_e2e_preflight import build_rag_evidence_private_test_e2e_preflight, render_rag_evidence_private_test_e2e_preflight_markdown
from rag_evidence_private_test_e2e_replay import build_rag_evidence_private_test_e2e_replay, render_rag_evidence_private_test_e2e_replay_markdown
from rag_evidence_private_test_e2e_live_reply import build_rag_evidence_private_test_e2e_live_reply_report, render_rag_evidence_private_test_e2e_live_reply_markdown
from rag_evidence_private_test_e2e_send_retry import build_rag_evidence_private_test_e2e_send_retry_report, render_rag_evidence_private_test_e2e_send_retry_markdown
from rag_evidence_private_test_e2e_live_closeout import build_rag_evidence_private_test_e2e_live_closeout, render_rag_evidence_private_test_e2e_live_closeout_markdown
from rag_evidence_private_test_phase34_final_lock import build_rag_evidence_private_test_phase34_final_lock, render_rag_evidence_private_test_phase34_final_lock_markdown
from phase35a_post_mvp_safety_audit import build_phase35a_post_mvp_safety_audit, render_phase35a_post_mvp_safety_audit_markdown
from local_knowledge_ingestion_preview import build_local_knowledge_ingestion_preview, render_local_knowledge_ingestion_preview_markdown
from evidence_quality_preview import build_evidence_quality_preview, render_evidence_quality_preview_markdown
from agent_routing_dry_preview import build_agent_routing_dry_preview, render_agent_routing_dry_preview_markdown
from agent_evidence_pack_composer import build_agent_evidence_pack_composer, render_agent_evidence_pack_composer_markdown
from agent_prompt_preview import build_agent_prompt_preview, render_agent_prompt_preview_markdown
from agent_review_packet import build_agent_review_packet, render_agent_review_packet_markdown
from manual_approval_packet_preview import build_manual_approval_packet_preview, render_manual_approval_packet_preview_markdown
from operator_manual_checklist import build_operator_manual_checklist, render_operator_manual_checklist_markdown
from no_live_rehearsal_packet import build_no_live_rehearsal_packet, render_no_live_rehearsal_packet_markdown
from operations_dashboard_lock import build_operations_dashboard_lock, render_operations_dashboard_lock_markdown
from forbidden_behavior_sentinel import build_forbidden_behavior_sentinel, render_forbidden_behavior_sentinel_markdown
from phase36_entry_gate import build_phase36_entry_gate, render_phase36_entry_gate_markdown
from private_test_one_shot_llm_draft_preflight import build_private_test_one_shot_llm_draft_preflight, render_private_test_one_shot_llm_draft_preflight_markdown
from private_test_one_shot_llm_draft_mock_packet import build_private_test_one_shot_llm_draft_mock_packet, render_private_test_one_shot_llm_draft_mock_packet_markdown
from one_shot_llm_draft_output_safety_rehearsal import build_one_shot_llm_draft_output_safety_rehearsal, render_one_shot_llm_draft_output_safety_rehearsal_markdown
from actual_one_shot_llm_draft_call_preflight import build_actual_one_shot_llm_draft_call_preflight, render_actual_one_shot_llm_draft_call_preflight_markdown
from actual_one_shot_llm_draft_call import build_actual_one_shot_llm_draft_call, render_actual_one_shot_llm_draft_call_markdown
from actual_one_shot_llm_draft_call_closeout import build_actual_one_shot_llm_draft_call_closeout, render_actual_one_shot_llm_draft_call_closeout_markdown
from one_shot_llm_no_send_final_lock import build_one_shot_llm_no_send_final_lock, render_one_shot_llm_no_send_final_lock_markdown
from post_llm_call_dashboard_lock import build_post_llm_call_dashboard_lock, render_post_llm_call_dashboard_lock_markdown
from phase37_entry_gate import build_phase37_entry_gate, render_phase37_entry_gate_markdown
from private_test_llm_draft_review_packet import build_private_test_llm_draft_review_packet, render_private_test_llm_draft_review_packet_markdown
from private_test_discord_send_preflight_preview import build_private_test_discord_send_preflight_preview, render_private_test_discord_send_preflight_preview_markdown
from private_test_send_approval_rehearsal import build_private_test_send_approval_rehearsal, render_private_test_send_approval_rehearsal_markdown
from actual_private_test_send_manual_preflight import build_actual_private_test_send_manual_preflight, render_actual_private_test_send_manual_preflight_markdown
from mock_private_test_send_rehearsal import build_mock_private_test_send_rehearsal, render_mock_private_test_send_rehearsal_markdown
from private_test_send_no_send_lock import build_private_test_send_no_send_lock, render_private_test_send_no_send_lock_markdown
from actual_private_test_send_contract import build_actual_private_test_send_contract, render_actual_private_test_send_contract_markdown
from final_would_send_payload_freeze import build_final_would_send_payload_freeze, render_final_would_send_payload_freeze_markdown
from private_test_send_rollback_gate import build_private_test_send_rollback_gate, render_private_test_send_rollback_gate_markdown
from private_test_send_operator_checklist import build_private_test_send_operator_checklist, render_private_test_send_operator_checklist_markdown
from private_test_live_send_entry_gate import build_private_test_live_send_entry_gate, render_private_test_live_send_entry_gate_markdown
from actual_private_test_one_shot_send import build_actual_private_test_one_shot_send, render_actual_private_test_one_shot_send_markdown
from actual_private_test_send_safety_gate import build_actual_private_test_send_safety_gate, render_actual_private_test_send_safety_gate_markdown
from actual_private_test_send_blocked_report import build_actual_private_test_send_blocked_report, render_actual_private_test_send_blocked_report_markdown
from phase39b_manual_send_reentry_packet import build_phase39b_manual_send_reentry_packet, render_phase39b_manual_send_reentry_packet_markdown
from phase39b_manual_send_no_send_lock import build_phase39b_manual_send_no_send_lock, render_phase39b_manual_send_no_send_lock_markdown
from rag_evidence_private_test_send_preflight import build_rag_evidence_private_test_send_preflight, render_rag_evidence_private_test_send_preflight_markdown
from rag_evidence_prompt_envelope import build_rag_evidence_prompt_envelope, render_rag_evidence_prompt_envelope_markdown
from rag_evidence_review_packet import build_rag_evidence_review_packet, render_rag_evidence_review_packet_markdown
from rag_evidence_would_send_preview import build_rag_evidence_would_send_preview, render_rag_evidence_would_send_preview_markdown
from rag_llm_private_test_reply import build_rag_llm_private_test_reply_preflight, render_rag_llm_private_test_reply_markdown
from rag_llm_prompt_envelope import build_rag_llm_prompt_envelope, render_rag_llm_prompt_envelope_markdown
from rag_llm_would_send_preview import build_rag_llm_would_send_preview, render_rag_llm_would_send_preview_markdown
from rag_llm_private_test_reply_replay import build_rag_llm_private_test_reply_replay_report, render_rag_llm_private_test_reply_replay_markdown
from rag_llm_live_readiness_review import build_rag_llm_live_readiness_review, render_rag_llm_live_readiness_markdown
from rag_llm_live_preflight_closeout import build_rag_llm_live_preflight_closeout, render_rag_llm_live_preflight_closeout_markdown
from rag_llm_live_success_closeout import build_rag_llm_live_success_closeout, render_rag_llm_live_success_closeout_markdown
from rag_llm_private_test_runtime import (
    build_rag_llm_private_test_runtime_report,
    render_rag_llm_private_test_runtime_markdown,
    run_discord_private_test_rag_llm_reply_bot,
)
from persistence import get_default_log_root
from readonly_runtime_stub import build_readonly_runtime_stub_report
from live_capture_stub import build_live_capture_stub_report
from registry_loader import load_registry
from replay import run_replay
from reply_planner import build_reply_planner_report
from review_packet import build_review_packet, export_review_packet
from would_send_preview import build_would_send_preview


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


def build_phase30_sample_bundle(root: str | Path | None = None) -> dict[str, Any]:
    visibility = build_sample_visibility_event()
    audit_record = build_live_event_audit_record(visibility, content="Sample live message content for Phase 30 audit preview.")
    routing_report = build_live_event_routing_report(audit_record)
    placeholder = build_agent_placeholder_response(audit_record, routing_report)
    preview = build_would_send_preview(audit_record, routing_report, placeholder)
    packet = build_live_event_review_packet(audit_record, routing_report, preview, placeholder)
    manifest = build_daily_live_event_manifest(root=root, date=audit_record["created_at"]) if root else {
        "manifest_type": "live_event_daily_manifest",
        "version": "phase30_audit_persistence",
        "date": audit_record["created_at"][:10].replace("-", ""),
        "record_count": 0,
        "message_sent": False,
        "external_execution": False,
        "llm_called": False,
        "rag_called": False,
    }
    return {
        "audit_record": audit_record,
        "routing_report": routing_report,
        "would_send_preview": preview,
        "review_packet": packet,
        "agent_placeholder_response": placeholder,
        "daily_manifest": manifest,
        "safety_assertions": {
            "discord_api_write_called": False,
            "message_sent": False,
            "external_execution": False,
            "llm_called": False,
            "rag_called": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run a local STOXL Hermes Gateway dry-run pipeline.")
    parser.add_argument("--text", help="Local request text.")
    parser.add_argument("--channel", help="Source channel name for --text input, or channel filter for operations viewer.")
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
    parser.add_argument("--discord-token-report", action="store_true", help="Print Phase 29 Discord token presence report without token values.")
    parser.add_argument("--send-block-report", action="store_true", help="Print Phase 29 outbound action blocking report.")
    parser.add_argument("--live-event-pipeline-report", action="store_true", help="Print Phase 29 audit-only live event pipeline report.")
    parser.add_argument("--discord-readonly-runtime-report", action="store_true", help="Print Phase 29 read-only runtime report.")
    parser.add_argument("--run-discord-readonly", action="store_true", help="Run the Phase 29 read-only Discord Gateway runtime.")
    parser.add_argument("--run-discord-private-test-reply", action="store_true", help="Run the Phase 31B private-test-only Discord reply runtime.")
    parser.add_argument("--run-discord-private-test-llm-reply", action="store_true", help="Run the Phase 32D guarded private-test-only LLM reply runtime.")
    parser.add_argument("--run-discord-private-test-rag-llm-reply", action="store_true", help="Run the Phase 33D-1 guarded private-test-only RAG+LLM reply runtime after separate manual approval.")
    parser.add_argument("--live-event-audit-report", action="store_true", help="Print Phase 30 live event audit record report.")
    parser.add_argument("--would-send-preview-report", action="store_true", help="Print Phase 30 would-send preview report.")
    parser.add_argument("--live-event-review-packet-report", action="store_true", help="Print Phase 30 live event review packet report.")
    parser.add_argument("--phase30-audit-ops-report", action="store_true", help="Print Phase 30 audit operations bundle report.")
    parser.add_argument("--operations-viewer", action="store_true", help="Print Phase 31A operations packet viewer report.")
    parser.add_argument("--operations-packet", action="store_true", help="Print Phase 31A operations packet detail.")
    parser.add_argument("--agent-placeholder-response-report", action="store_true", help="Print Phase 31C deterministic agent placeholder response report.")
    parser.add_argument("--private-test-reply-report", action="store_true", help="Print Phase 31B private test channel reply report.")
    parser.add_argument("--private-test-reply-safety-report", action="store_true", help="Print Phase 31D private test reply safety closeout report.")
    parser.add_argument("--private-test-reply-replay-report", action="store_true", help="Print Phase 31E private test reply replay closeout report.")
    parser.add_argument("--llm-preflight-report", action="store_true", help="Print Phase 32A local-only LLM safety preflight report.")
    parser.add_argument("--llm-safety-policy-report", action="store_true", help="Print Phase 32A local-only LLM safety policy report.")
    parser.add_argument("--llm-prompt-envelope-report", action="store_true", help="Print Phase 32A local-only LLM prompt envelope preview.")
    parser.add_argument("--llm-dry-call-report", action="store_true", help="Print Phase 32B private-test-only LLM dry call report.")
    parser.add_argument("--llm-response-packet-report", action="store_true", help="Print Phase 32C local LLM response packet report.")
    parser.add_argument("--llm-response-packet-live-closeout", action="store_true", help="Print Phase 32C-LIVE closeout from latest LLM dry call artifact.")
    parser.add_argument("--llm-private-test-reply-report", action="store_true", help="Print Phase 32D guarded private-test-only LLM reply preflight.")
    parser.add_argument("--llm-private-test-reply-replay-report", action="store_true", help="Print Phase 32D closeout replay/audit report without live send.")
    parser.add_argument("--rag-preflight-report", action="store_true", help="Print Phase 33A RAG preflight without retrieval.")
    parser.add_argument("--rag-local-retrieval-report", action="store_true", help="Print Phase 33B local read-only RAG retrieval report.")
    parser.add_argument("--rag-response-packet-report", action="store_true", help="Print Phase 33C RAG response packet without LLM or Discord send.")
    parser.add_argument("--rag-llm-private-test-reply-report", action="store_true", help="Print Phase 33D-safe RAG+LLM private test reply preflight.")
    parser.add_argument("--rag-llm-prompt-envelope-report", action="store_true", help="Print Phase 33D-safe RAG+LLM prompt envelope preview.")
    parser.add_argument("--rag-llm-would-send-preview", action="store_true", help="Print Phase 33D-safe RAG+LLM would-send preview.")
    parser.add_argument("--rag-llm-private-test-replay-report", action="store_true", help="Print Phase 33D-safe RAG+LLM private test replay/audit report.")
    parser.add_argument("--rag-llm-live-readiness-review", action="store_true", help="Print Phase 33D live readiness review without live execution.")
    parser.add_argument("--rag-llm-private-test-runtime-report", action="store_true", help="Print Phase 33D-1 guarded RAG+LLM private test runtime preflight report.")
    parser.add_argument("--rag-llm-live-preflight-closeout", action="store_true", help="Print Phase 33D-2 live preflight closeout without live execution.")
    parser.add_argument("--rag-llm-live-success-closeout", action="store_true", help="Print Phase 33D-4 single live success replay/audit closeout without live execution.")
    parser.add_argument("--knowledge-manifest", action="store_true", help="Print Phase 34A local knowledge manifest without content dumps.")
    parser.add_argument("--knowledge-ingestion-boundary", action="store_true", help="Print Phase 34A local text-only knowledge ingestion boundary.")
    parser.add_argument("--knowledge-source-routing", action="store_true", help="Print Phase 34B agent knowledge source routing policy.")
    parser.add_argument("--knowledge-evidence-packet", action="store_true", help="Print Phase 34C local citation/evidence packet without LLM or Discord send.")
    parser.add_argument("--rag-evidence-integration", action="store_true", help="Print Phase 34D local evidence-to-RAG response packet integration report.")
    parser.add_argument("--rag-evidence-review-packet", action="store_true", help="Print Phase 34E private-test review packet for local evidence output.")
    parser.add_argument("--knowledge-dry-chain", action="store_true", help="Print Phase 34F local sample knowledge dry chain report.")
    parser.add_argument("--rag-evidence-prompt-envelope", action="store_true", help="Print Phase 34G RAG evidence prompt envelope preview without API calls.")
    parser.add_argument("--rag-evidence-llm-dry-readiness", action="store_true", help="Print Phase 34H-0 no-API/mock-only LLM dry-call readiness report.")
    parser.add_argument("--rag-evidence-llm-dry-call-report", action="store_true", help="Print Phase 34H-1 manually approved RAG evidence LLM dry-call report.")
    parser.add_argument("--rag-evidence-llm-dry-call-closeout", action="store_true", help="Print Phase 34H-2 closeout from embedded sanitized RAG evidence LLM dry-call fixture.")
    parser.add_argument("--rag-evidence-would-send-preview", action="store_true", help="Print Phase 34I private-test would-send preview without Discord API.")
    parser.add_argument("--rag-evidence-private-test-send-preflight", action="store_true", help="Print Phase 34J-0 private-test send preflight without Discord API.")
    parser.add_argument("--rag-evidence-private-test-send", action="store_true", help="Run/report Phase 34J-1 one private-test Discord send gate.")
    parser.add_argument("--rag-evidence-private-test-send-closeout", action="store_true", help="Print Phase 34J-2 send closeout from embedded sanitized fixture.")
    parser.add_argument("--rag-evidence-private-test-e2e-preflight", action="store_true", help="Print Phase 34K private-test E2E preflight without live runtime.")
    parser.add_argument("--rag-evidence-private-test-e2e-replay", action="store_true", help="Print Phase 34L-0 no-live/no-api/no-send E2E replay.")
    parser.add_argument("--rag-evidence-private-test-e2e-live-reply", action="store_true", help="Run/report Phase 34L-1 one manually approved private-test E2E live reply.")
    parser.add_argument("--rag-evidence-private-test-e2e-send-retry", action="store_true", help="Print Phase 34L-1E no-LLM private-test E2E send retry report.")
    parser.add_argument("--rag-evidence-private-test-e2e-live-closeout", action="store_true", help="Print Phase 34L-2 E2E live reply and no-LLM send retry closeout.")
    parser.add_argument("--rag-evidence-private-test-phase34-final-lock", action="store_true", help="Print Phase 34M private-test E2E MVP final lock report.")
    parser.add_argument("--phase35a-post-mvp-safety-audit", action="store_true", help="Print Phase 35A post-MVP safety audit report.")
    parser.add_argument("--local-knowledge-ingestion-preview", action="store_true", help="Print Phase 35B local knowledge ingestion preview.")
    parser.add_argument("--evidence-quality-preview", action="store_true", help="Print Phase 35B evidence quality dry preview.")
    parser.add_argument("--agent-routing-dry-preview", action="store_true", help="Print Phase 35B agent routing dry preview.")
    parser.add_argument("--agent-evidence-pack-composer", action="store_true", help="Print Phase 35C agent evidence pack composer report.")
    parser.add_argument("--agent-prompt-preview", action="store_true", help="Print Phase 35C agent prompt preview report.")
    parser.add_argument("--agent-review-packet", action="store_true", help="Print Phase 35D agent review packet report.")
    parser.add_argument("--manual-approval-packet-preview", action="store_true", help="Print Phase 35D manual approval packet preview.")
    parser.add_argument("--operator-manual-checklist", action="store_true", help="Print Phase 35E operator manual checklist.")
    parser.add_argument("--no-live-rehearsal-packet", action="store_true", help="Print Phase 35E no-live rehearsal packet.")
    parser.add_argument("--operations-dashboard-lock", action="store_true", help="Print Phase 35F operations dashboard lock.")
    parser.add_argument("--forbidden-behavior-sentinel", action="store_true", help="Print Phase 35G forbidden behavior sentinel.")
    parser.add_argument("--phase36-entry-gate", action="store_true", help="Print Phase 36 entry gate preview.")
    parser.add_argument("--private-test-one-shot-llm-draft-preflight", action="store_true", help="Print Phase 36A private-test one-shot LLM draft preflight without API calls.")
    parser.add_argument("--private-test-one-shot-llm-draft-mock-packet", action="store_true", help="Print Phase 36B one-shot LLM draft mock packet without API calls.")
    parser.add_argument("--one-shot-llm-draft-output-safety-rehearsal", action="store_true", help="Print Phase 36B one-shot LLM draft output safety rehearsal.")
    parser.add_argument("--actual-one-shot-llm-draft-call-preflight", action="store_true", help="Print Phase 36C actual one-shot LLM draft call preflight without API calls.")
    parser.add_argument("--actual-one-shot-llm-draft-call", action="store_true", help="Print/run Phase 36D manually gated one-shot LLM draft call report.")
    parser.add_argument("--actual-one-shot-llm-draft-call-closeout", action="store_true", help="Print Phase 36E one-shot LLM draft call no-send closeout report.")
    parser.add_argument("--one-shot-llm-no-send-final-lock", action="store_true", help="Print Phase 36F one-shot LLM no-send final lock.")
    parser.add_argument("--post-llm-call-dashboard-lock", action="store_true", help="Print Phase 36G post-LLM-call dashboard lock.")
    parser.add_argument("--phase37-entry-gate", action="store_true", help="Print Phase 37 entry gate report.")
    parser.add_argument("--private-test-llm-draft-review-packet", action="store_true", help="Print Phase 37A private-test LLM draft review packet.")
    parser.add_argument("--private-test-discord-send-preflight-preview", action="store_true", help="Print Phase 37B private-test Discord send preflight preview.")
    parser.add_argument("--private-test-send-approval-rehearsal", action="store_true", help="Print Phase 37C private-test send approval rehearsal.")
    parser.add_argument("--actual-private-test-send-manual-preflight", action="store_true", help="Print Phase 37D actual private-test send manual preflight.")
    parser.add_argument("--mock-private-test-send-rehearsal", action="store_true", help="Print Phase 37E mock private-test send rehearsal.")
    parser.add_argument("--private-test-send-no-send-lock", action="store_true", help="Print Phase 37F private-test send no-send lock.")
    parser.add_argument("--actual-private-test-send-contract", action="store_true", help="Print Phase 38A actual private-test send contract.")
    parser.add_argument("--final-would-send-payload-freeze", action="store_true", help="Print Phase 38B final would-send payload freeze.")
    parser.add_argument("--private-test-send-rollback-gate", action="store_true", help="Print Phase 38C private-test send rollback gate.")
    parser.add_argument("--private-test-send-operator-checklist", action="store_true", help="Print Phase 38D private-test send operator checklist.")
    parser.add_argument("--private-test-live-send-entry-gate", action="store_true", help="Print Phase 38E private-test live send entry gate.")
    parser.add_argument("--actual-private-test-one-shot-send", action="store_true", help="Print Phase 39A actual private-test one-shot send path blocked report.")
    parser.add_argument("--actual-private-test-send-safety-gate", action="store_true", help="Print Phase 39A actual private-test send safety gate.")
    parser.add_argument("--actual-private-test-send-blocked-report", action="store_true", help="Print Phase 39A actual private-test send blocked report.")
    parser.add_argument("--allow-actual-private-test-send", action="store_true", help="Mark the Phase 39 actual private-test send allow flag as present; Phase 39A still does not send.")
    parser.add_argument("--execute-actual-private-test-send", action="store_true", help="Mark the Phase 39B actual private-test send execution flag as present; Hotfix 3 still uses no-send mock gate.")
    parser.add_argument("--phase39b-manual-send-reentry-packet", action="store_true", help="Print Phase 39B-0 manual send re-entry packet.")
    parser.add_argument("--phase39b-manual-send-no-send-lock", action="store_true", help="Print Phase 39B-0 no-send lock.")
    parser.add_argument("--source", default="operation", help="RAG source for local retrieval reports.")
    parser.add_argument("--query", default="STOXL brand tone", help="RAG query preview for local retrieval reports.")
    parser.add_argument("--allow-llm-api-call", action="store_true", help="Allow Phase 32B to attempt one gated provider call when env gates pass.")
    parser.add_argument("--allow-rag-evidence-llm-api-call", action="store_true", help="Allow Phase 34H-1 to attempt one manually approved provider call when env gates pass.")
    parser.add_argument("--allow-rag-evidence-private-test-discord-send", action="store_true", help="Allow Phase 34J-1 to send one private-test Discord message when env gates pass.")
    parser.add_argument("--allow-rag-evidence-private-test-e2e-live-reply", action="store_true", help="Allow Phase 34L-1 to run one private-test E2E live reply when env gates pass.")
    parser.add_argument("--allow-rag-evidence-private-test-e2e-send-retry", action="store_true", help="Allow Phase 34L-1E mock/injected no-LLM E2E send retry when gates pass.")
    parser.add_argument("--allow-actual-one-shot-llm-draft-call", action="store_true", help="Allow Phase 36D to attempt one manually approved OpenRouter call when gates pass.")
    parser.add_argument("--write-artifact", action="store_true", help="Write supported local-only report artifacts.")
    parser.add_argument("--latest", action="store_true", help="Use latest local artifact for supported reports.")
    parser.add_argument("--markdown", action="store_true", help="Print supported reports as Markdown.")
    parser.add_argument("--limit", type=int, default=20, help="Limit rows for viewer reports.")
    parser.add_argument("--date", help="Date filter in YYYYMMDD or YYYY-MM-DD format.")
    parser.add_argument("--workflow-role", help="Workflow role filter for operations viewer.")
    parser.add_argument("--agent", help="Agent route filter for operations viewer.")
    parser.add_argument("--decision", help="Decision filter for operations viewer.")
    parser.add_argument("--event-id", help="Event id for operations packet detail.")
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

    if args.discord_token_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_token_loader_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord token report")
            print(f"- token_present: {output.get('token_present')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.send_block_report:
        output = build_send_block_report()
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord send block report")
            print(f"- default_allowed: {output.get('default_allowed')}")
            print(f"- blocked_actions: {len(output.get('blocked_actions', []))}")
        return 0

    if args.live_event_pipeline_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_live_event_pipeline_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL live event pipeline report")
            print(f"- pipeline_mode: {output.get('pipeline_mode')}")
            print(f"- message_sent: {output.get('safety_assertions', {}).get('message_sent')}")
        return 0

    if args.discord_readonly_runtime_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_readonly_runtime_report(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord read-only runtime report")
            print(f"- runtime_mode: {output.get('runtime_mode')}")
            print(f"- can_connect_gateway: {output.get('can_connect_gateway')}")
            print(f"- can_send_messages: {output.get('can_send_messages')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.run_discord_readonly:
        cfg = load_config(Path(__file__).resolve())
        output = run_readonly_discord_bot(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord read-only runtime")
            print(f"- started: {output.get('started')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.run_discord_private_test_reply:
        cfg = load_config(Path(__file__).resolve())
        output = run_discord_private_test_reply_bot(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord private test reply runtime")
            print(f"- started: {output.get('started')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- reason: {output.get('reason', '')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.run_discord_private_test_llm_reply:
        cfg = load_config(Path(__file__).resolve())
        output = run_discord_private_test_llm_reply_bot(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord private test LLM reply runtime")
            print(f"- started: {output.get('started')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- reason: {output.get('reason', '')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.run_discord_private_test_rag_llm_reply:
        cfg = load_config(Path(__file__).resolve())
        output = run_discord_private_test_rag_llm_reply_bot(cfg.repo_root)
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Discord private test RAG+LLM reply runtime")
            print(f"- started: {output.get('started')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- reason: {output.get('reason', '')}")
            print(f"- token_value_logged: {output.get('token_value_logged')}")
        return 0

    if args.live_event_audit_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_phase30_sample_bundle(cfg.repo_root)["audit_record"]
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL live event audit record")
            print(f"- decision: {output.get('decision')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.would_send_preview_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_phase30_sample_bundle(cfg.repo_root)["would_send_preview"]
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL would-send preview")
            print(f"- would_send_kind: {output.get('would_send_kind')}")
            print(f"- will_send: {output.get('will_send')}")
        return 0

    if args.live_event_review_packet_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_phase30_sample_bundle(cfg.repo_root)["review_packet"]
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL live event review packet")
            print(f"- required: {output.get('human_review', {}).get('required')}")
            print(f"- message_sent: {output.get('safety_assertions', {}).get('message_sent')}")
        return 0

    if args.phase30_audit_ops_report:
        cfg = load_config(Path(__file__).resolve())
        output = {
            "report_type": "phase30_audit_operations",
            "version": "phase30_local_only",
            "bundle": build_phase30_sample_bundle(cfg.repo_root),
            "flow": ["visibility_event", "audit_record", "routing_report", "would_send_preview", "review_packet", "daily_manifest"],
            "safety_assertions": {
                "discord_api_write_called": False,
                "message_sent": False,
                "external_execution": False,
                "llm_called": False,
                "rag_called": False,
            },
        }
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 30 audit operations")
            print("- message_sent: false")
            print("- llm_called: false")
            print("- rag_called: false")
        return 0

    if args.operations_viewer:
        cfg = load_config(Path(__file__).resolve())
        output = build_operations_packet_viewer_report(
            cfg.repo_root,
            limit=args.limit,
            date=args.date,
            channel_name=args.channel,
            workflow_role=args.workflow_role,
            agent_route_candidate=args.agent,
            decision=args.decision,
        )
        if args.markdown:
            print(render_operations_summary_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL operations packet viewer")
            print(f"- recent_live_events: {len(output.get('recent_live_events', []))}")
            print(f"- recent_review_packets: {len(output.get('recent_review_packets', []))}")
            print(f"- message_sent: {output.get('safety_assertions', {}).get('message_sent')}")
        return 0

    if args.operations_packet:
        cfg = load_config(Path(__file__).resolve())
        output = load_review_packet(cfg.repo_root, event_id=args.event_id)
        if args.markdown:
            if output:
                from live_event_review_packet import render_live_event_review_packet_markdown

                print(render_live_event_review_packet_markdown(output))
            else:
                print("# Live Event Review Packet\n\nNo packet found.\n")
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL operations packet detail")
            print(f"- found: {bool(output)}")
            print(f"- event_id: {output.get('event_id', '') if output else ''}")
        return 0

    if args.agent_placeholder_response_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_phase30_sample_bundle(cfg.repo_root)["agent_placeholder_response"]
        if args.markdown:
            print(render_agent_placeholder_response_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent placeholder response")
            print(f"- agent: {output.get('agent_route_candidate')}")
            print(f"- will_send: {output.get('will_send')}")
            print(f"- llm_enabled: {output.get('llm_enabled')}")
        return 0

    if args.private_test_reply_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_private_test_reply_report(cfg.repo_root)
        if args.markdown:
            print(render_private_test_reply_report_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private test reply report")
            print(f"- allowed_example: {output.get('allowed_example', {}).get('allowed')}")
            print(f"- blocked_example: {output.get('blocked_example', {}).get('blocked')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.private_test_reply_safety_report:
        output = build_private_test_reply_safety_report()
        if args.markdown:
            print(render_private_test_reply_safety_report_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private test reply safety report")
            print(f"- cooldown_seconds: {output.get('policy', {}).get('cooldown_seconds')}")
            print(f"- max_replies_per_session: {output.get('policy', {}).get('max_replies_per_session')}")
            print(f"- circuit_breaker_open: {output.get('state', {}).get('circuit_breaker_open')}")
        return 0

    if args.private_test_reply_replay_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_private_test_reply_replay_report(cfg.repo_root)
        if args.markdown:
            print(render_private_test_reply_replay_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private test reply replay report")
            print(f"- events_replayed: {output.get('events_replayed')}")
            print(f"- historical_sent: {output.get('summary', {}).get('sent')}")
            print(f"- blocked: {output.get('summary', {}).get('blocked')}")
        return 0

    if args.llm_preflight_report:
        output = build_llm_preflight_report()
        if args.markdown:
            print(render_llm_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM safety preflight")
            print(f"- llm_enabled: {output.get('llm_enabled')}")
            print(f"- provider: {output.get('provider')}")
            print(f"- ready_for_llm_call: {output.get('ready_for_llm_call')}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
        return 0

    if args.llm_safety_policy_report:
        output = build_llm_safety_policy_report()
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            policy = output.get("policy", {})
            print("STOXL LLM safety policy")
            print(f"- private_test_only: {policy.get('private_test_only')}")
            print(f"- allow_discord_send: {policy.get('allow_discord_send')}")
            print(f"- blocked_output_intents: {len(policy.get('blocked_output_intents', []))}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
        return 0

    if args.llm_prompt_envelope_report:
        output = build_llm_prompt_envelope("marin", "Phase 32A private test LLM prompt envelope preview.")
        if args.markdown:
            print(render_llm_prompt_envelope_preview(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM prompt envelope preview")
            print(f"- agent_route_candidate: {output.get('agent_route_candidate')}")
            print(f"- channel_scope: {output.get('channel_scope')}")
            print(f"- llm_api_called: {output.get('safety_assertions', {}).get('llm_api_called')}")
        return 0

    if args.llm_dry_call_report:
        cfg = load_config(Path(__file__).resolve())
        request = build_llm_dry_call_request(agent_route_candidate=args.agent or "marin", user_content_preview=args.text)
        output = run_llm_dry_call(request, allow_api_call=args.allow_llm_api_call)
        if args.write_artifact:
            artifact = write_llm_dry_call_artifact(output, root=cfg.repo_root)
            output["artifact_paths"] = artifact.get("artifact_paths", [])
        if args.markdown:
            print(render_llm_dry_call_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            result = output.get("client_result", {})
            print("STOXL LLM dry call report")
            print(f"- api_call_attempted: {result.get('api_call_attempted')}")
            print(f"- api_call_succeeded: {result.get('api_call_succeeded')}")
            print(f"- output_allowed: {output.get('output_safety', {}).get('allowed')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.llm_response_packet_report:
        cfg = load_config(Path(__file__).resolve())
        if args.latest:
            output = build_latest_llm_response_packet_report(cfg.repo_root, write_artifact=True)
            packet = output.get("packet", {}) if isinstance(output.get("packet"), dict) else {}
        else:
            dry_request = build_llm_dry_call_request(agent_route_candidate=args.agent or "marin", user_content_preview=args.text)
            dry_report = run_llm_dry_call(dry_request, allow_api_call=False)
            packet = build_llm_response_packet(dry_report)
            output = packet
        if args.markdown:
            print(render_llm_response_packet_markdown(packet) if packet else "# LLM Response Packet\n\nNo latest packet source found.\n")
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM response packet")
            print(f"- provider: {packet.get('provider')}")
            print(f"- model: {packet.get('model')}")
            print(f"- output_safety_allowed: {packet.get('output_safety', {}).get('allowed')}")
            print(f"- message_sent: {packet.get('message_sent', False)}")
        return 0

    if args.llm_response_packet_live_closeout:
        cfg = load_config(Path(__file__).resolve())
        output = build_llm_response_packet_live_closeout(cfg.repo_root)
        if args.markdown:
            print(render_llm_response_packet_live_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM response packet live closeout")
            print(f"- latest_dry_call_found: {output.get('latest_dry_call_found')}")
            print(f"- llm_response_packet_created: {output.get('llm_response_packet_created')}")
            print(f"- output_safety_allowed: {output.get('output_safety_allowed')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.llm_private_test_reply_report:
        output = build_llm_private_test_reply_preflight()
        if args.markdown:
            print(render_llm_private_test_reply_report_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM private test reply preflight")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- blocked_reasons: {len(output.get('blocked_reasons', []))}")
        return 0

    if args.llm_private_test_reply_replay_report:
        output = build_llm_private_test_reply_replay_report()
        if args.markdown:
            print(render_llm_private_test_reply_replay_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL LLM private test reply replay closeout")
            print(f"- live_success_fixture_verified: {output.get('live_success_fixture_verified')}")
            print(f"- events_replayed: {output.get('summary', {}).get('events_replayed')}")
            print(f"- sent_in_fixture: {output.get('summary', {}).get('sent')}")
            print(f"- message_sent: {output.get('message_sent')}")
        return 0

    if args.rag_preflight_report:
        output = build_rag_preflight_report()
        if args.markdown:
            print(render_rag_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG preflight")
            print(f"- ready_for_rag_retrieval: {output.get('ready_for_rag_retrieval')}")
            print(f"- ready_for_phase33b_local_readonly_retrieval: {output.get('ready_for_phase33b_local_readonly_retrieval')}")
        return 0

    if args.rag_local_retrieval_report:
        cfg = load_config(Path(__file__).resolve())
        output = run_rag_local_retrieval(cfg.repo_root, source=args.source, query=args.query)
        if args.markdown:
            print(render_rag_local_retrieval_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG local retrieval")
            print(f"- source: {output.get('source')}")
            print(f"- documents_returned: {output.get('documents_returned')}")
            print(f"- embedding_api_called: {output.get('embedding_api_called')}")
        return 0

    if args.rag_response_packet_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_response_packet_report(cfg.repo_root, source=args.source, query=args.query)
        if args.markdown:
            print(render_rag_response_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG response packet")
            print(f"- source: {output.get('source')}")
            print(f"- response_available: {output.get('response_available')}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
        return 0

    if args.rag_llm_private_test_reply_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_private_test_reply_preflight(root=str(cfg.repo_root), source=args.source, query=args.query)
        if args.markdown:
            print(render_rag_llm_private_test_reply_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM private test reply preflight")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- live_implementation: {output.get('ready_for_phase33d_live_implementation')}")
        return 0

    if args.rag_llm_prompt_envelope_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_prompt_envelope(root=str(cfg.repo_root), source=args.source, query=args.query, agent_route_candidate=args.agent or "marin")
        if args.markdown:
            print(render_rag_llm_prompt_envelope_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM prompt envelope")
            print(f"- source: {output.get('source')}")
            print(f"- context_safety_allowed: {output.get('context_safety_allowed')}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
        return 0

    if args.rag_llm_would_send_preview:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_would_send_preview(root=str(cfg.repo_root), source=args.source, query=args.query)
        if args.markdown:
            print(render_rag_llm_would_send_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM would-send preview")
            print(f"- will_send: {output.get('will_send')}")
            print(f"- message_sent: {output.get('message_sent')}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
        return 0

    if args.rag_llm_private_test_replay_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_private_test_reply_replay_report(root=str(cfg.repo_root))
        if args.markdown:
            print(render_rag_llm_private_test_reply_replay_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM private test replay")
            print(f"- events_replayed: {output.get('events_replayed')}")
            print(f"- actual_message_sent: {output.get('actual_message_sent')}")
            print(f"- ready_for_phase33d_live_review: {output.get('ready_for_phase33d_live_review')}")
        return 0

    if args.rag_llm_live_readiness_review:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_live_readiness_review(root=str(cfg.repo_root))
        if args.markdown:
            print(render_rag_llm_live_readiness_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM live readiness review")
            print(f"- go: {output.get('go')}")
            print(f"- ready_for_manual_phase33d_implementation_request: {output.get('ready_for_manual_phase33d_implementation_request')}")
            print(f"- actual_discord_send: {output.get('actual_discord_send')}")
        return 0

    if args.rag_llm_private_test_runtime_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_private_test_runtime_report(root=str(cfg.repo_root))
        if args.markdown:
            print(render_rag_llm_private_test_runtime_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM private test runtime report")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- runtime_executed_by_report: {output.get('runtime_executed_by_report')}")
        return 0

    if args.rag_llm_live_preflight_closeout:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_llm_live_preflight_closeout(root=str(cfg.repo_root))
        if args.markdown:
            print(render_rag_llm_live_preflight_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM live preflight closeout")
            print(f"- default_preflight_blocked: {output.get('default_preflight_blocked')}")
            print(f"- mock_live_ready_fixture_passed: {output.get('mock_live_ready_fixture_passed')}")
            print(f"- runtime_executed: {output.get('runtime_executed')}")
            print(f"- ready_for_single_live_private_test: {output.get('ready_for_single_live_private_test')}")
        return 0

    if args.rag_llm_live_success_closeout:
        output = build_rag_llm_live_success_closeout()
        if args.markdown:
            print(render_rag_llm_live_success_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG+LLM single live test closeout")
            print(f"- closeout_passed: {output.get('closeout_passed')}")
            print(f"- sent_exactly_once: {output.get('sent_exactly_once')}")
            print(f"- self_loop_prevented: {output.get('safety_assertions', {}).get('self_loop_prevented')}")
            print(f"- ready_for_phase34_knowledge_ingestion: {output.get('ready_for_phase34_knowledge_ingestion')}")
        return 0

    if args.knowledge_manifest:
        cfg = load_config(Path(__file__).resolve())
        output = build_knowledge_manifest(root=cfg.repo_root)
        if args.markdown:
            print(render_knowledge_manifest_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL knowledge manifest")
            print(f"- ready_for_local_text_ingestion: {output.get('ready_for_local_text_ingestion')}")
            print(f"- operations_source_present: {output.get('operations_source_present')}")
            print(f"- full_content_included: {output.get('full_content_included')}")
        return 0

    if args.knowledge_ingestion_boundary:
        cfg = load_config(Path(__file__).resolve())
        output = build_knowledge_ingestion_boundary_report(root=cfg.repo_root)
        if args.markdown:
            print(render_knowledge_ingestion_boundary_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL knowledge ingestion boundary")
            print(f"- ready_for_local_text_ingestion: {output.get('ready_for_local_text_ingestion')}")
            print(f"- ready_for_embedding: {output.get('ready_for_embedding')}")
            print(f"- ready_for_external_sources: {output.get('ready_for_external_sources')}")
        return 0

    if args.knowledge_source_routing:
        output = build_knowledge_source_routing_report()
        if args.markdown:
            print(render_knowledge_source_routing_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL knowledge source routing")
            print(f"- review_only: {output.get('review_only')}")
            print(f"- agents: {len(output.get('agent_source_policy', {}))}")
            print(f"- forbidden_sources: {', '.join(output.get('forbidden_sources', []))}")
        return 0

    if args.knowledge_evidence_packet:
        cfg = load_config(Path(__file__).resolve())
        output = build_knowledge_evidence_packet(root=cfg.repo_root, source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_knowledge_evidence_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL knowledge evidence packet")
            print(f"- source: {output.get('source')}")
            print(f"- agent: {output.get('agent')}")
            print(f"- ready_for_rag_response_packet: {output.get('ready_for_rag_response_packet')}")
            print(f"- ready_for_llm_prompt: {output.get('ready_for_llm_prompt')}")
        return 0

    if args.rag_evidence_integration:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_integration_report(root=cfg.repo_root, source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_rag_evidence_integration_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence integration")
            print(f"- source: {output.get('source')}")
            print(f"- agent: {output.get('agent')}")
            print(f"- rag_response_packet_created: {output.get('rag_response_packet_created')}")
            print(f"- ready_for_private_test_review: {output.get('ready_for_private_test_review')}")
        return 0

    if args.rag_evidence_review_packet:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_review_packet(root=str(cfg.repo_root), source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_rag_evidence_review_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence review packet")
            print(f"- source: {output.get('source')}")
            print(f"- agent: {output.get('agent')}")
            print(f"- human_review_required: {output.get('human_review_required')}")
            print(f"- ready_for_private_test_review: {output.get('ready_for_private_test_review')}")
        return 0

    if args.knowledge_dry_chain:
        cfg = load_config(Path(__file__).resolve())
        output = build_knowledge_dry_chain_report(root=cfg.repo_root, source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_knowledge_dry_chain_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL knowledge dry chain")
            print(f"- sample_files_present: {output.get('sample_files_present')}")
            print(f"- citation_count: {output.get('citation_count')}")
            print(f"- ready_for_private_test_review: {output.get('ready_for_private_test_review')}")
        return 0

    if args.rag_evidence_prompt_envelope:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_prompt_envelope(root=cfg.repo_root, source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_rag_evidence_prompt_envelope_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence prompt envelope")
            print(f"- ready_for_prompt_preview: {output.get('ready_for_prompt_preview')}")
            print(f"- ready_for_llm_api_call: {output.get('ready_for_llm_api_call')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.rag_evidence_llm_dry_readiness:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_llm_dry_readiness_report(root=cfg.repo_root, source=args.source, agent=args.agent or "kasumi", query=args.query)
        if args.markdown:
            print(render_rag_evidence_llm_dry_readiness_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence LLM dry readiness")
            print(f"- ready_for_actual_llm_dry_call: {output.get('ready_for_actual_llm_dry_call')}")
            print(f"- actual_llm_api_call: {output.get('actual_llm_api_call')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.rag_evidence_llm_dry_call_report:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_llm_dry_call_report(
            root=cfg.repo_root,
            source=args.source,
            agent=args.agent or "kasumi",
            query=args.query,
            allow_api_call=args.allow_rag_evidence_llm_api_call,
        )
        if args.markdown:
            print(render_rag_evidence_llm_dry_call_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence LLM dry call")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- actual_llm_api_call: {output.get('actual_llm_api_call')}")
            print(f"- api_call_attempted: {output.get('api_call_attempted')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.rag_evidence_llm_dry_call_closeout:
        output = build_rag_evidence_llm_dry_call_closeout()
        if args.markdown:
            print(render_rag_evidence_llm_dry_call_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence LLM dry call closeout")
            print(f"- actual_dry_call_observed: {output.get('actual_dry_call_observed')}")
            print(f"- api_call_succeeded_count: {output.get('api_call_succeeded_count')}")
            print(f"- output_safety_allowed: {output.get('output_safety_allowed')}")
            print(f"- closeout_passed: {output.get('closeout_passed')}")
            print(f"- ready_for_phase34i_private_test_would_send_preview: {output.get('ready_for_phase34i_private_test_would_send_preview')}")
        return 0

    if args.rag_evidence_would_send_preview:
        output = build_rag_evidence_would_send_preview()
        if args.markdown:
            print(render_rag_evidence_would_send_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence would-send preview")
            print(f"- would_send_preview_created: {output.get('would_send_preview_created')}")
            print(f"- private_test_channel_only: {output.get('private_test_channel_only')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- ready_for_actual_discord_send: {output.get('ready_for_actual_discord_send')}")
        return 0

    if args.rag_evidence_private_test_send_preflight:
        output = build_rag_evidence_private_test_send_preflight()
        if args.markdown:
            print(render_rag_evidence_private_test_send_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test send preflight")
            print(f"- would_send_preview_available: {output.get('would_send_preview_available')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
            print(f"- ready_for_phase34j1_manual_live_send: {output.get('ready_for_phase34j1_manual_live_send')}")
        return 0

    if args.rag_evidence_private_test_send:
        output = build_rag_evidence_private_test_send_report(allow_send=args.allow_rag_evidence_private_test_discord_send)
        if args.markdown:
            print(render_rag_evidence_private_test_send_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test send")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- message_sent_count: {output.get('message_sent_count')}")
        return 0

    if args.rag_evidence_private_test_send_closeout:
        output = build_rag_evidence_private_test_send_closeout()
        if args.markdown:
            print(render_rag_evidence_private_test_send_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test send closeout")
            print(f"- closeout_passed: {output.get('closeout_passed')}")
            print(f"- discord_message_sent_count: {output.get('discord_message_sent_count')}")
        return 0

    if args.rag_evidence_private_test_e2e_preflight:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_private_test_e2e_preflight(root=cfg.repo_root)
        if args.markdown:
            print(render_rag_evidence_private_test_e2e_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test E2E preflight")
            print(f"- ready_for_phase34l1_manual_e2e_live_reply: {output.get('ready_for_phase34l1_manual_e2e_live_reply')}")
            print(f"- ready_for_unattended_auto_reply: {output.get('ready_for_unattended_auto_reply')}")
        return 0

    if args.rag_evidence_private_test_e2e_replay:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_private_test_e2e_replay(root=cfg.repo_root)
        if args.markdown:
            print(render_rag_evidence_private_test_e2e_replay_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test E2E replay")
            print(f"- e2e_replay_passed: {output.get('e2e_replay_passed')}")
            print(f"- ready_for_phase34l1_manual_e2e_live_reply: {output.get('ready_for_phase34l1_manual_e2e_live_reply')}")
        return 0

    if args.rag_evidence_private_test_e2e_live_reply:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_private_test_e2e_live_reply_report(
            root=cfg.repo_root,
            allow_live_reply=args.allow_rag_evidence_private_test_e2e_live_reply,
        )
        if args.markdown:
            print(render_rag_evidence_private_test_e2e_live_reply_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test E2E live reply")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- discord_live_runtime_executed: {output.get('discord_live_runtime_executed')}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- ready_for_phase34l2_e2e_live_reply_closeout: {output.get('ready_for_phase34l2_e2e_live_reply_closeout')}")
        return 0

    if args.rag_evidence_private_test_e2e_send_retry:
        output = build_rag_evidence_private_test_e2e_send_retry_report(
            allow_send_retry=args.allow_rag_evidence_private_test_e2e_send_retry,
        )
        if args.markdown:
            print(render_rag_evidence_private_test_e2e_send_retry_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test E2E send retry")
            print(f"- partial_success_available: {output.get('partial_success_available')}")
            print(f"- llm_api_called: {output.get('llm_api_called')}")
            print(f"- ready_for_actual_send_retry: {output.get('ready_for_actual_send_retry')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- ready_for_phase34l2_e2e_live_reply_closeout: {output.get('ready_for_phase34l2_e2e_live_reply_closeout')}")
        return 0

    if args.rag_evidence_private_test_e2e_live_closeout:
        output = build_rag_evidence_private_test_e2e_live_closeout()
        if args.markdown:
            print(render_rag_evidence_private_test_e2e_live_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test E2E live closeout")
            print(f"- closeout_passed: {output.get('closeout_passed')}")
            print(f"- llm_api_call_count: {output.get('llm_api_call_count')}")
            print(f"- send_retry_llm_call_count: {output.get('no_llm_send_retry', {}).get('llm_api_call_count')}")
            print(f"- final_discord_message_sent_count: {output.get('final_result', {}).get('message_sent_count')}")
            print(f"- ready_for_phase34m_final_lock: {output.get('final_result', {}).get('ready_for_phase34m_final_lock')}")
        return 0

    if args.rag_evidence_private_test_phase34_final_lock:
        cfg = load_config(Path(__file__).resolve())
        output = build_rag_evidence_private_test_phase34_final_lock(root=str(cfg.repo_root))
        if args.markdown:
            print(render_rag_evidence_private_test_phase34_final_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL RAG evidence private-test Phase 34 final lock")
            print(f"- phase34_private_test_mvp_complete: {output.get('phase34_private_test_mvp_complete')}")
            print(f"- phase34m_final_lock_passed: {output.get('phase34m_final_lock_passed')}")
            print(f"- llm_api_call_count: {output.get('e2e_live_reply_closeout', {}).get('llm_api_call_count')}")
            print(f"- send_retry_llm_call_count: {output.get('no_llm_send_retry_closeout', {}).get('llm_api_call_count')}")
            print(f"- final_discord_message_sent_count: {output.get('no_llm_send_retry_closeout', {}).get('message_sent_count')}")
        return 0

    if args.phase35a_post_mvp_safety_audit:
        cfg = load_config(Path(__file__).resolve())
        output = build_phase35a_post_mvp_safety_audit(root=str(cfg.repo_root))
        if args.markdown:
            print(render_phase35a_post_mvp_safety_audit_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            counts = output.get("final_e2e_counts", {})
            print("STOXL Phase 35A post-MVP safety audit")
            print(f"- phase35a_audit_passed: {output.get('phase35a_audit_passed')}")
            print(f"- phase34_private_test_mvp_complete: {output.get('phase34_private_test_mvp_complete')}")
            print(f"- total_llm_call_count: {counts.get('total_llm_call_count')}")
            print(f"- send_retry_llm_call_count: {counts.get('send_retry_llm_call_count')}")
            print(f"- final_discord_message_sent_count: {counts.get('final_discord_message_sent_count')}")
        return 0

    if args.local_knowledge_ingestion_preview:
        output = build_local_knowledge_ingestion_preview(source=args.source)
        if args.markdown:
            print(render_local_knowledge_ingestion_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL local knowledge ingestion preview")
            print(f"- ready_for_local_text_ingestion: {output.get('ready_for_local_text_ingestion')}")
            print(f"- ready_for_embedding: {output.get('ready_for_embedding')}")
        return 0

    if args.evidence_quality_preview:
        output = build_evidence_quality_preview()
        if args.markdown:
            print(render_evidence_quality_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL evidence quality preview")
            print(f"- citation_sufficiency_checked: {output.get('citation_sufficiency_checked')}")
            print(f"- full_content_included: {output.get('full_content_included')}")
        return 0

    if args.agent_routing_dry_preview:
        output = build_agent_routing_dry_preview()
        if args.markdown:
            print(render_agent_routing_dry_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent routing dry preview")
            print(f"- routing_rule_only: {output.get('routing_rule_only')}")
            print(f"- llm_called: {output.get('llm_called')}")
        return 0

    if args.agent_evidence_pack_composer:
        output = build_agent_evidence_pack_composer()
        if args.markdown:
            print(render_agent_evidence_pack_composer_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent evidence pack composer")
            print(f"- rule_only: {output.get('rule_only')}")
            print(f"- ready_for_llm_call: {output.get('ready_for_llm_call')}")
        return 0

    if args.agent_prompt_preview:
        output = build_agent_prompt_preview()
        if args.markdown:
            print(render_agent_prompt_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent prompt preview")
            print(f"- rule_only: {output.get('rule_only')}")
            print(f"- ready_for_llm_call: {output.get('ready_for_llm_call')}")
        return 0

    if args.agent_review_packet:
        output = build_agent_review_packet()
        if args.markdown:
            print(render_agent_review_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL agent review packet")
            print(f"- rule_only: {output.get('rule_only')}")
            print(f"- human_review_required: {output.get('human_review_required')}")
            print(f"- ready_for_llm_call: {output.get('ready_for_llm_call')}")
        return 0

    if args.manual_approval_packet_preview:
        output = build_manual_approval_packet_preview()
        if args.markdown:
            print(render_manual_approval_packet_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL manual approval packet preview")
            print(f"- rule_only: {output.get('rule_only')}")
            print(f"- approval_phrase_generated: {output.get('approval_phrase_generated')}")
            print(f"- ready_for_actual_approval: {output.get('ready_for_actual_approval')}")
        return 0

    if args.operator_manual_checklist:
        output = build_operator_manual_checklist()
        if args.markdown:
            print(render_operator_manual_checklist_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL operator manual checklist")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- ready_for_live_runtime: {output.get('ready_for_live_runtime')}")
        return 0

    if args.no_live_rehearsal_packet:
        output = build_no_live_rehearsal_packet()
        if args.markdown:
            print(render_no_live_rehearsal_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL no-live rehearsal packet")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- live_runtime_executed: {output.get('live_runtime_executed')}")
        return 0

    if args.operations_dashboard_lock:
        output = build_operations_dashboard_lock()
        if args.markdown:
            print(render_operations_dashboard_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL operations dashboard lock")
            print(f"- dashboard_lock_available: {output.get('dashboard_lock_available')}")
            print(f"- ready_for_live_runtime: {output.get('ready_for_live_runtime')}")
        return 0

    if args.forbidden_behavior_sentinel:
        output = build_forbidden_behavior_sentinel()
        if args.markdown:
            print(render_forbidden_behavior_sentinel_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL forbidden behavior sentinel")
            print(f"- sentinel_passed: {output.get('forbidden_behavior_sentinel_passed')}")
        return 0

    if args.phase36_entry_gate:
        output = build_phase36_entry_gate()
        if args.markdown:
            print(render_phase36_entry_gate_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 36 entry gate")
            print(f"- phase36_not_started: {output.get('phase36_not_started')}")
            print(f"- ready_for_phase36_live_execution: {output.get('ready_for_phase36_live_execution')}")
        return 0

    if args.private_test_one_shot_llm_draft_preflight:
        output = build_private_test_one_shot_llm_draft_preflight()
        if args.markdown:
            print(render_private_test_one_shot_llm_draft_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test one-shot LLM draft preflight")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- candidate_agents: {', '.join(output.get('candidate_agents', [])) or 'none'}")
            print(f"- ready_for_actual_llm_call: {output.get('ready_for_actual_llm_call')}")
        return 0

    if args.private_test_one_shot_llm_draft_mock_packet:
        output = build_private_test_one_shot_llm_draft_mock_packet()
        if args.markdown:
            print(render_private_test_one_shot_llm_draft_mock_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test one-shot LLM draft mock packet")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- mock_candidate_agents: {', '.join(output.get('mock_candidate_agents', [])) or 'none'}")
            print(f"- ready_for_actual_llm_call: {output.get('ready_for_actual_llm_call')}")
        return 0

    if args.one_shot_llm_draft_output_safety_rehearsal:
        output = build_one_shot_llm_draft_output_safety_rehearsal()
        if args.markdown:
            print(render_one_shot_llm_draft_output_safety_rehearsal_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL one-shot LLM draft output safety rehearsal")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- output_safety_allowed_agents: {', '.join(output.get('output_safety_allowed_agents', [])) or 'none'}")
            print(f"- ready_for_phase36c_actual_llm_call_preflight: {output.get('ready_for_phase36c_actual_llm_call_preflight')}")
        return 0

    if args.actual_one_shot_llm_draft_call_preflight:
        output = build_actual_one_shot_llm_draft_call_preflight()
        if args.markdown:
            print(render_actual_one_shot_llm_draft_call_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual one-shot LLM draft call preflight")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- candidate_agent: {output.get('candidate_agent')}")
            print(f"- preflight_ready_for_manual_llm_call: {output.get('preflight_ready_for_manual_llm_call')}")
            print(f"- ready_for_actual_llm_call: {output.get('ready_for_actual_llm_call')}")
        return 0

    if args.actual_one_shot_llm_draft_call:
        output = build_actual_one_shot_llm_draft_call(
            allow_actual_call=args.allow_actual_one_shot_llm_draft_call,
        )
        if args.markdown:
            print(render_actual_one_shot_llm_draft_call_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual one-shot LLM draft call")
            print(f"- ready: {output.get('ready')}")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- llm_api_call_attempted: {output.get('llm_api_call_attempted')}")
            print(f"- llm_api_call_count: {output.get('llm_api_call_count')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
        return 0

    if args.actual_one_shot_llm_draft_call_closeout:
        output = build_actual_one_shot_llm_draft_call_closeout()
        if args.markdown:
            print(render_actual_one_shot_llm_draft_call_closeout_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual one-shot LLM draft call closeout")
            print(f"- phase36e_closeout_passed: {output.get('phase36e_closeout_passed')}")
            print(f"- llm_api_called_count: {output.get('llm_api_called_count')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.one_shot_llm_no_send_final_lock:
        output = build_one_shot_llm_no_send_final_lock()
        if args.markdown:
            print(render_one_shot_llm_no_send_final_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL one-shot LLM no-send final lock")
            print(f"- llm_call_count_locked: {output.get('llm_call_count_locked')}")
            print(f"- discord_send_count_locked: {output.get('discord_send_count_locked')}")
            print(f"- phase36f_no_send_final_lock_passed: {output.get('phase36f_no_send_final_lock_passed')}")
        return 0

    if args.post_llm_call_dashboard_lock:
        output = build_post_llm_call_dashboard_lock()
        if args.markdown:
            print(render_post_llm_call_dashboard_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL post-LLM-call dashboard lock")
            print(f"- total_phase36_llm_call_count: {output.get('total_phase36_llm_call_count')}")
            print(f"- total_phase36_discord_message_sent_count: {output.get('total_phase36_discord_message_sent_count')}")
            print(f"- ready_for_phase37_entry_gate: {output.get('ready_for_phase37_entry_gate')}")
        return 0

    if args.phase37_entry_gate:
        output = build_phase37_entry_gate()
        if args.markdown:
            print(render_phase37_entry_gate_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 37 entry gate")
            print(f"- phase37_not_started: {output.get('phase37_not_started')}")
            print(f"- requires_explicit_user_approval: {output.get('requires_explicit_user_approval')}")
            print(f"- ready_for_phase37_live_execution: {output.get('ready_for_phase37_live_execution')}")
        return 0

    if args.private_test_llm_draft_review_packet:
        output = build_private_test_llm_draft_review_packet()
        if args.markdown:
            print(render_private_test_llm_draft_review_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test LLM draft review packet")
            print(f"- draft_review_packet_created: {output.get('draft_review_packet_created')}")
            print(f"- human_review_required: {output.get('human_review_required')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.private_test_discord_send_preflight_preview:
        output = build_private_test_discord_send_preflight_preview()
        if args.markdown:
            print(render_private_test_discord_send_preflight_preview_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test Discord send preflight preview")
            print(f"- private_test_scope_only: {output.get('private_test_scope_only')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
        return 0

    if args.private_test_send_approval_rehearsal:
        output = build_private_test_send_approval_rehearsal()
        if args.markdown:
            print(render_private_test_send_approval_rehearsal_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test send approval rehearsal")
            print(f"- approval_phrase_generated: {output.get('approval_phrase_generated')}")
            print(f"- manual_approval_actualized: {output.get('manual_approval_actualized')}")
            print(f"- ready_for_phase37d_actual_private_test_send: {output.get('ready_for_phase37d_actual_private_test_send')}")
        return 0

    if args.actual_private_test_send_manual_preflight:
        output = build_actual_private_test_send_manual_preflight()
        if args.markdown:
            print(render_actual_private_test_send_manual_preflight_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual private-test send manual preflight")
            print(f"- manual_approval_required: {output.get('manual_approval_required')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
        return 0

    if args.mock_private_test_send_rehearsal:
        output = build_mock_private_test_send_rehearsal()
        if args.markdown:
            print(render_mock_private_test_send_rehearsal_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL mock private-test send rehearsal")
            print(f"- mock_send_rehearsal_count: {output.get('mock_send_rehearsal_count')}")
            print(f"- actual_discord_api_send_called: {output.get('actual_discord_api_send_called')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
        return 0

    if args.private_test_send_no_send_lock:
        output = build_private_test_send_no_send_lock()
        if args.markdown:
            print(render_private_test_send_no_send_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test send no-send lock")
            print(f"- mock_send_rehearsal_count_locked: {output.get('mock_send_rehearsal_count_locked')}")
            print(f"- actual_discord_send_count_locked: {output.get('actual_discord_send_count_locked')}")
            print(f"- ready_for_phase38_actual_private_test_send_path: {output.get('ready_for_phase38_actual_private_test_send_path')}")
        return 0

    if args.actual_private_test_send_contract:
        output = build_actual_private_test_send_contract()
        if args.markdown:
            print(render_actual_private_test_send_contract_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual private-test send contract")
            print(f"- send_scope: {output.get('send_scope')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
        return 0

    if args.final_would_send_payload_freeze:
        output = build_final_would_send_payload_freeze()
        if args.markdown:
            print(render_final_would_send_payload_freeze_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL final would-send payload freeze")
            print(f"- would_send_payload_frozen: {output.get('would_send_payload_frozen')}")
            print(f"- would_send_review_only: {output.get('would_send_review_only')}")
            print(f"- ready_for_discord_send: {output.get('ready_for_discord_send')}")
        return 0

    if args.private_test_send_rollback_gate:
        output = build_private_test_send_rollback_gate()
        if args.markdown:
            print(render_private_test_send_rollback_gate_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test send rollback gate")
            print(f"- rollback_checklist_ready: {output.get('rollback_checklist_ready')}")
            print(f"- emergency_disable_gates_listed: {output.get('emergency_disable_gates_listed')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
        return 0

    if args.private_test_send_operator_checklist:
        output = build_private_test_send_operator_checklist()
        if args.markdown:
            print(render_private_test_send_operator_checklist_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test send operator checklist")
            print(f"- operator_checklist_ready: {output.get('operator_checklist_ready')}")
            print(f"- ready_for_phase38e_live_send_entry_gate: {output.get('ready_for_phase38e_live_send_entry_gate')}")
            print(f"- ready_for_actual_private_test_send: {output.get('ready_for_actual_private_test_send')}")
        return 0

    if args.private_test_live_send_entry_gate:
        output = build_private_test_live_send_entry_gate()
        if args.markdown:
            print(render_private_test_live_send_entry_gate_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL private-test live send entry gate")
            print(f"- actual_private_test_send_not_started: {output.get('actual_private_test_send_not_started')}")
            print(f"- phase39_not_started: {output.get('phase39_not_started')}")
            print(f"- ready_for_phase39_live_execution: {output.get('ready_for_phase39_live_execution')}")
        return 0

    if args.actual_private_test_one_shot_send:
        output = build_actual_private_test_one_shot_send(
            allow_flag_present=args.allow_actual_private_test_send,
            execute_flag_present=args.execute_actual_private_test_send,
        )
        if args.markdown:
            print(render_actual_private_test_one_shot_send_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual private-test one-shot send path")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- ready_for_phase39b_manual_one_shot_send: {output.get('ready_for_phase39b_manual_one_shot_send')}")
        return 0

    if args.actual_private_test_send_safety_gate:
        output = build_actual_private_test_send_safety_gate()
        if args.markdown:
            print(render_actual_private_test_send_safety_gate_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual private-test send safety gate")
            print(f"- conditions_met: {output.get('conditions_met')}")
            print(f"- actual_send_allowed: {output.get('actual_send_allowed')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
        return 0

    if args.actual_private_test_send_blocked_report:
        output = build_actual_private_test_send_blocked_report()
        if args.markdown:
            print(render_actual_private_test_send_blocked_report_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL actual private-test send blocked report")
            print(f"- blocked: {output.get('blocked')}")
            print(f"- phase39a_no_execution_policy: {output.get('phase39a_no_execution_policy')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
        return 0

    if args.phase39b_manual_send_reentry_packet:
        output = build_phase39b_manual_send_reentry_packet()
        if args.markdown:
            print(render_phase39b_manual_send_reentry_packet_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 39B manual send re-entry packet")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- allow_flag_cli_available: {output.get('allow_flag_cli_available')}")
            print(f"- discord_api_send_called: {output.get('discord_api_send_called')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- ready_for_phase39b_actual_send_manual_attempt: {output.get('ready_for_phase39b_actual_send_manual_attempt')}")
        return 0

    if args.phase39b_manual_send_no_send_lock:
        output = build_phase39b_manual_send_no_send_lock()
        if args.markdown:
            print(render_phase39b_manual_send_no_send_lock_markdown(output))
        elif args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("STOXL Phase 39B manual send no-send lock")
            print(f"- report_only: {output.get('report_only')}")
            print(f"- actual_discord_send_count: {output.get('actual_discord_send_count')}")
            print(f"- discord_message_sent: {output.get('discord_message_sent')}")
            print(f"- ready_for_phase39c_send_closeout: {output.get('ready_for_phase39c_send_closeout')}")
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
        or args.discord_token_report
        or args.send_block_report
        or args.live_event_pipeline_report
        or args.discord_readonly_runtime_report
        or args.run_discord_readonly
        or args.run_discord_private_test_reply
        or args.run_discord_private_test_llm_reply
        or args.run_discord_private_test_rag_llm_reply
        or args.live_event_audit_report
        or args.would_send_preview_report
        or args.live_event_review_packet_report
        or args.phase30_audit_ops_report
        or args.operations_viewer
        or args.operations_packet
        or args.agent_placeholder_response_report
        or args.private_test_reply_report
        or args.private_test_reply_safety_report
        or args.private_test_reply_replay_report
        or args.llm_preflight_report
        or args.llm_safety_policy_report
        or args.llm_prompt_envelope_report
        or args.llm_dry_call_report
        or args.llm_response_packet_report
        or args.llm_response_packet_live_closeout
        or args.llm_private_test_reply_report
        or args.llm_private_test_reply_replay_report
        or args.rag_preflight_report
        or args.rag_local_retrieval_report
        or args.rag_response_packet_report
        or args.rag_llm_private_test_reply_report
        or args.rag_llm_prompt_envelope_report
        or args.rag_llm_would_send_preview
        or args.rag_llm_private_test_replay_report
        or args.rag_llm_live_readiness_review
        or args.rag_llm_private_test_runtime_report
        or args.rag_llm_live_preflight_closeout
        or args.rag_llm_live_success_closeout
        or args.knowledge_manifest
        or args.knowledge_ingestion_boundary
        or args.knowledge_source_routing
        or args.knowledge_evidence_packet
        or args.rag_evidence_integration
        or args.rag_evidence_review_packet
        or args.knowledge_dry_chain
        or args.rag_evidence_prompt_envelope
        or args.rag_evidence_llm_dry_readiness
        or args.rag_evidence_llm_dry_call_report
        or args.rag_evidence_llm_dry_call_closeout
        or args.rag_evidence_would_send_preview
        or args.rag_evidence_private_test_send_preflight
        or args.rag_evidence_private_test_send
        or args.rag_evidence_private_test_send_closeout
        or args.rag_evidence_private_test_e2e_preflight
        or args.rag_evidence_private_test_e2e_replay
        or args.rag_evidence_private_test_e2e_live_reply
        or args.rag_evidence_private_test_e2e_send_retry
        or args.rag_evidence_private_test_e2e_live_closeout
        or args.rag_evidence_private_test_phase34_final_lock
        or args.phase35a_post_mvp_safety_audit
        or args.local_knowledge_ingestion_preview
        or args.evidence_quality_preview
        or args.agent_routing_dry_preview
        or args.agent_evidence_pack_composer
        or args.agent_prompt_preview
        or args.agent_review_packet
        or args.manual_approval_packet_preview
        or args.operator_manual_checklist
        or args.no_live_rehearsal_packet
        or args.operations_dashboard_lock
        or args.forbidden_behavior_sentinel
        or args.phase36_entry_gate
        or args.private_test_one_shot_llm_draft_preflight
        or args.private_test_one_shot_llm_draft_mock_packet
        or args.one_shot_llm_draft_output_safety_rehearsal
        or args.actual_one_shot_llm_draft_call_preflight
        or args.actual_one_shot_llm_draft_call
        or args.actual_one_shot_llm_draft_call_closeout
        or args.one_shot_llm_no_send_final_lock
        or args.post_llm_call_dashboard_lock
        or args.phase37_entry_gate
        or args.private_test_llm_draft_review_packet
        or args.private_test_discord_send_preflight_preview
        or args.private_test_send_approval_rehearsal
        or args.actual_private_test_send_manual_preflight
        or args.mock_private_test_send_rehearsal
        or args.private_test_send_no_send_lock
        or args.actual_private_test_send_contract
        or args.final_would_send_payload_freeze
        or args.private_test_send_rollback_gate
        or args.private_test_send_operator_checklist
        or args.private_test_live_send_entry_gate
        or args.actual_private_test_one_shot_send
        or args.actual_private_test_send_safety_gate
        or args.actual_private_test_send_blocked_report
        or args.allow_actual_private_test_send
        or args.execute_actual_private_test_send
        or args.phase39b_manual_send_reentry_packet
        or args.phase39b_manual_send_no_send_lock
        or args.allow_llm_api_call
        or args.allow_actual_one_shot_llm_draft_call
        or args.allow_rag_evidence_llm_api_call
        or args.allow_rag_evidence_private_test_discord_send
        or args.allow_rag_evidence_private_test_e2e_live_reply
        or args.allow_rag_evidence_private_test_e2e_send_retry
        or args.write_artifact
        or args.latest
        or args.force
        or args.strict
        or args.export_log
        or args.log_root
        or args.review_packet
        or args.export_review_packet
        or args.review_export_root
        or args.dry_run_export
        or args.markdown
        or args.limit != 20
        or args.date
        or args.channel
        or args.workflow_role
        or args.agent
        or args.decision
        or args.event_id
        or args.source != "operation"
        or args.query != "STOXL brand tone"
    ):
        parser.error("Replay/export/readiness options require the matching mode option.")
    if args.event:
        event = load_event_file(args.event)
    elif args.text:
        event = event_from_text(args.text, args.channel or "대표-회의실", args.author_role)
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

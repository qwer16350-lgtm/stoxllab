"""Phase 31A operations packet viewer tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_operations_packet_viewer.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from live_event_audit_persistence import build_daily_live_event_manifest, build_live_event_audit_record, build_sample_visibility_event
from live_event_review_packet import build_live_event_review_packet, write_live_event_review_packet
from live_event_routing_report import build_live_event_routing_report
from operations_packet_viewer import (
    assert_viewer_output_safe,
    build_operations_packet_viewer_report,
    filter_events,
    list_recent_live_events,
    list_recent_review_packets,
    load_daily_manifest,
    load_review_packet,
    render_operations_summary_markdown,
)
from would_send_preview import build_would_send_preview


ROOT = APP_DIR.parents[1]
TEST_ROOT = ROOT / "logs" / "hermes_gateway_test" / "phase31_viewer"
LONG_NUMBER_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def setup_artifacts() -> dict:
    date = "20260613"
    knowledge_dir = TEST_ROOT / "knowledge" / "operation"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    (knowledge_dir / "stoxl_operation_tone_sample.md").write_text("STOXL brand tone local review evidence for operation.", encoding="utf-8")
    (knowledge_dir / "stoxl_private_test_workflow_sample.md").write_text("STOXL brand tone private test workflow evidence.", encoding="utf-8")
    log_dir = TEST_ROOT / "logs" / "hermes_gateway" / "live_events"
    log_dir.mkdir(parents=True, exist_ok=True)
    visibility = build_sample_visibility_event()
    visibility["created_at"] = "2026-06-13T01:00:00+00:00"
    visibility["event_id"] = "event_redacted_0000"
    audit = build_live_event_audit_record(visibility, content="hello from marketing")
    ignored_visibility = dict(visibility)
    ignored_visibility.update(
        {
            "created_at": "2026-06-13T01:05:00+00:00",
            "decision": "ignored_unmapped_channel",
            "reason": "ignored_unmapped_channel",
            "channel_mapped": False,
            "workflow_role": "",
            "agent_route_candidate": "unrouted",
        }
    )
    ignored = build_live_event_audit_record(ignored_visibility, content="")
    log_path = log_dir / f"readonly_events_{date}.jsonl"
    log_path.write_text(json.dumps(audit, ensure_ascii=False) + "\n" + json.dumps(ignored, ensure_ascii=False) + "\n", encoding="utf-8")
    build_daily_live_event_manifest(root=TEST_ROOT, date="2026-06-13T00:00:00+00:00")
    routing = build_live_event_routing_report(audit)
    preview = build_would_send_preview(audit, routing)
    packet = build_live_event_review_packet(audit, routing, preview)
    paths = write_live_event_review_packet(packet, root=TEST_ROOT)
    return {"audit": audit, "packet": packet, "paths": paths}


def test_recent_events_returned() -> None:
    setup_artifacts()
    events = list_recent_live_events(TEST_ROOT, date="20260613")
    assert_true(len(events) >= 2, "Recent events should be returned")


def test_limit_applied() -> None:
    setup_artifacts()
    assert_true(len(list_recent_live_events(TEST_ROOT, limit=1, date="20260613")) == 1, "Limit should be applied")


def test_date_filter_applied() -> None:
    setup_artifacts()
    assert_true(list_recent_live_events(TEST_ROOT, date="19990101") == [], "Missing date should return no events")


def test_channel_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", channel_name="marketing-brief")
    assert_true(all(item["channel_name"] == "marketing-brief" for item in report["recent_live_events"]), "Channel filter should apply")


def test_workflow_role_filter() -> None:
    setup_artifacts()
    events = filter_events(list_recent_live_events(TEST_ROOT, date="20260613"), workflow_role="marketing_intake")
    assert_true(all(item["workflow_role"] == "marketing_intake" for item in events), "Workflow filter should apply")


def test_agent_route_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", agent_route_candidate="marin")
    assert_true(all(item["agent_route_candidate"] == "marin" for item in report["recent_live_events"]), "Agent route filter should apply")


def test_decision_filter() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613", decision="accepted_mapped_channel")
    assert_true(all(item["decision"] == "accepted_mapped_channel" for item in report["recent_live_events"]), "Decision filter should apply")


def test_review_packet_list_returned() -> None:
    setup_artifacts()
    packets = list_recent_review_packets(TEST_ROOT)
    assert_true(len(packets) >= 1, "Review packet list should be returned")


def test_load_packet_by_event_id() -> None:
    data = setup_artifacts()
    packet = load_review_packet(TEST_ROOT, event_id=data["packet"]["event_id"])
    assert_true(packet["packet_type"] == "live_event_review_packet", "Packet detail should load by event_id")


def test_daily_manifest_load() -> None:
    setup_artifacts()
    manifest = load_daily_manifest(TEST_ROOT, date="20260613")
    assert_true(manifest["total_events"] >= 2, "Daily manifest summary should load")


def test_markdown_summary_render() -> None:
    setup_artifacts()
    markdown = render_operations_summary_markdown(build_operations_packet_viewer_report(TEST_ROOT, date="20260613"))
    assert_true("# STOXL Hermes Operations Viewer" in markdown, "Markdown summary should render")


def test_no_raw_token_or_id() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    text = json.dumps(report, ensure_ascii=False).lower()
    assert_true("sk-" not in text and "xoxb-" not in text and "mfa." not in text, "Token markers should be absent")
    assert_true(not LONG_NUMBER_RE.search(text), "Raw Discord-like IDs should be absent")


def test_no_env_or_local_mapping_read_flags() -> None:
    setup_artifacts()
    safety = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["safety_assertions"]
    assert_true(safety["env_file_read"] is False, ".env should not be read")
    assert_true(safety["local_mapping_file_read"] is False, "local mapping should not be read")


def test_safety_flags_false() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    assert_viewer_output_safe(report)
    safety = report["safety_assertions"]
    assert_true(safety["discord_api_called"] is False, "Discord API should not be called")
    assert_true(safety["message_sent"] is False, "Message should not be sent")
    assert_true(safety["external_execution"] is False, "External execution should be false")
    assert_true(safety["llm_called"] is False, "LLM should not be called")
    assert_true(safety["rag_called"] is False, "RAG should not be called")


def test_rag_llm_scaffold_summary() -> None:
    setup_artifacts()
    scaffold = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_private_test_scaffold"]
    assert_true(scaffold["preflight_available"] is True, "RAG+LLM preflight should be available")
    assert_true(scaffold["context_safety_available"] is True, "Context safety should be available")
    assert_true(scaffold["prompt_envelope_available"] is True, "Prompt envelope should be available")
    assert_true(scaffold["would_send_preview_available"] is True, "Would-send should be available")
    assert_true(scaffold["replay_available"] is True, "Replay should be available")
    assert_true(scaffold["actual_discord_send"] is False, "No actual Discord send")
    assert_true(scaffold["actual_llm_api_call"] is False, "No actual LLM API call")
    assert_true(scaffold["embedding_api_call"] is False, "No embedding API call")
    assert_true(scaffold["external_execution"] is False, "No external execution")


def test_rag_llm_live_readiness_summary() -> None:
    setup_artifacts()
    readiness = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_live_readiness_review"]
    assert_true(readiness["available"] is True, "Readiness review should be available")
    assert_true(readiness["go"] is False, "Live readiness should be no-go")
    assert_true(readiness["ready_for_manual_phase33d_implementation_request"] is True, "Manual request should be ready")
    assert_true(readiness["actual_discord_send"] is False, "No actual Discord send")
    assert_true(readiness["actual_llm_api_call"] is False, "No actual LLM API call")
    assert_true(readiness["embedding_api_called"] is False, "No embedding API call")
    assert_true(readiness["external_execution"] is False, "No external execution")


def test_rag_llm_private_test_runtime_summary() -> None:
    setup_artifacts()
    runtime = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_private_test_runtime"]
    assert_true(runtime["available"] is True, "Runtime report should be available")
    assert_true(runtime["runtime_option_added"] is True, "Runtime option should be represented")
    assert_true(runtime["runtime_executed_by_report"] is False, "Viewer should not execute runtime")
    assert_true(runtime["actual_discord_send"] is False, "No actual Discord send")
    assert_true(runtime["actual_llm_api_call"] is False, "No actual LLM API call")
    assert_true(runtime["embedding_api_called"] is False, "No embedding API call")
    assert_true(runtime["external_execution"] is False, "No external execution")


def test_rag_llm_live_preflight_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_live_preflight_closeout"]
    assert_true(closeout["available"] is True, "Live preflight closeout should be available")
    assert_true(closeout["runtime_executed"] is False, "Viewer should not execute runtime")
    assert_true(closeout["ready_for_single_live_private_test"] is True, "Single live private test should be ready for separate approval")
    assert_true(closeout["actual_discord_send"] is False, "No actual Discord send")
    assert_true(closeout["actual_llm_api_call"] is False, "No actual LLM API call")
    assert_true(closeout["embedding_api_called"] is False, "No embedding API call")
    assert_true(closeout["external_execution"] is False, "No external execution")


def test_rag_llm_single_live_test_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_llm_single_live_test_closeout"]
    assert_true(closeout["available"] is True, "Single live test closeout should be available")
    assert_true(closeout["closeout_passed"] is True, "Single live test closeout should pass")
    assert_true(closeout["sent_exactly_once"] is True, "Discord message should be sent exactly once in fixture")
    assert_true(closeout["self_loop_prevented"] is True, "Self-loop should be prevented")
    assert_true(closeout["private_test_channel_only"] is True, "Private test channel only")
    assert_true(closeout["llm_api_called_once"] is True, "LLM API should be observed once")
    assert_true(closeout["discord_message_sent_once"] is True, "Discord message should be observed once")
    assert_true(closeout["embedding_api_called"] is False, "No embedding API call")
    assert_true(closeout["external_execution"] is False, "No external execution")
    assert_true(closeout["ready_for_phase34_knowledge_ingestion"] is True, "Phase 34 readiness should be true")


def test_knowledge_foundation_summary() -> None:
    setup_artifacts()
    knowledge = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["knowledge_foundation"]
    assert_true(knowledge["available"] is True, "Knowledge foundation should be available")
    assert_true(knowledge["ready_for_local_text_ingestion"] is True, "Local text ingestion should be ready")
    assert_true(knowledge["ready_for_embedding"] is False, "Embedding should be deferred")
    assert_true(knowledge["ready_for_external_sources"] is False, "External sources should be deferred")
    assert_true(knowledge["source_routing_available"] is True, "Source routing should be available")
    assert_true(knowledge["evidence_packet_available"] is True, "Evidence packet should be available")
    assert_true("operation" in knowledge["canonical_sources"], "operation should be canonical")
    assert_true("operations" not in knowledge["canonical_sources"], "operations should not be canonical")
    assert_true(knowledge["operations_source_present"] is False, "operations folder should be absent")
    assert_true(knowledge["embedding_api_called"] is False, "No embedding API call")
    assert_true(knowledge["llm_api_called"] is False, "No LLM API call")
    assert_true(knowledge["discord_message_sent"] is False, "No Discord message sent")
    assert_true(knowledge["external_execution"] is False, "No external execution")


def test_rag_evidence_integration_summary() -> None:
    setup_artifacts()
    integration = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_integration"]
    assert_true(integration["available"] is True, "RAG evidence integration should be available")
    assert_true(integration["evidence_packet_available"] is True, "Evidence packet should be available")
    assert_true(integration["rag_response_packet_created"] is True, "RAG response packet should be created")
    assert_true(integration["citations_included"] is True, "Citations should be included")
    assert_true(integration["ready_for_private_test_review"] is True, "Private test review should be ready")
    assert_true(integration["ready_for_llm_prompt"] is False, "LLM prompt should remain false")
    assert_true(integration["ready_for_embedding"] is False, "Embedding should remain false")
    assert_true(integration["ready_for_external_sources"] is False, "External sources should remain false")
    assert_true(integration["embedding_api_called"] is False, "No embedding API call")
    assert_true(integration["llm_api_called"] is False, "No LLM API call")
    assert_true(integration["discord_message_sent"] is False, "No Discord message sent")
    assert_true(integration["external_execution"] is False, "No external execution")


def test_rag_evidence_review_packet_summary() -> None:
    setup_artifacts()
    review = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_review_packet"]
    assert_true(review["available"] is True, "RAG evidence review packet should be available")
    assert_true(review["review_only"] is True, "Review only should be true")
    assert_true(review["human_review_required"] is True, "Human review should be required")
    assert_true(review["ready_for_private_test_review"] is True, "Private test review should be ready")
    assert_true(review["ready_for_llm_prompt"] is False, "LLM prompt should be false")
    assert_true(review["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(review["ready_for_embedding"] is False, "Embedding should be false")
    assert_true(review["ready_for_external_sources"] is False, "External sources should be false")


def test_knowledge_dry_chain_summary() -> None:
    setup_artifacts()
    chain = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["knowledge_dry_chain"]
    assert_true(chain["available"] is True, "Knowledge dry chain should be available")
    assert_true(chain["sample_files_present"] is True, "Sample files should be present")
    assert_true(chain["manifest_available"] is True, "Manifest should be available")
    assert_true(chain["evidence_packet_available"] is True, "Evidence packet should be available")
    assert_true(chain["rag_response_packet_available"] is True, "RAG response packet should be available")
    assert_true(chain["review_packet_available"] is True, "Review packet should be available")
    assert_true(chain["ready_for_private_test_review"] is True, "Private test review should be ready")
    assert_true(chain["ready_for_llm_prompt"] is False, "LLM prompt should be false")
    assert_true(chain["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(chain["ready_for_embedding"] is False, "Embedding should be false")
    assert_true(chain["ready_for_external_sources"] is False, "External sources should be false")


def test_rag_evidence_prompt_envelope_summary() -> None:
    setup_artifacts()
    prompt = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_prompt_envelope"]
    assert_true(prompt["available"] is True, "Prompt envelope should be available")
    assert_true(prompt["review_only"] is True, "Review only should be true")
    assert_true(prompt["human_review_required"] is True, "Human review should be required")
    assert_true(prompt["ready_for_prompt_preview"] is True, "Prompt preview should be ready")
    assert_true(prompt["ready_for_llm_api_call"] is False, "LLM API call should be false")
    assert_true(prompt["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(prompt["ready_for_embedding"] is False, "Embedding should be false")
    assert_true(prompt["ready_for_external_sources"] is False, "External sources should be false")


def test_rag_evidence_llm_dry_readiness_summary() -> None:
    setup_artifacts()
    dry = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_llm_dry_readiness"]
    assert_true(dry["available"] is True, "Dry readiness should be available")
    assert_true(dry["prompt_envelope_available"] is True, "Prompt envelope should be available")
    assert_true(dry["prompt_safety_allowed"] is True, "Prompt safety should be allowed")
    assert_true(dry["mock_response_created"] is True, "Mock response should be created")
    assert_true(dry["mock_response_safety_allowed"] is True, "Mock response safety should pass")
    assert_true(dry["llm_response_packet_created"] is True, "LLM response packet should be created")
    assert_true(dry["ready_for_actual_llm_dry_call"] is True, "Actual dry call readiness should be true")
    assert_true(dry["actual_llm_api_call"] is False, "Actual LLM API call should be false")
    assert_true(dry["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(dry["embedding_api_called"] is False, "Embedding API call should be false")
    assert_true(dry["external_execution"] is False, "External execution should be false")


def test_rag_evidence_llm_dry_call_summary() -> None:
    setup_artifacts()
    dry = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_llm_dry_call"]
    assert_true(dry["available"] is True, "Dry call summary should be available")
    assert_true(dry["manual_approval_required"] is True, "Manual approval should be required")
    assert_true(dry["manual_approval_approved"] is False, "Viewer should not approve actual call")
    assert_true(dry["blocked"] is True, "Viewer default dry call should be blocked")
    assert_true(dry["actual_llm_api_call"] is False, "Viewer should not call LLM API")
    assert_true(dry["api_call_attempted"] is False, "Viewer should not attempt API call")
    assert_true(dry["llm_response_packet_created"] is False, "Blocked default should not create packet")
    assert_true(dry["output_safety_allowed"] is False, "Blocked default should not be output-ready")
    assert_true(dry["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(dry["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(dry["embedding_api_called"] is False, "Embedding API call should be false")
    assert_true(dry["external_execution"] is False, "External execution should be false")


def test_rag_evidence_llm_dry_call_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_llm_dry_call_closeout"]
    assert_true(closeout["available"] is True, "Dry call closeout summary should be available")
    assert_true(closeout["actual_dry_call_observed"] is True, "Actual dry call should be observed")
    assert_true(closeout["api_call_succeeded_count"] == 1, "One API call should be recorded from fixture")
    assert_true(closeout["llm_response_packet_created"] is True, "Response packet should be created")
    assert_true(closeout["output_safety_allowed"] is True, "Output safety should pass")
    assert_true(closeout["ready_for_discord_send"] is False, "Discord send should be false")
    assert_true(closeout["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(closeout["embedding_api_called"] is False, "Embedding API call should be false")
    assert_true(closeout["external_execution"] is False, "External execution should be false")
    assert_true(closeout["additional_llm_api_call"] is False, "No additional LLM call should happen")
    assert_true(closeout["ready_for_phase34i_private_test_would_send_preview"] is True, "Phase 34I preview should be ready")


def test_rag_evidence_would_send_preview_summary() -> None:
    setup_artifacts()
    preview = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_would_send_preview"]
    assert_true(preview["available"] is True, "Would-send preview summary should be available")
    assert_true(preview["would_send_preview_created"] is True, "Would-send preview should be created")
    assert_true(preview["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(preview["public_channel_send_allowed"] is False, "Public send should be false")
    assert_true(preview["team_channel_send_allowed"] is False, "Team send should be false")
    assert_true(preview["discord_api_send_allowed"] is False, "Discord API send allowed should be false")
    assert_true(preview["discord_api_send_called"] is False, "Discord API send called should be false")
    assert_true(preview["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(preview["ready_for_actual_discord_send"] is False, "Actual Discord send should be false")
    assert_true(preview["ready_for_phase34j_private_test_send_preflight"] is True, "Phase 34J preflight should be ready")


def test_rag_evidence_private_test_send_preflight_summary() -> None:
    setup_artifacts()
    preflight = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_send_preflight"]
    assert_true(preflight["available"] is True, "Preflight summary should be available")
    assert_true(preflight["would_send_preview_available"] is True, "Would-send preview should be available")
    assert_true(preflight["manual_approval_required"] is True, "Manual approval should be required")
    assert_true(preflight["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(preflight["public_channel_send_allowed"] is False, "Public send should be false")
    assert_true(preflight["team_channel_send_allowed"] is False, "Team send should be false")
    assert_true(preflight["discord_api_send_allowed"] is False, "Discord API send should be false")
    assert_true(preflight["discord_api_send_called"] is False, "Discord API send called should be false")
    assert_true(preflight["discord_message_sent"] is False, "Discord message sent should be false")
    assert_true(preflight["ready_for_actual_private_test_send"] is False, "Actual private-test send should be false")
    assert_true(preflight["ready_for_phase34j1_manual_live_send"] is True, "Phase 34J-1 should be ready")


def test_rag_evidence_private_test_send_summary() -> None:
    setup_artifacts()
    send = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_send"]
    assert_true(send["available"] is True, "Private-test send summary should be available")
    assert_true(send["manual_approval_required"] is True, "Manual approval should be required")
    assert_true(send["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(send["public_channel_send_allowed"] is False, "Public channel send should be false")
    assert_true(send["team_channel_send_allowed"] is False, "Team channel send should be false")
    assert_true(send["discord_api_send_called"] is False, "Viewer should not call Discord send")
    assert_true(send["discord_message_sent"] is False, "Viewer should not send Discord")
    assert_true(send["message_sent_count"] == 0, "Viewer default should have zero sends")
    assert_true(send["ready_for_phase34j2_send_closeout"] is False, "No send closeout readiness without live send")
    assert_true(send["llm_api_called"] is False, "Viewer should not call LLM")
    assert_true(send["embedding_api_called"] is False, "Viewer should not call embeddings")
    assert_true(send["external_execution"] is False, "Viewer should not execute external action")


def main() -> int:
    tests = [
        test_recent_events_returned,
        test_limit_applied,
        test_date_filter_applied,
        test_channel_filter,
        test_workflow_role_filter,
        test_agent_route_filter,
        test_decision_filter,
        test_review_packet_list_returned,
        test_load_packet_by_event_id,
        test_daily_manifest_load,
        test_markdown_summary_render,
        test_no_raw_token_or_id,
        test_no_env_or_local_mapping_read_flags,
        test_safety_flags_false,
        test_rag_llm_scaffold_summary,
        test_rag_llm_live_readiness_summary,
        test_rag_llm_private_test_runtime_summary,
        test_rag_llm_live_preflight_closeout_summary,
        test_rag_llm_single_live_test_closeout_summary,
        test_knowledge_foundation_summary,
        test_rag_evidence_integration_summary,
        test_rag_evidence_review_packet_summary,
        test_knowledge_dry_chain_summary,
        test_rag_evidence_prompt_envelope_summary,
        test_rag_evidence_llm_dry_readiness_summary,
        test_rag_evidence_llm_dry_call_summary,
        test_rag_evidence_llm_dry_call_closeout_summary,
        test_rag_evidence_would_send_preview_summary,
        test_rag_evidence_private_test_send_preflight_summary,
        test_rag_evidence_private_test_send_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations packet viewer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

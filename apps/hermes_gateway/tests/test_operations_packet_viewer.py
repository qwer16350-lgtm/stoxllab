"""Phase 31A operations packet viewer tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_operations_packet_viewer.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
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
TEST_ROOT = Path(tempfile.gettempdir()) / "stoxl_hermes_gateway_test" / "phase31_viewer"
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


def test_rag_evidence_private_test_send_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_send_closeout"]
    assert_true(closeout["available"] is True, "Send closeout should be available")
    assert_true(closeout["actual_private_test_send_observed"] is True, "Prior send should be observed")
    assert_true(closeout["discord_api_send_called_count"] == 1, "Send call count should be one")
    assert_true(closeout["discord_message_sent_count"] == 1, "Sent count should be one")
    assert_true(closeout["sent_channel_scope"] == "private_test_only", "Scope should be private-test only")
    assert_true(closeout["additional_discord_send"] is False, "No additional send")
    assert_true(closeout["llm_api_called"] is False, "No LLM call")
    assert_true(closeout["embedding_api_called"] is False, "No embedding")
    assert_true(closeout["external_execution"] is False, "No external execution")
    assert_true(closeout["closeout_passed"] is True, "Closeout should pass")
    assert_true(closeout["ready_for_phase34k_private_test_e2e_preflight"] is True, "Phase 34K should be ready")


def test_rag_evidence_private_test_e2e_preflight_summary() -> None:
    setup_artifacts()
    preflight = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_e2e_preflight"]
    assert_true(preflight["available"] is True, "E2E preflight should be available")
    assert_true(preflight["private_test_channel_only"] is True, "Private-test only")
    assert_true(preflight["public_channel_reply_allowed"] is False, "Public reply false")
    assert_true(preflight["team_channel_reply_allowed"] is False, "Team reply false")
    assert_true(preflight["discord_live_runtime_executed"] is False, "No live runtime")
    assert_true(preflight["discord_message_sent"] is False, "No Discord message")
    assert_true(preflight["llm_api_called"] is False, "No LLM call")
    assert_true(preflight["embedding_api_called"] is False, "No embedding")
    assert_true(preflight["external_execution"] is False, "No external execution")
    assert_true(preflight["ready_for_phase34l1_manual_e2e_live_reply"] is True, "Phase 34L-1 should be ready")
    assert_true(preflight["ready_for_unattended_auto_reply"] is False, "Unattended false")


def test_rag_evidence_private_test_e2e_replay_summary() -> None:
    setup_artifacts()
    replay = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_e2e_replay"]
    assert_true(replay["available"] is True, "E2E replay should be available")
    assert_true(replay["e2e_replay_passed"] is True, "E2E replay should pass")
    assert_true(replay["discord_live_runtime_executed"] is False, "No live runtime")
    assert_true(replay["discord_message_sent"] is False, "No Discord message")
    assert_true(replay["llm_api_called"] is False, "No LLM call")
    assert_true(replay["embedding_api_called"] is False, "No embedding")
    assert_true(replay["external_execution"] is False, "No external execution")
    assert_true(replay["ready_for_phase34l1_manual_e2e_live_reply"] is True, "Phase 34L-1 should be ready")
    assert_true(replay["ready_for_unattended_auto_reply"] is False, "Unattended false")


def test_rag_evidence_private_test_e2e_live_reply_summary() -> None:
    setup_artifacts()
    live = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_e2e_live_reply"]
    assert_true(live["available"] is True, "E2E live reply summary should be available")
    assert_true(live["manual_approval_required"] is True, "Manual approval should be required")
    assert_true(live["manual_approval_approved"] is False, "Viewer should not approve live reply")
    assert_true(live["private_test_channel_only"] is True, "Private-test only should be true")
    assert_true(live["public_channel_reply_allowed"] is False, "Public reply should be false")
    assert_true(live["team_channel_reply_allowed"] is False, "Team reply should be false")
    assert_true(isinstance(live["openrouter_api_key_present"], bool), "OpenRouter key presence should be boolean")
    assert_true("OPENROUTER_API_KEY" in live["openrouter_api_key_aliases_checked"], "OPENROUTER alias should be checked")
    assert_true("HERMES_OPENROUTER_API_KEY" in live["openrouter_api_key_aliases_checked"], "HERMES alias should be checked")
    assert_true(live["openrouter_api_key_value_logged"] is False, "OpenRouter key value should not be logged")
    assert_true(live["blocked"] is True, "Viewer default live reply should be blocked")
    assert_true(live["discord_live_runtime_executed"] is False, "Viewer should not run live runtime")
    assert_true(live["prompt_safety_checked"] is False, "Viewer default should not check prompt safety")
    assert_true(live["llm_stage_reached"] is False, "Viewer default should not reach LLM stage")
    assert_true(live["llm_call_allowed"] is False, "Viewer default should not allow LLM call")
    assert_true(live["llm_dispatch_invoked"] is False, "Viewer default should not invoke dispatch")
    assert_true(live["llm_dispatch_mode"] == "", "Viewer default dispatch mode should be empty")
    assert_true(live["llm_dispatch_blocked_reason"] == "", "Viewer default blocked reason should be empty")
    assert_true(live["llm_api_call_attempted"] is False, "Viewer default should not attempt LLM call")
    assert_true(live["llm_api_called"] is False, "Viewer should not call LLM")
    assert_true(live["llm_response_packet_created"] is False, "Viewer default should not create response packet")
    assert_true(live["output_safety_checked"] is False, "Viewer default should not check output safety")
    assert_true(live["output_safety_blocked"] is False, "Viewer default should not block output safety early")
    assert_true(live["discord_message_sent"] is False, "Viewer should not send Discord")
    assert_true(live["message_sent_count"] == 0, "Viewer default should have zero sends")
    assert_true(live["ready_for_phase34l2_e2e_live_reply_closeout"] is False, "Closeout should not be ready by default")
    assert_true(live["ready_for_unattended_auto_reply"] is False, "Unattended false")


def test_rag_evidence_private_test_e2e_send_retry_summary() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    partial = report["rag_evidence_private_test_e2e_partial_success"]
    retry = report["rag_evidence_private_test_e2e_send_retry"]
    assert_true(partial["available"] is False, "Viewer default should not invent live partial success")
    assert_true(partial["llm_api_called"] is False, "Viewer default should not call LLM")
    assert_true(partial["discord_message_sent"] is False, "Viewer default should not send Discord")
    assert_true(retry["available"] is True, "Retry summary should be available")
    assert_true(retry["llm_recall_allowed"] is False, "Retry should never allow LLM recall")
    assert_true(retry["manual_approval_required"] is True, "Retry should require manual approval")
    assert_true(retry["actual_send_retry_sender_available"] is False, "Viewer default should not expose sender")
    assert_true(retry["actual_send_retry_sender_not_provided"] is False, "Viewer should not report sender-not-provided")
    assert_true(retry["ready_for_actual_send_retry"] is False, "Viewer default retry should be blocked")
    assert_true(retry["discord_message_sent"] is False, "Viewer retry should not send")
    assert_true(retry["message_sent_count"] == 0, "Viewer retry send count should be zero")


def test_rag_evidence_private_test_e2e_live_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_e2e_live_closeout"]
    assert_true(closeout["available"] is True, "E2E live closeout should be available")
    assert_true(closeout["e2e_live_reply_observed"] is True, "Observed fixture should be true")
    assert_true(closeout["llm_api_call_count"] == 1, "Total LLM count should be one")
    assert_true(closeout["send_retry_llm_call_count"] == 0, "Send retry LLM count should be zero")
    assert_true(closeout["final_discord_message_sent_count"] == 1, "Final sent count should be one")
    assert_true(closeout["sent_channel_scope"] == "private_test_only", "Sent scope should be private test")
    assert_true(closeout["closeout_passed"] is True, "Closeout should pass")
    assert_true(closeout["ready_for_phase34m_final_lock"] is True, "Phase 34M should be ready")
    assert_true(closeout["ready_for_unattended_auto_reply"] is False, "Unattended false")


def test_rag_evidence_private_test_phase34_final_lock_summary() -> None:
    setup_artifacts()
    final_lock = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["rag_evidence_private_test_phase34_final_lock"]
    assert_true(final_lock["available"] is True, "Final lock should be available")
    assert_true(final_lock["phase34_private_test_mvp_complete"] is True, "MVP should be complete")
    assert_true(final_lock["llm_api_call_count"] == 1, "LLM count should be one")
    assert_true(final_lock["send_retry_llm_call_count"] == 0, "Retry LLM count should be zero")
    assert_true(final_lock["final_discord_message_sent_count"] == 1, "Final sent count should be one")
    assert_true(final_lock["sent_channel_scope"] == "private_test_only", "Scope should be private-test only")
    assert_true(final_lock["ready_for_unattended_auto_reply"] is False, "Unattended false")
    assert_true(final_lock["phase34m_final_lock_passed"] is True, "Final lock should pass")


def test_phase35a_post_mvp_safety_audit_summary() -> None:
    setup_artifacts()
    audit = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["phase35a_post_mvp_safety_audit"]
    assert_true(audit["available"] is True, "Phase 35A audit should be available")
    assert_true(audit["phase34_private_test_mvp_complete"] is True, "MVP should be complete")
    assert_true(audit["phase34m_final_lock_passed"] is True, "Final lock should pass")
    assert_true(audit["total_llm_call_count"] == 1, "Total LLM count should be one")
    assert_true(audit["send_retry_llm_call_count"] == 0, "Retry LLM count should be zero")
    assert_true(audit["final_discord_message_sent_count"] == 1, "Final sent count should be one")
    assert_true(audit["sent_channel_scope"] == "private_test_only", "Scope should be private-test only")
    assert_true(audit["public_team_blocked"] is True, "Public/team should be blocked")
    assert_true(audit["unattended_auto_reply_allowed"] is False, "Unattended false")
    assert_true(audit["embedding_external_disabled"] is True, "Embedding/external should be disabled")
    assert_true(audit["phase35a_audit_passed"] is True, "Audit should pass")


def test_phase35b_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    local = report["phase35b_local_knowledge_ingestion_preview"]
    quality = report["phase35b_evidence_quality_preview"]
    routing = report["phase35b_agent_routing_dry_preview"]
    assert_true(local["available"] is True, "Local preview should be available")
    assert_true(local["ready_for_local_text_ingestion"] is True, "Local text ready")
    assert_true(local["ready_for_embedding"] is False, "Embedding false")
    assert_true(local["ready_for_external_sources"] is False, "External false")
    assert_true(local["canonical_operation_source"] is True, "operation canonical")
    assert_true(local["forbidden_operations_source"] is True, "operations forbidden")
    assert_true(quality["citation_sufficiency_checked"] is True, "Citation checked")
    assert_true(quality["duplicate_evidence_checked"] is True, "Duplicate checked")
    assert_true(quality["stale_doc_suspicion_checked"] is True, "Stale checked")
    assert_true(quality["relative_paths_only"] is True, "Relative paths")
    assert_true(quality["full_content_included"] is False, "No full content")
    assert_true(routing["routing_rule_only"] is True, "Rule-only")
    assert_true(routing["llm_called"] is False, "No LLM")
    assert_true(routing["discord_message_sent"] is False, "No Discord")
    assert_true(routing["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase35c_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    composer = report["phase35c_agent_evidence_pack_composer"]
    prompt = report["phase35c_agent_prompt_preview"]
    assert_true(composer["available"] is True, "Composer available")
    assert_true(composer["rule_only"] is True, "Composer rule-only")
    assert_true(composer["relative_paths_only"] is True, "Relative paths")
    assert_true(composer["full_content_included"] is False, "No full content")
    assert_true(composer["ready_for_llm_call"] is False, "No LLM ready")
    assert_true(composer["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(composer["ready_for_embedding"] is False, "No embedding ready")
    assert_true(composer["ready_for_external_sources"] is False, "No external ready")
    assert_true(prompt["available"] is True, "Prompt preview available")
    assert_true(prompt["rule_only"] is True, "Prompt rule-only")
    assert_true(prompt["llm_called"] is False, "No LLM")
    assert_true(prompt["discord_message_sent"] is False, "No Discord")
    assert_true(prompt["ready_for_llm_call"] is False, "No LLM ready")
    assert_true(prompt["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(prompt["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase35d_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    review = report["phase35d_agent_review_packet"]
    approval = report["phase35d_manual_approval_packet_preview"]
    assert_true(review["available"] is True, "Review packet available")
    assert_true(review["rule_only"] is True, "Review packet rule-only")
    assert_true(review["human_review_required"] is True, "Human review required")
    assert_true(review["ready_for_llm_call"] is False, "No LLM ready")
    assert_true(review["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(review["ready_for_embedding"] is False, "No embedding ready")
    assert_true(review["ready_for_external_sources"] is False, "No external ready")
    assert_true(review["full_content_included"] is False, "No full content")
    assert_true(approval["available"] is True, "Approval preview available")
    assert_true(approval["rule_only"] is True, "Approval preview rule-only")
    assert_true(approval["approval_phrase_generated"] is False, "No approval phrase generated")
    assert_true(approval["approval_phrase_value_logged"] is False, "No approval phrase value logged")
    assert_true(approval["ready_for_actual_approval"] is False, "No actual approval")
    assert_true(approval["ready_for_llm_call"] is False, "No LLM ready")
    assert_true(approval["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(approval["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase35e_g_and_phase36_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    checklist = report["phase35e_operator_manual_checklist"]
    rehearsal = report["phase35e_no_live_rehearsal_packet"]
    dashboard = report["phase35f_operations_dashboard_lock"]
    sentinel = report["phase35g_forbidden_behavior_sentinel"]
    gate = report["phase36_entry_gate"]
    assert_true(checklist["available"] is True, "Checklist available")
    assert_true(checklist["report_only"] is True, "Checklist report-only")
    assert_true(checklist["approval_phrase_generated"] is False, "No approval phrase")
    assert_true(checklist["ready_for_actual_approval"] is False, "No actual approval")
    assert_true(checklist["ready_for_llm_call"] is False, "No LLM ready")
    assert_true(checklist["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(rehearsal["available"] is True, "Rehearsal available")
    assert_true(rehearsal["report_only"] is True, "Rehearsal report-only")
    assert_true(rehearsal["live_runtime_executed"] is False, "No live runtime")
    assert_true(rehearsal["llm_called"] is False, "No LLM")
    assert_true(rehearsal["discord_message_sent"] is False, "No Discord")
    assert_true(dashboard["available"] is True, "Dashboard lock available")
    assert_true(dashboard["phase34_private_test_mvp_complete"] is True, "MVP complete")
    assert_true(dashboard["total_llm_call_count"] == 1, "One LLM call")
    assert_true(dashboard["final_discord_message_sent_count"] == 1, "One final Discord message")
    assert_true(dashboard["ready_for_live_runtime"] is False, "No live readiness")
    assert_true(sentinel["available"] is True, "Sentinel available")
    assert_true(sentinel["forbidden_behavior_sentinel_passed"] is True, "Sentinel passed")
    assert_true(sentinel["public_team_blocked"] is True, "Public/team blocked")
    assert_true(sentinel["unattended_auto_reply_allowed"] is False, "No unattended")
    assert_true(sentinel["embedding_vector_disabled"] is True, "Embedding/vector disabled")
    assert_true(sentinel["external_execution"] is False, "No external")
    assert_true(gate["available"] is True, "Phase 36 gate available")
    assert_true(gate["phase36_not_started"] is True, "Phase 36 not started")
    assert_true(gate["requires_explicit_user_approval"] is True, "Explicit approval required")
    assert_true(gate["ready_for_phase36_live_execution"] is False, "No Phase 36 live execution")


def test_phase36a_preflight_summary() -> None:
    setup_artifacts()
    preflight = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["phase36a_private_test_one_shot_llm_draft_preflight"]
    assert_true(preflight["available"] is True, "Phase 36A preflight available")
    assert_true(preflight["report_only"] is True, "Report only")
    assert_true(preflight["phase36_started"] is False, "Phase 36 not started")
    assert_true(preflight["requires_explicit_user_approval"] is True, "Explicit approval")
    assert_true(preflight["llm_called"] is False, "No LLM")
    assert_true(preflight["discord_message_sent"] is False, "No Discord")
    assert_true(preflight["candidate_agents"] == ["kasumi"], "Candidate agent is Kasumi")
    assert_true(preflight["ready_for_actual_llm_call"] is False, "No actual LLM ready")
    assert_true(preflight["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(preflight["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase36b_mock_and_safety_summary() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    mock = report["phase36b_one_shot_llm_draft_mock_packet"]
    safety = report["phase36b_output_safety_rehearsal"]
    assert_true(mock["available"] is True, "Phase 36B mock available")
    assert_true(mock["report_only"] is True, "Mock report only")
    assert_true(mock["phase36_live_execution_started"] is False, "No live execution")
    assert_true(mock["llm_called"] is False, "No LLM")
    assert_true(mock["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(mock["discord_message_sent"] is False, "No Discord")
    assert_true(mock["mock_candidate_agents"] == ["kasumi"], "Kasumi mock candidate")
    assert_true(mock["ready_for_output_safety_rehearsal"] is True, "Ready for rehearsal")
    assert_true(mock["ready_for_actual_llm_call"] is False, "No actual LLM ready")
    assert_true(mock["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(safety["available"] is True, "Safety rehearsal available")
    assert_true(safety["report_only"] is True, "Safety report only")
    assert_true(safety["output_safety_allowed_agents"] == ["kasumi"], "Kasumi safety allowed")
    assert_true(safety["negative_fixtures_passed"] is True, "Negative fixtures passed")
    assert_true(safety["ready_for_phase36c_actual_llm_call_preflight"] is True, "Ready for Phase 36C preflight")
    assert_true(safety["ready_for_actual_llm_call"] is False, "No actual LLM ready")
    assert_true(safety["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(safety["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase36c_actual_llm_call_preflight_summary() -> None:
    setup_artifacts()
    preflight = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["phase36c_actual_one_shot_llm_draft_call_preflight"]
    assert_true(preflight["available"] is True, "Phase 36C preflight available")
    assert_true(preflight["report_only"] is True, "Report only")
    assert_true(preflight["candidate_agent"] == "kasumi", "Kasumi candidate")
    assert_true(isinstance(preflight["openrouter_api_key_present"], bool), "Key presence boolean")
    assert_true(preflight["manual_approval_required"] is True, "Manual approval required")
    assert_true(preflight["manual_approval_actualized"] is False, "Manual approval not actualized")
    assert_true(preflight["ready_for_actual_llm_call"] is False, "No actual LLM ready")
    assert_true(preflight["ready_for_discord_send"] is False, "No Discord ready")
    assert_true(preflight["llm_called"] is False, "No LLM")
    assert_true(preflight["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(preflight["discord_message_sent"] is False, "No Discord message")
    assert_true(preflight["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase36d_actual_llm_draft_call_summary() -> None:
    setup_artifacts()
    call = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["phase36d_actual_one_shot_llm_draft_call"]
    assert_true(call["available"] is True, "Phase 36D available")
    assert_true(call["manual_approval_required"] is True, "Manual approval required")
    assert_true(call["manual_approval_approved"] is False, "Manual approval not approved")
    assert_true(call["allow_flag_present"] is False, "Allow flag absent")
    assert_true(call["candidate_agent"] == "kasumi", "Kasumi candidate")
    assert_true(call["candidate_agent_allowed"] is True, "Kasumi allowed")
    assert_true(call["allowed_sources"] == ["operation"], "Operation only")
    assert_true(call["ready"] is False, "Default not ready")
    assert_true(call["blocked"] is True, "Default blocked")
    assert_true(call["llm_api_call_attempted"] is False, "No LLM attempt")
    assert_true(call["llm_api_call_count"] == 0, "No LLM count")
    assert_true(call["llm_response_packet_created"] is False, "No packet")
    assert_true(call["output_safety_checked"] is False, "No output safety until call")
    assert_true(call["discord_message_sent"] is False, "No Discord")
    assert_true(call["ready_for_discord_send"] is False, "Discord send false")
    assert_true(call["ready_for_phase36e_closeout"] is False, "No closeout")
    assert_true(call["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase36e_actual_llm_draft_call_closeout_summary() -> None:
    setup_artifacts()
    closeout = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")["phase36e_actual_one_shot_llm_draft_call_closeout"]
    assert_true(closeout["available"] is True, "Phase 36E available")
    assert_true(closeout["report_only"] is True, "Report only")
    assert_true(closeout["phase36d_actual_llm_draft_call_complete"] is True, "36D complete")
    assert_true(closeout["llm_call_count"] == 1, "LLM count one")
    assert_true(closeout["llm_response_packet_created"] is True, "Packet created")
    assert_true(closeout["output_safety_allowed"] is True, "Output allowed")
    assert_true(closeout["discord_message_sent"] is False, "No Discord")
    assert_true(closeout["message_sent_count"] == 0, "No message count")
    assert_true(closeout["ready_for_discord_send"] is False, "Discord send false")
    assert_true(closeout["phase36e_closeout_passed"] is True, "Closeout passed")
    assert_true(closeout["ready_for_phase36f_no_send_final_lock"] is True, "Ready for 36F")
    assert_true(closeout["ready_for_unattended_auto_reply"] is False, "No unattended")


def test_phase36f_g_and_phase37_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    final_lock = report["phase36f_one_shot_llm_no_send_final_lock"]
    dashboard = report["phase36g_post_llm_call_dashboard_lock"]
    gate = report["phase37_entry_gate"]
    assert_true(final_lock["available"] is True, "36F available")
    assert_true(final_lock["report_only"] is True, "36F report only")
    assert_true(final_lock["llm_call_count_locked"] == 1, "36F LLM lock")
    assert_true(final_lock["discord_send_count_locked"] == 0, "36F Discord lock")
    assert_true(final_lock["phase36f_no_send_final_lock_passed"] is True, "36F passed")
    assert_true(final_lock["ready_for_discord_send"] is False, "36F no Discord ready")
    assert_true(final_lock["ready_for_phase37_live_execution"] is False, "36F no live")
    assert_true(dashboard["available"] is True, "36G available")
    assert_true(dashboard["report_only"] is True, "36G report only")
    assert_true(dashboard["total_phase36_llm_call_count"] == 1, "36G LLM count")
    assert_true(dashboard["total_phase36_discord_message_sent_count"] == 0, "36G Discord count")
    assert_true(dashboard["forbidden_behavior_sentinel_passed"] is True, "36G sentinel")
    assert_true(dashboard["ready_for_phase37_entry_gate"] is True, "36G ready for gate")
    assert_true(gate["available"] is True, "37 available")
    assert_true(gate["phase37_not_started"] is True, "37 not started")
    assert_true(gate["requires_explicit_user_approval"] is True, "37 approval required")
    assert_true(gate["ready_for_phase37_live_execution"] is False, "37 no live")
    assert_true(gate["ready_for_discord_send"] is False, "37 no send")


def test_phase37a_b_c_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    review = report["phase37a_private_test_llm_draft_review_packet"]
    preview = report["phase37b_private_test_discord_send_preflight_preview"]
    rehearsal = report["phase37c_private_test_send_approval_rehearsal"]
    assert_true(review["available"] is True, "37A available")
    assert_true(review["report_only"] is True, "37A report only")
    assert_true(review["draft_review_packet_created"] is True, "37A packet")
    assert_true(review["human_review_required"] is True, "37A human review")
    assert_true(review["new_llm_api_call_attempted"] is False, "37A no LLM")
    assert_true(review["discord_message_sent"] is False, "37A no Discord")
    assert_true(review["ready_for_discord_send"] is False, "37A no send ready")
    assert_true(preview["available"] is True, "37B available")
    assert_true(preview["report_only"] is True, "37B report only")
    assert_true(preview["private_test_scope_only"] is True, "37B private")
    assert_true(preview["would_send_preview_created"] is True, "37B preview")
    assert_true(preview["discord_api_send_called"] is False, "37B no API send")
    assert_true(preview["discord_message_sent"] is False, "37B no Discord")
    assert_true(preview["ready_for_actual_private_test_send"] is False, "37B no actual send")
    assert_true(rehearsal["available"] is True, "37C available")
    assert_true(rehearsal["report_only"] is True, "37C report only")
    assert_true(rehearsal["approval_phrase_generated"] is False, "37C no phrase")
    assert_true(rehearsal["manual_approval_actualized"] is False, "37C no approval")
    assert_true(rehearsal["future_send_scope"] == "private_test_only", "37C private")
    assert_true(rehearsal["ready_for_phase37d_actual_private_test_send"] is False, "37C no 37D")
    assert_true(rehearsal["ready_for_discord_send"] is False, "37C no send ready")


def test_phase37d_e_f_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    preflight = report["phase37d_actual_private_test_send_manual_preflight"]
    rehearsal = report["phase37e_mock_private_test_send_rehearsal"]
    lock = report["phase37f_private_test_send_no_send_lock"]
    assert_true(preflight["available"] is True, "37D available")
    assert_true(preflight["report_only"] is True, "37D report only")
    assert_true(preflight["private_test_scope_only"] is True, "37D private")
    assert_true(preflight["manual_approval_required"] is True, "37D manual approval")
    assert_true(preflight["manual_approval_actualized"] is False, "37D no approval")
    assert_true(preflight["discord_api_send_called"] is False, "37D no API send")
    assert_true(preflight["discord_message_sent"] is False, "37D no message")
    assert_true(preflight["ready_for_actual_private_test_send"] is False, "37D no actual send")
    assert_true(rehearsal["available"] is True, "37E available")
    assert_true(rehearsal["report_only"] is True, "37E report only")
    assert_true(rehearsal["mock_send_rehearsal_count"] == 1, "37E mock count")
    assert_true(rehearsal["actual_discord_api_send_called"] is False, "37E no API send")
    assert_true(rehearsal["actual_discord_message_sent"] is False, "37E no message")
    assert_true(rehearsal["ready_for_actual_private_test_send"] is False, "37E no actual send")
    assert_true(lock["available"] is True, "37F available")
    assert_true(lock["report_only"] is True, "37F report only")
    assert_true(lock["mock_send_rehearsal_count_locked"] == 1, "37F mock count locked")
    assert_true(lock["actual_discord_send_count_locked"] == 0, "37F actual send count locked")
    assert_true(lock["phase37f_no_send_lock_passed"] is True, "37F passed")
    assert_true(lock["phase38_not_started"] is True, "37F phase 38 not started")
    assert_true(lock["ready_for_phase38_actual_private_test_send_path"] is False, "37F no phase 38 path")


def test_phase38a_e_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    contract = report["phase38a_actual_private_test_send_contract"]
    freeze = report["phase38b_final_would_send_payload_freeze"]
    rollback = report["phase38c_private_test_send_rollback_gate"]
    checklist = report["phase38d_private_test_send_operator_checklist"]
    gate = report["phase38e_private_test_live_send_entry_gate"]
    assert_true(contract["available"] is True, "38A available")
    assert_true(contract["report_only"] is True, "38A report only")
    assert_true(contract["send_scope"] == "private_test_only", "38A private")
    assert_true(contract["discord_api_send_called"] is False, "38A no API send")
    assert_true(contract["discord_message_sent"] is False, "38A no message")
    assert_true(contract["ready_for_actual_private_test_send"] is False, "38A no actual readiness")
    assert_true(freeze["available"] is True, "38B available")
    assert_true(freeze["report_only"] is True, "38B report only")
    assert_true(freeze["would_send_payload_frozen"] is True, "38B frozen")
    assert_true(freeze["would_send_review_only"] is True, "38B review only")
    assert_true(freeze["discord_message_sent"] is False, "38B no message")
    assert_true(freeze["ready_for_discord_send"] is False, "38B no send ready")
    assert_true(rollback["available"] is True, "38C available")
    assert_true(rollback["report_only"] is True, "38C report only")
    assert_true(rollback["rollback_checklist_ready"] is True, "38C checklist")
    assert_true(rollback["emergency_disable_gates_listed"] is True, "38C gate names")
    assert_true(rollback["discord_message_sent"] is False, "38C no message")
    assert_true(checklist["available"] is True, "38D available")
    assert_true(checklist["report_only"] is True, "38D report only")
    assert_true(checklist["operator_checklist_ready"] is True, "38D ready")
    assert_true(checklist["ready_for_actual_private_test_send"] is False, "38D no actual readiness")
    assert_true(gate["available"] is True, "38E available")
    assert_true(gate["report_only"] is True, "38E report only")
    assert_true(gate["actual_private_test_send_not_started"] is True, "38E not started")
    assert_true(gate["phase39_not_started"] is True, "38E phase39 not started")
    assert_true(gate["requires_explicit_user_approval"] is True, "38E approval required")
    assert_true(gate["ready_for_phase39_live_execution"] is False, "38E no live")


def test_phase39a_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    send_path = report["phase39a_actual_private_test_one_shot_send_path"]
    safety = report["phase39a_actual_private_test_send_safety_gate"]
    blocked = report["phase39a_actual_private_test_send_blocked_report"]
    assert_true(send_path["available"] is True, "39A path available")
    assert_true(send_path["report_only"] is True, "39A report only")
    assert_true(send_path["implementation_only"] is True, "39A implementation only")
    assert_true(send_path["actual_send_executed"] is False, "39A no actual send")
    assert_true(send_path["discord_api_send_called"] is False, "39A no API send")
    assert_true(send_path["discord_message_sent"] is False, "39A no message")
    assert_true(send_path["message_sent_count"] == 0, "39A no message count")
    assert_true(send_path["ready_for_actual_private_test_send"] is False, "39A no ready")
    assert_true(send_path["ready_for_phase39b_manual_one_shot_send"] is False, "39A no 39B ready")
    assert_true(safety["available"] is True, "39A safety available")
    assert_true(safety["actual_send_allowed"] is False, "39A no allow")
    assert_true(safety["actual_send_executed"] is False, "39A no safety execution")
    assert_true(safety["secret_values_logged"] is False, "39A no secrets")
    assert_true(blocked["available"] is True, "39A blocked available")
    assert_true(blocked["blocked"] is True, "39A blocked")
    assert_true(blocked["phase39a_no_execution_policy"] is True, "39A policy")


def test_phase39b_zero_send_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    reentry = report["phase39b_manual_send_reentry_packet"]
    ready = report["phase39b_manual_send_ready_gate"]
    execution = report["phase39b_actual_send_execution_gate"]
    real_selection = report["phase39b_real_adapter_selection"]
    lock = report["phase39b_manual_send_no_send_lock"]
    assert_true(reentry["available"] is True, "39B reentry available")
    assert_true(reentry["report_only"] is True, "39B reentry report only")
    assert_true(reentry["actual_send_executed"] is False, "39B reentry no send")
    assert_true(reentry["discord_api_send_called"] is False, "39B reentry no API")
    assert_true(reentry["discord_message_sent"] is False, "39B reentry no message")
    assert_true(reentry["message_sent_count"] == 0, "39B reentry count 0")
    assert_true(reentry["actual_send_must_be_run_from_same_user_powershell_session"] is True, "39B same shell")
    assert_true(reentry["ready_for_phase39b_actual_send_manual_attempt"] is False, "39B reentry not ready")
    assert_true(ready["available"] is True, "39B ready gate available")
    assert_true(ready["phase39b_manual_execution"] is True, "39B ready manual execution")
    assert_true(ready["phase39a_implementation_only"] is False, "39B ready not 39A only")
    assert_true(ready["manual_approval_actualized"] is True, "39B ready approval")
    assert_true(ready["approval_phrase_exact_match"] is True, "39B ready exact phrase")
    assert_true(ready["ready_for_phase39b_manual_one_shot_send"] is True, "39B ready true")
    assert_true(ready["ready_for_discord_send"] is False, "39B no direct send ready")
    assert_true(ready["actual_private_test_send_executed"] is False, "39B ready no actual send")
    assert_true(ready["discord_api_send_called"] is False, "39B ready no API")
    assert_true(ready["discord_message_sent"] is False, "39B ready no message")
    assert_true(ready["message_sent_count"] == 0, "39B ready count 0")
    assert_true(execution["available"] is True, "39B execution gate available")
    assert_true(execution["report_only"] is True, "39B execution report only")
    assert_true(execution["mode"] == "phase39b_actual_send_execution", "39B execution mode")
    assert_true(execution["execute_flag_present"] is True, "39B execute flag")
    assert_true(execution["real_discord_send_execution_env_enabled"] is False, "39B real env false")
    assert_true(execution["execution_gate_conditions_met"] is True, "39B execution gate met")
    assert_true(execution["actual_execution_adapter"] == "mock", "39B mock adapter")
    assert_true(execution["ready_for_actual_private_test_send"] is True, "39B execution readiness")
    assert_true(execution["ready_for_discord_send"] is False, "39B execution no direct send ready")
    assert_true(execution["actual_private_test_send_executed"] is False, "39B execution no actual send")
    assert_true(execution["discord_api_send_called"] is False, "39B execution no API")
    assert_true(execution["discord_message_sent"] is False, "39B execution no message")
    assert_true(execution["message_sent_count"] == 0, "39B execution count 0")
    assert_true(real_selection["available"] is True, "39B real adapter selection available")
    assert_true(real_selection["mode"] == "phase39b_actual_send_execution", "39B real selection mode")
    assert_true(real_selection["execute_flag_present"] is True, "39B real execute flag")
    assert_true(real_selection["real_discord_send_execution_env_enabled"] is True, "39B real env true")
    assert_true(real_selection["execution_gate_conditions_met"] is True, "39B real gate met")
    assert_true(real_selection["actual_execution_adapter"] == "real", "39B real adapter")
    assert_true(real_selection["real_adapter_selected"] is True, "39B real selected")
    assert_true(real_selection["real_adapter_injected_for_test"] is True, "39B real injected")
    assert_true(real_selection["real_adapter_called"] is True, "39B real adapter called")
    assert_true(real_selection["ready_for_actual_private_test_send"] is True, "39B real readiness")
    assert_true(real_selection["ready_for_discord_send"] is False, "39B real no direct send ready")
    assert_true(real_selection["actual_private_test_send_executed"] is False, "39B real no actual send in viewer")
    assert_true(real_selection["discord_api_send_called"] is False, "39B real no API in viewer")
    assert_true(real_selection["discord_message_sent"] is False, "39B real no message in viewer")
    assert_true(real_selection["message_sent_count"] == 0, "39B real count 0")
    assert_true(real_selection["ready_for_phase39c_send_closeout"] is False, "39B real no closeout without send")
    assert_true(lock["available"] is True, "39B no-send lock available")
    assert_true(lock["report_only"] is True, "39B lock report only")
    assert_true(lock["actual_discord_send_count"] == 0, "39B actual send count 0")
    assert_true(lock["phase39c_closeout_not_available"] is True, "39C unavailable")
    assert_true(lock["ready_for_phase39c_send_closeout"] is False, "39C not ready")


def test_phase39c_closeout_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    closeout = report["phase39c_actual_send_closeout"]
    no_repeat = report["phase39c_no_repeat_send_lock"]
    safety = report["phase39c_post_send_safety_audit"]
    push = report["phase39c_push_readiness"]
    assert_true(closeout["available"] is True, "39C closeout available")
    assert_true(closeout["report_only"] is True, "39C closeout report")
    assert_true(closeout["phase39b_actual_send_success"] is True, "39B success")
    assert_true(closeout["actual_discord_send_count"] == 1, "39C observed count")
    assert_true(closeout["phase39c_additional_send_count"] == 0, "39C no additional")
    assert_true(closeout["phase39c_closeout_completed"] is True, "39C closeout complete")
    assert_true(no_repeat["available"] is True, "39C no-repeat available")
    assert_true(no_repeat["actual_discord_send_count_locked"] == 1, "39C locked count")
    assert_true(no_repeat["repeat_send_allowed"] is False, "39C repeat false")
    assert_true(no_repeat["automatic_retry_allowed"] is False, "39C auto retry false")
    assert_true(no_repeat["ready_for_repeat_send"] is False, "39C ready repeat false")
    assert_true(safety["available"] is True, "39C safety available")
    assert_true(safety["gate_off_verified"] is True, "39C gate off")
    assert_true(safety["total_actual_discord_send_count_this_sequence"] == 1, "39C total count")
    assert_true(safety["public_team_forbidden"] is True, "39C public/team forbidden")
    assert_true(safety["unattended_auto_reply_allowed"] is False, "39C unattended false")
    assert_true(push["available"] is True, "39C push available")
    assert_true(push["remote_push_required"] is True, "39C push required")
    assert_true(push["push_executed_by_codex"] is False, "Codex no push")


def test_phase40_runtime_readiness_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    state = report["phase40_post_phase39_state_audit"]
    plan = report["phase40_private_test_runtime_plan"]
    replay = report["phase40_inbound_event_replay_dry_run"]
    decision = report["phase40_reply_decision_audit"]
    queue = report["phase40_outbound_queue_lock"]
    idempotency = report["phase40_session_idempotency_lock"]
    handoff = report["phase40_operator_handoff_packet"]
    entry_gate = report["phase40_live_runtime_entry_gate"]
    summary = report["phase40_safe_overnight_summary"]
    assert_true(state["available"] is True, "40A available")
    assert_true(state["actual_discord_send_count_locked"] == 1, "40A locked count")
    assert_true(state["ready_for_live_runtime_execution"] is False, "40A not live")
    assert_true(plan["runtime_scope"] == "private_test_only", "40B scope")
    assert_true(plan["live_runtime_started"] is False, "40B no runtime")
    assert_true(replay["uses_recorded_or_synthetic_events_only"] is True, "40C synthetic")
    assert_true(replay["message_sent_count"] == 0, "40C no send")
    assert_true(decision["reply_text_generated"] is False, "40D no generation")
    assert_true(decision["discord_message_sent"] is False, "40D no send")
    assert_true(queue["send_worker_enabled"] is False, "40E worker off")
    assert_true(queue["repeat_send_allowed"] is False, "40E repeat off")
    assert_true(idempotency["one_reply_per_human_message"] is True, "40F one reply")
    assert_true(idempotency["duplicate_message_id_guard"] is True, "40F dedupe")
    assert_true(handoff["operator_must_confirm_before_live_runtime"] is True, "40G operator confirm")
    assert_true(entry_gate["live_runtime_start_allowed"] is False, "40H blocked")
    assert_true(summary["safe_to_review_next_morning"] is True, "40I safe")


def test_phase40j_n_readonly_runtime_entry_summaries() -> None:
    setup_artifacts()
    report = build_operations_packet_viewer_report(TEST_ROOT, date="20260613")
    preflight = report["phase40j_private_test_readonly_runtime_preflight"]
    launch = report["phase40k_readonly_runtime_launch_packet"]
    closeout = report["phase40l_live_capture_closeout_packet"]
    abort = report["phase40m_runtime_abort_kill_switch_packet"]
    gate = report["phase40n_phase41_reply_runtime_entry_gate"]
    assert_true(preflight["available"] is True, "40J available")
    assert_true(preflight["report_only"] is True, "40J report")
    assert_true(preflight["live_runtime_started"] is False, "40J no runtime")
    assert_true(preflight["ready_for_manual_readonly_runtime_launch"] is False, "40J not launch ready")
    assert_true(launch["available"] is True, "40K available")
    assert_true(launch["manual_launch_only"] is True, "40K manual")
    assert_true(launch["codex_must_not_launch"] is True, "40K codex no launch")
    assert_true(closeout["available"] is True, "40L available")
    assert_true(closeout["live_capture_observed"] is False, "40L no capture")
    assert_true(closeout["captured_event_count"] == 0, "40L no events")
    assert_true(abort["available"] is True, "40M available")
    assert_true(abort["manual_abort_available"] is True, "40M abort")
    assert_true(gate["available"] is True, "40N available")
    assert_true(gate["phase41_reply_runtime_allowed"] is False, "40N blocked")


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
        test_rag_evidence_private_test_send_closeout_summary,
        test_rag_evidence_private_test_e2e_preflight_summary,
        test_rag_evidence_private_test_e2e_replay_summary,
        test_rag_evidence_private_test_e2e_live_reply_summary,
        test_rag_evidence_private_test_e2e_send_retry_summary,
        test_rag_evidence_private_test_e2e_live_closeout_summary,
        test_rag_evidence_private_test_phase34_final_lock_summary,
        test_phase35a_post_mvp_safety_audit_summary,
        test_phase35b_summaries,
        test_phase35c_summaries,
        test_phase35d_summaries,
        test_phase35e_g_and_phase36_summaries,
        test_phase36a_preflight_summary,
        test_phase36b_mock_and_safety_summary,
        test_phase36c_actual_llm_call_preflight_summary,
        test_phase36d_actual_llm_draft_call_summary,
        test_phase36e_actual_llm_draft_call_closeout_summary,
        test_phase36f_g_and_phase37_summaries,
        test_phase37a_b_c_summaries,
        test_phase37d_e_f_summaries,
        test_phase38a_e_summaries,
        test_phase39a_summaries,
        test_phase39b_zero_send_summaries,
        test_phase39c_closeout_summaries,
        test_phase40_runtime_readiness_summaries,
        test_phase40j_n_readonly_runtime_entry_summaries,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All operations packet viewer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

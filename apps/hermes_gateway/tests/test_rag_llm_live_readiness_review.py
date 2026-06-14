"""Phase 33D live readiness review tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from operations_packet_viewer import build_operations_packet_viewer_report
from rag_llm_live_readiness_review import build_rag_llm_live_readiness_review, render_rag_llm_live_readiness_markdown


LONG_ID_RE = re.compile(r"\b\d{15,25}\b")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_default_go_false() -> None:
    assert_true(build_rag_llm_live_readiness_review()["go"] is False, "Review phase should be no-go")


def test_no_go_reasons() -> None:
    reasons = build_rag_llm_live_readiness_review()["no_go_reasons"]
    assert_true("manual_approval_required" in reasons, "Manual approval required")
    assert_true("live_runtime_not_enabled_by_review_phase" in reasons, "Runtime not enabled")


def test_all_scaffold_components_represented() -> None:
    components = build_rag_llm_live_readiness_review()["ready_components"]
    for key in ("rag_preflight", "local_readonly_retrieval", "rag_response_packet", "rag_context_safety", "rag_llm_prompt_envelope", "rag_llm_would_send_preview", "rag_llm_replay"):
        assert_true(key in components, f"Missing component {key}")


def test_required_live_gates() -> None:
    gates = build_rag_llm_live_readiness_review()["required_live_gates"]
    for key in (
        "private_test_channel_id_required",
        "source_validation_required",
        "rag_context_safety_required",
        "rag_response_packet_required",
        "llm_output_safety_required",
        "cooldown_required",
        "budget_required",
        "circuit_breaker_required",
    ):
        assert_true(gates[key] is True, f"{key} should be required")


def test_forbidden_scope() -> None:
    forbidden = build_rag_llm_live_readiness_review()["forbidden_live_scope"]
    assert_true(forbidden["public_team_channel_reply"] is True, "Public/team channel forbidden")
    assert_true(forbidden["source_operations"] is True, "operations forbidden")
    assert_true(forbidden["channel_name_only_allow"] is True, "Channel-name-only allow forbidden")


def test_actual_execution_flags_false() -> None:
    report = build_rag_llm_live_readiness_review()
    assert_true(report["actual_discord_send"] is False, "No Discord send")
    assert_true(report["actual_llm_api_call"] is False, "No LLM API")
    assert_true(report["embedding_api_called"] is False, "No embedding")
    assert_true(report["external_execution"] is False, "No external execution")


def test_no_secret_or_raw_id() -> None:
    text = json.dumps(build_rag_llm_live_readiness_review(), ensure_ascii=False).lower()
    assert_true("sk-" not in text and "token=" not in text and "xoxb-" not in text, "No secret")
    assert_true(not LONG_ID_RE.search(text), "No raw Discord ID")


def test_markdown_render_works() -> None:
    markdown = render_rag_llm_live_readiness_markdown(build_rag_llm_live_readiness_review())
    assert_true("STOXL RAG+LLM Live Readiness Review" in markdown, "Markdown should render")
    assert_true("Go: false" in markdown, "Markdown should show go false")


def test_operations_viewer_includes_readiness_summary() -> None:
    viewer = build_operations_packet_viewer_report()
    readiness = viewer["rag_llm_live_readiness_review"]
    assert_true(readiness["available"] is True, "Readiness available")
    assert_true(readiness["go"] is False, "Viewer go false")
    assert_true(readiness["ready_for_manual_phase33d_implementation_request"] is True, "Manual implementation request ready")
    assert_true(readiness["actual_discord_send"] is False, "Viewer no send")
    assert_true(readiness["actual_llm_api_call"] is False, "Viewer no LLM")


def main() -> int:
    tests = [
        test_default_go_false,
        test_no_go_reasons,
        test_all_scaffold_components_represented,
        test_required_live_gates,
        test_forbidden_scope,
        test_actual_execution_flags_false,
        test_no_secret_or_raw_id,
        test_markdown_render_works,
        test_operations_viewer_includes_readiness_summary,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All RAG+LLM live readiness review tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

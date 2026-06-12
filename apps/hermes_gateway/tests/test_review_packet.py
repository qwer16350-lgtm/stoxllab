"""Local approval review packet tests.

Run without pytest:
  python apps\hermes_gateway\tests\test_review_packet.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from replay import run_replay
from review_packet import build_review_packet, export_review_packet, render_review_packet_markdown


ROOT = APP_DIR.parents[1]
EVENTS = ROOT / "apps" / "hermes_gateway" / "examples" / "review_packet_events.example.json"
ACTIONS = ROOT / "apps" / "hermes_gateway" / "examples" / "review_packet_actions.example.json"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def packet_with_actions() -> dict:
    return build_review_packet(run_replay(EVENTS, ACTIONS))


def test_review_packet_created() -> None:
    packet = packet_with_actions()
    assert_true(packet["packet_type"] == "approval_review_packet", "Packet type should match")


def test_approval_items_present() -> None:
    packet = packet_with_actions()
    assert_true(len(packet["items"]) >= 1, "Review packet should include approval items")


def test_medium_and_high_risk_present() -> None:
    risks = {item["risk_level"] for item in packet_with_actions()["items"]}
    assert_true("medium" in risks, "Medium risk item should be present")
    assert_true("high" in risks, "High risk item should be present")


def test_secret_request_redacted() -> None:
    text = json.dumps(packet_with_actions(), ensure_ascii=False)
    assert_true("sk-review-secret" not in text, "Secret literal should be redacted")
    assert_true("[REDACTED]" in text, "Redaction marker should be present")


def test_markdown_required_sections() -> None:
    md = render_review_packet_markdown(packet_with_actions())
    for section in [
        "# STOXL Approval Review Packet",
        "## Summary",
        "## Decision Maker Notice",
        "## Pending / Decided Items",
        "## Safety Assertions",
        "## What This Packet Does Not Do",
    ]:
        assert_true(section in md, f"Markdown should include {section}")


def test_external_execution_count_zero() -> None:
    packet = packet_with_actions()
    assert_true(packet["summary"]["external_execution_count"] == 0, "External execution count must stay zero")


def test_approved_item_external_execution_false() -> None:
    packet = packet_with_actions()
    approved = [item for item in packet["items"] if item["status"] == "approved"]
    assert_true(approved, "There should be an approved mock item")
    assert_true(all(item["external_execution_allowed"] is False for item in approved), "Approved items must not allow external execution")


def test_dry_run_export_creates_no_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "review_packets"
        packet = packet_with_actions()
        summary = export_review_packet(packet, root, dry_run=True)
        assert_true(summary["exported"] is False, "Dry-run export should not write files")
        assert_true(not root.exists(), "Dry-run export should not create export root")


def test_actual_export_creates_json_and_md() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "review_packets"
        summary = export_review_packet(packet_with_actions(), root)
        assert_true(Path(summary["json_path"]).exists(), "JSON review packet should be exported")
        assert_true(Path(summary["markdown_path"]).exists(), "Markdown review packet should be exported")


def test_existing_tests_can_coexist() -> None:
    packet = packet_with_actions()
    assert_true(packet["summary"]["total_events"] >= 6, "Replay summary should remain available")


def main() -> int:
    tests = [
        test_review_packet_created,
        test_approval_items_present,
        test_medium_and_high_risk_present,
        test_secret_request_redacted,
        test_markdown_required_sections,
        test_external_execution_count_zero,
        test_approved_item_external_execution_false,
        test_dry_run_export_creates_no_files,
        test_actual_export_creates_json_and_md,
        test_existing_tests_can_coexist,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("All review packet tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

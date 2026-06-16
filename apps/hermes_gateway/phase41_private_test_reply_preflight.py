"""Phase 41A private-test reply runtime preflight only."""

from __future__ import annotations

from typing import Any, Mapping

from phase40y_phase41_reply_preflight_gate import (
    build_phase40y_phase41_reply_preflight_gate,
    render_phase40y_phase41_reply_preflight_gate_markdown,
)


def build_phase41_private_test_reply_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    gate = build_phase40y_phase41_reply_preflight_gate(env=env)
    report = dict(gate)
    report["report_type"] = "phase41_private_test_reply_preflight"
    report["version"] = "phase41_private_test_reply_preflight"
    report["ready_for_manual_private_test_reply"] = bool(report.get("ready_for_phase41_manual_private_test_reply"))
    return report


def render_phase41_private_test_reply_preflight_markdown(report: Mapping[str, Any]) -> str:
    return render_phase40y_phase41_reply_preflight_gate_markdown(report).replace("Phase 40Y Phase 41 Reply Preflight Gate", "Phase 41 Private-test Reply Preflight")

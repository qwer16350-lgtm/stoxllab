"""Phase 40T CLI command wrapper for private-test read-only runtime."""

from __future__ import annotations

from typing import Any, Mapping

from private_test_readonly_runtime import (
    build_private_test_readonly_runtime_preflight,
    render_private_test_readonly_runtime_preflight_markdown,
)


VERSION = "phase40t_private_test_readonly_runtime_command"


def build_phase40t_private_test_readonly_runtime_command(
    env: Mapping[str, str] | None = None,
    *,
    report_only: bool = False,
) -> dict[str, Any]:
    report = build_private_test_readonly_runtime_preflight(env=env, report_only=report_only)
    report["version"] = VERSION
    return report


def render_phase40t_private_test_readonly_runtime_command_markdown(report: dict[str, Any]) -> str:
    return render_private_test_readonly_runtime_preflight_markdown(report)

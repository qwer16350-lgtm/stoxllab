"""Phase 40T CLI command wrapper for private-test read-only runtime."""

from __future__ import annotations

from typing import Any, Mapping

from private_test_readonly_live_runner import ReadOnlyLiveAdapter, run_phase40t_readonly_live_runtime
from private_test_readonly_runtime import (
    build_private_test_readonly_runtime_preflight,
    render_private_test_readonly_runtime_preflight_markdown,
)
from phase40t_readonly_runtime_closeout import render_phase40t_readonly_runtime_closeout_markdown
from phase40t_readonly_live_execution_gate import render_phase40t_readonly_live_execution_gate_markdown
from phase40t_discord_login_failure_closeout import (
    build_phase40t_discord_login_failure_closeout,
    build_phase40t_missing_env_before_login_closeout,
    render_phase40t_discord_login_failure_closeout_markdown,
)
from phase40t_readonly_preflight_snapshot import snapshot_has_login_prerequisites


VERSION = "phase40t_private_test_readonly_runtime_command"


def build_phase40t_private_test_readonly_runtime_command(
    env: Mapping[str, str] | None = None,
    *,
    report_only: bool = False,
    execute_flag_present: bool = False,
    timeout_seconds: int = 60,
    max_events: int = 10,
    capture_root: str | None = None,
    root: str | None = None,
    adapter: ReadOnlyLiveAdapter | None = None,
) -> dict[str, Any]:
    if execute_flag_present:
        return run_phase40t_readonly_live_runtime(
            env=env,
            execute_flag_present=True,
            timeout_seconds=timeout_seconds,
            max_events=max_events,
            capture_root=capture_root,
            root=root,
            adapter=adapter,
        )
    report = build_private_test_readonly_runtime_preflight(env=env, report_only=report_only)
    report["version"] = VERSION
    report["execute_flag_present"] = False
    return report


def build_phase40t_discord_login_failure_closeout_command(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    preflight = build_private_test_readonly_runtime_preflight(env=env, report_only=True)
    snapshot = preflight.get("preflight_snapshot")
    if not snapshot_has_login_prerequisites(snapshot if isinstance(snapshot, dict) else None):
        return build_phase40t_missing_env_before_login_closeout(
            env=env,
            preflight_snapshot=snapshot if isinstance(snapshot, dict) else None,
            execute_flag_present=True,
        )
    return build_phase40t_discord_login_failure_closeout(
        env=env,
        preflight_snapshot=snapshot if isinstance(snapshot, dict) else None,
        execute_flag_present=True,
        preflight_passed=bool(preflight.get("preflight_passed")),
    )


def render_phase40t_private_test_readonly_runtime_command_markdown(report: dict[str, Any]) -> str:
    if report.get("report_type") == "phase40t_readonly_runtime_closeout":
        return render_phase40t_readonly_runtime_closeout_markdown(report)
    if report.get("report_type") == "phase40t_discord_login_failure_closeout":
        return render_phase40t_discord_login_failure_closeout_markdown(report)
    if report.get("report_type") == "phase40t_readonly_live_execution_gate":
        return render_phase40t_readonly_live_execution_gate_markdown(report)
    return render_private_test_readonly_runtime_preflight_markdown(report)

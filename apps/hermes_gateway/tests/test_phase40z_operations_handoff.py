from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from phase40z_operations_handoff import build_phase40z_operations_handoff


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_phase40z_handoff_summary() -> None:
    report = build_phase40z_operations_handoff()
    assert_true(report["phase40t_gateway_connect_verified"] is True, "Gateway verified")
    assert_true(report["phase40u_closeout_ready"] is True, "40U ready")
    assert_true(report["phase40x_reply_dry_run_ready"] is True, "40X ready")
    assert_true(report["phase41_actual_reply_default_blocked"] is True, "Phase 41 blocked")
    assert_true(report["ready_for_actual_reply_send"] is False, "No actual reply send")
    assert_true(report["discord_api_send_called"] is False, "No API")
    assert_true(report["discord_message_sent"] is False, "No message")
    assert_true(report["message_sent_count"] == 0, "Count 0")


def main() -> int:
    test_phase40z_handoff_summary()
    print("PASS test_phase40z_handoff_summary")
    print("All Phase 40Z operations handoff tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# STOXL Actual Private-test One-shot Send Path

Phase 39A adds the structure for a future actual private-test one-shot send path,
but the default path is blocked and report-only.

This phase does not run a Discord live runtime, does not call Discord send, and
does not send a message. The actual send remains reserved for a later Phase 39B
manual request with a separate prompt, explicit approval, and separate command.

Phase 39A Hotfix 1 adds parser support for
`--allow-actual-private-test-send`. The flag only marks
`allow_flag_present=true` in the report. It does not start Discord, does not
call Discord API send, and does not send a message.

Phase 39B-0 adds a manual re-entry packet and no-send lock. It documents that a
future actual send must be run from the same user PowerShell session where
token/channel env presence is true. Phase 39B-0 does not run the actual send and
keeps Phase 39C closeout unavailable.

Phase 39B Hotfix 2 separates the default Phase 39A blocked mode from the Phase
39B manual readiness gate. When the allow flag and every env/manual gate are
present, the report can enter `phase39b_manual_ready_gate` with
`ready_for_phase39b_manual_one_shot_send=true`. This readiness state still does
not call Discord API send and still keeps `ready_for_discord_send=false`.

Phase 39B Hotfix 3 adds a second explicit flag,
`--execute-actual-private-test-send`, to separate readiness from execution-mode
intent. With the allow flag, exact manual approval gates, and this execute flag,
the report may enter `phase39b_actual_send_execution`. In this hotfix the
execution adapter is `mock`: `ready_for_actual_private_test_send=true` can be
reported, but `ready_for_discord_send=false`, `discord_api_send_called=false`,
`discord_message_sent=false`, and `message_sent_count=0` remain locked.

`HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION` is reserved for a later separately
approved implementation. This document and report only expose its boolean
enabled state, never secret values.

The approval phrase is compared by exact code constant. Reports must show only
presence and exact-match booleans, never the approval phrase value.

Safety state:

- Actual send path available: true
- Phase 39A implementation only: true
- Actual private-test send executed: false
- Discord API send called: false
- Discord message sent: false
- Message sent count: 0
- Ready for actual private-test send: false
- Ready for Discord send: false
- Ready for Phase 39B manual one-shot send: false
- Phase 39B actual execution adapter: mock when execute gate is explicitly met

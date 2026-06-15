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

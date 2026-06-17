# STOXL Phase 42 Supervised Private-test Session

Phase 42 adds a deterministic supervised private-test session preflight and a
manual-gated actual supervised-session runtime CLI. The runtime gate is blocked
by default and requires an explicit allow flag before it can select an adapter.

The scaffold requires manual approval, exact approval phrase, max session messages, max reply/send counts, timeout, cooldown, private-test-only mode, deterministic/frozen reply mode, session lock, duplicate/self/bot guards, and disabled LLM/RAG/embedding/external execution before a later manual phase can consider a supervised session.

This safe bundle does not open the Phase 42 manual gate, does not run a live runtime, does not call Discord API send, and sends no Discord messages. Phase 41B repeat send remains locked. The next actual operation must be a separate Manual Gate 2 request for the Phase 42 supervised deterministic private-test session.

Phase 42-0 hotfix updates the preflight to read the current process environment
when no test env mapping is injected. The CLI diagnostics command prints only
booleans and counts:

```powershell
python apps\hermes_gateway\cli.py --phase42-env-diagnostics --json
python apps\hermes_gateway\cli.py --phase42-supervised-private-test-session-preflight --json
python apps\hermes_gateway\cli.py --phase42-supervised-private-test-session --json
```

When all Phase 42 process-env gates are present, the preflight may report
`manual_gate_open=true` and `ready_for_phase42_manual_supervised_session=true`.
That is readiness only: actual runtime execution, Discord API send, Discord
message sent, LLM/RAG/embedding, and external execution remain false.

Phase 42-1 adds:

- `--phase42-supervised-private-test-session`
- `--allow-actual-phase42-supervised-session`

Without the allow flag, the runtime CLI returns a blocked report with
`actual_runtime_executed=false`, `discord_api_send_called=false`,
`discord_message_sent=false`, and `message_sent_count=0`. Tests exercise only a
fake adapter success/blocked contract. The real Discord adapter boundary is
wired for a later Manual Gate 2 run, but this safe bundle does not invoke it.

Phase 42 actual supervised private-test session has now been observed as a
successful separate Manual Gate 2 operation with `message_sent_count=1`,
`sent_scope=private_test_only`, and `session_lock_consumed=true`. The repeat
supervised-session lock is now active. Safe Mega Bundle 3 records that closeout
only and performs no additional Discord runtime/send.

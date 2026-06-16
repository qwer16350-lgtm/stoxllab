# STOXL Phase 41B Private-test Reply One-shot

Phase 41B adds a safe-prep report for a future actual private-test deterministic reply one-shot. The default command is blocked and performs no Discord login, API send, message send, LLM call, RAG call, embedding, vector creation, or external execution.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase41-private-test-reply-one-shot --json
python apps\hermes_gateway\cli.py --phase41b-env-diagnostics --json
```

The future manual gate requires token presence, private-test channel presence, explicit manual approval, exact approval phrase match, send flags, private-test-only reply mode, one-shot lock availability, and self/bot/duplicate/public/team guards. The report records only booleans, never secret values, raw Discord IDs, raw content, or approval phrase values.

Phase 41B-0 hotfix reads these process environment keys directly when no test env mapping is injected: `DISCORD_BOT_TOKEN`, `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID`, `HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED`, `HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE`, `HERMES_DISCORD_SEND_MESSAGES`, `HERMES_DISCORD_PRIVATE_TEST_REPLY`, `HERMES_DISCORD_REPLY_MODE`, `HERMES_LLM_DISCORD_SEND_ENABLED`, `HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED`, `HERMES_DISCORD_RAG_ENABLED`, `HERMES_LLM_RAG_ENABLED`, and `HERMES_RAG_LLM_REPLY_ENABLED`. Blocked reasons use failure names such as `token_missing`, `approval_phrase_mismatch`, and `reply_mode_not_private_test_only`.

Phase 41B-1 separates safe prep from the actual runtime path. The default command remains preflight/report-only. The actual runtime path is available only when the manual `--allow-actual-private-test-reply` flag and every gate are true; Codex must not run that command in this implementation phase. Runtime tests use `FakePhase41BReplyAdapter` only and verify one deterministic private-test reply, timeout/no-message, self/bot/duplicate/public/team guards, and one-shot lock blocking.

Phase 41B-2 hotfix wires the real Discord reply adapter after a manual attempt
found an eligible private-test human message but failed the send path with a
sanitized `RuntimeError`. The cause was the real adapter trying to send from a
message object after the collection client had already closed. The real adapter
now records only a private send target internally and performs the manual-gated
send through a fresh private-test channel `send(...)` path. Reports classify the
old failure shape as `adapter_not_wired_or_contract_error` without logging the
error value, token, channel ID, approval phrase, raw Discord IDs, session IDs,
or raw content. This hotfix does not run the actual flag, does not call Discord
API send, and does not send a Discord message; tests use fake adapters only.

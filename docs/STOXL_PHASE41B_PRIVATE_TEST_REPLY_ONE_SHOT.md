# STOXL Phase 41B Private-test Reply One-shot

Phase 41B adds a safe-prep report for a future actual private-test deterministic reply one-shot. The default command is blocked and performs no Discord login, API send, message send, LLM call, RAG call, embedding, vector creation, or external execution.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase41-private-test-reply-one-shot --json
python apps\hermes_gateway\cli.py --phase41b-env-diagnostics --json
```

The future manual gate requires token presence, private-test channel presence, explicit manual approval, exact approval phrase match, send flags, private-test-only reply mode, one-shot lock availability, and self/bot/duplicate/public/team guards. The report records only booleans, never secret values, raw Discord IDs, raw content, or approval phrase values.

Phase 41B-0 hotfix reads these process environment keys directly when no test env mapping is injected: `DISCORD_BOT_TOKEN`, `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID`, `HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVED`, `HERMES_PHASE41B_PRIVATE_TEST_REPLY_APPROVAL_PHRASE`, `HERMES_DISCORD_SEND_MESSAGES`, `HERMES_DISCORD_PRIVATE_TEST_REPLY`, `HERMES_DISCORD_REPLY_MODE`, `HERMES_LLM_DISCORD_SEND_ENABLED`, `HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED`, `HERMES_DISCORD_RAG_ENABLED`, `HERMES_LLM_RAG_ENABLED`, and `HERMES_RAG_LLM_REPLY_ENABLED`. Blocked reasons use failure names such as `token_missing`, `approval_phrase_mismatch`, and `reply_mode_not_private_test_only`.

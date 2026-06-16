# STOXL Phase 41B Private-test Reply One-shot

Phase 41B adds a safe-prep report for a future actual private-test deterministic reply one-shot. The default command is blocked and performs no Discord login, API send, message send, LLM call, RAG call, embedding, vector creation, or external execution.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase41-private-test-reply-one-shot --json
```

The future manual gate requires token presence, private-test channel presence, explicit manual approval, exact approval phrase match, send flags, private-test-only reply mode, one-shot lock availability, and self/bot/duplicate/public/team guards. The report records only booleans, never secret values, raw Discord IDs, raw content, or approval phrase values.

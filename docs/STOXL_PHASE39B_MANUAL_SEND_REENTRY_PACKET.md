# STOXL Phase 39B Manual Send Re-entry Packet

Phase 39B-0 is a report-only re-entry packet before any actual private-test
one-shot Discord send.

The observed blocker is session separation:

- The user's PowerShell process may load `.env` values into its own process env.
- Codex runs in a different process context and may not see those values.
- Therefore the actual send must be run by the user from the same PowerShell
  session where token/channel presence is true.

This document does not print token, channel ID, approval phrase, API key, raw
Discord ID, `.env` content, or full message content.

Phase 39B Hotfix 2 adds a readiness gate before any actual send. The readiness
gate can confirm that all manual/env conditions are satisfied, but it still does
not execute Discord API send. The actual send remains a separate user-run action
from the same PowerShell session.

Allowed next-phase command, for a separately approved manual run only:

```powershell
python apps\hermes_gateway\cli.py --actual-private-test-one-shot-send --json --allow-actual-private-test-send
```

Safety state:

- Report only: true
- Discord live runtime executed: false
- Discord API send called: false
- Discord message sent: false
- Message sent count: 0
- Actual private-test send executed: false
- OpenRouter/LLM API call attempted: false
- RAG called: false
- Embedding/vector created: false
- External execution: false
- Public/team send or reply allowed: false
- Unattended auto reply allowed: false
- Repeat send allowed: false
- Automatic retry allowed: false
- Ready for Phase 39B actual send manual attempt: false
- Ready for Phase 39C send closeout: false

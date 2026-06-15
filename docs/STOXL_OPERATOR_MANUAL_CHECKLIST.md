# STOXL Operator Manual Checklist

Phase 35E adds a report-only operator checklist for a no-live rehearsal.

## Safety State

- Discord live runtime executed: false
- Discord message sent: false
- OpenRouter or LLM API called: false
- Approval phrase generated: false
- Approval phrase value logged: false
- Manual approval activated: false
- Ready for actual approval: false
- Ready for live runtime: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## CLI

```powershell
python apps\hermes_gateway\cli.py --operator-manual-checklist --json
python apps\hermes_gateway\cli.py --operator-manual-checklist --markdown
```

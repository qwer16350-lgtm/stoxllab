# STOXL No-live Rehearsal Packet

Phase 35E adds a no-live rehearsal packet. It combines the operator checklist
and manual approval packet preview without enabling any live gate.

## Safety State

- Live runtime executed: false
- LLM called: false
- Discord message sent: false
- Approval phrase generated: false
- Ready for actual approval: false
- Ready for live runtime: false
- Ready for LLM call: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## CLI

```powershell
python apps\hermes_gateway\cli.py --no-live-rehearsal-packet --json
python apps\hermes_gateway\cli.py --no-live-rehearsal-packet --markdown
```

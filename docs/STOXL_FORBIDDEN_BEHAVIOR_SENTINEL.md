# STOXL Forbidden Behavior Sentinel

Phase 35G adds a regression sentinel for forbidden behavior. The sentinel fails
if a dangerous capability is accidentally enabled.

## Locked False

- Public channel reply
- Team channel reply
- Public channel send
- Team channel send
- Unattended auto reply
- Scheduler auto reply
- Embedding API call
- Vector index creation
- External execution
- Full content dump
- Approval phrase generation
- API key, token, raw Discord ID, or approval phrase value logging

## CLI

```powershell
python apps\hermes_gateway\cli.py --forbidden-behavior-sentinel --json
python apps\hermes_gateway\cli.py --forbidden-behavior-sentinel --markdown
```

## Phase 36A Use

The Phase 36A preflight depends on this sentinel staying green. Public/team
send/reply, unattended auto reply, embeddings, external execution, full content
dumps, and secret logging remain forbidden.

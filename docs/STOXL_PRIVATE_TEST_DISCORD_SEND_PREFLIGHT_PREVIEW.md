# STOXL Private-test Discord Send Preflight Preview

Phase 37B creates a no-send private-test Discord send preflight preview.

## Scope

- Private-test scope only: true
- Public/team send and reply: false
- Token value logged: false
- Private-test channel ID value logged: false
- Would-send preview is review-only
- External action claim: false

Token and channel ID presence may be reported as booleans, but values must not
be printed.

## Safety State

- Discord API send allowed: false
- Discord API send called: false
- Discord message sent: false
- Ready for actual private-test send: false
- Ready for Discord send: false

## CLI

```powershell
python apps\hermes_gateway\cli.py --private-test-discord-send-preflight-preview --json
python apps\hermes_gateway\cli.py --private-test-discord-send-preflight-preview --markdown
```

Phase 37D-F consumes this preview only for manual preflight, mock rehearsal, and
no-send lock reports. It does not start Discord, call a send API, or mark Phase
38 actual private-test send ready.

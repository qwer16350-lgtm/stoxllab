# STOXL Phase 40H Live Runtime Entry Gate

Phase 40H exposes a future live runtime gate but keeps it blocked by default. It does not start Discord runtime.

Future flag names:

- HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVED=true.
- HERMES_PHASE40_PRIVATE_TEST_LIVE_RUNTIME_APPROVAL_PHRASE exact.
- HERMES_DISCORD_SEND_MESSAGES=false for read-only runtime.
- HERMES_DISCORD_PRIVATE_TEST_REPLY=false until reply phase.

No actual approval phrase value, token, private test channel ID, API key, or raw Discord ID is printed.

Current state:

- Live runtime entry gate available: true.
- Live runtime start allowed: false.
- Discord Gateway connected: false.
- Discord API send called: false.
- Discord message sent: false.
- Ready for live runtime execution: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40-live-runtime-entry-gate --json
```

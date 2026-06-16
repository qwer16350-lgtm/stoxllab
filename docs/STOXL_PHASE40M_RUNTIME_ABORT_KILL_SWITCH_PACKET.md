# STOXL Phase 40M Runtime Abort Kill-switch Packet

Phase 40M defines abort and kill-switch expectations for a future read-only live runtime. It is report-only and performs no runtime action.

Abort triggers:

- Any send attempt.
- Public/team channel event.
- Unexpected reply mode.
- LLM enabled.
- RAG enabled.
- External execution enabled.

Kill-switch env names:

- HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED=false.
- HERMES_DISCORD_SEND_MESSAGES=false.
- HERMES_DISCORD_PRIVATE_TEST_REPLY=false.
- HERMES_DISCORD_REPLY_MODE=.

Current state:

- Discord API send called: false.
- Discord message sent: false.
- LLM/RAG/embedding/external: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40m-runtime-abort-kill-switch-packet --json
```

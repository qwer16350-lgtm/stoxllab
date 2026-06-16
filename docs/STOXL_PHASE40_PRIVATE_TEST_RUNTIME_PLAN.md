# STOXL Phase 40B Private-test Runtime Plan

Phase 40B describes the future private-test runtime guard plan without starting that runtime. It is a readiness document and report-only CLI path.

Planned guards:

- Private-test channel ID only.
- Self-message guard.
- Bot-message guard.
- Duplicate message ID guard.
- One reply per human message.
- Manual operator abort.
- No public/team send.
- No unattended auto reply.
- No LLM by default.
- No RAG by default.

Safety state:

- Live runtime started: false.
- Discord Gateway connected: false.
- Discord API send called: false.
- Discord message sent: false.
- Ready for live runtime execution: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40-private-test-runtime-plan --json
```

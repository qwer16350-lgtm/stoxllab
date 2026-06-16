# STOXL Phase 40J Private-test Read-only Runtime Preflight

Phase 40J prepares a future private-test read-only live runtime entry. It is report-only and does not start Discord runtime, connect the Gateway, call Discord API send, send a message, call LLM, call RAG, create embeddings, or execute external actions.

Future runtime conditions are names only:

- DISCORD_BOT_TOKEN present.
- HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID present.
- HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED=true.
- HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE exact.
- HERMES_DISCORD_SEND_MESSAGES=false.
- HERMES_DISCORD_PRIVATE_TEST_REPLY=false.
- HERMES_DISCORD_REPLY_MODE=readonly_private_test_only.
- LLM false.
- RAG false.
- Embedding false.
- External false.

Current state:

- Phase 39 actual send count locked: 1.
- Phase 40 readiness completed: true.
- Live runtime started: false.
- Discord Gateway connected: false.
- Ready for manual read-only runtime launch: false.
- Ready for reply send: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40j-private-test-readonly-runtime-preflight --json
```

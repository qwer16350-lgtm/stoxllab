# STOXL Phase51/52 Read-only Live Runtime Preflight

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase51-52-readonly-live-runtime-preflight --json
```

Manual Gate approval phrase:

```text
I_APPROVE_PHASE40J_PRIVATE_TEST_READONLY_RUNTIME
```

Authoritative environment keys:

- `HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED`
- `HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`

The report reads the current process environment when no test environment is
injected. It reports approval and safety checks as booleans only and does not
print the approval phrase value.

This preflight does not execute actual Discord runtime, connect to Discord
Gateway, call Discord API send, send Discord messages, attempt or call
LLM/OpenRouter, call RAG, create embeddings/vector data, run scheduler/cron live
execution, enable unattended auto reply, or execute external actions.

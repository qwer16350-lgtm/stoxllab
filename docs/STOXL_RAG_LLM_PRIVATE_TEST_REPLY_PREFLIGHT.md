# STOXL RAG+LLM Private Test Reply Preflight

Phase 33D-safe preflight checks whether a future private-test-only RAG+LLM reply
could be reviewed. It does not start Discord, does not call an LLM provider,
does not call embeddings, and does not send messages.

## Default State

- `ready=false`
- `blocked=true`
- `HERMES_RAG_LLM_REPLY_ENABLED=false`
- `HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED=false`
- `HERMES_DISCORD_SEND_MESSAGES=false`

The default blocked state is intentional.

## Checks

- canonical source validation
- `operations` rejected in favor of `operation`
- RAG mode must be `local_readonly`
- RAG response packet must be required
- private test channel must be configured before any future live review
- Discord send and LLM reply gates remain disabled in this scaffold

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-llm-private-test-reply-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-reply-report --markdown
```

## Safety

- Discord live runtime: not run
- Discord message sent: false
- LLM API called: false
- embedding API called: false
- external execution: false
- RAG+LLM live reply: not implemented

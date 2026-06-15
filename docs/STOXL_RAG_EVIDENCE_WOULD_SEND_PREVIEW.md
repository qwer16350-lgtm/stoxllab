# STOXL RAG Evidence Would-send Preview

Phase 34I converts the successful RAG evidence LLM dry-call closeout into a private-test would-send preview.

This phase does not run Discord live runtime, call Discord send APIs, send Discord messages, call OpenRouter/LLM again, call embeddings, ingest external sources, or execute external actions.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-would-send-preview --json
python apps\hermes_gateway\cli.py --rag-evidence-would-send-preview --markdown
```

## Message Safety

The preview message must include:

- `[REVIEW ONLY / NOT SENT]`
- `No external action has been taken.`
- relative evidence paths only

The preview blocks or escapes:

- `@everyone`
- `@here`
- raw Discord user/role mentions
- token-like or API-key-like values
- raw Discord-like numeric IDs
- absolute filesystem paths

## Send Boundary

The report keeps these values false:

- `public_channel_send_allowed`
- `team_channel_send_allowed`
- `discord_api_send_allowed`
- `discord_api_send_called`
- `discord_message_sent`
- `ready_for_actual_discord_send`
- `llm_api_called`
- `embedding_api_called`
- `external_execution`

Passing Phase 34I only means Phase 34J-0 send preflight design can be reviewed.

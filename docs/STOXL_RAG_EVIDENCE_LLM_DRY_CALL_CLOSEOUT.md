# STOXL RAG Evidence LLM Dry Call Closeout

Phase 34H-2 records the successful Phase 34H-1 RAG evidence LLM dry call as an embedded sanitized fixture and runs replay/audit validation against it.

This phase does not call OpenRouter again. It does not run Discord live runtime, send Discord messages, call embeddings, create vector DB indexes, ingest external sources, or perform external execution.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-closeout --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-closeout --markdown
```

The CLI uses the embedded sanitized fixture only.

## Observed Successful Dry Call

- Provider: `openrouter`
- Model: `openai/gpt-5.4-mini`
- API call attempted count: `1`
- API call succeeded count: `1`
- Prompt tokens: `335`
- Completion tokens: `101`
- Total tokens: `436`
- Provider cost USD: `0.00070575`

The fixture includes only relative evidence paths:

- `knowledge/operation/stoxl_operation_tone_sample.md`
- `knowledge/operation/stoxl_private_test_workflow_sample.md`

## Safety Requirements

The closeout must keep these values false:

- `ready_for_discord_send`
- `discord_message_sent`
- `discord_send_attempted`
- `embedding_api_called`
- `external_execution`
- `additional_llm_api_call`

The closeout also rejects secret-like values and raw Discord-like IDs.

## Next Phase

When Phase 34H-2 passes, the next safe step is Phase 34I private-test would-send preview. That step should remain preview-only unless separately approved.

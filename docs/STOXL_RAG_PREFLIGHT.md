# STOXL RAG Preflight

Phase 33A checks RAG source readiness without retrieval.

It does not read documents, call embeddings, call LLMs, send Discord messages, or execute external actions.

## Canonical Sources

Only these sources are canonical:

- marketing
- operation
- strategy
- brand
- archive

`operation` is valid. `operations` is invalid and returns `suggested_source=operation`.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-preflight-report --json
python apps\hermes_gateway\cli.py --rag-preflight-report --markdown
```

## Safety

- retrieval_executed=false
- embedding_api_called=false
- llm_api_called=false
- discord_message_sent=false
- external_execution=false

Phase 33A is ready for Phase 33B local read-only retrieval only.

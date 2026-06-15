# STOXL RAG Evidence Integration

Phase 34D connects the local evidence packet to the existing RAG response packet.

This phase is local-only. It does not start Discord, send Discord messages, call OpenRouter/LLM APIs, call embeddings, create a vector DB/index, ingest external sources, or perform external execution.

## Purpose

- Accept an existing local evidence packet.
- Add evidence/citation summary to the RAG response packet.
- Keep file content preview-only.
- Keep citation paths relative.
- Validate agent source routing before packet readiness.
- Keep `operation` canonical and `operations` blocked.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-integration --json
python apps\hermes_gateway\cli.py --rag-evidence-integration --markdown
```

Related reports:

```powershell
python apps\hermes_gateway\cli.py --rag-response-packet-report --json
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --json
python apps\hermes_gateway\cli.py --operations-viewer --json
```

## Expected Values

- `ready_for_private_test_review=true`
- `ready_for_llm_prompt=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`
- `embedding_api_called=false`
- `llm_api_called=false`
- `discord_message_sent=false`
- `external_execution=false`

## Still Deferred

- LLM prompt live connection
- embedding/vector DB/index creation
- external source ingestion
- public/team channel reply
- general automatic response

Phase 34D is only evidence-to-RAG-packet integration.

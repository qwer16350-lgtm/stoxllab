# STOXL Knowledge Ingestion Boundary

Phase 34A defines the local-only boundary for knowledge files.

This phase allows repo-local text foundation work only. It does not call embeddings, create a vector DB, ingest NAS/Drive/Notion/Web sources, call LLM APIs, send Discord messages, or perform external execution.

## Canonical Sources

- `marketing`
- `operation`
- `strategy`
- `brand`
- `archive`

Use `operation`, not `operations`.

## Forbidden Sources

- `operations`
- `external`
- `nas`
- `drive`
- `notion`
- `web`

## Extension Policy

Allowed local text:

- `.txt`
- `.md`
- `.json`
- `.yaml`
- `.yml`

Deferred:

- `.pdf`
- `.docx`
- `.xlsx`
- `.pptx`
- `.png`
- `.jpg`
- `.jpeg`

Blocked:

- `.env`
- `.key`
- `.pem`
- `.p12`
- `.sqlite`
- `.db`
- `.zip`
- `.7z`
- `.exe`
- `.ps1`
- `.bat`

## CLI

```powershell
python apps\hermes_gateway\cli.py --knowledge-ingestion-boundary --json
python apps\hermes_gateway\cli.py --knowledge-ingestion-boundary --markdown
```

Expected flags:

- `ready_for_local_text_ingestion=true`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`
- `embedding_api_called=false`
- `llm_api_called=false`
- `discord_message_sent=false`
- `external_execution=false`

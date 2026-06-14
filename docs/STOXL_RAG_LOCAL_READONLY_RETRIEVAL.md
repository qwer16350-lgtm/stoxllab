# STOXL RAG Local Read-only Retrieval

Phase 33B performs local read-only retrieval from repo-local knowledge folders.

It does not call embedding APIs, LLM APIs, Discord, vector databases, or external services.

## Source Roots

```text
knowledge/marketing/
knowledge/operation/
knowledge/strategy/
knowledge/brand/
knowledge/archive/
```

Missing folders are warnings, not crashes.

## Allowed Files

- `.txt`
- `.md`
- `.json`
- `.yaml`
- `.yml`

Excluded:

- `.env`
- `.git/`
- `exports/`
- `logs/`
- `apps/hermes_gateway/local/`
- `__pycache__/`
- `node_modules/`

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --json
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --markdown
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --source operation --query "STOXL brand tone" --json
```

## Safety

- local read-only only
- write_performed=false
- embedding_api_called=false
- llm_api_called=false
- discord_message_sent=false
- external_execution=false
- token/API key/raw Discord ID values are redacted or excluded

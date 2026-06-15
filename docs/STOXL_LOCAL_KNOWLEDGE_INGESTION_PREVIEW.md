# STOXL Local Knowledge Ingestion Preview

Phase 35B adds report-only local text knowledge ingestion UX checks.

- Allowed canonical sources: `marketing`, `operation`, `strategy`, `brand`, `archive`
- Forbidden source: `operations`
- Relative paths only
- Full content dumps disabled
- `ready_for_embedding=false`
- `ready_for_external_sources=false`
- `ready_for_llm_prompt=false`
- `ready_for_discord_send=false`

CLI:

```powershell
python apps\hermes_gateway\cli.py --local-knowledge-ingestion-preview --json
python apps\hermes_gateway\cli.py --local-knowledge-ingestion-preview --markdown
```

This preview does not run Discord, send messages, call LLMs, create embeddings/vector indexes, or execute external actions.

Phase 35C keeps the same source policy while composing agent evidence packs and prompt previews.

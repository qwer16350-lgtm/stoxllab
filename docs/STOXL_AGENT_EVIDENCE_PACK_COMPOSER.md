# STOXL Agent Evidence Pack Composer

Phase 35C composes agent-specific evidence packs from local, dry preview data.

- Rule-only
- Agent allowed sources only
- `operation` is canonical
- `operations` remains forbidden
- Relative paths and citation summaries only
- Full content dumps disabled
- `ready_for_llm_call=false`
- `ready_for_discord_send=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`

CLI:

```powershell
python apps\hermes_gateway\cli.py --agent-evidence-pack-composer --json
python apps\hermes_gateway\cli.py --agent-evidence-pack-composer --markdown
```

This report does not run Discord, send messages, call LLMs, create embeddings/vector indexes, or execute external actions.

## Phase 35D Follow-up

The Phase 35D agent review packet consumes this composer output as report-only
input. It keeps the same source boundaries, relative-path citation rule, and
full-content exclusion.

# STOXL RAG Evidence LLM Dry Call

Phase 34H-1 adds a manually approved dry-call boundary for sending a local evidence prompt envelope to the configured LLM provider.

This phase does not send Discord messages, create embeddings, build vector indexes, ingest external sources, or execute external actions.

## Default Behavior

The default command is report-only:

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-report --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-report --markdown
```

Without explicit approval, the report stays blocked and `actual_llm_api_call=false`.

## Manual Approval Gate

One actual provider dry call requires both the CLI flag and the environment gate:

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-report --json --allow-rag-evidence-llm-api-call
```

Required environment values:

- `HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED=true`
- `HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE` must exactly match the documented approval phrase.

The approval phrase value is never logged. The report only exposes booleans such as `approval_phrase_present` and `approved`.

## Safety Assertions

Every Phase 34H-1 report keeps these false:

- `ready_for_discord_send`
- `discord_message_sent`
- `discord_send_attempted`
- `embedding_api_called`
- `external_execution`

The report also redacts secret-like text and raw Discord-like numeric IDs.

## Operations Viewer

`--operations-viewer` includes a default Phase 34H-1 summary. The viewer does not pass the allow flag and does not perform an LLM API call.

## Phase 34H-2 Closeout

Phase 34H-2 records the successful Phase 34H-1 dry call as an embedded sanitized fixture and validates it without another OpenRouter call:

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-closeout --json
```

The closeout keeps Discord send, embeddings, external execution, and additional LLM API calls disabled.

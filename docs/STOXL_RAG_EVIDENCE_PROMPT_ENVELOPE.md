# STOXL RAG Evidence Prompt Envelope

Phase 34G converts a local RAG evidence review packet into a prompt envelope preview.

This phase does not call OpenRouter or any LLM API. It does not send Discord messages, call embeddings, create a vector DB/index, ingest external sources, or perform external execution.

## Required System Instruction

```text
Review-only draft.
No external action has been taken.
Do not publish, submit, send, approve, confirm, or execute external actions.
Use only the provided local evidence preview.
If evidence is insufficient, say that evidence is insufficient.
```

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-prompt-envelope --json
python apps\hermes_gateway\cli.py --rag-evidence-prompt-envelope --markdown
```

## Expected Values

- `ready_for_prompt_preview=true`
- `ready_for_llm_api_call=false`
- `ready_for_discord_send=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`
- `full_content_included=false`
- `content_preview_only=true`

This is prompt preview only. Actual LLM dry call requires a later separate approval phase.

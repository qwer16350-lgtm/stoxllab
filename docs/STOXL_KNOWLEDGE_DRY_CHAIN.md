# STOXL Knowledge Dry Chain

Phase 34F verifies a local sample knowledge dry chain:

```text
knowledge sample files -> manifest -> evidence packet -> RAG response packet -> review packet
```

This phase uses repo-local sample files only. It does not call LLM APIs, embeddings, Discord, external sources, vector DB/index creation, or external execution.

## Sample Files

- `knowledge/operation/stoxl_operation_tone_sample.md`
- `knowledge/operation/stoxl_private_test_workflow_sample.md`

The samples contain no tokens, API keys, raw Discord IDs, private personal data, or external execution instructions.

## CLI

```powershell
python apps\hermes_gateway\cli.py --knowledge-dry-chain --json
python apps\hermes_gateway\cli.py --knowledge-dry-chain --markdown
```

## Expected Values

- `sample_files_present=true`
- `manifest_available=true`
- `evidence_packet_available=true`
- `rag_response_packet_available=true`
- `review_packet_available=true`
- `citation_count >= 1`
- `ready_for_private_test_review=true`
- `ready_for_llm_prompt=false`
- `ready_for_discord_send=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`

## Phase 34G-H0 Follow-up

The dry chain can feed a prompt envelope preview and no-API/mock-only LLM dry readiness report.

Those follow-up reports do not call OpenRouter/LLM APIs, do not send Discord messages, do not call embeddings, and do not perform external execution.

# STOXL RAG Evidence Review Packet

Phase 34E converts local evidence integration output into a private-test review packet.

This phase does not start Discord, send messages, call OpenRouter/LLM APIs, call embeddings, ingest external sources, create a vector DB/index, or perform external execution.

## Purpose

- Present RAG evidence output for human review.
- Require a RAG response packet.
- Require an evidence packet.
- Require a citation summary.
- Keep the packet review-only.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-review-packet --json
python apps\hermes_gateway\cli.py --rag-evidence-review-packet --markdown
```

## Expected Values

- `review_only=true`
- `human_review_required=true`
- `ready_for_private_test_review=true`
- `ready_for_llm_prompt=false`
- `ready_for_discord_send=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`

This packet is not a live reply and not a general automatic response.

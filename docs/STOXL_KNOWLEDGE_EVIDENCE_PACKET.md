# STOXL Knowledge Evidence Packet

Phase 34C converts local retrieval results into a citation/evidence packet.

This packet is designed for later review packet or prompt-envelope integration. It does not call an LLM, does not send Discord messages, does not call embeddings, and does not perform external execution.

Phase 34D connects this evidence packet to the RAG response packet through:

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-integration --json
```

The integration remains local-only and keeps `ready_for_llm_prompt=false`.

## Packet Rules

- Use relative paths only.
- Include source name.
- Include excerpt preview only.
- Limit documents to `max_documents`.
- Limit excerpts to `max_excerpt_chars`.
- Do not include full file dumps.
- Do not include `.env` content.
- Do not include API keys or tokens.
- Do not include raw Discord IDs.
- Do not include absolute paths.

## Default Packet Shape

```json
{
  "report_type": "knowledge_evidence_packet",
  "version": "phase34c_local_evidence_packet",
  "source": "operation",
  "agent": "kasumi",
  "max_documents": 5,
  "max_excerpt_chars": 600,
  "full_content_included": false,
  "content_preview_only": true,
  "ready_for_rag_response_packet": true,
  "ready_for_llm_prompt": false
}
```

## CLI

```powershell
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --json
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --markdown
```

Safety flags remain false for embedding, LLM, Discord send, and external execution.

## Phase 34D Integration

The RAG response packet now includes:

- `evidence_packet`
- `citation_summary`

The integration is ready for private-test review only. It does not enable live LLM prompts, embeddings, vector DB/index creation, external source ingestion, public/team replies, or general automatic replies.

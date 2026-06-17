# STOXL Phase52 Review Packet Base

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase52-review-packet-composer --json
python apps\hermes_gateway\cli.py --phase52-readonly-synthetic-replay --json
```

Phase52 composes read-only review packets from normalized synthetic events,
event guards, and session context. The packet is the output of this phase, not a
Discord reply.

Review packet posture:

- `packet_type=readonly_review_packet`
- `external_action_taken=false`
- `discord_send_allowed=false`
- `llm_call_allowed=false`
- `rag_call_allowed=false`
- `requires_human_review=true`
- `recommended_next_action=review_only`
- `evidence_shell_created=true`
- `raw_content_included=false`
- `raw_discord_ids_logged=false`

Agent routing is deterministic and rule-based only. LLM and RAG remain
placeholders and are not called.

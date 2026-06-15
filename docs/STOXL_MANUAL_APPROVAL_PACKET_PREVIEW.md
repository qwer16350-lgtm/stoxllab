# STOXL Manual Approval Packet Preview

Phase 35D adds a manual approval packet preview. It does not approve anything and does not generate or log any approval phrase value.

## Purpose

The preview shows which manual approval gate would be required before a future live run. It is intentionally not a live approval artifact.

## Safety State

- Approval phrase generated: false
- Approval phrase value logged: false
- Ready for actual approval: false
- Ready for LLM call: false
- Ready for Discord send: false
- Ready for embedding: false
- Ready for external sources: false
- Ready for unattended auto reply: false

## Preview Rules

- Review packets that are ready may show a future scope of `private_test_only`.
- Review packets that are not ready show `approval_scope=none`.
- `discord_send_allowed=false` for every agent.
- `llm_call_allowed=false` for every agent.
- `embedding_allowed=false` for every agent.
- `external_execution_allowed=false` for every agent.

## CLI

```powershell
python apps\hermes_gateway\cli.py --manual-approval-packet-preview --json
python apps\hermes_gateway\cli.py --manual-approval-packet-preview --markdown
```

Both commands are report-only and do not call Discord, LLM, RAG, embeddings, or external systems.

## Phase 35E-G Use

The operator checklist and no-live rehearsal use this preview to show future
manual gate names only. Approval phrase values are not generated or logged.

## Phase 36A Use

The private-test one-shot LLM draft preflight lists future manual gate names
only. It does not generate approval phrase values or activate approval.

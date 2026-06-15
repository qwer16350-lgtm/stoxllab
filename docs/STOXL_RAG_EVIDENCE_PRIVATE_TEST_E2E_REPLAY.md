# STOXL RAG Evidence Private-test E2E Replay

Phase 34L-0 replays the private-test RAG evidence flow without live Discord events, LLM API calls, embeddings, or Discord sends.

The replay uses mock user events and sanitized fixtures from previous phases.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-replay --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-replay --markdown
```

## Replay Assertions

- mock private-test message accepted
- public/team mock messages rejected
- knowledge/evidence/prompt/LLM/would-send/send closeout chain replayed
- self-loop guard replayed
- duplicate-send guard replayed
- no live runtime
- no Discord send
- no LLM API call
- no embedding call
- no external execution

Passing this phase sets `ready_for_phase34l1_manual_e2e_live_reply=true` while keeping unattended auto reply disabled.

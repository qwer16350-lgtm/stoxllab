# STOXL RAG+LLM Private Test Reply Replay

Phase 33D-safe replay represents a future guarded RAG+LLM private test flow
without live Discord send, LLM API calls, embeddings, or external execution.

## Replay Cases

- human private test event would-send preview
- self message skipped before retrieval
- bot message skipped before retrieval
- public channel blocked before retrieval
- private channel ID mismatch blocked
- invalid source blocked
- `operations` source blocked
- context too large blocked
- too many documents blocked
- missing RAG response packet blocked
- LLM preflight failed blocked
- output safety blocked
- cooldown blocked
- budget exhausted blocked
- rate limit circuit breaker
- send exception circuit breaker

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --markdown
```

## Safety

- actual message sent: false
- LLM API called: false
- embedding API called: false
- Discord message sent: false
- external execution: false

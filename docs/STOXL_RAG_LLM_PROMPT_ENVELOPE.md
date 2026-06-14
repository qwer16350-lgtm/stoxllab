# STOXL RAG+LLM Prompt Envelope

Phase 33D-safe prompt envelope previews the shape of a future RAG+LLM prompt.
It does not include full raw context and does not call an LLM provider.

## Envelope Rules

- private test scope only
- review-only system instruction
- local read-only context previews only
- max context chars: 3000
- max documents: 5
- no publish, submit, send, approve, confirm, or external execution language

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-llm-prompt-envelope-report --json
python apps\hermes_gateway\cli.py --rag-llm-prompt-envelope-report --markdown
```

## Safety

- raw full context included: false
- content preview only: true
- LLM API called: false
- Discord message sent: false
- external execution: false

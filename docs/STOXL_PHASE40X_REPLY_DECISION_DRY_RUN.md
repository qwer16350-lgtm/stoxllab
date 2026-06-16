# STOXL Phase 40X Reply Decision Dry-run

Phase 40X evaluates synthetic fixtures without sending anything.

Rules:

- private-test human message: `would_reply=true`
- self message: `would_reply=false`
- bot message: `would_reply=false`
- duplicate message: `would_reply=false`
- public/team channel: `would_reply=false`

The reply payload is a frozen deterministic placeholder. Actual Discord send,
LLM, RAG, embedding, and external execution remain false.

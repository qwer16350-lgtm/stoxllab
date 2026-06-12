# STOXL Would-send Preview

Phase 30 can build deterministic local previews of what kind of response might be useful later.

## Purpose

The preview is a review aid only. It is not an LLM-generated reply and it is not sent to Discord.

## Preview Rule

Preview content is a deterministic placeholder:

```text
[NO SEND] Received live event in marketing-brief. Candidate route: marin. Reply generation is disabled.
```

## Future Reply Phase

Any real reply behavior requires a later approved phase. Phase 30 keeps:

- `will_send=false`
- `requires_manual_enable=true`
- `requires_future_reply_phase=true`
- `message_sent=false`
- `llm_called=false`
- `rag_called=false`
- `external_execution=false`

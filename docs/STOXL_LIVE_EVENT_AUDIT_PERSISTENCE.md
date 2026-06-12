# STOXL Live Event Audit Persistence

Phase 30 stores read-only live Discord event observations as local audit artifacts.

## Purpose

The audit record gives an operator a stable, redacted record of what the bot observed and how the event was classified. It does not send a Discord message, call LLM/RAG, or execute external actions.

## Paths

```text
logs/hermes_gateway/live_events/readonly_events_YYYYMMDD.jsonl
logs/hermes_gateway/live_events/manifests/readonly_manifest_YYYYMMDD.json
```

Both paths are local artifacts. The `logs/hermes_gateway/` tree is ignored by git.

## Record Shape

Each record includes decision, reason, channel, workflow role, candidate route, content presence/length, redacted content preview, and safety assertions.

## Redaction

- content preview is capped at 120 characters
- newlines are normalized to spaces
- token-like and secret-like values are redacted
- long Discord-like numeric IDs are redacted

## Safety

All records preserve:

- `message_sent=false`
- `will_send=false`
- `external_execution=false`
- `llm_called=false`
- `rag_called=false`

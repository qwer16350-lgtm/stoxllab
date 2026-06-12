# STOXL Live Event Pipeline

Phase 29 introduces an audit-only live event pipeline for Discord message events.

## Purpose

The pipeline normalizes a Discord-shaped message, runs the existing local evaluator and dispatch planner, creates an audit payload, builds a would-send payload, and then blocks all outbound action.

## Pipeline Steps

1. Normalize the live message into a local raw event shape.
2. Ignore self or bot-authored messages.
3. Evaluate the request with the local STOXL evaluator.
4. Build a dispatch plan.
5. Build a would-send payload for review only.
6. Build a disabled reply plan.
7. Build an audit payload.
8. Block outbound action through the send blocking guard.

## Safety Rules

- No Discord write API call.
- No message send.
- No external execution.
- No LLM call.
- No RAG read.
- Long Discord-like IDs are redacted in reports.
- Attachment originals are not stored in audit payloads.

## Report Command

```powershell
python apps\hermes_gateway\cli.py --live-event-pipeline-report --json
```

The report uses a local sample event and does not connect to Discord.

# STOXL Live Event Review Packet

Phase 30 groups the audit record, routing report, and would-send preview into a local review packet.

## Purpose

The packet lets a human review live event handling without enabling Discord replies or external execution.

## Contents

- event summary
- audit record
- routing report
- would-send preview
- optional deterministic agent placeholder response
- human review policy
- safety assertions

## Human Review

Allowed actions:

- review only
- manual follow-up outside the bot

Disallowed actions:

- auto reply
- external execution
- LLM call
- RAG call

## Outputs

```text
exports/hermes_gateway/live_event_packets/YYYYMMDD/
```

The export path is local and ignored by git.

## Phase 31C Placeholder

Review packets may include `agent_placeholder_response` with title and summary fields. The field is optional and backward compatible; missing placeholders are represented as `available=false`.

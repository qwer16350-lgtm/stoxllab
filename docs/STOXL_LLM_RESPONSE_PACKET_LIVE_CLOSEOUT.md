# STOXL LLM Response Packet Live Closeout

Phase 32C-LIVE verifies the local path from a gated LLM dry-call artifact to a human-review response packet.

It does not send Discord messages, does not call RAG, and does not execute external actions.

## Flow

```powershell
python apps\hermes_gateway\cli.py --llm-dry-call-report --json --allow-llm-api-call --write-artifact
python apps\hermes_gateway\cli.py --llm-response-packet-report --latest --json
python apps\hermes_gateway\cli.py --llm-response-packet-report --latest --markdown
python apps\hermes_gateway\cli.py --llm-response-packet-live-closeout --json
```

The first command may attempt a single provider call only when the Phase 32B gates pass. The later commands read local artifacts and do not make provider calls.

## Local Artifacts

Dry-call reports are written under:

```text
exports/hermes_gateway/llm_dry_calls/YYYYMMDD/
```

Response packets are written under:

```text
exports/hermes_gateway/llm_response_packets/YYYYMMDD/
```

Both artifact families are local review records. They must not contain API keys, raw Discord IDs, tokens, or `.env` values.

## Closeout Report

The closeout report records:

- latest dry-call artifact found
- LLM response packet created
- operations viewer summary available
- provider and model
- output safety allowed
- response available
- ready for a later guarded private-test LLM reply phase
- message_sent=false
- discord_send_attempted=false
- rag_called=false
- external_execution=false

## Safety Boundary

Phase 32C-LIVE is not a Discord reply phase.

The preferred LLM safety wording is allowed by output safety:

```text
This is a review-only draft. No external action has been taken.
```

That sentence is treated as a negated safety disclaimer, not as a claim that an external action occurred.

Allowed:

- read the latest local dry-call artifact
- create a local response packet
- summarize the latest packet for operations viewer review
- produce a local closeout report

Forbidden:

- Discord message send
- public/team channel reply
- RAG lookup
- external posting, submission, email, contract, pricing, or delivery action
- token/API key/raw Discord ID output

## Next Phase Candidate

Phase 32D may design a guarded private-test-only LLM reply path. That phase still needs a separate safety gate and must not inherit general Discord send permission.

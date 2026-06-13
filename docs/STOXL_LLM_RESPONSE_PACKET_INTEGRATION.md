# STOXL LLM Response Packet Integration

Phase 32C connects LLM dry call results to local review workflows.

It does not send Discord messages, does not call RAG, and does not execute external actions.

## Difference From Phase 32B

Phase 32B creates an LLM dry call report.

Phase 32C converts that report into:

- a local LLM response packet
- optional would-send preview summary
- optional live event review packet summary
- operations viewer summary

## Packet Structure

The packet stores:

- agent route candidate
- provider and model
- redacted response text
- response summary
- output safety result
- safe disclaimer metadata
- provider usage and cost summary
- human review policy
- safety assertions

Human review is always required. The packet disallows:

- auto reply
- external execution
- RAG call
- public publish

## Would-send Preview Integration

Would-send previews may include:

```json
{
  "llm_response": {
    "available": true,
    "provider": "openrouter",
    "model": "openai/gpt-5.4-mini",
    "summary": "...",
    "will_send": false
  }
}
```

This is a preview only. It is never posted to Discord.

## Review Packet Integration

Live event review packets may include:

```json
{
  "llm_response_packet": {
    "available": true,
    "provider": "openrouter",
    "model": "openai/gpt-5.4-mini",
    "output_safety_allowed": true,
    "summary": "..."
  }
}
```

If no LLM response packet is attached, the field is present as `available=false`.

## Operations Viewer

The operations viewer can summarize recent LLM response packets:

- provider
- model
- output safety status
- cost
- sent to Discord: false

Phase 32C-LIVE also exposes the latest local response packet as
`latest_llm_response_packet` so operators can see the newest safe LLM response
without opening the raw artifact directly.

## Live Closeout Flow

Phase 32C-LIVE closes the local workflow:

```powershell
python apps\hermes_gateway\cli.py --llm-dry-call-report --json --allow-llm-api-call --write-artifact
python apps\hermes_gateway\cli.py --llm-response-packet-report --latest --json
python apps\hermes_gateway\cli.py --llm-response-packet-live-closeout --json
```

The latest dry-call artifact is read from:

```text
exports/hermes_gateway/llm_dry_calls/YYYYMMDD/
```

The generated response packet is written under:

```text
exports/hermes_gateway/llm_response_packets/YYYYMMDD/
```

The closeout report records:

- latest dry-call artifact found
- response packet created
- operations viewer summary available
- provider/model
- output safety status
- ready-for-next-phase flag
- message_sent=false
- discord_send_attempted=false
- rag_called=false
- external_execution=false

## Why Discord Send Is Still Forbidden

Phase 32C is a review integration step only. LLM text can be inspected locally, but no message is sent to Discord and no external action is performed.

## Output Safety

Allowed output can be reviewed locally. Blocked output is still packaged for human inspection, but remains non-sendable.

## Next Phases

- Phase 32D: guarded private test LLM reply, manual enable only.
- Phase 33A: RAG preflight.

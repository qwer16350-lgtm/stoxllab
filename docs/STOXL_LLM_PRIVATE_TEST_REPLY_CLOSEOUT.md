# STOXL LLM Private Test Reply Closeout

Phase 32D closeout turns the observed private-test LLM reply success into a reproducible local replay/audit report.

It does not start Discord, does not send a message, does not call OpenRouter, does not read RAG, and does not execute external actions.

## Verified Live Success

The redacted fixture confirms:

- private test LLM runtime became ready
- the private test channel was configured
- one human private test message was accepted
- one LLM call was allowed in the live run
- output safety passed
- one private test LLM reply was sent in the live run
- the bot self-message was ignored
- no second LLM call occurred after the self-message
- public send, RAG, and external execution were disabled

The fixture uses only redacted Discord IDs.

## Replay Purpose

The replay report is a closeout artifact. It records what the live success proved and replays blocked scenarios locally:

- self message skipped
- bot message skipped
- duplicate message blocked
- cooldown blocked
- budget exhausted blocked
- public channel blocked
- private channel ID mismatch blocked
- output safety blocked
- provider error blocked
- packet safety blocked
- rate-limit circuit breaker
- send-exception circuit breaker

The replay summary may show `sent=1` because the fixture represents the observed live success. The replay itself keeps `message_sent=false` and `live_discord_send_executed=false`.

## CLI

```powershell
python apps\hermes_gateway\cli.py --llm-private-test-reply-replay-report --json
python apps\hermes_gateway\cli.py --llm-private-test-reply-replay-report --markdown
python apps\hermes_gateway\cli.py --operations-viewer --json
```

These commands are no-live-send commands.

## Operations Viewer

The operations viewer includes:

```json
{
  "llm_private_test_reply_closeout": {
    "available": true,
    "live_success_fixture_verified": true,
    "sent_in_fixture": 1,
    "self_messages_skipped": 1,
    "public_channel_blocked": 1,
    "llm_api_called_by_replay": false,
    "discord_send_by_replay": false,
    "ready_for_phase33a_rag_preflight": true
  }
}
```

## Safety Assertions

- replay Discord send: false
- replay LLM API call: false
- RAG called: false
- external execution: false
- API key value logged: false
- raw Discord IDs logged: false

## Next Phase Suggestions

- Phase 33A: RAG preflight only
- Phase 33B: RAG read-only local retrieval
- Phase 33C: RAG response packet, no Discord send
- Phase 33D: guarded RAG+LLM private test reply, plan-only until separate review

Public/team LLM replies remain forbidden after Phase 32D.

## RAG Follow-up Boundary

The next safe RAG flow is limited to:

- source registry and preflight checks
- repo-local read-only retrieval from `knowledge/<source>`
- response packet generation for human review
- operations viewer summaries

The RAG follow-up does not implement RAG+LLM Discord reply, does not read
external/NAS RAG roots, does not call embedding APIs, and does not send Discord
messages. Public/team channel replies remain forbidden.

# STOXL Private Test Reply Replay Closeout

Phase 31E verifies private test reply visibility through local replay and viewer summaries.

## Purpose

The private test reply runtime has already proven the basic live path: one human message can produce one deterministic placeholder reply, self replies are skipped, and Phase 31D safety controls bound the runtime. Phase 31E does not add live behavior. It verifies that sent, blocked, skipped, cooldown, budget, and circuit breaker states can be tracked consistently in local reports.

## Replay vs Discord Send

Replay is a local summary of historical or example states. It does not connect to Discord and does not send messages.

Top-level `message_sent=false` means the replay command did not send anything. Historical sent states are represented only inside event metadata with `historical_message_sent=true`.

## Event Kinds

- `human_allowed_sent`
- `self_message_skipped`
- `duplicate_message_blocked`
- `cooldown_blocked`
- `budget_exhausted_blocked`
- `rate_limit_circuit_breaker`
- `send_exception_circuit_breaker`
- `public_channel_blocked`

## Operations Viewer

The operations viewer includes a `private_test_reply_summary` section with:

- historical sent count
- blocked count
- self-message skipped count
- cooldown blocked count
- budget exhausted count
- circuit breaker count

The Markdown viewer renders the same summary under `## Private Test Reply`.

## Safety Assertions

- Discord API called: false
- Message sent during replay: false
- LLM called: false
- RAG called: false
- External execution: false
- Env file read: false
- Local mapping file read: false
- Raw token logged: false
- Raw Discord IDs logged: false

## Phase 31 Closeout Criteria

Private test reply is considered closed out when:

- live reply remains private-test-channel-only
- self/bot messages are skipped
- duplicate messages are blocked
- cooldown and budget controls are visible
- circuit breaker states are replayable
- operations viewer exposes a human-readable summary
- no LLM, RAG, external execution, public reply, or team reply is enabled

## Next Phase Candidates

- Phase 32A: LLM Preflight
- Phase 32B: private test LLM response only

Neither phase is implemented here.

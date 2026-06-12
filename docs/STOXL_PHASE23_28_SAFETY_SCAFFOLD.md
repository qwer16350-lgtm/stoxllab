# STOXL Phase 23-28 Safety Scaffold

## Purpose

This consolidated scaffold covers Phase 23 through Phase 28 without enabling real Discord connection, replies, LLM, RAG, or external execution.

## Included Phases

- Phase 23: read-only connection preflight
- Phase 24: read-only runtime stub
- Phase 25: live capture audit-only stub
- Phase 26: reply planner disabled by default
- Phase 27: approval interaction spec/mock only
- Phase 28: agent response interface only

## Currently Possible

- validate local mapping readiness
- generate no-connection preflight report
- describe future Discord dependency plan
- build read-only runtime config shape
- build audit-only capture shape
- build would-send reply plans
- describe approval interaction modes
- build agent response placeholder schema

## Still Not Allowed

- Discord Gateway connection
- Discord API call
- Discord bot execution
- Discord message send
- Bot Token read or output
- `.env` read
- LLM call
- RAG call
- external DB/RAG original access
- SNS posting
- homepage upload
- grant submission
- email sending
- contract, price, or delivery confirmation
- approval-to-external-execution conversion

## Global Safety Defaults

- `send_messages=false`
- `message_sent=false`
- `discord_api_called=false`
- `gateway_connected=false`
- `llm_called=false`
- `rag_called=false`
- `external_execution_enabled=false`
- `human_only_execution_preserved=true`

## Phase 29 Candidate

Phase 29 can propose a read-only dependency installation and runtime entrypoint review. Actual Discord connection must still require explicit approval in that phase.

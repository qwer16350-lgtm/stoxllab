# STOXL Live Capture Audit-Only Stub

## Purpose

The live capture stub defines the audit-only shape for a future live Discord event capture path.

It is not live capture yet. It does not connect to Gateway or receive real Discord events.

## Planned Future Flow

A future phase may pass a raw Discord-shaped event into the adapter boundary and build an audit payload. This phase only defines that skeleton.

## Current Restrictions

- no live Gateway
- no Discord API call
- no message sending
- no LLM call
- no RAG call
- no external execution
- no automatic persistence unless a later phase explicitly enables it

## Safety Flags

The stub report keeps:

- `discord_api_called=false`
- `gateway_connected=false`
- `message_sent=false`
- `llm_called=false`
- `rag_called=false`
- `external_execution_enabled=false`

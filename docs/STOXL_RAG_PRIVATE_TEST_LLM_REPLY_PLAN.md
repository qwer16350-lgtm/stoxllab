# STOXL RAG Private Test LLM Reply Plan - Phase 33D

## Goal

- guarded private test RAG+LLM reply
- private test channel only
- source validation required
- local retrieval only
- retrieved context size cap
- RAG response packet required
- LLM output safety required
- Discord send only after all gates

## Prerequisites

- Phase 33A RAG Preflight complete
- Phase 33B Local Read-only Retrieval complete
- Phase 33C RAG Response Packet complete
- Phase 32D private test LLM reply safety complete

## Forbidden

- public/team channel reply
- channel-name-based allow
- `source=operations`
- external execution
- write/update/delete
- unbounded context
- raw Discord ID logging
- token/API key logging

## Future Gates

- `HERMES_RAG_ENABLED=true`
- `HERMES_RAG_MODE=local_readonly`
- `HERMES_RAG_ALLOWED_SOURCES=marketing,operation,strategy,brand,archive`
- `HERMES_RAG_PRIVATE_TEST_ONLY=true`
- `HERMES_RAG_LLM_REPLY_ENABLED=true`
- `HERMES_RAG_REQUIRE_RESPONSE_PACKET=true`
- `HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED=true`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` present

## Future Tests

- invalid source blocks before retrieval
- public channel blocks before retrieval
- self/bot blocks before retrieval
- retrieval result too large blocks before LLM
- output safety blocked prevents send
- packet safety failure prevents send
- exactly one send in private test channel
- self echo skipped

Phase 33D is not implemented in this phase.
This document is a plan only.

## Phase 33D-safe Scaffold Status

The safe scaffold adds preflight, context safety, prompt envelope preview,
would-send preview, and replay/audit reports. It still does not implement live
RAG+LLM Discord reply.

Live implementation requires a separate manual approval and review phase.

## Live Readiness Review

The live readiness review is now available as a deterministic report. Its
default result is `go=false` because manual approval is still required and the
live runtime is not enabled by the review phase.

The review may say the repo is ready for a separate manual implementation
request, but it does not implement RAG+LLM live reply.

## Phase 33D-1 Runtime Code

Phase 33D-1 adds guarded runtime code for private-test-only RAG+LLM replies.
The implementation keeps public/team channels blocked before retrieval, rejects
`source=operations`, requires local read-only retrieval, context safety, RAG
response packets, LLM output safety, cooldown, budget, duplicate guard, and
circuit breaker checks.

The runtime option exists, but live execution still requires separate manual
approval.

# STOXL RAG+LLM Live Rollback Checklist

Use this checklist before any future Phase 33D live implementation review and
again during emergency shutdown. This document is review-only and does not run
commands.

## Emergency Gate Off

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_REPLY_ENABLED="false"
```

## Runtime Shutdown

- Stop any live runtime with Ctrl+C.
- Open the circuit breaker after rate-limit or send exceptions.
- Confirm public/team channel events block before retrieval, LLM, and send.
- Confirm self/bot messages block before retrieval, LLM, and send.
- Do not inspect token/API key values in logs.
- Do not print `.env` contents.

## No-go Conditions

- missing manual approval
- private test channel ID missing or mismatched
- source is `operations`
- context exceeds max documents or max chars
- RAG response packet missing
- LLM output safety not passed
- cooldown, budget, duplicate guard, or circuit breaker not active

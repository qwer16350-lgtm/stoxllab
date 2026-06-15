# STOXL Hermes Operator Runbook

## Current Operating State

- Phase 34 private-test E2E MVP complete.
- This is not a production/public/team channel bot.
- The only completed live send scope is `private_test_only`.
- Future live runs still require manual approval.

## Default Safety State

- All send and LLM live gates are off by default.
- Public/team channel send and reply are forbidden.
- Unattended auto reply is false.
- Embedding/vector DB auto creation is disabled.
- External execution is disabled.
- Token, API key, approval phrase, and raw Discord ID values must never be logged.

## Allowed Manual Live Run Scope

- Private-test channel only.
- One-run and one-send only.
- Manual approval gate required for each run.
- Token/key values remain private.
- Raw Discord IDs remain redacted.

## Emergency Gate Off

```powershell
$env:HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE=""

$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE=""

$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE=""

$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_DISCORD_REPLY_MODE=""

$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_REPLY_ENABLED="false"
```

## Forbidden Operations

- Public/team channel reply.
- Unattended auto reply.
- Scheduler or cron auto reply.
- Embedding/vector DB automatic creation.
- External execution.
- Token/key logging.
- Raw Discord ID logging.
- Approval phrase value logging.

## Restart Checklist

- Validator Errors 0.
- Required tests pass.
- Operations viewer final lock and Phase 35A audit summaries pass.
- Manual approval phrase is present only for the one approved run.
- Safety gates are turned off immediately after any manual run.

## No-live Rehearsal Lock

Before any Phase 36 work, review the operator checklist, no-live rehearsal
packet, operations dashboard lock, forbidden behavior sentinel, and Phase 36
entry gate reports. These reports do not generate approval phrases and do not
enable live runtime, LLM calls, Discord sends, embeddings, or external
execution.

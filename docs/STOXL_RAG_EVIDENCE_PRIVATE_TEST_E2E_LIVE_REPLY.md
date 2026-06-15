# STOXL RAG Evidence Private-test E2E Live Reply

Phase 34L-1 adds the final manual private-test E2E live reply boundary for one run only.

Default execution is blocked. The default report does not run the Discord live runtime, does not call OpenRouter/LLM, does not send a Discord message, does not call embeddings, and does not execute external actions.

Phase 34L-1A fixes safety stage ordering. Prompt/input safety is pre-LLM.
Output safety is post-LLM and is checked only after an LLM response packet
exists. `output_safety_blocked` must not occur before
`llm_response_packet_created=true`. The previous blocked run was safe because
`llm_api_called=false` and `discord_message_sent=false`; the next action is to
retry Phase 34L-1 after this hotfix.

Phase 34L-1B connects the approved E2E live path to the LLM call stage. After
private-test channel gating and prompt safety pass, the runtime enters the LLM
stage and may attempt exactly one LLM call only when the LLM manual approval
gate also passes. Output safety remains post-LLM, and Discord send remains
blocked unless output safety passes. The previous retry was safe because
`llm_api_called=false` and `discord_message_sent=false`.

Phase 34L-1C eliminates the LLM allowed-but-not-attempted no-op. If
`llm_call_allowed=true`, LLM dispatch must be invoked and the API call attempt
flag must become true. If dispatch cannot be invoked, `llm_call_allowed=false`
with an explicit `llm_dispatch_blocked_reason`, such as
`openrouter_api_key_missing`. The previous retry was safe because
`llm_api_called=false` and `discord_message_sent=false`.

Phase 34L-1D fixes OpenRouter API key detection in the E2E live dispatch path.
The E2E dispatcher accepts both `OPENROUTER_API_KEY` and
`HERMES_OPENROUTER_API_KEY`. Only API key presence is reported; API key values
are never logged. The previous retry was safe because `llm_api_called=false`
and `discord_message_sent=false`.

Phase 34L-1E handles Discord send disconnects after a successful E2E LLM call.
If the LLM call succeeds, output safety passes, and Discord send fails with a
disconnect such as `ServerDisconnectedError`, the report records a partial
success artifact. That artifact prepares a later manual send retry without
calling the LLM again. This hotfix does not run a live retry.

Phase 34L-2 closes out the observed E2E live reply plus the successful no-LLM
send retry. The closeout is replay/audit-only and does not run Discord, send
another message, call OpenRouter/LLM, call embeddings, or execute external
actions.

Phase 34M final lock marks the private-test E2E MVP complete. Future live runs
still require separate manual approvals.

## Allowed Scope

- One manually approved private-test channel event.
- One local knowledge evidence chain.
- One prompt envelope.
- One OpenRouter-compatible LLM API call.
- One Discord private-test reply only after output safety passes.
- No public/team channel reply.
- No unattended auto reply.

## Required Gates

- `--allow-rag-evidence-private-test-e2e-live-reply`
- `HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED=true`
- `HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE` exact match
- `HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED=true`
- `HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE` exact match
- `HERMES_DISCORD_SEND_MESSAGES=true`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`
- `HERMES_DISCORD_REPLY_MODE=private_test_only`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` present

Approval phrase values, token values, API keys, and raw Discord IDs are never logged.

## Default Verification

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-live-reply --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-live-reply --markdown
```

Expected default:

- `ready=false`
- `blocked=true`
- `discord_live_runtime_executed=false`
- `llm_api_called=false`
- `llm_stage_reached=false`
- `llm_call_allowed=false`
- `llm_dispatch_invoked=false`
- `llm_dispatch_mode=""`
- `llm_dispatch_blocked_reason=""`
- `llm_api_call_attempted=false`
- `llm_response_packet_created=false`
- `output_safety_checked=false`
- `output_safety_blocked=false`
- `discord_message_sent=false`
- `discord_send_failed=false`
- `ready_for_phase34l1e_send_retry_without_llm=false`
- `ready_for_unattended_auto_reply=false`

## Manual Live Command

Run this only when a human is ready to send exactly one private-test message:

```powershell
$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED="true"
$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_EVIDENCE_E2E_REPLY"

$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED="true"
$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE="I_APPROVE_ONE_RAG_EVIDENCE_LLM_DRY_CALL"

$env:HERMES_DISCORD_SEND_MESSAGES="true"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="true"
$env:HERMES_DISCORD_REPLY_MODE="private_test_only"

python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-live-reply --json --allow-rag-evidence-private-test-e2e-live-reply
```

After the run, immediately close the gates:

```powershell
$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_E2E_LIVE_REPLY_APPROVAL_PHRASE=""

$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE=""

$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_DISCORD_REPLY_MODE=""
```

## Success Criteria

- `discord_live_runtime_executed=true`
- `discord_event_received=true`
- `accepted_private_test_channel=true`
- `prompt_safety_checked=true`
- `prompt_safety_allowed=true`
- `llm_stage_reached=true`
- `llm_call_allowed=true`
- `llm_dispatch_invoked=true`
- `llm_dispatch_mode=actual_openrouter_once`
- `llm_api_call_attempted=true`
- `llm_api_called=true`
- `llm_api_call_count=1`
- `llm_response_packet_created=true`
- `output_safety_checked=true`
- `output_safety_allowed=true`
- `output_safety_blocked=false`
- `discord_message_sent=true`
- `message_sent_count=1`
- `sent_channel_scope=private_test_only`
- `self_loop_guard_triggered=true`
- `duplicate_send_blocked=true`
- `embedding_api_called=false`
- `external_execution=false`
- `ready_for_phase34l2_e2e_live_reply_closeout=true`
- `ready_for_unattended_auto_reply=false`

## Send Disconnect Handling

If Discord disconnects at the send boundary after LLM success:

- `discord_send_stage_reached=true`
- `discord_api_send_allowed=true`
- `discord_send_failed=true`
- `discord_send_failure_reason=ServerDisconnectedError`
- `discord_message_sent=false`
- `message_sent_count=0`
- `llm_response_available_for_send_retry=true`
- `ready_for_phase34l1e_send_retry_without_llm=true`
- `ready_for_phase34l2_e2e_live_reply_closeout=false`

The partial-success artifact keeps `llm_api_call_count=1` and
`output_safety_allowed=true`, but it does not authorize another LLM call. The
next step is a separate manual send retry without LLM.

## Prohibitions

- No public/team channel reply.
- No unattended auto reply.
- No self/bot message reply.
- No duplicate send.
- No second LLM API call.
- No embedding API call.
- No vector DB/index creation.
- No external ingest or execution.
- No token/API key/raw Discord ID/approval phrase value logging.

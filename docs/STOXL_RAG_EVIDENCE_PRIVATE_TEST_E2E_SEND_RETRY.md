# STOXL RAG Evidence Private-test E2E Send Retry

Phase 34L-1E prepares a no-LLM retry path for the case where the E2E live flow already completed the LLM call and output safety, but Discord send failed at the boundary.

Phase 34L-1F wires the actual Discord sender for that no-LLM retry path. The CLI can now auto-build the sender when all gates pass, but this hotfix verification uses mock/fixture tests only and does not execute a real Discord send.

Default execution is blocked. The default report does not run Discord live runtime, does not send a Discord message, does not call OpenRouter/LLM, does not call embeddings, and does not execute external actions.

## Purpose

- Reuse a prior partial-success artifact.
- Preserve the already safety-checked LLM response.
- Prevent any LLM recall during retry.
- Require a separate manual approval gate before a private-test send retry.
- Keep public/team channel sends blocked.

## Commands

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-send-retry --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-send-retry --markdown
```

The future manual retry gate is:

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-send-retry --json --allow-rag-evidence-private-test-e2e-send-retry
```

This hotfix implements the report and mockable boundary only. It does not run an actual Discord retry.

After Phase 34L-1F, the allow path no longer reports `actual_send_retry_sender_not_provided` when all gates and token presence checks pass. If the token is absent, the report blocks with `discord_token_missing`.

## Required Manual Gates

- `HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVED=true`
- `HERMES_RAG_EVIDENCE_E2E_SEND_RETRY_APPROVAL_PHRASE` exact match
- `HERMES_DISCORD_SEND_MESSAGES=true`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`
- `HERMES_DISCORD_REPLY_MODE=private_test_only`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` present
- `DISCORD_BOT_TOKEN` present

Approval phrase values, token values, API keys, and raw Discord IDs are never logged.

## Safety Guarantees

- `llm_recall_allowed=false`
- `llm_api_called=false`
- `llm_api_call_count=0`
- `public_channel_send_allowed=false`
- `team_channel_send_allowed=false`
- `actual_send_retry_sender_not_provided=false`
- `ready_for_unattended_auto_reply=false`
- `embedding_api_called=false`
- `external_execution=false`

## Closeout Meaning

Mock success may set `ready_for_phase34l2_e2e_live_reply_closeout=true` with `message_sent_count=1`. A real send retry still requires a separate human-run approval step.

Phase 34L-2 records the successful no-LLM send retry in the final E2E closeout. The closeout confirms `send_retry_llm_call_count=0`, final Discord message count `1`, `sent_channel_scope=private_test_only`, and `ready_for_phase34m_final_lock=true`.

Phase 34M final lock keeps this state fixed as part of the completed private-test E2E MVP.

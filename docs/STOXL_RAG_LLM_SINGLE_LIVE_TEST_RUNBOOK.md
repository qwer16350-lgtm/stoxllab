# STOXL RAG+LLM Single Live Private Test Runbook

Phase 33D-3 prepares the manual procedure for one guarded RAG+LLM private test reply.

This runbook is not an approval to start the runtime. Codex/agent must not run the live command automatically. The actual single live private test must be started by the user in PowerShell after separately confirming the gates below.

## 1. Purpose

The single live private test verifies that one human message in the configured Discord private test channel can receive one RAG+LLM review-only reply.

The test is intentionally narrow:

- one human message
- one private test channel
- canonical `source=operation`
- local read-only retrieval
- one OpenRouter LLM call
- output safety must allow the response
- one Discord reply only

## 2. Scope

Allowed for this single manual test:

- private test channel only
- channel ID match only
- canonical source only
- local read-only retrieval only
- OpenRouter LLM call
- output-safety-allowed response only
- Discord send exactly once

Forbidden:

- public or team channel reply
- `source=operations`
- external execution
- embedding API
- multiple messages
- automatic retry storm
- channel-name-only allow
- self-message reply
- bot-author reply
- unbounded context

## 3. Before-Run Commands

Run these no-live checks first:

```powershell
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --json
python scripts\validate_stoxl_configs.py
```

Expected no-live values:

```text
ready_for_single_live_private_test=true
runtime_executed=false
actual_discord_send=false
actual_llm_api_call=false
embedding_api_called=false
external_execution=false
```

If any value differs, do not run the live command.

## 4. Required Env Gates For User-Run Live Test

Set these only in the user's PowerShell session. Do not write them into `.env`, docs with real values, logs, or committed files.

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="true"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="true"
$env:HERMES_DISCORD_REPLY_MODE="private_test_only"
$env:HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID="<PRIVATE_TEST_CHANNEL_ID>"

$env:HERMES_RAG_ENABLED="true"
$env:HERMES_RAG_MODE="local_readonly"
$env:HERMES_RAG_PRIVATE_TEST_ONLY="true"
$env:HERMES_RAG_REQUIRE_RESPONSE_PACKET="true"
$env:HERMES_RAG_LLM_REPLY_ENABLED="true"
$env:HERMES_RAG_LLM_REPLY_MODE="private_test_only"
$env:HERMES_RAG_LLM_REQUIRE_RAG_PACKET="true"
$env:HERMES_RAG_LLM_REQUIRE_CONTEXT_SAFETY="true"
$env:HERMES_RAG_LLM_REQUIRE_OUTPUT_SAFETY="true"

$env:HERMES_LLM_ENABLED="true"
$env:HERMES_LLM_API_CALL_ENABLED="true"
$env:HERMES_LLM_PROVIDER="openrouter"
$env:HERMES_LLM_MODEL="openai/gpt-5.4-mini"
$env:HERMES_LLM_API_KEY="<OPENROUTER_KEY_PLACEHOLDER>"
$env:HERMES_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:HERMES_LLM_DRY_RUN_ONLY="false"
$env:HERMES_LLM_PRIVATE_TEST_ONLY="true"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="true"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="true"

$env:HERMES_DISCORD_EXTERNAL_EXECUTION="false"
$env:HERMES_LLM_EXTERNAL_EXECUTION="false"
```

The API key placeholder above must be replaced only in the user's local PowerShell session. Never paste the real value into this repository.

## 5. Actual Live Command

Manual-only command:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-rag-llm-reply --json
```

Codex/agent must not execute this command automatically. The user runs it directly in PowerShell only after confirming the before-run checks and env gates.

## 6. Test Message

Send exactly one human-authored message in Discord `hermes-private-test`.

Recommended message:

```text
operation source 기준으로 스톡슬 운영 답변을 review-only로 짧게 정리해주세요.
```

Do not send multiple test messages. Do not test from public or team channels.

## 7. Expected Logs

Expected successful path:

```text
[PRIVATE_TEST_RAG_LLM_READY] ...
[READONLY_EVENT] accepted_private_test_channel ...
[PRIVATE_TEST_RAG_LLM_REPLY] retrieval_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] context_safety_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] rag_packet_created
[PRIVATE_TEST_RAG_LLM_REPLY] llm_call_allowed
[PRIVATE_TEST_RAG_LLM_REPLY] output_safety_allowed
[PRIVATE_TEST_RAG_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test
[READONLY_EVENT] ignored_self_message ...
[PRIVATE_TEST_RAG_LLM_REPLY] skipped reason=self_message
```

Log expectations:

- `PRIVATE_TEST_RAG_LLM_REPLY_SENT` appears exactly once.
- The self message after the send is ignored.
- `llm_call_allowed` must not appear again after `ignored_self_message`.
- No public or team channel reply appears.
- No raw token, API key value, or raw Discord ID appears.

## 8. Immediate Shutdown

After one successful reply, stop the runtime:

```text
Ctrl+C
```

Then turn gates off in the same PowerShell session:

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_REPLY_ENABLED="false"
```

## 9. Abort Conditions

Immediately press `Ctrl+C` if any of these occur:

- public or team channel event is accepted
- `source=operations` is accepted
- self message triggers retrieval
- self message triggers LLM call
- more than one reply is sent
- output safety blocks but send is attempted
- rate limit or circuit breaker opens
- unknown exception loop appears
- channel name is accepted without channel ID match

After aborting, run the gate-off commands in Section 8.

## 10. After-Run Closeout

The next phase should be:

```text
Phase 33D-4: RAG+LLM single live reply replay/audit closeout
```

The closeout should verify the captured logs and replay/audit state. It should not commit `exports/`, `logs/`, or `apps/hermes_gateway/local/*`.

## 11. Safety Summary

- Codex/agent live runtime execution in Phase 33D-3: false
- Discord message sent by Codex/agent in Phase 33D-3: false
- OpenRouter/LLM API call by Codex/agent in Phase 33D-3: false
- embedding API call in Phase 33D-3: false
- external execution in Phase 33D-3: false
- single live test execution: user-run PowerShell only

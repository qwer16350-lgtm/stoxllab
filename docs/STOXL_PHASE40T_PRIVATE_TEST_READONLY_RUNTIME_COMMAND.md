# STOXL Phase 40T Private-test Read-only Runtime Command

Phase 40T fixes the missing CLI command for the manual private-test read-only
runtime entry:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json
```

This command is blocked by default. In this phase Codex does not start the
Discord live runtime, does not connect the Gateway, does not call Discord API
send, and does not send any Discord message.

The companion report-only preflight command is:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly-preflight --json
```

## Required Manual Runtime Conditions

The command can report `manual_runtime_launch_allowed=true` only when all of the
following are true in the user's own PowerShell session:

- `DISCORD_BOT_TOKEN` is present.
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` is present.
- `HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVED=true`.
- `HERMES_PHASE40J_READONLY_LIVE_RUNTIME_APPROVAL_PHRASE` exactly matches the
  expected internal phrase.
- `HERMES_DISCORD_SEND_MESSAGES=false`.
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=false`.
- `HERMES_DISCORD_REPLY_MODE=readonly_private_test_only`.
- LLM, RAG, embedding/vector, and external execution gates are false.

The report never prints the token, channel id, approval phrase, API key, raw
Discord id, or full message content. It prints presence booleans only.

## Safety Assertions

Even when the preflight passes, Phase 40T reports:

- `started=false`
- `live_runtime_started=false`
- `discord_gateway_connected=false`
- `discord_api_send_called=false`
- `discord_message_sent=false`
- `message_sent_count=0`
- `llm_called=false`
- `rag_called=false`
- `embedding_api_called=false`
- `vector_index_created=false`
- `external_execution=false`

Public/team channel send and reply remain forbidden. Unattended auto reply
remains false.

## Operator Note

Phase 40T only restores the missing argparse command and its safe preflight
report. The actual read-only runtime launch remains a separate manual operator
action after reviewing the blocked/ready report.

## Phase 40T-1 Execute Flag

Phase 40T-1 adds a separate user-only execute flag:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json --execute-readonly-live-runtime
```

Codex must not run this command. Without the execute flag,
`--run-discord-private-test-readonly` remains preflight/report-only and keeps
`started=false`, `live_runtime_started=false`, and
`discord_gateway_connected=false`.

Optional runtime controls:

```powershell
--readonly-runtime-timeout-seconds 60
--readonly-runtime-max-events 10
--readonly-capture-root apps/hermes_gateway/local/captures
```

The execute path is read-only: no send, no reply, no LLM, no RAG, no embedding,
and no external execution.

## Phase 40T-3 Preflight Snapshot

Phase 40T-3 preserves a sanitized boolean-only preflight snapshot into the
execute path. This prevents a successful preflight from later producing a
contradictory failure closeout with token/channel presence set to false.

If token or channel presence is false, the execute path blocks before Discord
login and reports `login_attempted=false`.

If token and channel presence are true but Discord returns LoginFailure or HTTP
401, the failure closeout preserves `discord_token_present=true` and
`private_test_channel_id_present=true`, reports `discord_token_valid=false`,
and uses `discord_login_failure_reason=invalid_or_unauthorized_token`.

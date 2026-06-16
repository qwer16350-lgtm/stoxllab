# STOXL Phase 40T Discord Login Failure Closeout

Phase 40T-2 converts Discord login failures from raw tracebacks into a safe JSON
closeout. The closeout is used when a user-run private-test read-only runtime
fails before Gateway connection, such as an invalid or unauthorized Discord bot
token.

Codex does not run the live runtime or retry Discord login in this phase.

## Report-only Diagnosis

```powershell
python apps\hermes_gateway\cli.py --phase40t-discord-login-failure-closeout --json
```

This command does not attempt Discord login. It returns the expected safe
failure shape only.

## Safe Failure Shape

The report includes:

- `discord_token_present` as a boolean only.
- `discord_token_valid=false`.
- `private_test_channel_id_present` as a boolean only.
- `discord_login_failure_reason=invalid_or_unauthorized_token` for
  LoginFailure or HTTP 401.
- `traceback_included=false`.
- `discord_gateway_connected=false`.
- `discord_api_send_called=false`.
- `discord_message_sent=false`.
- `message_sent_count=0`.
- `retry_attempted=false`.
- `llm_api_call_attempted=false`.
- `rag_called=false`.
- `embedding_api_called=false`.
- `external_execution=false`.

## Never Logged

The closeout must not print:

- Discord bot token value.
- Private test channel ID value.
- Approval phrase value.
- API key value.
- Raw Discord IDs.
- Raw message content.
- `.env` content.
- Raw traceback.

## Operator Action

If this closeout appears after a user-run command, the next action is to refresh
or correct the Discord bot token manually, then rerun the user-only read-only
runtime from the operator's PowerShell session. No automatic retry is allowed.

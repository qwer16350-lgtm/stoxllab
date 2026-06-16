# STOXL Phase 40T Read-only Preflight Snapshot

Phase 40T-3 preserves a sanitized preflight snapshot across the user-only
read-only execute path. The snapshot contains booleans only, so an execute
failure closeout can remain consistent with the preflight that allowed launch
without storing or printing sensitive values.

## Snapshot Fields

The snapshot records:

- `discord_token_present`
- `private_test_channel_id_present`
- `approval_actualized`
- `approval_phrase_present`
- `approval_phrase_exact_match`
- `send_messages_enabled`
- `private_test_reply_enabled`
- `reply_mode_readonly_private_test_only`
- `llm_disabled`
- `rag_disabled`
- `embedding_disabled`
- `external_execution`

It never records token values, channel ID values, approval phrase values, API
keys, raw Discord IDs, raw message content, or `.env` content.

## Missing Env Guard

If token or private-test channel presence is false, the execute path must block
before Discord login:

- `login_attempted=false`
- `discord_login_failure=false`
- `discord_login_failure_reason=missing_token_or_channel`
- `discord_gateway_connected=false`
- `discord_api_send_called=false`
- `discord_message_sent=false`
- `message_sent_count=0`

## Invalid Token Guard

If token and channel presence are true but Discord returns LoginFailure or HTTP
401, the closeout keeps the snapshot presence values:

- `discord_token_present=true`
- `private_test_channel_id_present=true`
- `login_attempted=true`
- `discord_token_valid=false`
- `discord_login_failure_reason=invalid_or_unauthorized_token`

Raw traceback output remains forbidden.

## Consistency Fields

Execute closeouts include:

- `preflight_snapshot_preserved`
- `presence_consistency_verified`
- `login_attempt_requires_token_and_channel`

These fields let operations viewer, dashboard lock, and forbidden behavior
sentinel detect any future mismatch between preflight and closeout reporting.

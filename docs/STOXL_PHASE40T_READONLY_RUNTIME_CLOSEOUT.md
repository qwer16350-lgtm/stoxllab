# STOXL Phase 40T Read-only Runtime Closeout

The Phase 40T closeout summarizes a future user-run read-only runtime. Codex
does not produce an actual live closeout in this implementation phase.

## Closeout Fields

A successful user-run closeout may show:

- `started=true`
- `live_runtime_started=true`
- `discord_gateway_connected=true`
- `capture_file_written=true`
- `ready_for_capture_closeout=true`

It must still show:

- `discord_api_send_called=false`
- `discord_message_sent=false`
- `message_sent_count=0`
- `send_messages_enabled=false`
- `private_test_reply_enabled=false`
- `reply_mode_readonly_private_test_only=true`
- `llm_called=false`
- `rag_called=false`
- `embedding_api_called=false`
- `vector_index_created=false`
- `external_execution=false`
- `ready_for_phase41_reply_runtime=false`
- `ready_for_reply_send=false`

Raw content, raw Discord ids, token, channel id, API key, and approval phrase
values must not be printed or stored.

## Login Failure Closeout

If the runtime fails before Gateway connection because Discord rejects the
token, the closeout type is `phase40t_discord_login_failure_closeout` instead
of a capture closeout. In that state:

- `started=false`
- `live_runtime_started=false`
- `discord_gateway_connected=false`
- `discord_login_failure=true`
- `discord_token_valid=false`
- `traceback_included=false`
- `capture_file_written=false`
- `discord_api_send_called=false`
- `discord_message_sent=false`
- `message_sent_count=0`
- `retry_attempted=false`

The operator must correct the Discord bot token manually before any future
read-only live runtime attempt.

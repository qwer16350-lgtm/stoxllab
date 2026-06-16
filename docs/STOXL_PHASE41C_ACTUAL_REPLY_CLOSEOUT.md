# STOXL Phase 41C Actual Reply Closeout

Phase 41C records the already observed Phase 41B actual private-test reply success. It does not run Discord live runtime, call Discord API send, or send a Discord message.

Closeout rules:

- `message_sent_count=1` with `private_test_only` scope is the locked success shape.
- `discord_api_send_called_during_phase41c=false` and `discord_message_sent_during_phase41c=false` prove Phase 41C did not send.
- The previous failed attempt is recorded as `failed_previous_attempt_message_sent_count=0` and is not counted as success.
- `message_sent_count>1`, public/team scope, or repeat attempts fail.
- Phase 41B repeat send remains blocked.
- Phase 42 supervised deterministic session is the next separate manual gate.
- Self-loop, bot, and duplicate messages are ignored.

No secret values, raw Discord IDs, raw Discord session IDs, or raw message content are emitted.

Example:

- `apps/hermes_gateway/examples/phase41c_actual_reply_closeout_success.example.json`

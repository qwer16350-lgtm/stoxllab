# STOXL Private Test Reply Safety Closeout

Phase 31D closes the private test reply runtime with session-local safety controls.

## Purpose

Phase 31B proved that a human message in `hermes-private-test` can receive one deterministic placeholder reply and that the bot's own reply is skipped as `self_message`. Phase 31D adds additional runtime brakes so the private test path stays bounded after the first successful live test.

## Added Safety Controls

- Cooldown: default `10` seconds between successful replies.
- Session budget: default maximum `3` replies per runtime session.
- Duplicate guard: repeated message IDs are blocked.
- Circuit breaker: send exceptions and rate-limit-like errors open a breaker.
- Self/bot guard: self messages and bot-authored messages never reach send.

## Allowed Case

A reply can be attempted only when all earlier private test gates pass and the Phase 31D safety decision is allowed:

- private test channel ID matches
- source is `agent_placeholder_response`
- author is human
- message ID is not a duplicate
- cooldown has expired
- reply budget remains
- circuit breaker is closed
- LLM, RAG, and external execution are disabled

## Blocked Cases

- `duplicate_message`
- `cooldown_active`
- `reply_budget_exhausted`
- `circuit_breaker_open`
- `send_exception_seen`
- `rate_limit_seen`
- `self_message`
- `bot_message`
- `not_private_test_channel`

## Runtime Logs

```text
[PRIVATE_TEST_REPLY_SAFETY] allowed reply_count=1 max=3
[PRIVATE_TEST_REPLY_SAFETY] blocked reason=cooldown_active
[PRIVATE_TEST_REPLY_SAFETY] blocked reason=reply_budget_exhausted
[PRIVATE_TEST_REPLY_SAFETY] circuit_breaker_open reason=send_exception
```

## Rollback

To stop private test replies without code changes, set any of these in the real local environment:

```env
HERMES_DISCORD_SEND_MESSAGES=false
HERMES_DISCORD_PRIVATE_TEST_REPLY=false
HERMES_DISCORD_REPLY_MODE=disabled
```

The default `.env.example` keeps private test replies disabled.

## Still Not Enabled

- public replies
- team channel replies
- LLM calls
- RAG access
- external execution
- production deployment
- Discord server, channel, or role modification
- buttons, slash commands, or interaction workflows

## Local Reports

```powershell
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --json
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --markdown
```

These reports do not connect to Discord and do not send messages.

## Replay Closeout

Phase 31E adds local replay summaries for sent, blocked, skipped, cooldown, budget, and circuit breaker states:

```powershell
python apps\hermes_gateway\cli.py --private-test-reply-replay-report --json
```

Replay does not call Discord and does not send messages.

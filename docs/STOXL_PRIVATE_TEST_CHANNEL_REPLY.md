# STOXL Private Test Channel Reply

Phase 31B adds the first narrowly guarded Discord reply path.

This is not a general bot reply feature. It is only for one configured private test channel, with deterministic placeholder text, and only when a human explicitly enables all private test flags.

## Required Gates

All gates must be true before a reply can be attempted:

- `HERMES_DISCORD_SEND_MESSAGES=true`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`
- `HERMES_DISCORD_REPLY_MODE=private_test_only`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` is configured
- the observed message channel exactly matches the private test channel ID
- response source is `agent_placeholder_response`
- LLM is disabled
- RAG is disabled
- external execution is disabled

If any gate fails, the runtime records a blocked private test reply audit decision and sends nothing.

## Self-message Loop Guard

Self messages and bot-authored messages never enter the private test reply path.

The runtime skips private reply decision/build/send when any of these are true:

- `message.author.bot=true`
- `message.author.id` matches the connected bot user ID
- visibility decision is `ignored_self_message`
- event `author_is_bot=true`

Expected self-message visibility:

```text
[READONLY_EVENT] ignored_self_message channel=hermes-private-test ...
[PRIVATE_TEST_REPLY] skipped reason=self_message
```

These lines must never appear for a self message:

```text
[PRIVATE_TEST_REPLY] private_test_reply_allowed ...
[PRIVATE_TEST_REPLY_SENT] message_sent=true ...
```

The runtime also keeps an in-memory processed message ID set. A repeated private test message ID is skipped with:

```text
[PRIVATE_TEST_REPLY] skipped reason=skipped_duplicate_message
```

## Phase 31D Safety Closeout

Phase 31D adds session-local safety limits around the private test reply path:

- cooldown, default `10` seconds
- maximum replies per session, default `3`
- duplicate message blocking
- circuit breaker after send exceptions or rate-limit-like failures

Safety report commands:

```powershell
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --json
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --markdown
```

## Unmapped Private Test Channel

The private test channel is not added to the normal work channel mapping.

Instead, the live event pipeline checks the raw channel ID against `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID`. If the ID matches, an otherwise unmapped private test channel can be recorded as:

- `decision=accepted_private_test_channel`
- `channel_is_private_test=true`
- `channel_mapped=false`

The channel name alone is never enough. A channel named `hermes-private-test` is still blocked when the channel ID does not match.

Private test routing is deterministic and local only:

- `마린` or `marin` routes to `marin`
- `루시` or `lucy` routes to `lucy`
- `카스미` or `kasumi` routes to `kasumi`
- `메이코` or `meiko` routes to `meiko`
- `레제` or `reze` routes to `reze`
- no keyword routes to `marin`

No LLM or RAG is used for this routing.

## Still Blocked

- regular `message_create`
- public or team channel replies
- mapped work channel replies such as `marketing-brief`, `operation-brief`, `homepage`, or `new-business`
- reactions
- slash command responses
- button or modal interactions
- Discord server, channel, or role modification
- LLM calls
- RAG reads
- external posting, submission, email, contract, or payment actions

## Message Source

The only allowed source is the deterministic Phase 31C `agent_placeholder_response`.

The rendered reply includes:

- candidate agent
- deterministic placeholder mode
- placeholder title
- placeholder summary
- next step
- review note
- safety lines showing LLM, RAG, and external execution are disabled

It does not include raw token values, `.env` content, full Discord IDs, or raw message content.

## Audit Behavior

Before runtime send, the payload keeps:

- `will_send=true`
- `message_sent=false`
- `message_source=agent_placeholder_response`

After the guarded runtime send function completes in the private test channel, an audit record may show:

- `event_type=private_test_reply_sent`
- `message_sent=true`
- `llm_called=false`
- `rag_called=false`
- `external_execution=false`

Blocked cases use `event_type=private_test_reply_blocked`.

## Console Visibility

When private test replies are enabled, ready visibility separates general send from the private test exception:

```text
[READONLY_READY] runtime_mode=readonly ... general_send_disabled=true private_test_reply_enabled=true private_test_channel_configured=true ...
```

Allowed private test reply:

```text
[PRIVATE_TEST_REPLY] private_test_reply_allowed channel=hermes-private-test source=agent_placeholder_response will_send=true
[PRIVATE_TEST_REPLY_SENT] message_sent=true channel=hermes-private-test
```

Blocked private test reply:

```text
[PRIVATE_TEST_REPLY] blocked reason=channel_not_private_test
```

## Report Command

These commands are local reports only. They do not connect to Discord and do not send messages.

```powershell
python apps\hermes_gateway\cli.py --private-test-reply-report --json
python apps\hermes_gateway\cli.py --private-test-reply-report --markdown
```

## Runtime Command

The strict read-only runtime remains separate:

```powershell
python apps\hermes_gateway\cli.py --run-discord-readonly --json
```

That command still blocks `HERMES_DISCORD_SEND_MESSAGES=true`.

The private test reply runtime uses a separate Phase 31B preflight:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-reply --json
```

It can start only when all private-test gates pass. A failed preflight returns a blocked report such as:

```json
{
  "started": false,
  "blocked": true,
  "reason": "private_test_reply_preflight_failed:reply_mode_private_test_only",
  "message_sent": false
}
```

## Manual Enablement Reminder

The default `.env.example` keeps private test replies disabled. A real `.env` value must be configured manually outside committed files, and the bot token value must never be printed or committed.

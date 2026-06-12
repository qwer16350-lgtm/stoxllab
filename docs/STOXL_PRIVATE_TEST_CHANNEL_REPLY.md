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

## Manual Enablement Reminder

The default `.env.example` keeps private test replies disabled. A real `.env` value must be configured manually outside committed files, and the bot token value must never be printed or committed.

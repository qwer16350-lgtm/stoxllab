# STOXL Discord Send Blocking Guard

Phase 29 keeps all outbound actions blocked by default.

Phase 31B adds one exception type, `private_test_reply_send`, but it is allowed only when the private test reply policy passes every gate. Regular `message_create` remains blocked.

## Guard Module

`apps/hermes_gateway/discord_safety_wrapper.py`

## Blocked Action Families

- Discord message create/update
- Private test reply send unless all Phase 31B gates pass
- Reaction create
- Channel create/update
- Role create/update
- Webhook create
- External post
- External submission
- External email
- Contract-like response
- LLM call
- RAG read

## Required Safety Defaults

- `can_send_messages=false`
- `can_manage_channels=false`
- `can_manage_roles=false`
- `can_execute_external_actions=false`
- `llm_enabled=false`
- `rag_enabled=false`
- `human_only_execution_preserved=true`

## Phase 31B Private Test Exception

`private_test_reply_send` can be allowed only when:

- `send_messages=true`
- `private_test_reply_enabled=true`
- `reply_mode=private_test_only`
- private test channel ID is configured
- `external_execution=false`
- `llm_enabled=false`
- `rag_enabled=false`

This exception does not allow public channel replies, team channel replies, reactions, slash command responses, role changes, channel changes, LLM calls, RAG reads, or external execution.

## Report Command

```powershell
python apps\hermes_gateway\cli.py --send-block-report --json
```

The report is a local safety assertion. It is not a Discord API call and it is not an apply script.

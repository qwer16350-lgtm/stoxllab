# STOXL Discord Send Blocking Guard

Phase 29 keeps all outbound actions blocked by default.

## Guard Module

`apps/hermes_gateway/discord_safety_wrapper.py`

## Blocked Action Families

- Discord message create/update
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

## Report Command

```powershell
python apps\hermes_gateway\cli.py --send-block-report --json
```

The report is a local safety assertion. It is not a Discord API call and it is not an apply script.

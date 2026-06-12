# STOXL Discord Adapter Stub

## Purpose

Phase 18 adds a local future Discord runtime adapter stub. It accepts Discord-shaped raw event dictionaries and produces normalized requests, evaluator results, dispatch plans, and would-send payloads.

This is not a real Discord bot implementation.

## Why This Follows Readiness Checks

Phase 17 confirmed that mapping, env key names, channel placeholders, and safety rules are documented. Phase 18 uses that preparation to define the shape of a future adapter without connecting to Discord.

## Stub vs Real Adapter

The stub:

- reads local JSON raw events
- normalizes event fields
- calls the existing local evaluator bridge
- builds dispatch plans
- renders would-send payloads

The stub does not:

- connect to Discord Gateway
- call Discord APIs
- send Discord messages
- use a bot token
- import `discord.py` or `discord.js`
- call LLM providers
- access external RAG originals
- perform external execution

## Raw Event Shape

The example raw event file is:

```text
apps/hermes_gateway/examples/discord_raw_event_stub.example.json
```

It uses local JSON objects with fields such as:

- `event_type`
- `guild_id`
- `channel_id`
- `channel_name`
- `category_name`
- `author`
- `content`
- `mentions`
- `attachments`
- `timestamp`

Only TODO placeholders are used for Discord IDs.

## Normalized Request Shape

The stub converts raw events into:

- `text`
- `actor_role`
- `actor_agent`
- `author_display_name`
- `source_channel`
- `source_category`
- `mentioned_agents`
- `requested_action`
- `requested_source`
- `current_status`
- `requested_next_status`
- `attachments`
- `timestamp`

Attachment originals are not stored.

## Would-Send Payload

The renderer returns:

```json
{
  "would_send": true,
  "message_kind": "",
  "target_channel": "",
  "content": "",
  "metadata": {},
  "safety": {
    "discord_api_called": false,
    "message_sent": false,
    "external_execution": false,
    "human_only_execution": true
  }
}
```

Message kinds:

- `agent_dispatch`
- `blocked_request`
- `approval_required`
- `review_packet_hint`
- `audit_notice`

## Message Renderer

`message_renderer.py` creates short Korean review messages for local inspection. It redacts secret-like content and never sends anything.

## Usage

```powershell
python apps\hermes_gateway\cli.py --discord-raw-event apps\hermes_gateway\examples\discord_raw_event_stub.example.json --json
python apps\hermes_gateway\tests\test_discord_adapter_stub.py
```

## Safety

The adapter stub preserves:

```text
discord_api_called=false
gateway_connected=false
message_sent=false
external_execution=false
human_only_execution=true
```

## Phase 19+ Plan

- strengthen channel ID mapping validation
- local message replay with would-send payload snapshots
- prepare read-only private server connection checklist

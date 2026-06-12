# STOXL Reply Planner Disabled By Default

## Purpose

The reply planner defines how a future reply could be planned from a would-send payload without sending anything.

## Default Mode

Reply planning is disabled by default.

Allowed planning modes:

- `disabled`
- `would_send_only`
- `private_test_later`

The current mode is would-send only. It never sends a Discord message.

## Restrictions

- public channel replies are forbidden
- real Discord sends are forbidden
- blocked requests can only produce a blocked notice plan
- enabling replies requires a later explicit phase

## Safety Flags

Each reply plan keeps:

- `discord_api_called=false`
- `message_sent=false`
- `external_execution=false`
- `human_only_execution=true`

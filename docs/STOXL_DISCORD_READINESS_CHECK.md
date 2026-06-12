# STOXL Discord Readiness Check

## Purpose

Phase 17 prepares for a future read-only Discord connection by adding a local readiness checker and a runtime mapping template.

This phase does not connect to Discord. It does not call the Discord API, open a Gateway connection, request a bot token value, read `.env`, or run a real bot.

## Why This Comes After Review Packets

Phase 16 created approval review packets for Decision Makers. Before any future Discord read-only adapter can consume real channel events, the project needs a way to check that channel, role, owner, approval, audit, and safety mappings are prepared without exposing secrets.

## What The Checker Verifies

- Required Discord env key names are documented in `.env.example`.
- `registry/stoxl_agent_registry.example.json` exists and can be read.
- The mapping template exists and parses.
- All registry channels are represented in the mapping template.
- Decision Maker owner placeholders are present.
- The final approval channel is mapped.
- Discord intent requirements are documented as a checklist.
- Phase 17 safety rules remain active.
- External execution remains disabled.

## Required Env Key Names

The checker only verifies that these key names are documented. It does not request or read real values.

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`
- `HERMES_CONFIG_PATH`

## Mapping Template

The template is:

```text
apps/hermes_gateway/examples/discord_runtime_mapping.template.json
```

It contains:

- guild placeholder
- owner placeholders
- role placeholders
- category placeholders
- channel placeholders
- intent checklist
- approval interaction notes
- audit locations
- safety rules

All real Discord IDs must be filled later in a private runtime mapping file, not in the committed template.

## Discord Intents Checklist

The template documents these future needs:

- guilds
- guild messages
- message content
- reactions later
- members later
- slash commands later
- approval buttons later

No intent is enabled in Phase 17.

## Approval Interactions

Approval is still mock-only. Future options are documented as:

- reaction
- button
- slash command
- manual CLI

Even after approval:

```text
external_execution_after_approval=false
human_only_execution=true
```

## Usage

```powershell
python apps\hermes_gateway\cli.py --discord-readiness --json
python apps\hermes_gateway\cli.py --discord-readiness --mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --json
python apps\hermes_gateway\tests\test_discord_readiness.py
```

## Safety Guarantees

The readiness report always states:

```json
{
  "discord_api_called": false,
  "gateway_connected": false,
  "bot_token_required": false,
  "external_execution_enabled": false,
  "human_only_execution_preserved": true
}
```

## Next Phase Suggestions

- Phase 18: Discord adapter stub, still no Gateway connection.
- Phase 19: local channel ID mapping validation.
- Phase 20: read-only private server connection after explicit approval.

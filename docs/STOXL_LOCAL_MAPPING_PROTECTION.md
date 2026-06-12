# STOXL Local Mapping Protection

## Purpose

Phase 22 adds a protected local folder and helper for managing a private Discord runtime mapping file.

This phase does not fill real Discord IDs, connect to Discord, call Discord APIs, read `.env`, request a Bot Token, or send messages.

## Relationship To Earlier Phases

Phase 20 added the Discord runtime mapping validator.

Phase 21 documented the private server read-only plan and manual mapping workflow.

Phase 22 makes that workflow safer by adding:

- ignored local runtime mapping folder
- copy helper from template to local mapping
- local mapping validation helper
- strict validation support
- overwrite protection

## Why Local Mapping Must Be Ignored

A runtime mapping can contain actual Discord server, channel, role, and user IDs. Those values are not Bot Tokens or API keys, but they are still private runtime identifiers.

The repo now ignores:

```gitignore
apps/hermes_gateway/local/*
!apps/hermes_gateway/local/.gitkeep
!apps/hermes_gateway/local/README.md
```

This keeps `discord_runtime_mapping.local.json` out of git while preserving the folder and its README.

## Local Mapping Path

Recommended local file:

```text
apps/hermes_gateway/local/discord_runtime_mapping.local.json
```

This file is not committed.

## Create Local Mapping

```powershell
python apps\hermes_gateway\cli.py --init-local-mapping --json
```

This copies:

```text
apps/hermes_gateway/examples/discord_runtime_mapping.template.json
```

to:

```text
apps/hermes_gateway/local/discord_runtime_mapping.local.json
```

If the local file already exists, the helper refuses to overwrite it.

To intentionally overwrite:

```powershell
python apps\hermes_gateway\cli.py --init-local-mapping --force --json
```

Use `--force` carefully because it can replace locally filled IDs.

## Validate Local Mapping

```powershell
python apps\hermes_gateway\cli.py --validate-local-mapping --json
python apps\hermes_gateway\cli.py --validate-local-mapping --strict --json
```

Non-strict validation can report TODO placeholders as manual work.

Strict validation treats TODO placeholders as failures.

## What May Go In The Mapping

The local mapping may contain:

- Discord guild ID
- Discord channel IDs
- Discord role IDs
- Discord owner user IDs
- audit channel ID
- read-only bot role ID

## What Must Not Go In The Mapping

Never put these in the mapping:

- Discord Bot Token
- OpenAI API key
- OpenRouter API key
- password
- secret
- DB credential
- NAS credential
- private key
- access key
- refresh token

The mapping validator flags secret-like values and redacts them in reports.

## Read-Only Connection Gate

Before any later real Discord read-only connection:

- local mapping exists
- strict validation passes
- TODO placeholder count is 0
- secret-like value count is 0
- `ready_for_readonly_connection=true`
- message send remains disabled
- external execution remains disabled
- human-only execution remains preserved

Passing this gate does not itself authorize a Discord connection. It only means the local mapping file is structurally ready for a later approved phase.

## Safety Assertions

The local mapping helper reports:

- `discord_api_called=false`
- `gateway_connected=false`
- `bot_token_required=false`
- `env_file_read=false`
- `message_sent=false`
- `external_execution_enabled=false`
- `human_only_execution_preserved=true`

## Next Phase Candidates

- Phase 23: local mapping fill walkthrough
- Phase 24: read-only Discord dependency plan
- Phase 25: private server read-only connection dry-run

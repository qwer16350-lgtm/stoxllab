# STOXL Discord Manual Mapping Guide

## Purpose

This guide explains how a human can copy `discord_runtime_mapping.template.json` and fill actual Discord IDs in a private runtime mapping file.

This is not a secret or token guide. Do not put Bot Tokens, API keys, passwords, DB credentials, NAS credentials, or provider credentials in the mapping file.

## Recommended Copy Path

Recommended private path:

```text
apps/hermes_gateway/local/discord_runtime_mapping.local.json
```

Phase 21 does not create this file. The path is documented only as a suggested local-only location for a later phase.

## Git Safety

The local mapping file should not be committed to git.

Before using a real mapping file, confirm that local/private mapping paths are excluded from version control. If no `.gitignore` rule exists for that path, add or verify it in a later approved phase.

## How To Find Discord IDs

1. Open Discord user settings.
2. Enable Developer Mode.
3. Right-click the private test server and copy the server ID.
4. Right-click each channel and copy channel IDs.
5. Right-click each role and copy role IDs.
6. Right-click each owner user and copy user IDs.

Only use IDs from the private test server intended for the read-only trial.

## Values To Fill

Fill these mapping sections:

- `guild`
- `owners`
- `roles`
- `categories`
- `channels`
- `audit`
- approval channel mapping
- read-only bot role mapping

Required owner env key references:

- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`

Required roles:

- `Decision Maker`
- `Lucy`
- `Marin`
- `Meiko`
- `Kasumi`
- `Reze`
- `Human Operator`
- `Read Only Bot`

Required channel coverage:

- all channels listed in the generated registry
- final approval channel
- owner meeting channel
- junior/senior handoff channels
- archive channels
- audit log channel

## Values Not To Fill

Do not put these in the mapping file:

- Bot Token
- OpenAI API key
- OpenRouter API key
- password
- secret
- DB credential
- NAS credential
- private key
- access key
- refresh token

If a value looks like a credential rather than a Discord ID, stop and do not paste it.

## Validation Commands

After filling a private local mapping file:

```powershell
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\local\discord_runtime_mapping.local.json --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\local\discord_runtime_mapping.local.json --strict --json
```

## Pass Criteria

Before any read-only connection phase:

- non-strict validation has no blocked reasons
- strict validation has zero TODO placeholders
- two owner mappings exist
- all required roles exist
- all registry channels are mapped
- approval channel exists
- audit channel exists
- secret-like values count is 0
- `ready_for_readonly_connection=true`
- Bot Token is not in the mapping file

## Final Reminder

Mapping validation is still local. Passing validation does not mean a bot may connect to Discord. A later phase must explicitly approve any real read-only connection.

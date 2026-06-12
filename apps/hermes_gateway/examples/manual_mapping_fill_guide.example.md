# Manual Mapping Fill Guide

This is a short checklist for filling a private Discord runtime mapping file.

Do not put tokens, API keys, passwords, provider keys, DB credentials, or NAS credentials in the mapping file.

## 1. Copy The Template

Copy:

```text
apps/hermes_gateway/examples/discord_runtime_mapping.template.json
```

Suggested private local copy:

```text
apps/hermes_gateway/local/discord_runtime_mapping.local.json
```

Do not commit the local copy.

## 2. Enable Discord Developer Mode

In Discord:

1. Open User Settings.
2. Open Advanced.
3. Enable Developer Mode.

## 3. Fill Server And Owner IDs

Fill:

- `DISCORD_GUILD_ID`
- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`

Use only the private test server and the intended owner accounts.

## 4. Fill Role IDs

Fill role IDs for:

- `Decision Maker`
- `Lucy`
- `Marin`
- `Meiko`
- `Kasumi`
- `Reze`
- `Human Operator`
- `Read Only Bot`

The Read Only Bot role must not have message send or manage server permissions.

## 5. Fill Channel IDs

Fill all mapped channel IDs, including:

- `대표-회의실`
- `최종-승인요청`
- `marin-초안`
- `lucy-검토`
- `kasumi-리서치`
- `meiko-검토`
- `reze-전략기획`
- `공모전-지원사업`
- `일정-마감관리`
- archive channels
- audit log channel

## 6. Validate

Run:

```powershell
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\local\discord_runtime_mapping.local.json --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\local\discord_runtime_mapping.local.json --strict --json
```

Expected before moving forward:

- `overall_valid=true`
- `ready_for_readonly_connection=true`
- `todo_placeholders=0`
- `secret_like_values=0`

## 7. Stop If Any Forbidden Value Appears

Stop if the mapping contains:

- Bot Token
- OpenAI API key
- OpenRouter API key
- password
- secret
- DB credential
- NAS credential
- bearer token
- private key

## 8. Final Human Review

Before any later real read-only connection:

- review rollback plan
- confirm message send disabled
- confirm external execution disabled
- confirm human-only execution
- confirm private test server only

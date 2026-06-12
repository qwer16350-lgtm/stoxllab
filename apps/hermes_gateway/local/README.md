# Hermes Gateway Local Runtime Mapping

This folder is for a private local copy of the Discord runtime mapping.

Recommended file name:

```text
discord_runtime_mapping.local.json
```

The local mapping may contain actual Discord server, channel, role, and user IDs. It must not be committed to git.

Do not put these values in this folder:

- Discord Bot Token
- API key
- password
- secret
- DB credential
- NAS credential
- provider credential

Do not create a `.env` file here.

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

Existing local mapping files are not overwritten unless `--force` is used.

## Validate Local Mapping

```powershell
python apps\hermes_gateway\cli.py --validate-local-mapping --json
python apps\hermes_gateway\cli.py --validate-local-mapping --strict --json
```

Strict validation must pass before any later real Discord read-only connection is considered.

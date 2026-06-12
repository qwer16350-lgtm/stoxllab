# STOXL Actual Read-only Discord Connection

Phase 29 adds a code path for a later actual Discord Gateway connection in read-only mode.

This phase does not run the Gateway, does not call the Discord API during tests, does not send messages, and does not print token values.

## Scope

- Runtime module: `apps/hermes_gateway/discord_readonly_runtime.py`
- Token report module: `apps/hermes_gateway/discord_token_loader.py`
- CLI reports:
  - `python apps\hermes_gateway\cli.py --discord-token-report --json`
  - `python apps\hermes_gateway\cli.py --discord-readonly-runtime-report --json`

## Runtime Mode

- `HERMES_DISCORD_RUNTIME_MODE=readonly`
- `HERMES_DISCORD_SEND_MESSAGES=false`
- `HERMES_DISCORD_EXTERNAL_EXECUTION=false`
- `HERMES_DISCORD_LLM_ENABLED=false`
- `HERMES_DISCORD_RAG_ENABLED=false`

The read-only runtime may only be started by a human with explicit approval. The normal validation and report commands do not connect to Discord.

## Phase 23 vs Phase 29 Readiness

Phase 23 no-connection preflight still treats a declared Discord runtime dependency as a failure, because that phase is planning-only.

Phase 29 read-only runtime readiness uses a separate check. In this phase, `discord.py` in `requirements.txt` is allowed, while these runtime conditions remain mandatory:

- local mapping strict validation is ready
- `token_present=true` is available to runtime startup
- send messages flag is false
- external execution flag is false
- LLM flag is false
- RAG flag is false
- send blocking guard is active
- token value is not logged

## Token Handling

- `DISCORD_BOT_TOKEN` is referenced only by key name in `.env.example`.
- Reports show only `token_present=true/false`.
- Token values are not printed, returned in JSON reports, committed, or written to files.
- Actual `.env` content is not documented in this repo.

## Human-only Execution

Even after a decision maker approves an action, the bot system does not perform external posting, submission, email, contract, payment, RAG ingest, or LLM execution. These remain human-only actions.

## Manual Run Command

Reserved for a later approved private server read-only run:

```powershell
python apps\hermes_gateway\cli.py --run-discord-readonly --json
```

This command is not part of the automated test flow and was not executed in Phase 29.

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
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=false`
- `HERMES_DISCORD_REPLY_MODE=disabled`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=`
- `HERMES_DISCORD_EXTERNAL_EXECUTION=false`
- `HERMES_DISCORD_LLM_ENABLED=false`
- `HERMES_DISCORD_RAG_ENABLED=false`

The read-only runtime may only be started by a human with explicit approval. The normal validation and report commands do not connect to Discord.

## Phase 31B Private Test Reply Exception

The runtime can support one manually enabled private test channel reply path. It is disabled by default and is not part of the normal read-only report flow.

The exception requires:

- `HERMES_DISCORD_SEND_MESSAGES=true`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`
- `HERMES_DISCORD_REPLY_MODE=private_test_only`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` matching the observed event channel
- deterministic `agent_placeholder_response` source
- `HERMES_DISCORD_EXTERNAL_EXECUTION=false`
- `HERMES_DISCORD_LLM_ENABLED=false`
- `HERMES_DISCORD_RAG_ENABLED=false`

All mapped work channels and public/team channels remain no-reply zones. The exception does not allow LLM, RAG, external execution, reactions, slash commands, server modification, channel modification, or role modification.

The private test channel is identified by channel ID, not by name and not by normal work channel mapping. If the configured ID matches, the live event can be recorded as `accepted_private_test_channel` even when `channel_mapped=false`.

## Live Visibility

When the read-only runtime is actually started by a human, it prints a redaction-safe ready line:

```text
[READONLY_READY] runtime_mode=readonly bot_user=name:discord_id_redacted:1234 guilds=1 target_guild_configured=true general_send_disabled=true private_test_reply_enabled=true private_test_channel_configured=true external_disabled=true llm_disabled=true rag_disabled=true
```

Each observed message also prints one redaction-safe event line and appends a JSONL record under `logs/hermes_gateway/live_events/`.

No message content, token value, full user ID, or full channel ID is printed.

Private test reply visibility is also redaction-safe:

```text
[PRIVATE_TEST_REPLY] private_test_reply_allowed channel=hermes-private-test source=agent_placeholder_response will_send=true
[PRIVATE_TEST_REPLY_SENT] message_sent=true channel=hermes-private-test
```

Blocked cases print only the reason, for example:

```text
[PRIVATE_TEST_REPLY] blocked reason=channel_not_private_test
```

Self messages are skipped before private reply decision/build/send:

```text
[READONLY_EVENT] ignored_self_message channel=hermes-private-test ...
[PRIVATE_TEST_REPLY] skipped reason=self_message
```

Duplicate message IDs are skipped in memory to avoid repeat replies:

```text
[PRIVATE_TEST_REPLY] skipped reason=skipped_duplicate_message
```

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

Reserved for a later approved private server strict read-only run:

```powershell
python apps\hermes_gateway\cli.py --run-discord-readonly --json
```

This command still blocks `HERMES_DISCORD_SEND_MESSAGES=true`.

Reserved for a later approved private test reply run:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-reply --json
```

This command uses the Phase 31B private test reply preflight. It requires send messages, private test reply, private-test-only mode, a configured private test channel ID, and disabled external execution, LLM, and RAG.

Neither command is part of the automated test flow.

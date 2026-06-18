# STOXL Phase74 Limited Auto Mode Prep

Phase74 prepares limited supervised auto mode for the next separate Manual
Gate. It is not production unattended mode, does not execute Discord runtime,
does not perform real Discord send, does not call LLM/OpenRouter or RAG, does
not create embedding/vector data, and does not start scheduler/cron live
execution.

Allowed scope:

- Known team channel only.
- Low-risk intent only.
- Deterministic template only.
- Review packet exists.
- Ops queue item exists.
- Max session seconds.
- Max send count.
- Max reply count.
- Cooldown seconds.
- Kill switch ready.
- Manual Gate required.
- Human override available.

Blocked scope:

- Public channel.
- Unknown channel.
- High-risk intent.
- Secret, token, or API key handling.
- Legal or financial advice.
- Code deploy or push.
- External command execution.
- File delete/write outside allowed docs.
- LLM/RAG live reply.
- Scheduler live.
- Multi-message send.
- Unbounded session.
- Production unattended.

Manual Gate keys:

- `HERMES_PHASE74_LIMITED_AUTO_APPROVED`
- `HERMES_PHASE74_LIMITED_AUTO_APPROVAL_PHRASE`
- `HERMES_PHASE74_LIMITED_AUTO_CHANNEL_ID`
- `HERMES_PHASE74_LIMITED_AUTO_KILL_SWITCH_READY`
- `HERMES_PHASE74_LIMITED_AUTO_MAX_SESSION_SECONDS`
- `HERMES_PHASE74_LIMITED_AUTO_MAX_SEND_COUNT`
- `HERMES_PHASE74_LIMITED_AUTO_MAX_REPLY_COUNT`
- `HERMES_PHASE74_LIMITED_AUTO_COOLDOWN_SECONDS`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`
- `HERMES_SCHEDULER_LIVE_ENABLED`

Required reply mode:

```text
limited_team_low_risk_auto_mode_only
```

Reports must not log approval phrase values, team channel ID values, raw
Discord IDs, raw content, API keys, tokens, or secrets.

CLI reports:

```powershell
python apps\hermes_gateway\cli.py --phase74-limited-auto-mode-prep --json
python apps\hermes_gateway\cli.py --phase74-limited-auto-mode-preflight --json
python apps\hermes_gateway\cli.py --actual-phase74-limited-auto-mode --json
```

The actual path remains default blocked. The allow command is reserved for a
later separate Manual Gate and is not executed in this Safe Bundle.

Current verified level:

```text
level4_supervised_team_channel_auto_ops_verified_once
```

Next target level:

```text
level4_limited_auto_mode_short_run
```

Level matrix:

- Level 1: read-only observation verified.
- Level 2: manual deterministic reply verified.
- Level 3: supervised private-test auto-reply verified.
- Level 4: low-risk team-channel canary verified once.
- Level 4: supervised team-channel auto-ops verified once.
- Level 4: limited auto mode prepared, not executed.
- Level 5: production unattended not ready.

Next actual operation must be a separate Manual Gate for actual Phase74 limited
auto mode short run exactly once.

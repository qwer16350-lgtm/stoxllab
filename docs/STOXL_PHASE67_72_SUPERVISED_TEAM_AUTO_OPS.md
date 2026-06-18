# STOXL Phase67-72 Supervised Team Auto-Ops

This Large Lean Safe Bundle prepares supervised team-channel auto-ops after the
Phase60 low-risk team canary was verified exactly once. It performs no actual
Discord runtime, no real Discord send, no LLM/RAG, no external execution, and no
scheduler live execution.

Phase67 Safe Closeout:

- Phase67 actual supervised team-channel auto-ops was already executed exactly
  once before closeout.
- Historical `message_sent_count` is fixed at `1`.
- Closeout performs no new Discord send.
- Repeat Phase67 team auto-ops send is locked with
  `phase67_team_auto_ops_already_consumed`.
- Historical real-send semantics are recorded as
  `real_team_auto_ops_send_performed=true` only in the metadata-only closeout.

Pipeline:

- Team-channel event classifier.
- Low-risk intent classifier.
- Ops queue.
- Review packet.
- Deterministic reply candidate.
- Manual Gate before any actual send.

Manual Gate keys:

- `HERMES_PHASE67_TEAM_AUTO_OPS_APPROVED`
- `HERMES_PHASE67_TEAM_AUTO_OPS_APPROVAL_PHRASE`
- `HERMES_PHASE67_TEAM_AUTO_OPS_CHANNEL_ID`
- `HERMES_PHASE67_TEAM_AUTO_OPS_KILL_SWITCH_READY`
- `HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SESSION_SECONDS`
- `HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SEND_COUNT`
- `HERMES_PHASE67_TEAM_AUTO_OPS_MAX_REPLY_COUNT`
- `HERMES_PHASE67_TEAM_AUTO_OPS_COOLDOWN_SECONDS`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`

Reply mode:

```text
supervised_team_low_risk_auto_ops_only
```

Approval phrase:

```text
I_APPROVE_PHASE67_TEAM_AUTO_OPS
```

Reports must not log the approval phrase value or team channel ID value.

Safety:

- Public, unknown, high-risk, and multi-message events are blocked.
- LLM/OpenRouter, RAG, embedding/vector, external execution, scheduler live
  execution, and production unattended mode remain disabled.
- Phase60 consumed lock remains preserved.
- Actual team auto-ops send is default blocked and reserved for a separate
  Manual Gate exactly once.

Autonomy matrix:

- Level 1: read-only observation verified.
- Level 2: manual-gate deterministic reply verified.
- Level 3: supervised private-test auto-reply verified.
- Level 4: low-risk team-channel canary verified once.
- Level 4: supervised team-channel auto-ops verified once.
- Level 5: production unattended not ready.

Next target is Limited Auto Mode Prep. Next actual operation must be a separate
Manual Gate.

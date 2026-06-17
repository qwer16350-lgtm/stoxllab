# STOXL Phase60-65 Team Canary Autonomy Stage

This Large Lean Mega Bundle prepares the low-risk team-channel canary path
without actual Discord runtime, real Discord send, LLM/RAG, external execution,
or scheduler live execution.

Phase60 team canary path:

- Team canary actual path is available.
- Manual Gate is required.
- Known team channel only.
- Non-public only.
- Low-risk intent only.
- Deterministic template only.
- Max one reply per event.
- Human override and kill switch are required.
- LLM/RAG, embedding/vector, external execution, and scheduler live execution
  stay disabled by default.

Manual Gate keys:

- `HERMES_PHASE60_TEAM_CANARY_APPROVED`
- `HERMES_PHASE60_TEAM_CANARY_APPROVAL_PHRASE`
- `HERMES_PHASE60_TEAM_CANARY_KILL_SWITCH_READY`
- `HERMES_PHASE60_TEAM_CANARY_MAX_SEND_COUNT`
- `HERMES_PHASE60_TEAM_CANARY_MAX_REPLY_COUNT`
- `HERMES_PHASE60_TEAM_CANARY_COOLDOWN_SECONDS`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`

Reply mode:

```text
known_team_low_risk_canary_only
```

Approval phrase:

```text
I_APPROVE_PHASE60_TEAM_CANARY
```

The approval phrase value must not be printed in reports or logs. Reports emit
only boolean presence and exact-match fields.

Low-risk examples:

- Status summary.
- Simple acknowledgement.
- Meeting/reminder style non-sensitive ops note.
- Review packet ready notice.

High-risk blocked examples:

- Legal or financial advice.
- Secret/API key/token handling.
- File deletion.
- Code push/deploy.
- External command execution.
- Public channel message.
- Unknown channel.
- Multi-message send.
- LLM/RAG live reply without Manual Gate.

Phase61 scheduler sync:

- Dry-run preview categories remain available:
  `daily_summary_preview`, `read_only_digest_preview`,
  `review_packet_queue_summary`, and `manual_gate_reminder_preview`.
- Live categories remain blocked: `auto_send`, `auto_reply`,
  `live_cron_start`, `external_execution`,
  `llm_call_without_manual_gate`, and `rag_call_without_manual_gate`.

Phase62/65 autonomy:

- Level 1: read-only observation verified.
- Level 2: manual-gate deterministic reply verified.
- Level 3: supervised private-test auto-reply verified.
- Level 4: low-risk team-channel canary path ready, not executed.
- Level 5: production unattended not ready.

Next actual operation must be a separate Manual Gate: actual Phase60 low-risk
team-channel canary exactly once.

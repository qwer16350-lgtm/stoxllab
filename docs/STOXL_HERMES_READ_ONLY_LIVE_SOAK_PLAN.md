# STOXL Hermes Read-Only Live Soak Plan

Read-only soak is live observation only.

This step only prepares the plan/preflight. Actual soak requires separate
Manual Gate. Production unattended remains blocked.

This plan does not execute Discord runtime, connect to Discord Gateway, call
Discord API send, send Discord messages, call LLM/OpenRouter, call RAG, create
embeddings or vectors, run scheduler/cron live execution, or execute external
actions.

Scope:

- Observation only.
- No send/reply.
- No LLM/RAG.
- No external execution.
- No scheduler live.
- Metadata-only capture policy.
- Token, channel ID, approval phrase, raw Discord ID, raw session ID, and raw
  content values must not be logged.

Recommended bounds:

- Duration: 300 seconds.
- Max events: 25.

Stop conditions:

- Any send attempted.
- Any reply attempted.
- LLM or RAG call attempted.
- External execution attempted.
- Scheduler live starts.
- Secret value logged.
- Raw Discord ID logged.
- Raw user content dumped.
- Event count exceeds configured max.
- Operator kill switch triggered.

Success criteria:

- Gateway connects.
- Events captured as metadata only.
- No send/reply.
- No LLM/RAG/external/scheduler.
- No raw/secrets/channel values.
- Operator can stop session.
- Post-soak review packet generated.

Report commands:

```powershell
python apps\hermes_gateway\cli.py --hermes-read-only-soak-plan --json
python apps\hermes_gateway\cli.py --hermes-read-only-soak-preflight --json
python apps\hermes_gateway\cli.py --actual-read-only-live-soak --json
```

Later Manual Gate placeholder:

```powershell
python apps\hermes_gateway\cli.py --actual-read-only-live-soak --json --allow-actual-read-only-live-soak
```

In this phase, the actual command is default blocked and does not connect to
Discord Gateway.

Recommended next stage: Manual Gate - actual read-only live soak, no send.

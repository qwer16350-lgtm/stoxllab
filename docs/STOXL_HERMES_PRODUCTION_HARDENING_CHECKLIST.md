# STOXL Hermes Production Hardening Checklist

MVP complete does not mean production unattended ready.

Production unattended is still blocked. This checklist is report-only and does
not execute Discord runtime, connect to Discord Gateway, call Discord API send,
send Discord messages, call LLM/OpenRouter, call RAG, create embeddings or
vectors, run scheduler/cron live execution, or execute external actions.

Required hardening categories:

- kill switch
- rollback
- rate limit
- cooldown
- max session
- max send count
- max reply count
- audit log
- secret redaction
- channel scope
- public/unknown block
- high-risk block
- LLM/RAG disabled by default
- external execution disabled
- scheduler live disabled
- Manual Gate required
- operator override
- repeat lock integrity
- env presence boolean only
- dry-run required before live

Required before production unattended:

- Kill switch live tested: false
- Rollback runbook tested: false
- Rate limit live tested: false
- Audit log persistence tested: false
- Long-running runtime soak tested: false
- Scheduler live tested: false
- Production env reviewed: false
- Operator on-call defined: false
- Cost guard tested: false
- Incident stop procedure tested: false

Safety defaults:

- Next live action must require Manual Gate.
- Scheduler live remains disabled by default.
- LLM/RAG live reply remains disabled by default.
- External execution remains disabled.
- Public, unknown, and high-risk auto reply remain blocked.
- Consumed/no-repeat locks remain authoritative.
- Token, channel ID, API key, approval phrase, raw Discord ID, raw session ID,
  and raw content values must not be logged.

SSOT references:

- MVP state registry: `apps/hermes_gateway/mvp_state_registry.py`
- Runtime facade: `apps/hermes_gateway/runtime_facade.py`
- Docs consolidation index: `apps/hermes_gateway/docs_consolidation_index.py`

Report command:

```powershell
python apps\hermes_gateway\cli.py --hermes-production-hardening-checklist --json
```

Recommended next stage: Production Hardening G - dry-run safety audit, no live
action.

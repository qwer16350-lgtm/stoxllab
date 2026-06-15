# STOXL Phase 35 Entry Plan

Phase 35 should stay within report-only or local-only work unless a later request explicitly opens a new manual gate.

## Allowed Next Work

A. Local knowledge ingestion UX improvement

- Still local text only.
- No embedding.
- No external source.
- No live Discord.
- Strengthen source canonical validation.
- Phase 35B adds report-only local knowledge ingestion preview.

B. Evidence quality scoring

- Citation sufficiency.
- Duplicate evidence detection.
- Stale document detection.
- Relative path only.
- Phase 35B adds dry evidence quality preview.

C. Agent routing preview

- Marin/Lucy/Kasumi/Meiko/Reze routing dry preview.
- Enforce `operation`, not `operations`.
- No LLM call.
- No Discord send.
- Phase 35B adds rule-only agent routing dry preview.

D. Operator dashboard

- Final lock, audit, and viewer summary hardening.
- Report-only.

## Hold

- Embedding/vector DB.
- Actual Discord multi-turn private-test runtime.
- OpenRouter multi-call mode.
- Scheduler/cron.
- File watcher ingestion.

## Forbidden

- Public/team channel auto reply.
- Unattended auto reply.
- External execution.
- Token/key logging.
- Raw Discord ID logging.
- Approval phrase logging.

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

E. Agent evidence/prompt preview

- Agent-specific evidence packs.
- Prompt preview summaries only.
- No full content.
- No LLM call.
- No Discord send.

F. Agent review and manual approval packet preview

- Agent-specific review packets for human inspection.
- Manual approval gate preview only.
- No approval phrase generation.
- No actual approval.
- No LLM call.
- No Discord send.
- No embedding or external source access.

G. No-live operator rehearsal and safety lock

- Operator checklist and no-live rehearsal only.
- Operations dashboard lock summarizes Phase 34M and Phase 35A-D state.
- Forbidden behavior sentinel fails if public/team, unattended, embedding,
  external execution, full content, secret logging, or approval phrase
  generation is re-enabled.
- Phase 36 entry gate is report-only and keeps live execution false.

## Phase 36A Safe Preflight

- Private-test one-shot LLM draft preflight only.
- No LLM API call.
- No Discord send.
- No approval phrase generation.
- `kasumi` may be listed as a future candidate from operation evidence.
- Actual LLM draft remains blocked until a later explicit approval phase.

## Phase 36B Safe Mock

- Mock one-shot LLM draft packet only.
- Output safety rehearsal only.
- No OpenRouter/LLM API call or attempt.
- No Discord send.
- Negative fixtures must block secret values, approval phrases, raw Discord IDs,
  public/team send instructions, unattended reply instructions, and full content.

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

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

## Phase 36C Safe Preflight

- Actual one-shot LLM draft call preflight only.
- OpenRouter key presence is reported as a boolean only.
- No LLM API call or attempt.
- No Discord send.
- No approval phrase generation or manual approval activation.
- `ready_for_actual_llm_call=false` remains locked.

## Phase 36F-G Safe Lock

- Phase 36 LLM draft call count is locked to `1`.
- Phase 36 Discord send/message count is locked to `0`.
- Dashboard and forbidden behavior sentinel remain report-only.
- Phase 37 entry gate is available, but Phase 37 live/send execution is not started.

## Phase 37A-C Safe Preview

- Private-test LLM draft review packet only.
- Private-test Discord send preflight preview only.
- Private-test send approval rehearsal only.
- No new LLM call, Discord send, approval phrase generation, embedding, or external execution.

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
# Phase 38A-E Note

The current safe maximum path includes Phase 38A-E report-only preparation for a
future private-test send: contract, payload freeze, rollback gate, operator
checklist, and live send entry gate. This does not start Phase 39, does not send
Discord messages, and does not enable unattended replies.

# Phase 39A Note

Phase 39A adds the actual private-test one-shot send path as an implementation
boundary that is still default blocked.

- Discord live runtime: not run.
- Discord API send: not called.
- Discord message sent: false.
- Actual private-test send executed: false.
- OpenRouter/LLM API call attempted: false.
- Approval phrase generated: false.
- Manual approval actualized: false.
- Embedding/vector creation: false.
- External execution: false.
- Public/team channel send or reply: forbidden.
- Unattended auto reply: false.
- Phase 39B manual one-shot actual send: not run.

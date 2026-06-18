# STOXL Hermes Post-MVP Compaction Plan

MVP supervised Discord Agent OS complete. Production unattended not ready.

This plan is report-only. It does not delete files, move files, remove CLI
commands, weaken Manual Gates, weaken consumed/no-repeat locks, execute Discord
runtime, perform Discord send, call LLM/OpenRouter or RAG, create embeddings or
vectors, run external execution, or start scheduler/cron live execution.

Current frozen state:

- `mvp_supervised_discord_agent_os_complete=true`
- `current_verified_level=level4_limited_auto_mode_short_run_verified_once`
- `production_unattended_ready=false`
- `next_target_level=production_hardening_refactor_compaction`

No-repeat locks consumed:

- Phase58 private-test reply.
- Phase59 supervised private-test auto-reply.
- Phase60 team canary.
- Phase67 supervised team auto-ops.
- Phase74 limited auto mode short run.

Manual Gate required for any future real send/runtime/LLM/RAG/scheduler live.
No secret/channel/raw ID values are documented.

CLI inventory categories:

- Safe report-only: state reports, inventory reports, closeout reports, and
  compaction plan reports.
- Preflight: read-only readiness checks for a future manually approved gate.
- Blocked report: commands that prove a denied or consumed gate sends nothing.
- Manual-gate actual: commands that must require explicit allow flags and gate
  environment, and cannot be reused after consumption.
- Closeout: metadata-only reports that fix historical success and lock repeats.
- Deprecated/consumed: any completed actual path now guarded by consumed locks.

Recommended next steps:

- Consolidate phase report builders into shared state registry.
- Deduplicate Manual Gate environment parsing.
- Deduplicate blocked report builders.
- Deduplicate send result safety assertions.
- Centralize consumed lock policy.
- Centralize allowed scopes and forbidden scopes.
- Archive old docs by index before deleting anything.

Do not change:

- Manual Gate required behavior.
- Consumed/no-repeat locks.
- Secret redaction.
- Public/unknown/high-risk blocking.
- LLM/RAG/external disabled by default.
- Scheduler live disabled by default.

Next phase is compaction/refactor/hardening, not new automation expansion.

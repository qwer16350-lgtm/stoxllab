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

Code Compaction B centralizes the first helper layer:

- `manual_gate_helpers.py` for redacted env presence, boolean approval checks,
  reply mode checks, disabled flag checks, blocked reason assembly, and consumed
  lock reason assembly.
- `safety_report_builders.py` for no-runtime/no-send, no-LLM/RAG/external,
  scheduler-disabled, secret-redaction, blocked report, and consumed-lock report
  fragments.

Phase60, Phase67, and Phase74 now use the shared consumed-lock helper while
preserving existing CLI commands, report field names, blocked reasons, Manual
Gate behavior, no-repeat locks, public/unknown/high-risk blocking, and secret
redaction. No files are deleted or moved.

Code Compaction B report:

```powershell
python apps\hermes_gateway\cli.py --post-mvp-compaction-b-report --json
```

Recommended next stage is Code Compaction C: consolidate old phase docs/runtime
index before deletion.

Code Compaction C adds the old phase runtime/docs index and archive plan before
any deletion. No files are deleted or moved. Archive candidates are
recommendations only, MVP registry remains the current SSOT, consumed locks
remain authoritative, and production unattended is still not ready.

Code Compaction C report commands:

```powershell
python apps\hermes_gateway\cli.py --hermes-phase-archive-index --json
python apps\hermes_gateway\cli.py --hermes-phase-archive-plan --json
```

Recommended next stage is Code Compaction D: safe module consolidation pass, no
deletion yet.

# STOXL Hermes Phase Archive Index

No files deleted in Code Compaction C. No files moved in Code Compaction C.
Archive candidates are recommendations only.

MVP registry is current SSOT. Consumed locks remain authoritative. Production
unattended is still not ready.

Active / do-not-delete files:

- `apps/hermes_gateway/cli.py`
- `apps/hermes_gateway/mvp_state_registry.py`
- `apps/hermes_gateway/manual_gate_helpers.py`
- `apps/hermes_gateway/safety_report_builders.py`
- `apps/hermes_gateway/phase60_65_team_canary_autonomy_stage.py`
- `apps/hermes_gateway/phase67_72_supervised_team_auto_ops.py`
- `apps/hermes_gateway/phase74_limited_auto_mode_prep.py`

Consumed historical gates:

- Phase58 private-test deterministic reply.
- Phase59 supervised private-test auto-reply.
- Phase60 team canary.
- Phase67 supervised team auto-ops.
- Phase74 limited auto mode.

Archive candidates, recommendation only:

- Older report-only phase docs.
- Duplicated closeout reports.
- Superseded prep docs.
- Legacy phase-specific blocked report docs.

Archive plan safeguards:

- Do not remove existing CLI.
- Do not weaken Manual Gate behavior.
- Do not weaken consumed/no-repeat locks.
- Do not weaken public/unknown/high-risk blocking.
- Do not weaken secret redaction.
- Do not enable LLM/RAG/external by default.
- Do not enable scheduler live by default.

Report commands:

```powershell
python apps\hermes_gateway\cli.py --hermes-phase-archive-index --json
python apps\hermes_gateway\cli.py --hermes-phase-archive-plan --json
```

Recommended next stage is Code Compaction D: safe module consolidation pass, no
deletion yet.

# STOXL Hermes Docs Consolidation Index

Code Compaction E does not delete or move files. Runtime facade is report-only.
Docs consolidation index is recommendation-only.

MVP registry remains SSOT. Consumed locks remain authoritative. Production
unattended is still not ready.

SSOT / do-not-delete docs:

- `docs/STOXL_HERMES_MVP_FINAL_CLOSEOUT.md`
- `docs/STOXL_HERMES_CURRENT_STATE.md`
- `docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md`
- `docs/STOXL_HERMES_PRODUCTION_ROADMAP.md`
- `docs/STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md`
- `docs/STOXL_HERMES_PHASE_ARCHIVE_INDEX.md`
- `docs/STOXL_HERMES_DOCS_CONSOLIDATION_INDEX.md`

Recommendation-only archive candidates:

- Superseded phase-specific closeout docs.
- Duplicated manual gate notes already covered by SSOT docs.
- Older report-only prep docs already mapped to MVP registry.

Future merge candidates:

- Historical phase closeout docs into `STOXL_HERMES_MVP_FINAL_CLOSEOUT.md`.
- Manual Gate phase notes into `STOXL_HERMES_ALLOWED_MANUAL_GATES.md`.
- Post-MVP compaction notes into `STOXL_HERMES_POST_MVP_COMPACTION_PLAN.md`.

Report commands:

```powershell
python apps\hermes_gateway\cli.py --hermes-runtime-facade-report --json
python apps\hermes_gateway\cli.py --hermes-docs-consolidation-index --json
```

Next recommended stage is Code Compaction F: production hardening checklist and
safe launch runbook.

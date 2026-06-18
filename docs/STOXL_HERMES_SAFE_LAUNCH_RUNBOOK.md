# STOXL Hermes Safe Launch Runbook

This runbook is report-only. It is not a production unattended launch approval
and it does not run any live action.

MVP complete does not mean production unattended ready. Production unattended is
still blocked.

Recommended launch sequence:

1. Confirm MVP state report.
2. Confirm runtime facade report.
3. Confirm consumed lock inventory.
4. Confirm production hardening checklist.
5. Run dry-run safety audit.
6. Run read-only live observation.
7. Run supervised manual-gate short session.
8. Review audit logs.
9. Only then consider a limited production unattended proposal.

Stop conditions:

- Secret value logged.
- Raw Discord ID logged.
- Public or unknown channel send attempted.
- High-risk intent auto reply attempted.
- `message_sent_count` exceeds configured max.
- LLM/RAG call attempted without explicit Manual Gate.
- External execution attempted.
- Scheduler live starts without Manual Gate.
- Kill switch not ready.

Launch constraints:

- Next live action must require Manual Gate.
- Scheduler live remains disabled by default.
- LLM/RAG live reply remains disabled by default.
- External execution remains disabled.
- Production unattended auto reply remains disabled.
- Existing consumed locks and repeat-send/session blocks remain authoritative.
- Token, channel ID, API key, approval phrase, raw Discord ID, raw session ID,
  and raw content values must not be logged.

Report command:

```powershell
python apps\hermes_gateway\cli.py --hermes-safe-launch-runbook --json
```

Recommended next stage: Production Hardening G - dry-run safety audit, no live
action.

# STOXL Phase 40R Phase 41 Reply Preflight Matrix

Phase 40R keeps Phase 41 reply runtime blocked by default.

Required before Phase 41 reply:

- Phase 40O manual read-only runtime launched by user.
- Phase 40Q capture review closeout completed.
- No send occurred during read-only runtime.
- At least one private-test human event reviewed.
- Operator approves one reply-mode rehearsal.
- Reply send remains blocked until separate Phase 41 send gate.

Current state:

- Reply text generation allowed: false.
- LLM reply allowed: false.
- RAG reply allowed: false.
- Discord reply send allowed: false.
- Unattended auto reply allowed: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40r-phase41-reply-preflight-matrix --json
```

# STOXL Phase 40N Phase 41 Reply Runtime Entry Gate

Phase 40N creates the gate for a future Phase 41 reply runtime. The gate is blocked by default.

Required before Phase 41:

- Phase 40J manual read-only runtime completed.
- Phase 40L live capture closeout completed.
- No additional send during read-only runtime.
- Captured event audit passed.
- Operator approves one private-test reply runtime.

Current blocked state:

- Phase 41 reply runtime allowed: false.
- Reply send allowed: false.
- LLM reply allowed: false.
- RAG reply allowed: false.
- Unattended auto reply allowed: false.
- Ready for Phase 41 reply runtime: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40n-phase41-reply-runtime-entry-gate --json
```

Phase 40R expands this into a reply-runtime preflight matrix. Phase 41 remains
blocked until a user-run read-only capture is reviewed and a separate reply gate
is approved.

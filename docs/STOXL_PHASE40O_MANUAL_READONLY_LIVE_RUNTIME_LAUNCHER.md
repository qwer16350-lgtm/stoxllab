# STOXL Phase 40O Manual Read-only Live Runtime Launcher

Phase 40O prepares launch support for a future user-run read-only Discord runtime. Codex does not run the command.

Planned command for later manual execution:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json
```

Required posture:

- Manual launch only: true.
- Codex must not launch: true.
- Phase 39 actual send count locked: 1.
- Phase 40 additional send count: 0.
- Send/reply disabled.
- LLM/RAG/embedding/external disabled.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40o-manual-readonly-live-runtime-launcher --json
```

Phase 40T-0 adds the missing runtime command parser entry:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json
```

It is blocked by default and does not connect the Gateway or send messages in
Codex verification.

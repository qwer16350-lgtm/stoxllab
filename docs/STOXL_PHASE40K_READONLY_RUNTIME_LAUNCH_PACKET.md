# STOXL Phase 40K Read-only Runtime Launch Packet

Phase 40K creates a manual-only launch packet for a future private-test read-only runtime. Codex must not launch the runtime in this phase.

Planned command:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json
```

This command is documented for a later human-run step. It is not executed by Codex in Phase 40J-40N.

Required runtime posture:

- Runtime scope: private_test_readonly.
- Send messages required false.
- Private-test reply required false.
- Reply mode: readonly_private_test_only.
- Live runtime started: false.
- Discord Gateway connected: false.
- Discord API send called: false.
- Discord message sent: false.
- Ready for manual read-only runtime launch: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40k-readonly-runtime-launch-packet --json
```

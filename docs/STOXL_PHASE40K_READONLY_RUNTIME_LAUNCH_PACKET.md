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

Phase 40O reuses the same planned command as a manual launch support packet.
The command remains for user execution only.

Phase 40T-0 registers this command in argparse with a blocked-by-default
preflight. In Codex verification it returns a sanitized report only:
`started=false`, `discord_gateway_connected=false`,
`discord_api_send_called=false`, `discord_message_sent=false`, and
`message_sent_count=0`.

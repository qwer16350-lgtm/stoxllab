# STOXL Phase51/52 Read-only Live Runtime Launch Packet

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase51-52-readonly-live-runtime-launch-packet --json
```

The launch packet records the user-run command for the next separate Manual
Gate:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json --readonly-runtime-timeout-seconds 300 --readonly-runtime-max-events 20
```

Required safety posture:

- Discord send disabled
- Private-test reply disabled
- Reply mode `readonly_private_test_only`
- LLM disabled
- RAG disabled
- Embedding/vector disabled
- External execution disabled
- Scheduler live execution disabled

The launch packet itself is report-only and does not start the runtime.

# STOXL Phase 40L Live Capture Closeout Packet

Phase 40L prepares the packet that will close out a future manually run read-only live capture. It is available before live capture and currently records no observed live events.

Current state:

- Capture closeout available: true.
- Live capture observed: false.
- Captured event count: 0.
- Captured private-test human message count: 0.
- Captured self message count: 0.
- Captured bot message count: 0.
- Captured public/team message count: 0.
- Discord API send called: false.
- Discord message sent: false.
- Ready for capture closeout after manual runtime: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40l-live-capture-closeout-packet --json
```

Phase 40P and Phase 40Q add the redacted capture schema and closeout parser.
Capture files must not contain raw message content, raw Discord IDs, tokens, API
keys, or approval phrase values.

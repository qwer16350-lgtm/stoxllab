# STOXL Phase 40Q Capture Review Closeout

Phase 40Q reviews a redacted capture file if a user provides one later. Without a capture file it returns a graceful no-capture report.

Default state:

- Capture file present: false.
- Capture review completed: false.
- Live capture observed: false.
- Captured event count: 0.
- Discord API send called: false.
- Discord message sent: false.
- Ready for Phase 41 reply runtime: false.

Optional later usage:

```powershell
python apps\hermes_gateway\cli.py --phase40q-capture-review-closeout --json --capture-file <path>
```

The closeout must not print raw message content, raw author ID, raw channel ID, token, API key, or approval phrase values.

# STOXL Phase 40C Inbound Event Replay Dry-run

Phase 40C verifies inbound event decisions with recorded or synthetic events only. It does not connect to Discord and does not receive live events.

Dry-run decisions:

- Synthetic human private-test message can be processed for future manual reply eligibility.
- Self message is skipped.
- Bot message is skipped.
- Duplicate message is skipped.
- Public channel message is blocked.
- Team channel message is blocked.

Safety state:

- Discord Gateway connected: false.
- Live runtime started: false.
- Discord API send called: false.
- Discord message sent: false.
- Message sent count: 0.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40-inbound-event-replay-dry-run --json
```

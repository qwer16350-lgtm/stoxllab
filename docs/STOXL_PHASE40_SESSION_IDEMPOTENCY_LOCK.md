# STOXL Phase 40F Session Idempotency Lock

Phase 40F defines the idempotency expectations for a later private-test live runtime. It does not persist runtime state and does not send messages.

Required guards:

- Dedupe key strategy: message_id.
- One reply per human message.
- Duplicate message ID guard.
- Self-message guard.
- Bot-message guard.
- Duplicate send prevented.

Forbidden state:

- Repeat send allowed: false.
- Automatic retry allowed: false.
- Manual retry allowed: false.
- Discord API send called: false.
- Discord message sent: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40-session-idempotency-lock --json
```

# STOXL Phase 40P Read-only Capture Schema

Phase 40P defines the redacted capture schema for a future read-only runtime. Codex does not create a live capture file in this phase.

Allowed fields:

- event_id_hash
- message_id_hash
- channel_scope
- author_kind
- is_self
- is_bot
- is_duplicate
- decision
- timestamp_iso

Forbidden fields:

- raw_message_content
- raw_author_id
- raw_channel_id
- discord_token
- api_key
- approval_phrase

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40p-readonly-capture-schema --json
```

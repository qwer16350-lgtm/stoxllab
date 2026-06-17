# STOXL Phase51 Read-only Event Schema

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase51-readonly-event-schema --json
```

Phase51 defines the read-only Discord-like event shape for synthetic fixtures.
It does not start Discord runtime, open a Discord Gateway connection, call
Discord API send, call LLM/OpenRouter, call RAG, create embeddings/vector data,
or execute external actions.

Normalized event fields include:

- `event_id_present`
- `source`
- `channel_scope`
- `channel_risk`
- `author_kind`
- `message_kind`
- `content_present`
- `raw_content_logged=false`
- `raw_discord_ids_logged=false`

Raw message content and raw Discord IDs are not included in reports. Only
presence, length, and hash-safe metadata are allowed.

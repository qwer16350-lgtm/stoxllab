# STOXL Phase 40T Read-only Capture Writer

Phase 40T capture files are redacted local artifacts only. The default root is:

```text
apps/hermes_gateway/local/captures
```

This path is not a commit target.

## Allowed Event Fields

- `event_id_hash`
- `message_id_hash`
- `channel_scope`
- `author_kind`
- `is_self`
- `is_bot`
- `is_duplicate`
- `decision`
- `timestamp_iso`

## Forbidden Fields

- `raw_message_content`
- `content`
- `author_id`
- `channel_id`
- `guild_id`
- `discord_token`
- `api_key`
- `approval_phrase`

The writer rejects forbidden fields and stores only hashed event/message ids.

## Safety

Capture safety flags must remain:

- `raw_content_included=false`
- `raw_discord_ids_included=false`
- `secret_values_included=false`
- `discord_send_called=false`
- `message_sent_count=0`

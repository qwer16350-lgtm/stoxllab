# STOXL Phase 40V Capture Review Closeout

Phase 40V hardens capture review classification.

Valid classes:

- `valid_no_event_timeout_capture`
- `valid_private_test_human_message_capture`

Invalid classes:

- `invalid_raw_content_capture`
- `invalid_raw_discord_id_capture`
- `invalid_secret_capture`
- `invalid_public_team_capture`

Capture path values, raw content, raw Discord IDs, token values, API keys, and
approval phrases must not be logged. No send/reply/LLM/RAG/external execution is
performed.

# STOXL Hermes Safety Contract

This contract is fixed for the Phase 41B~45A Safe Prep Mega Bundle.

Forbidden in this bundle:

- Discord live runtime execution.
- `--execute-readonly-live-runtime`.
- Discord API send calls.
- Discord message sends.
- Actual private-test/team/public reply or send.
- Unattended auto reply, automatic retry, or repeat send.
- OpenRouter/LLM API calls or attempts.
- RAG calls, embedding/vector creation, and external execution.
- Printing token values, channel ID values, API key values, approval phrase values, raw Discord IDs, raw message content, `.env` content, or full content dumps.

Commit exclusions remain `.env`, `exports/`, `logs/`, and `apps/hermes_gateway/local/*`.

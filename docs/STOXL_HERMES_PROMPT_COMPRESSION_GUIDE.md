# STOXL Hermes Prompt Compression Guide

For future prompts, reference these SSOT documents instead of restating the full history:

- `docs/STOXL_HERMES_CURRENT_STATE.md`
- `docs/STOXL_HERMES_SAFETY_CONTRACT.md`
- `docs/STOXL_HERMES_PRODUCTION_ROADMAP.md`
- `docs/STOXL_HERMES_ALLOWED_MANUAL_GATES.md`

Prompt rule: never include secret values, raw Discord IDs, raw message content, `.env` content, or approval phrase values. Ask for the next phase by name and state whether actual Discord or LLM execution is forbidden or manually approved.

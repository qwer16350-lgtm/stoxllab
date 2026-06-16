# STOXL Phase 44 LLM Preflight Contract

Phase 44 adds an LLM provider preflight and prompt packet contract without making provider calls.

The provider report exposes key presence as a boolean only. It does not print API key values. The prompt packet schema requires redacted content, no raw Discord IDs, no secrets, and no approval phrase values. Output schema validation is prepared for fake and later real responses.

# STOXL Discord Token Handling Rules

## Current Phase

Phase 23 does not request, read, print, store, or validate a Discord Bot Token value.

## Mapping File Rule

Bot Token must not be stored in any mapping JSON file.

Mapping files may contain Discord IDs, but they must not contain:

- Bot Token
- API keys
- passwords
- secrets
- bearer tokens
- private keys
- access keys
- refresh tokens
- DB credentials
- NAS credentials

## Code Rule

Bot Token must not be hardcoded in code.

No token value may appear in:

- Python source
- JSON examples
- Markdown docs
- test fixtures
- logs
- reports
- review packets

## Runtime Rule

A later approved runtime phase may read the token only inside the runtime entrypoint designed for the read-only Discord connection.

Allowed later sources, after approval:

- OS environment variable
- local `.env` file that is not committed

Still forbidden:

- printing token value
- logging token value
- including token in validation reports
- including token in mapping JSON

## `.env` Rule

`.env` must not be committed to git.

Phase 23 does not read `.env`. It only checks that required key names are documented in `.env.example`.

## Exposure Response

If a token or secret is exposed:

1. Stop any runtime process.
2. Rotate the token immediately.
3. Remove the exposed value from local files.
4. Inspect logs and reports.
5. Re-run validation and safety checks.

## Provider Keys

OpenAI, OpenRouter, API provider keys, DB credentials, and NAS credentials follow the same principle:

- never hardcode
- never commit
- never log
- never place in mapping JSON
- rotate immediately if exposed

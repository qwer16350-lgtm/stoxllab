# STOXL Read-Only Connection Preflight

## Purpose

Phase 23 adds a final local preflight report before a future private Discord read-only connection phase.

It is still no-connection work. The preflight does not call Discord APIs, connect to Gateway, read a Bot Token, read `.env`, send messages, or perform external execution.

## Why This Comes After Local Mapping Protection

Phase 22 created a protected local mapping workflow. Phase 23 checks whether that local mapping is now strict-valid and whether the surrounding safety conditions are still intact.

## What Preflight Checks

The preflight checks:

- local mapping strict validation readiness
- TODO placeholder count
- secret-like value count
- required env key names in `.env.example`
- local mapping `.gitignore` protection
- logs and exports `.gitignore` protection
- message send disabled
- external execution disabled
- human-only execution preserved
- dependency plan is still install-later

## What Preflight Does Not Do

The preflight does not:

- call Discord APIs
- connect to Discord Gateway
- read a Bot Token
- read `.env`
- read OS environment variable values
- send messages
- perform external execution
- print raw Discord IDs

## Usage

```powershell
python apps\hermes_gateway\cli.py --connection-preflight
python apps\hermes_gateway\cli.py --connection-preflight --json
python apps\hermes_gateway\tests\test_connection_preflight.py
```

## Ready Criteria

`ready_for_phase24_readonly_connection=true` only when:

- local mapping strict validation is ready
- `secret_like_values=0`
- `todo_placeholders=0`
- local mapping is gitignored
- logs and exports are gitignored
- required env key names are documented
- message send is disabled
- external execution is disabled
- human-only execution is preserved

Manual checks still remain before the next phase, including private server confirmation and rollback review.

## Failure Actions

If preflight fails:

- inspect `blocked_reasons`
- re-run local mapping strict validation
- remove TODO placeholders
- remove secret-like values
- confirm `.gitignore` rules
- confirm safety flags
- re-run the local test suite

Do not proceed to any Discord connection until preflight passes and a later phase explicitly authorizes the connection.

## Phase 24 Move Condition

Phase 24 can be considered only after:

- this preflight is ready
- local tests pass
- private server scope is confirmed
- token handling rules are accepted
- dependency installation is approved in that phase

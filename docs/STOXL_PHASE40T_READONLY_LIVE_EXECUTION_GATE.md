# STOXL Phase 40T Read-only Live Execution Gate

Phase 40T-1 adds a separate user-only execute flag for the private-test
read-only runtime:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-readonly --json --execute-readonly-live-runtime
```

Codex does not run this command. Without `--execute-readonly-live-runtime`, the
existing command remains preflight/report-only.

## Gate Conditions

Execution is allowed only when:

- Discord token and private-test channel id are present as booleans.
- Phase 40J manual approval is present and exact.
- `HERMES_DISCORD_SEND_MESSAGES=false`.
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=false`.
- `HERMES_DISCORD_REPLY_MODE=readonly_private_test_only`.
- LLM, RAG, embedding/vector, and external execution gates are false.
- Timeout is greater than 0 and at most 300 seconds.
- Max events is between 0 and 100.
- Capture root is under `apps/hermes_gateway/local/captures`.

The gate never prints token, channel id, approval phrase, API key, raw Discord
id, or raw message content.

## Safety

In Codex verification:

- Live runtime started: false.
- Discord Gateway connected: false.
- Discord API send called: false.
- Discord message sent: false.
- Message sent count: 0.
- LLM/RAG/embedding/external: false.

## Phase 40T-2 Login Failure Handling

If a user-run command reaches Discord login and fails with LoginFailure or HTTP
401, the runtime must return a safe
`phase40t_discord_login_failure_closeout` JSON report instead of printing a raw
traceback. The report records token presence and token validity booleans only,
keeps Gateway connected false, keeps all send/retry/LLM/RAG/external flags
false, and points the operator to refresh or correct the Discord bot token.

Phase 40T-3 preserves the preflight snapshot into that closeout. Missing token
or channel presence blocks before login with `login_attempted=false`; invalid
or unauthorized token after a passed preflight keeps token/channel presence true
and reports `discord_token_valid=false`.

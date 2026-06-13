# STOXL Private Test LLM Dry Call

Phase 32B adds the first LLM client boundary for private-test-only dry calls.

The default path is still mock-only. It does not call an LLM provider, does not send Discord messages, does not read RAG, and does not execute external actions.

## Difference From Phase 32A

Phase 32A defined preflight, safety policy, and prompt envelope previews.

Phase 32B adds:

- an LLM client wrapper
- a mock dry call result
- a gated one-call provider path for later manual use
- output safety checks
- local JSON/Markdown artifact support

## Default Behavior

```powershell
python apps\hermes_gateway\cli.py --llm-dry-call-report --json
python apps\hermes_gateway\cli.py --llm-dry-call-report --markdown
```

These commands use a mock response. They do not call OpenAI, OpenRouter, Anthropic, or any other provider.

## Actual API Call Gate

A provider call can only be attempted when the CLI option and all env gates are enabled:

```powershell
python apps\hermes_gateway\cli.py --llm-dry-call-report --json --allow-llm-api-call
```

Required conditions:

- `HERMES_LLM_ENABLED=true`
- `HERMES_LLM_API_CALL_ENABLED=true`
- `HERMES_LLM_PROVIDER` is not `disabled`
- `HERMES_LLM_MODEL` is configured
- `HERMES_LLM_API_KEY` is present
- `HERMES_LLM_DRY_CALL_MODE=private_test_only`
- `HERMES_LLM_DISCORD_SEND_ENABLED=false`
- `HERMES_DISCORD_SEND_MESSAGES=false`
- `HERMES_LLM_PRIVATE_TEST_ONLY=true`
- `HERMES_LLM_COST_GUARD_ENABLED=true`
- RAG disabled
- external execution disabled

If any condition fails, no API call is attempted and the report records a blocked dry call.

## Discord Send Is Still Forbidden

Phase 32B never sends an LLM answer to Discord.

The response can be stored as a local report or artifact only. A future would-send or review packet may reference the response, but this phase does not create a Discord reply.

## Private Test Only

The dry call request is scoped to:

- `channel_scope=private_test_only`
- no public channel response
- no team channel response
- no work channel response

## Output Safety

The output policy blocks:

- empty output
- output longer than the configured max
- external action claims
- approval claims
- price confirmation claims
- contract confirmation claims
- delivery confirmation claims
- public publish claims
- Discord send claims

Normal review-only draft text can pass as a local preview, but it is not approval and not execution.

## Artifacts

Artifacts are written under:

```text
exports/hermes_gateway/llm_dry_calls/YYYYMMDD/
```

Artifacts are local reports. They must not contain API keys, raw Discord IDs, `.env` values, or tokens.

## Rollback

To disable Phase 32B behavior:

- keep `HERMES_LLM_API_CALL_ENABLED=false`
- omit `--allow-llm-api-call`
- keep `HERMES_LLM_DISCORD_SEND_ENABLED=false`
- keep Discord send flags disabled

## Still Not Done

- Discord LLM reply
- RAG access
- public/team channel response
- external posting, submission, email, contract, pricing, or delivery execution

## Next Phases

- Phase 32C: private test LLM response preview into would-send/review packet.
- Phase 32D: guarded private test LLM reply, manual enable only.

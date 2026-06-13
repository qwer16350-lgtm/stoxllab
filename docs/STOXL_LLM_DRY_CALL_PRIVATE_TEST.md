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
python apps\hermes_gateway\cli.py --llm-dry-call-report --json --allow-llm-api-call --write-artifact
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

When `--allow-llm-api-call` is used, the report request mirrors that flag:

```json
{
  "request": {
    "allow_api_call": true
  }
}
```

## Discord Send Is Still Forbidden

Phase 32B never sends an LLM answer to Discord.

The response can be stored as a local report or artifact only. A future would-send or review packet may reference the response, but this phase does not create a Discord reply.

Phase 32C converts safe LLM dry call reports into local response packets that can be reviewed in would-send previews, live event review packets, and the operations viewer. This still does not create a Discord reply.

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
- public publish claims
- submission claims
- email send claims
- approval claims
- price confirmation claims
- contract confirmation claims
- delivery confirmation claims
- Discord send claims

Normal review-only draft text can pass as a local preview, but it is not approval and not execution.

Negated safety disclaimers are allowed when they clearly say that no external action happened, for example:

- no final publishing has been made
- no external delivery has been made
- not submitted
- no email has been sent
- no approval has been granted
- no contract or delivery date has been confirmed
- internal review only

Reports may include:

```json
{
  "safe_disclaimer_detected": true,
  "safe_disclaimer_reasons": ["negated_external_delivery", "review_only"]
}
```

## Artifacts

Artifacts are written under:

```text
exports/hermes_gateway/llm_dry_calls/YYYYMMDD/
```

Phase 32C-LIVE artifact filenames include a timestamp, provider, and model:

```text
llm_dry_call_YYYYMMDD_HHMMSS_openrouter_openai-gpt-5.4-mini.json
llm_dry_call_YYYYMMDD_HHMMSS_openrouter_openai-gpt-5.4-mini.md
```

Artifacts are local reports. They must not contain API keys, raw Discord IDs, `.env` values, or tokens.

## OpenRouter Error Visibility

OpenRouter uses an OpenAI-compatible chat completions request:

```text
POST {HERMES_LLM_BASE_URL}/chat/completions
Authorization: Bearer <HERMES_LLM_API_KEY>
Content-Type: application/json
```

The request body includes `model`, `messages`, `temperature`, and a bounded `max_tokens` value.

Non-2xx provider responses are stored only as sanitized diagnostics:

```json
{
  "error_type": "provider_error",
  "provider_status_code": 400,
  "provider_error_code": "model_not_found",
  "provider_error_message": "redacted/truncated safe message",
  "provider_response_redacted": true
}
```

The Authorization header, API key, raw token-like values, full provider response body, and raw Discord-like IDs are never stored in the report.

Successful responses are parsed from:

```json
{
  "choices": [
    {
      "message": {
        "content": "..."
      }
    }
  ],
  "usage": {}
}
```

If `content` is empty, output safety blocks the result as `empty_output`.

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

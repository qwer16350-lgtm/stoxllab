# STOXL LLM Private Test Reply

Phase 32D adds a guarded LLM reply path for the configured Discord private test channel only.

This is not a public bot reply feature. It is not enabled by default.

## Boundary

Allowed only when all gates pass:

- the event is from the configured private test channel ID
- the event author is a human, not the bot
- duplicate, cooldown, budget, and circuit breaker checks pass
- OpenRouter LLM call succeeds
- output safety allows the response
- an LLM response packet is created and passes packet safety
- Discord send is limited to the private test channel reply helper

Still forbidden:

- public or team channel LLM replies
- normal mapped work channel LLM replies
- channel-name-only allow rules
- self or bot message replies
- duplicate message replies
- RAG access
- external execution
- SNS, homepage, support application, email, contract, pricing, or delivery execution
- token/API key/raw Discord ID output

## Env Gates

The default `.env.example` keeps this phase disabled.

Required true or configured values:

```text
HERMES_DISCORD_SEND_MESSAGES=true
HERMES_DISCORD_PRIVATE_TEST_REPLY=true
HERMES_DISCORD_REPLY_MODE=private_test_only
HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=<private test channel id>
HERMES_LLM_ENABLED=true
HERMES_LLM_API_CALL_ENABLED=true
HERMES_LLM_PROVIDER=openrouter
HERMES_LLM_MODEL=<model>
HERMES_LLM_API_KEY=<present but never printed>
HERMES_LLM_DRY_RUN_ONLY=false
HERMES_LLM_DRY_CALL_MODE=private_test_only
HERMES_LLM_DISCORD_SEND_ENABLED=true
HERMES_LLM_PRIVATE_TEST_ONLY=true
HERMES_LLM_COST_GUARD_ENABLED=true
HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED=true
HERMES_LLM_PRIVATE_TEST_REPLY_MODE=private_test_only
HERMES_LLM_PRIVATE_TEST_REPLY_REQUIRE_PACKET=true
HERMES_DISCORD_RAG_ENABLED=false
HERMES_DISCORD_EXTERNAL_EXECUTION=false
HERMES_LLM_RAG_ENABLED=false
HERMES_LLM_EXTERNAL_EXECUTION=false
```

## Preflight

These commands do not connect to Discord and do not call the LLM provider:

```powershell
python apps\hermes_gateway\cli.py --llm-private-test-reply-report --json
python apps\hermes_gateway\cli.py --llm-private-test-reply-report --markdown
```

## Runtime

This command is separate from deterministic placeholder replies:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-llm-reply --json
```

Stop with `Ctrl+C`.

After testing, reset the high-risk env flags:

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
```

## Runtime Logs

Expected ready line:

```text
[PRIVATE_TEST_LLM_READY] runtime_mode=private_test_llm_reply private_test_channel_configured=true llm_enabled=true provider=openrouter model_configured=true discord_send_enabled=true public_send_disabled=true rag_disabled=true external_disabled=true
```

Expected event flow:

```text
[READONLY_EVENT] accepted_private_test_channel ...
[PRIVATE_TEST_LLM_REPLY] llm_call_allowed
[PRIVATE_TEST_LLM_REPLY] output_safety_allowed
[PRIVATE_TEST_LLM_REPLY_SENT] message_sent=true channel=hermes-private-test
[READONLY_EVENT] ignored_self_message ...
[PRIVATE_TEST_LLM_REPLY] skipped reason=self_message
```

## Payload Marker

Sent private test LLM replies start with:

```text
[PRIVATE TEST - LLM REVIEW DRAFT]
This is a review-only draft. No external action has been taken.
```

The marker is part of the safety boundary. It does not grant approval and does not claim execution.

## Audit

Local audit records are written under:

```text
exports/hermes_gateway/llm_private_test_replies/YYYYMMDD/
```

The audit includes redacted IDs only and keeps:

- RAG called: false
- external execution: false
- API key value logged: false
- raw Discord IDs logged: false

## Troubleshooting

- `preflight blocked`: check env gates and private test channel ID.
- `provider_error`: inspect sanitized provider status and code only.
- `output_safety_blocked`: the LLM response claimed publish, submit, send, approval, confirmation, or external action.
- `cooldown_active`: wait for the configured cooldown.
- `reply_budget_exhausted`: restart only after intentionally resetting session state.
- `rate_limit_seen` or `send_exception_seen`: circuit breaker opened; stop the runtime and inspect audit.
- `self_message`: bot echo was skipped before any LLM call.

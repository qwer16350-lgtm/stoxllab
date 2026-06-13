# STOXL LLM Safety Preflight

Phase 32A defines local-only checks that must pass before any later LLM dry call is considered.

This phase does not call OpenAI, OpenRouter, Anthropic, or any other provider. It does not read RAG sources, does not send Discord messages, and does not perform external actions.

## Purpose

- Check LLM env flags without exposing secrets.
- Keep provider/model/API key handling separate from Discord send behavior.
- Define a private-test-only LLM gate for later phases.
- Define deterministic prompt envelope previews.
- Define output safety checks for approval-like or execution-like responses.

## Environment Flags

```env
HERMES_LLM_ENABLED=false
HERMES_LLM_PROVIDER=disabled
HERMES_LLM_MODEL=
HERMES_LLM_MAX_INPUT_CHARS=4000
HERMES_LLM_MAX_OUTPUT_CHARS=1200
HERMES_LLM_MAX_CALLS_PER_SESSION=3
HERMES_LLM_COST_GUARD_ENABLED=true
HERMES_LLM_PRIVATE_TEST_ONLY=true
HERMES_LLM_ALLOW_DISCORD_SEND=false
HERMES_LLM_DRY_RUN_ONLY=true
HERMES_LLM_API_KEY=
```

`HERMES_LLM_API_KEY` is reported only as `api_key_present=true/false`. The value must never appear in reports, logs, docs, or commits.

## Dry-run-only Meaning

`HERMES_LLM_DRY_RUN_ONLY=true` means the system can prepare reports and prompt envelope previews, but it must not make a provider request. In Phase 32A, this is expected and keeps `ready_for_llm_call=false`.

## Private-test-only Gate

LLM use is scoped to a future private test channel path only. Public channels, team channels, and work channels such as `marketing-brief`, `operation-brief`, `homepage`, and `new-business` are outside the Phase 32A LLM scope.

## Discord Send Separation

LLM call readiness and Discord message sending are separate controls.

- `HERMES_LLM_ALLOW_DISCORD_SEND=false`
- Phase 32A reports do not send Discord messages.
- A future LLM response must not imply permission to post, publish, submit, email, or contract.

## Cost Guard

The preflight tracks:

- `HERMES_LLM_MAX_INPUT_CHARS`
- `HERMES_LLM_MAX_OUTPUT_CHARS`
- `HERMES_LLM_MAX_CALLS_PER_SESSION`
- `HERMES_LLM_COST_GUARD_ENABLED`

Invalid limits or a disabled cost guard block readiness.

## Prompt Envelope

The prompt envelope is a deterministic preview. It includes:

- agent route candidate
- private-test-only channel scope
- system safety constraints
- preview-only user content
- no raw Discord IDs
- no API keys or token-like values

It does not call an LLM.

## Output Safety Policy

The policy blocks or sends to review when output appears to perform or finalize external actions.

Blocked output intents:

- SNS publish
- homepage upload
- competition or grant submission
- external email send
- contract confirmation
- price confirmation
- delivery schedule confirmation

Normal draft or review-only language can be allowed as review-only, but still does not authorize external execution.

## Still Not Done

- actual LLM provider call
- Discord LLM reply
- RAG access
- public or team channel LLM response
- external posting, submission, email, contract, pricing, or delivery execution

## Local Commands

```powershell
python apps\hermes_gateway\cli.py --llm-preflight-report --json
python apps\hermes_gateway\cli.py --llm-preflight-report --markdown
python apps\hermes_gateway\cli.py --llm-safety-policy-report --json
python apps\hermes_gateway\cli.py --llm-prompt-envelope-report --json
python apps\hermes_gateway\cli.py --llm-prompt-envelope-report --markdown
```

## Next Phases

- Phase 32B: private test LLM dry call, no Discord send.
- Phase 32C: private test LLM reply with manual enable.

# STOXL Phase 45A Actual LLM One-shot Preflight

Phase 45A prepares the future actual LLM one-shot call gate. This bundle does not attempt the call.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase45-actual-llm-one-shot-preflight --json
```

The preflight is blocked by default and requires a later manual approval gate,
exact approval phrase match, cost guard, call-count guard, OpenRouter/API key
presence, provider config presence, model config presence, and Discord send
remaining false. API key, model/provider values, and approval phrase values are
never logged.

Even when all booleans are ready, this report performs no actual LLM/OpenRouter
API attempt or call. RAG, embeddings/vector generation, external execution, and
private-test Discord send remain false.

Phase45-0 fixes env aliases and gate naming:

- API key aliases: `HERMES_LLM_API_KEY`, `OPENROUTER_API_KEY`,
  `HERMES_OPENROUTER_API_KEY`
- Provider/model/base URL: `HERMES_LLM_PROVIDER`, `HERMES_LLM_MODEL`,
  `HERMES_LLM_BASE_URL`
- `gate_checks` uses positive state names such as `api_key_present`,
  `provider_config_present`, `model_config_present`, `base_url_present`, and
  `discord_send_disabled`
- `blocked_reasons` contains only failing reasons such as `api_key_missing` or
  `discord_send_enabled`

Boolean-only diagnostics:

```powershell
python apps\hermes_gateway\cli.py --phase45-llm-env-diagnostics --json
```

Phase45-1 separates readiness from execution in the operations dashboard lock.
The readiness flags `phase45_ready_for_actual_llm_one_shot_manual_gate` and
`phase45_ready_for_actual_llm_one_shot_call` are not execution. The unsafe
execution signals remain `actual_llm_api_call_attempted`,
`actual_llm_api_called`, and any LLM API call count above zero.

The legacy `--actual-one-shot-llm-draft-call` path now returns a blocked JSON
report without a traceback when the actual gate is not allowed. This hotfix does
not attempt or call OpenRouter/LLM and keeps Discord send disabled.

Phase45-2 bridges the Phase45A manual approval gate into the legacy actual LLM
draft command. The authoritative approval keys are:

- `HERMES_PHASE45A_MANUAL_APPROVAL`
- `HERMES_PHASE45A_APPROVAL_PHRASE`
- `HERMES_PHASE45A_COST_GUARD`
- `HERMES_PHASE45A_CALL_COUNT_GUARD`

When the Phase45A gate is open, the actual command reports
`manual_approval.approved=true`. Without the actual allow flag it still returns
blocked JSON with reason `actual_llm_allow_flag_missing`. Real LLM/OpenRouter
API calls remain unexecuted in this safe hotfix.

Phase45-3 records the later Manual Gate 3 actual LLM/OpenRouter call closeout.
The call succeeded exactly once, output safety blocked the generated draft for
`external_action_claim`, no response packet was created, and Discord send
remained disabled. The consumed Phase45 gate is now no-repeat locked, so repeat
actual command runs return blocked JSON with reason
`phase45_actual_llm_one_shot_already_consumed`.

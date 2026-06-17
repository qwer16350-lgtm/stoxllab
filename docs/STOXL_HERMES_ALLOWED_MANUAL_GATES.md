# STOXL Hermes Allowed Manual Gates

Allowed future manual gates are separated from this bundle:

- Manual Gate 3 is complete and locked. Phase 45 actual LLM one-shot provider
  call succeeded exactly once with Discord send disabled.
- Any future retry must be a separate manual gate with a new explicit approval
  policy. It must not be automatic and must not reuse the consumed Phase45 gate.
- Phase47 may design a new retry Manual Gate only if explicitly requested.
  Until then, automatic retry and repeat Phase45 LLM calls are forbidden.

Phase 41B actual private-test deterministic reply succeeded exactly once and is locked against repeat send. Every future manual gate must require explicit user approval, exact phrase match, scoped environment flags, private-test-only routing where relevant, count/cost guards, no-repeat locks, and operations closeout. This bundle only prepares reports and tests for those gates.

Manual Gate 2 is complete: Phase 42 actual supervised private-test session
succeeded with `message_sent_count=1`, `sent_scope=private_test_only`, and
`session_lock_consumed=true`. Phase 42 repeat supervised session is locked.

Phase 45A may read current process-env booleans for key/provider/model/cost and
call-count readiness, including `HERMES_LLM_API_KEY`,
`HERMES_LLM_PROVIDER`, `HERMES_LLM_MODEL`, and `HERMES_LLM_BASE_URL`.
Phase45 actual LLM execution has now been consumed exactly once. Discord send
remained disabled, and repeat LLM calls are locked.

Phase46 is review/policy only. It does not authorize any new LLM call, Discord
send, RAG, embedding/vector generation, or external execution.

Phase47 is human-review-only closeout plus disabled retry gate design. Retry
execution is not available in Phase47. Automatic retry, automatic send, Phase45
repeat LLM calls, blocked-output auto Discord send, and raw output dumps remain
forbidden. A future retry must be a new explicit Manual Gate with a new approval
policy, cost guard, call-count guard, and Discord disabled by default.

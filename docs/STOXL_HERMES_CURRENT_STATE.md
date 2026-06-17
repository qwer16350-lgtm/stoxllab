# STOXL Hermes Current State

Repository state for this bundle:

- Repo root: `C:\Users\architecture kim\dev\STOXL_LAB_PUSH`
- Branch: `feature/stoxl-hermes-agent-org`
- Baseline HEAD: `7689063 test: add Phase 40 read-only closeout and Phase 41 reply preflight`
- Phase 39 actual private-test Discord send count remains locked at `1`.
- Phase 40T actual read-only live runtime closeout is recorded as successful with gateway connected, timeout exit, zero captured events, no API send, no message sent, and `message_sent_count=0`.
- Phase 40U through Phase 41A safe bundle is complete.
- Phase 41 actual reply/send has not been run by this bundle.

Current bundle: Phase 41B~45A Safe Prep Mega Bundle. It prepares final production-bound gates without executing Discord live runtime, Discord reply/send, LLM provider calls, RAG, embedding/vector generation, or external execution.

Phase 41B-0 hotfix updates the one-shot gate to read the current process environment for manual reply readiness and to report failure-shaped blocked reasons. It adds boolean-only env diagnostics and still performs no actual reply/send.

Phase 41B-1 adds the actual private-test deterministic reply runtime path behind the manual allow flag and all existing gates. This phase implements adapter/runtime code and fake-adapter tests only. Codex still does not execute the actual Discord runtime or send path.

Phase 41B-2 hotfix wires the real Discord send adapter for the next manual
retry after a sanitized manual attempt reached an eligible private-test human
message but failed with `RuntimeError`. The adapter no longer reuses a closed
message object for sending; it uses a fresh manual-gated private-test channel
send path. Codex does not run the actual flag, does not call Discord API send,
and does not send a Discord message in this hotfix.

Phase 41C records the subsequent Phase 41B actual private-test reply success as
exactly one private-test-only message. It hardens Discord library log redaction
for session IDs and locks Phase 41B against repeat send. Phase 41C itself does
not run Discord live runtime, call Discord API send, or send a message.

Safe Mega Bundle 2 extends the locked state into Phase 42/43 prep. Phase 42 is
default blocked, manual-gate-only, deterministic/frozen-reply-only, private-test
only, and guarded by session/message/send count, timeout, duplicate/self/bot,
public/team, and no-repeat locks. Phase 43 syncs routing, rate-limit, and
session policy around that state. This bundle does not execute actual Discord
runtime/reply/send, LLM/RAG/embedding, or external actions.

Phase 42-0 hotfix makes the Phase 42 preflight and diagnostics read the current
process environment when no test env mapping is supplied. It may show the manual
gate as ready from env booleans/counts, but it still does not execute runtime,
call Discord API send, send messages, call LLM/RAG, create embeddings, or run
external actions.

Phase 42-1 adds the actual supervised private-test session runtime CLI and
manual allow flag:
`--phase42-supervised-private-test-session` and
`--allow-actual-phase42-supervised-session`. The CLI is default blocked without
the allow flag. This bundle verifies only the blocked CLI path and fake-adapter
success/guard tests; Codex does not run the actual Discord runtime, call
Discord API send, or send a Discord message. `message_sent_count=0` remains the
bundle verification state.

Safe Mega Bundle 3 records the separate Manual Gate 2 result: Phase 42 actual
supervised private-test session succeeded with `message_sent_count=1`,
`sent_scope=private_test_only`, and `session_lock_consumed=true`. Phase 42
repeat supervised session is now locked, and Phase 41B repeat send remains
locked. This bundle itself performs no Discord runtime/reply/send and adds no
new messages.

Phase 45A is prepared only as an actual LLM one-shot preflight. It reports
manual approval, approval phrase, OpenRouter/API key, provider, model, cost
guard, and call-count guard readiness as booleans only. It does not attempt or
call OpenRouter/LLM, does not call RAG, does not create embeddings/vector data,
does not execute external actions, and does not enable Discord send.

Phase45-0 fixes the LLM preflight env aliases and gate logic. The preflight now
recognizes `HERMES_LLM_API_KEY`, `OPENROUTER_API_KEY`, and
`HERMES_OPENROUTER_API_KEY` as API-key presence aliases, reads
`HERMES_LLM_PROVIDER`, `HERMES_LLM_MODEL`, and `HERMES_LLM_BASE_URL`, and keeps
`gate_checks` as positive booleans while `blocked_reasons` contains only failing
reasons. `--phase45-llm-env-diagnostics` reports only booleans and performs no
LLM/OpenRouter attempt or call.

Phase45-1 fixes the Manual Gate 3 readiness path. Operations dashboard safety
now treats Phase 45 readiness flags as non-execution state, while still blocking
actual LLM attempt/call/count signals. The legacy actual one-shot LLM draft
command returns blocked JSON without traceback when not allowed. This hotfix
does not attempt or call LLM/OpenRouter and keeps Discord send disabled.

Phase45-2 bridges Phase45A manual approval into the legacy actual LLM one-shot
draft command. `HERMES_PHASE45A_MANUAL_APPROVAL`,
`HERMES_PHASE45A_APPROVAL_PHRASE`, `HERMES_PHASE45A_COST_GUARD`, and
`HERMES_PHASE45A_CALL_COUNT_GUARD` are authoritative for the Phase45 actual
path. When the Phase45A gate is open, the command reports
`manual_approval.approved=true`; without the actual allow flag it still returns
blocked JSON and performs no LLM/OpenRouter attempt or call.

Phase45-3 closes out Manual Gate 3. The actual LLM/OpenRouter one-shot call
succeeded exactly once and is recorded with `phase45_actual_llm_call_count=1`.
The generated output was blocked by output safety for `external_action_claim`,
no response packet was created, Discord send stayed disabled, and no Discord
message was sent. Phase45 is now no-repeat locked:
`phase45_ready_for_repeat_llm_call=false`, and repeat actual LLM commands return
blocked JSON with reason `phase45_actual_llm_one_shot_already_consumed`.

Phase46 adds metadata-only review and retry policy for the blocked Phase45 LLM
output. Raw/full output is not included. Classifier calibration is fixture-only
and keeps negated external-action disclaimers from being treated as positive
external-action claims. Automatic retry is forbidden; any future retry requires
a new explicit manual gate and approval policy.

Phase47 adds human-review-only closeout and a disabled retry gate design packet.
It keeps the Phase45 blocked output metadata-only, requires human review,
forbids automatic retry and automatic send, includes no raw/full blocked output,
and exposes no retry execution path. The documented next options are Option A:
human-review-only project closeout, Option B: Phase48 new retry Manual Gate
design, and Option C: Phase48 Discord send review gate design. Phase47 does not
execute Option B or Option C.

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

Phase48A adds the human-review-only final closeout and operator handoff packet.
The historical completed external actions are fixed as: Phase41B private-test
reply exactly once, Phase42 supervised private-test session exactly once, and
Phase45 LLM/OpenRouter call exactly once. The blocked Phase45 output remains
metadata-only, raw/full output is not included, and no Discord send occurred
after the LLM output. External action freeze is active; automatic retry,
automatic Discord send, unattended auto reply, repeat actions, and production
unattended mode remain disabled.

Phase49/50 clarifies the final target as `STOXL_Discord_Agent_OS`, not a
human-review-only archive. Production unattended mode is still not ready.

Phase51/52 adds the continuous read-only runtime foundation using synthetic
fixtures only. It defines read-only event normalization, event guard
classification, session context, review packet composition, and synthetic replay
through the review-packet pipeline. It does not execute actual Discord runtime,
connect to Discord Gateway, call Discord API send, send Discord messages, call
LLM/OpenRouter, call RAG, create embeddings/vector data, run scheduler/cron live
execution, or execute external actions. Current automation level is Level 1
foundation, and the next operation must be a separate Manual Gate for longer
read-only live runtime with Discord send disabled.

Phase51/52-1 defines the read-only live runtime Manual Gate and launch packet.
The approval phrase is now documented, the authoritative process-env gate keys
are fixed, and the preflight/launch packet report readiness without exposing the
phrase value. This hotfix does not execute actual Discord runtime.

Phase52B closes out the separate operator-run read-only runtime Manual Gate as
metadata only. The Gateway connection is verified, the run timed out normally,
`captured_event_count=0`, empty capture is valid, and the capture file was not
read by this bundle. Discord API send, Discord message send,
LLM/OpenRouter, RAG, embedding/vector, scheduler live execution, and external
execution remain false.

Phase53 replays that empty capture into the review-packet pipeline without
external action. It produces `review_packet_count=0` from the empty capture and
marks the pipeline ready for the next real read-only capture canary. The next
actual operation must be a separate Manual Gate for one private-test human
message capture with Discord send disabled.
Automation levels are locked from Level 0 through Level 5, with current verified
state at Level 3 `prototype_verified`. Phase50 defines the final architecture,
manual gate matrix, release blocker matrix, and roadmap. The next actual
operation is the Phase53 read-only capture canary Manual Gate with one
private-test human message and Discord send disabled.

Phase54-57 closes out that separate read-only capture canary as metadata only:
Gateway connection verified, `captured_event_count=1`,
`captured_private_test_human_message_count=1`, and `review_packet_count=1`.
It prepares manual-approved reply preflight, a deterministic mock reply packet,
supervised private-test auto-reply safety prep, low-risk team auto-ops policy,
and scheduler dry-run policy. This Lean Mega Bundle does not execute actual
Discord runtime, call Discord API send, send a Discord message, attempt or call
LLM/OpenRouter, call RAG, create embeddings/vector data, run scheduler/cron live
execution, or execute external actions. The next actual operation must be a
separate Manual Gate for actual private-test manual-approved reply with Discord
send disabled until the approval gate is explicitly opened.

Phase58 adds a dedicated manual-approved deterministic private-test reply actual
path for the captured canary event, separate from older Phase39/41 send paths.
Phase58-1 enables the actual command to enter the send branch when all Manual
Gate checks pass, while this Lean Safe Hotfix verifies that branch only with a
fake sender. The approval phrase is defined for the later Manual Gate, but
phrase values are not logged in reports. The required verification commands do
not execute actual Discord runtime, perform real Discord send, call
LLM/OpenRouter, call RAG, create embeddings/vector data, run scheduler/cron live
execution, or execute external actions. The next actual operation must be a
separate Manual Gate: actual Phase58 private-test deterministic reply send
exactly once.

Phase58 closeout records the operator-run actual Phase58 private-test
deterministic reply send as metadata only. The historical
`message_sent_count=1` is fixed, closeout itself performs no Discord API send
and sends no message, and repeat send is locked with
`phase58_actual_manual_reply_already_consumed`. The next gate readiness is
supervised private-test auto-reply Manual Gate prep.

Phase59 adds the supervised private-test auto-reply runtime path for the next
Manual Gate. The Safe Hotfix verifies only preflight, blocked reports, and a
fake sender session in tests. Runtime scope is `private_test_only`, reply source
is `deterministic_template`, self/bot/duplicate/public/team events are guarded,
max session/reply/send/cooldown/kill-switch checks are represented, and real
Discord runtime/send, LLM/OpenRouter, RAG, embedding/vector, scheduler live
execution, and external execution remain disabled.

Phase59-62 wires the Phase59 real Discord sender adapter for the next separate
Manual Gate while keeping this Large Lean Mega Bundle no-runtime and no-send.
The `send_adapter_required_for_actual_manual_gate` block is resolved by
selecting the real adapter only after allow flag and gate checks pass; safe
verification still uses fake sender tests. Phase60 team canary policy and
Phase61 scheduler dry-run control are synchronized without live execution.
Phase62 sets Level 2 as manual-gate deterministic reply verified, Level 3 as
supervised private-test auto-reply nearly ready with sender wired, and keeps
Level 4 team auto-ops and Level 5 production unattended not ready.

Phase59-63 closes out the operator-run Phase59 supervised private-test
auto-reply short session as metadata only. The historical send count is fixed at
`historical_message_sent_count=1`, closeout itself performs no Discord API send
and sends no Discord message, and repeat Phase59 sessions are locked with
`phase59_supervised_auto_reply_session_already_consumed`. Phase60 low-risk
team-channel canary path and Phase61 scheduler dry-run control are prepared for
future Manual Gate work, while Level 3 is now verified and Level 4/5 remain not
ready.

Phase60-65 prepares the low-risk team-channel canary actual path without
external action. Public and unknown channels remain blocked, team canary is
default blocked, and only known team channel plus low-risk intent, Manual Gate,
kill switch, deterministic template, count guards, and disabled LLM/RAG/vector/
external/scheduler-live flags can reach the later actual path. This bundle
verifies the send branch only with a fake sender in tests. Phase61 scheduler
dry-run controls remain report-only, and the autonomy matrix stays at verified
Level 3 with next target Level 4 low-risk team-channel canary.

Phase60-65C fixes the authoritative team canary channel environment key to
`HERMES_PHASE60_TEAM_CANARY_CHANNEL_ID`. Reports expose only channel-ID
presence and never log the channel ID value. The actual Phase60 allow command
remains reserved for the next separate Manual Gate.

Phase60-66 closes out the operator-run Phase60 low-risk team-channel canary as
metadata only. The historical send count is fixed at
`historical_message_sent_count=1`, closeout itself performs no Discord API send
and sends no Discord message, and repeat team canary sends are locked with
`phase60_team_canary_already_consumed`. The historical real-send semantic is
recorded as `real_team_discord_send_performed=true` in closeout only. Current
verified level is now `level4_low_risk_team_channel_canary_verified_once`;
production unattended mode remains not ready.

Phase67-72 prepares supervised team-channel auto-ops with a team-event
classifier, low-risk classifier, ops queue, review packet, and deterministic
reply candidate. It is still manual-gated, default blocked for actual send, and
does not execute Discord runtime/send, LLM/OpenRouter, RAG, embedding/vector,
external execution, scheduler live execution, or production unattended mode.
Current verified level remains `level4_low_risk_team_channel_canary_verified_once`;
next target is `level4_supervised_team_channel_auto_ops`.

Phase67-73 closes out the operator-run supervised team-channel auto-ops session
as metadata only. The historical send count is fixed at
`historical_message_sent_count=1`, closeout itself performs no Discord API send
and sends no Discord message, and repeat Phase67 team auto-ops sends are locked
with `phase67_team_auto_ops_already_consumed`. Current verified level is
`level4_supervised_team_channel_auto_ops_verified_once`; next target is
`level4_limited_auto_mode_prep`. Production unattended mode remains not ready.

Phase74 prepares limited supervised auto mode without external action. The path
is Manual Gate only, known-team-channel only, low-risk-intent only,
deterministic-template only, bounded by max session/send/reply/cooldown guards,
and requires an ops queue item, review packet, kill switch, and human override.
The actual path is default blocked in this bundle and the allow command is
reserved for a separate Manual Gate. Phase67 remains verified exactly once and
locked against repeat team auto-ops sends. Current verified level remains
`level4_supervised_team_channel_auto_ops_verified_once`; next target is
`level4_limited_auto_mode_short_run`. Production unattended mode remains not
ready.

Phase74 Hotfix E0 wires the limited-auto actual Manual Gate branch without
executing it. The generic separate-gate hard block no longer masks a fully open
gate; missing allow flag, approval, approval phrase, token, team channel, kill
switch, reply mode, bounds, cooldown, disabled LLM/RAG/vector/external/
scheduler settings, and event eligibility now produce specific blocked reasons.
Safe verification uses only fake session tests and default-blocked CLI reports.

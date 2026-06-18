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

Phase48A is final closeout and operator handoff only. It authorizes no new
manual gate and no external action. Any future retry, Discord send review gate,
or production-readiness audit must be requested as a later explicit phase with a
new approval policy. Production unattended mode is not ready.

Phase49/50 defines the remaining Manual Gate roadmap without opening any gate.
Future gate types are read-only runtime, RAG/LLM no-send one-shot,
private-test supervised auto reply, team-channel low-risk canary, production
unattended limited launch, and emergency kill-switch verification. Every gate
requires an approval phrase, rate limit, cooldown, no-repeat or bounded-repeat
lock, and secret/raw log prohibition. Gates involving LLM require cost/count
guards; gates involving Discord send require channel allowlists.

Phase51/52 prepares the read-only runtime foundation but does not open the live
read-only runtime gate. The next allowed gate is a separate longer read-only live
runtime Manual Gate with Discord send disabled, LLM/RAG disabled, scheduler live
execution disabled, raw content/ID logging forbidden, and operator review packet
output only.

Phase51/52-1 defines the read-only live runtime Manual Gate approval phrase and
authoritative environment keys. The preflight reads process env booleans and
phrase match state, but reports only booleans. The approval phrase value must
not appear in reports, logs, or operation packets. This hotfix does not execute
the runtime.

Phase52B records the completed read-only runtime Manual Gate closeout as
metadata only: Gateway connection verified, timeout exit, zero captured events,
no Discord send, no LLM/OpenRouter, no RAG, no embedding/vector, no scheduler
live execution, and no external execution. The capture file content and path
value must not be dumped.

The next allowed gate is Phase53 read-only capture canary:
`capture_one_private_test_human_message_readonly`. It must be a separate
Manual Gate with Discord send disabled, reply disabled, LLM/RAG disabled,
embedding/vector disabled, external execution disabled, scheduler live
execution disabled, and raw content/Discord ID logging forbidden.

Phase54-57 closes out the completed read-only capture canary and does not open
any send gate. The next allowed Manual Gate is actual private-test
manual-approved reply. It must keep Discord send disabled until the explicit
approval gate is opened, must not call LLM/OpenRouter or RAG by default, must
hide approval phrase values and raw user content, and must produce a closeout
with `message_sent_count=0` unless a later explicit send gate is approved and
executed by the operator.

Phase58 defines the next Manual Gate keys for actual private-test deterministic
reply send exactly once:
`HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVED`,
`HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVAL_PHRASE`,
`HERMES_DISCORD_SEND_MESSAGES`, `HERMES_DISCORD_PRIVATE_TEST_REPLY`,
`HERMES_DISCORD_REPLY_MODE`, `HERMES_DISCORD_LLM_ENABLED`,
`HERMES_DISCORD_RAG_ENABLED`, `HERMES_EMBEDDING_ENABLED`,
`HERMES_VECTOR_ENABLED`, and `HERMES_DISCORD_EXTERNAL_EXECUTION`. The required
reply mode is `private_test_manual_approved_only`. This hotfix does not open or
execute that gate.

Phase59 defines the next supervised private-test auto-reply Manual Gate without
opening it. Required keys include
`HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVED`,
`HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVAL_PHRASE`,
`HERMES_PHASE59_MAX_SESSION_SECONDS`, `HERMES_PHASE59_MAX_REPLY_COUNT`,
`HERMES_PHASE59_MAX_SEND_COUNT`, `HERMES_PHASE59_COOLDOWN_SECONDS`,
`HERMES_PHASE59_KILL_SWITCH_READY`, Discord send/private-test reply/reply mode
keys, and LLM/RAG/embedding/vector/external disable keys. Required reply mode is
`private_test_supervised_auto_reply_only`. The actual short session must be a
separate Manual Gate.

Phase59-62 keeps that gate separate but wires the Phase59 real Discord sender
adapter so the later Manual Gate no longer fails on
`send_adapter_required_for_actual_manual_gate` once allow flag and all gates
pass. This bundle does not run the allow command, does not execute Discord
runtime, and does not perform real Discord send. Phase60 team canary, Phase61
scheduler live control, and Level 4/5 autonomy remain future gates.

Phase59 actual supervised private-test auto-reply has now been consumed exactly
once and is locked against repeat sessions with
`phase59_supervised_auto_reply_session_already_consumed`. The next allowed gate
is only Manual Gate prep for Phase60 low-risk team-channel canary. It must keep
public channels blocked, require known team channel scope, low-risk intent,
deterministic templates, max one reply per event, human override, kill switch,
LLM/RAG disabled by default, external execution disabled, and scheduler live
execution disabled.

Phase60 defines the next Manual Gate keys for actual low-risk team-channel
canary exactly once: `HERMES_PHASE60_TEAM_CANARY_APPROVED`,
`HERMES_PHASE60_TEAM_CANARY_APPROVAL_PHRASE`,
`HERMES_PHASE60_TEAM_CANARY_CHANNEL_ID`,
`HERMES_PHASE60_TEAM_CANARY_KILL_SWITCH_READY`,
`HERMES_PHASE60_TEAM_CANARY_MAX_SEND_COUNT`,
`HERMES_PHASE60_TEAM_CANARY_MAX_REPLY_COUNT`,
`HERMES_PHASE60_TEAM_CANARY_COOLDOWN_SECONDS`, Discord send/reply mode keys,
and LLM/RAG/embedding/vector/external disable keys. Required reply mode is
`known_team_low_risk_canary_only`. This bundle does not run the allow command
and does not perform real team-channel send.

Phase60 actual low-risk team-channel canary has now been consumed exactly once
and is locked against repeat sends with `phase60_team_canary_already_consumed`.
Any later team-channel automation must be a separate Manual Gate and must not
reuse the consumed Phase60 canary gate.

Phase67 defines the next Manual Gate keys for supervised team-channel auto-ops:
`HERMES_PHASE67_TEAM_AUTO_OPS_APPROVED`,
`HERMES_PHASE67_TEAM_AUTO_OPS_APPROVAL_PHRASE`,
`HERMES_PHASE67_TEAM_AUTO_OPS_CHANNEL_ID`,
`HERMES_PHASE67_TEAM_AUTO_OPS_KILL_SWITCH_READY`,
`HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SESSION_SECONDS`,
`HERMES_PHASE67_TEAM_AUTO_OPS_MAX_SEND_COUNT`,
`HERMES_PHASE67_TEAM_AUTO_OPS_MAX_REPLY_COUNT`,
`HERMES_PHASE67_TEAM_AUTO_OPS_COOLDOWN_SECONDS`, Discord send/reply mode keys,
and LLM/RAG/embedding/vector/external disable keys. Required reply mode is
`supervised_team_low_risk_auto_ops_only`. This bundle does not run the allow
command and does not perform real send.

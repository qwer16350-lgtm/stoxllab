# STOXL Hermes Gateway Handoff - 2026-06-13

## Current Milestone

- Phase 32D closeout replay/audit is complete.
- Phase 33A RAG preflight is available.
- Phase 33B local read-only RAG retrieval is available.
- Phase 33C RAG response packet generation is available.
- Phase 33D-safe scaffold is available for preflight, context safety, prompt envelope, would-send preview, and replay/audit.
- Phase 33D live RAG+LLM reply is not implemented.
- Phase 33D live readiness review is available and returns `go=false`.
- Phase 33D-1 guarded runtime code is available but has not been live-run.
- Phase 33D-2 live preflight closeout is available and does not execute the runtime.
- Phase 33D-3 single live private test runbook is available for user-run PowerShell execution only.
- Phase 33D-3A explicit single live approval env gate is required before the runtime can pass manual approval.
- Phase 33D-3B RAG+LLM private test runtime adapter is wired, while live execution remains user-run only.
- Phase 33D-4 single live private test closeout is available and marks the observed success ready for Phase 34 knowledge ingestion.
- Phase 34A-C local knowledge foundation is available for manifest, ingestion boundary, source routing, and citation/evidence packets.
- Phase 34D local evidence-to-RAG response packet integration is available for private-test review only.
- Phase 34E-F private-test evidence review packet and local sample dry-chain reports are available.
- Phase 34G-H0 prompt envelope preview and no-API/mock-only LLM dry readiness reports are available.
- Phase 34L-1E/F no-LLM send retry reporting is available for LLM-success/Discord-send-disconnect partial success, with the actual sender boundary wired behind manual gates.
- Phase 34L-2 E2E live reply plus no-LLM send retry closeout is available and marks the chain ready for Phase 34M final lock.
- Phase 34M final lock is available and marks the private-test E2E RAG+LLM+Discord MVP complete.
- Phase 35A post-MVP safety audit, operator runbook, and Phase 35 entry plan are available.
- Phase 35B local knowledge ingestion preview, evidence quality dry preview, and agent routing dry preview are available.
- Phase 35C agent evidence pack composer and agent prompt preview are available.
- Phase 39A actual private-test one-shot send path, safety gate, and blocked report are available, but execution remains default blocked.
- Phase 39B-0 manual send re-entry packet and no-send lock are available, but actual send remains not executed.

## Completed Chain

1. Discord read-only and private-test-only safety boundaries were separated.
2. Private test placeholder replies were guarded against public channel use, self-message loops, duplicates, cooldown issues, and circuit breaker failures.
3. LLM dry calls, LLM response packets, and guarded private-test-only LLM reply reports were added.
4. Phase 32D closeout replay/audit confirmed local verification without live Discord send or LLM API calls.
5. Phase 33A-C added local RAG readiness, local read-only retrieval, and RAG response packets.
6. Phase 33D-safe scaffold added review-only gates before any future RAG+LLM live reply.
7. Phase 33D live readiness review added go/no-go, manual enable, and rollback checklists.
8. Phase 33D-1 added guarded RAG+LLM private test runtime code with mockable LLM/send adapters.
9. Phase 33D-2 added a report-only closeout for default blocking, mock live-ready fixture checks, runtime option presence, and no live execution.
10. Phase 33D-3 added the manual runbook for one single live private test and its rollback/abort checklist.
11. Phase 33D-3A added `HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED` plus exact approval phrase gating.
12. Phase 33D-3B connected the live command to the RAG+LLM private-test adapter instead of the missing-adapter block.
13. Phase 33D-4 added a sanitized success-log parser, CLI report, operations viewer summary, and docs for the successful single live private test closeout.
14. Phase 34A-C added repo-local `knowledge/` source folders, text-only manifest rules, source routing policy, and evidence packet formatting.
15. Phase 34D connected evidence packets into RAG response packets with citation summaries and no live LLM/Discord/embedding behavior.
16. Phase 34E-F added private-test evidence review packets and a sample local knowledge dry chain.
17. Phase 34G-H0 added RAG evidence prompt envelope previews and mock-only LLM dry-call readiness reports.

## Current Safety Posture

- Discord live runtime was not started in Phase 33A-C.
- Discord messages are not sent by RAG preflight, retrieval, or response packet flows.
- OpenRouter/LLM API calls are not made by Phase 33A-C.
- Embedding APIs are not called.
- External DB/RAG source roots are not read.
- RAG ingest, indexing, vector DB creation, and external vector service connections are not performed.
- External posting, submission, email, contract, payment, or approval execution is not performed.
- Raw token/API key values and raw Discord IDs must not be printed.
- Phase 33D live implementation still requires separate manual approval.
- Current readiness review does not implement or run live RAG+LLM reply.
- Phase 33D-1 tests use mock LLM and mock send adapters only.
- Phase 33D-2 closeout does not start Discord, send Discord messages, call OpenRouter/LLM APIs, call embedding APIs, or execute external actions.
- Phase 33D-3 does not authorize Codex/agent to run the live command; the user must run the single live private test directly in PowerShell.
- Phase 33D-3A keeps the default runtime start blocked and logs only approval booleans, never the approval phrase value.
- Phase 33D-3B tests use mock adapters and token-missing checks only; no Discord runtime, LLM API, or send is executed during tests.
- Phase 33D-4 does not start Discord again, send another Discord message, call OpenRouter/LLM again, call embeddings, or execute external actions.
- Phase 33D-4 verifies that the observed live test sent exactly one Discord private-test reply and skipped the self-message.
- Phase 34A-C does not create embeddings, vector DB indexes, external source ingest, public/team channel replies, Discord sends, LLM API calls, or external execution.
- Phase 34A-C keeps `operation` canonical and keeps `operations` blocked.
- Phase 34D remains local evidence-to-RAG-packet integration only; `ready_for_llm_prompt=false`.
- Phase 34E-F remains review packet plus local sample dry chain only; `ready_for_discord_send=false`.
- Phase 34G-H0 remains prompt envelope preview plus no-API/mock-only LLM readiness only; `actual_llm_api_call=false`.
- Phase 34L-1E/F does not run live Discord runtime by default, does not send Discord messages in reports/tests, does not call OpenRouter/LLM again, does not call embeddings, and does not execute external actions. It prepares a manual send retry from an already safety-checked partial-success artifact.
- Phase 34L-2 does not run Discord, send another message, call OpenRouter/LLM, recall LLM, call embeddings, or execute external actions. It verifies LLM count 1, send retry LLM count 0, and final private-test sent count 1.
- Phase 34M final lock does not run Discord, send another message, call OpenRouter/LLM, recall LLM, call embeddings, or execute external actions. It keeps future live runs behind manual approvals.
- Phase 35A does not run Discord, send messages, call OpenRouter/LLM, recall LLM, create embeddings/vector indexes, schedule auto replies, or execute external actions. It confirms public/team channel send/reply remains forbidden and unattended auto reply remains false.
- Phase 35B does not run Discord, send messages, call OpenRouter/LLM, create embeddings/vector indexes, watch files, schedule auto replies, or execute external actions. It keeps `operation` canonical and `operations` forbidden.
- Phase 35C does not run Discord, send messages, call OpenRouter/LLM, execute prompts, create embeddings/vector indexes, dump full content, or execute external actions.
- Phase 39A does not run Discord live runtime, call Discord API send, send a Discord message, execute actual private-test send, call OpenRouter/LLM, generate or actualize an approval phrase, create embeddings/vector indexes, enable unattended auto reply, or execute external actions.

## Important Commands

```powershell
python apps\hermes_gateway\cli.py --rag-preflight-report --json
python apps\hermes_gateway\cli.py --rag-preflight-report --markdown
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --json
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --markdown
python apps\hermes_gateway\cli.py --rag-response-packet-report --json
python apps\hermes_gateway\cli.py --rag-response-packet-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-private-test-reply-report --json
python apps\hermes_gateway\cli.py --rag-llm-prompt-envelope-report --json
python apps\hermes_gateway\cli.py --rag-llm-would-send-preview --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --json
python apps\hermes_gateway\cli.py --rag-llm-live-readiness-review --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --json
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-success-closeout --json
python apps\hermes_gateway\cli.py --knowledge-manifest --json
python apps\hermes_gateway\cli.py --knowledge-ingestion-boundary --json
python apps\hermes_gateway\cli.py --knowledge-source-routing --json
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --json
python apps\hermes_gateway\cli.py --rag-evidence-integration --json
python apps\hermes_gateway\cli.py --rag-evidence-review-packet --json
python apps\hermes_gateway\cli.py --knowledge-dry-chain --json
python apps\hermes_gateway\cli.py --rag-evidence-prompt-envelope --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-readiness --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-report --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-report --markdown
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-closeout --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-call-closeout --markdown
python apps\hermes_gateway\cli.py --rag-evidence-would-send-preview --json
python apps\hermes_gateway\cli.py --rag-evidence-would-send-preview --markdown
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send-preflight --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send-preflight --markdown
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send --markdown
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send-closeout --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-preflight --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-replay --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-send-retry --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-live-closeout --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-phase34-final-lock --json
python apps\hermes_gateway\cli.py --phase35a-post-mvp-safety-audit --json
python apps\hermes_gateway\cli.py --local-knowledge-ingestion-preview --json
python apps\hermes_gateway\cli.py --evidence-quality-preview --json
python apps\hermes_gateway\cli.py --agent-routing-dry-preview --json
python apps\hermes_gateway\cli.py --agent-evidence-pack-composer --json
python apps\hermes_gateway\cli.py --agent-prompt-preview --json
python apps\hermes_gateway\cli.py --actual-private-test-one-shot-send --json
python apps\hermes_gateway\cli.py --actual-private-test-send-safety-gate --json
python apps\hermes_gateway\cli.py --actual-private-test-send-blocked-report --json
python apps\hermes_gateway\cli.py --operations-viewer --json
```

```powershell
python apps\hermes_gateway\tests\test_rag_preflight.py
python apps\hermes_gateway\tests\test_rag_local_retrieval.py
python apps\hermes_gateway\tests\test_rag_response_packet.py
python apps\hermes_gateway\tests\test_rag_context_safety.py
python apps\hermes_gateway\tests\test_rag_llm_private_test_reply.py
python apps\hermes_gateway\tests\test_rag_llm_prompt_envelope.py
python apps\hermes_gateway\tests\test_rag_llm_would_send_preview.py
python apps\hermes_gateway\tests\test_rag_llm_private_test_reply_replay.py
python apps\hermes_gateway\tests\test_rag_llm_live_readiness_review.py
python apps\hermes_gateway\tests\test_rag_llm_private_test_runtime.py
python apps\hermes_gateway\tests\test_rag_llm_live_preflight_closeout.py
python apps\hermes_gateway\tests\test_rag_llm_single_live_test_runbook.py
python apps\hermes_gateway\tests\test_rag_llm_live_success_closeout.py
python apps\hermes_gateway\tests\test_knowledge_manifest.py
python apps\hermes_gateway\tests\test_knowledge_ingestion_boundary.py
python apps\hermes_gateway\tests\test_knowledge_source_routing.py
python apps\hermes_gateway\tests\test_knowledge_evidence_packet.py
python apps\hermes_gateway\tests\test_rag_evidence_integration.py
python apps\hermes_gateway\tests\test_rag_evidence_review_packet.py
python apps\hermes_gateway\tests\test_knowledge_dry_chain.py
python apps\hermes_gateway\tests\test_rag_evidence_prompt_envelope.py
python apps\hermes_gateway\tests\test_rag_evidence_llm_dry_readiness.py
python apps\hermes_gateway\tests\test_rag_evidence_llm_dry_call.py
python apps\hermes_gateway\tests\test_rag_evidence_llm_dry_call_closeout.py
python apps\hermes_gateway\tests\test_rag_evidence_would_send_preview.py
python apps\hermes_gateway\tests\test_rag_evidence_private_test_send_preflight.py
python apps\hermes_gateway\tests\test_rag_evidence_private_test_send.py
python apps\hermes_gateway\tests\test_rag_evidence_private_test_send_closeout.py
python apps\hermes_gateway\tests\test_rag_evidence_private_test_e2e_preflight.py
python apps\hermes_gateway\tests\test_rag_evidence_private_test_e2e_replay.py
python apps\hermes_gateway\tests\test_llm_private_test_reply_replay.py
python apps\hermes_gateway\tests\test_llm_private_test_reply.py
python apps\hermes_gateway\tests\test_private_test_reply.py
python apps\hermes_gateway\tests\test_private_test_reply_replay.py
python apps\hermes_gateway\tests\test_private_test_reply_safety.py
python apps\hermes_gateway\tests\test_llm_response_packet.py
python apps\hermes_gateway\tests\test_llm_dry_call.py
python scripts\validate_stoxl_configs.py
```

## Live Gates To Keep Off

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="false"
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE=""
$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_LLM_DRY_CALL_APPROVAL_PHRASE=""
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE=""
```

## Next Recommended Phase

Before the next live attempt, read:

- `docs/STOXL_RAG_LLM_SINGLE_LIVE_TEST_RUNBOOK.md`

The user-run single live private test should only begin after human review of:

- source allow-list behavior
- private test channel ID gating
- retrieval context size limits
- response packet safety
- LLM output safety
- one-message-per-human-message send limits

Phase 34H-1 adds the manually approved actual LLM dry-call boundary. The default
report path remains no-call. A provider call requires the separate CLI allow flag
and manual env approval gate, and it still avoids Discord sends, external
ingestion, embedding APIs, vector DB/index creation, broad Discord replies,
public/team channel reply paths, and external execution.

Phase 34H-2 closes out the observed successful Phase 34H-1 dry call with an
embedded sanitized fixture. It performs no additional OpenRouter/LLM API call,
no Discord send, no embedding call, and no external execution. Passing closeout
sets `ready_for_phase34i_private_test_would_send_preview=true`.

Phase 34I creates a private-test would-send preview only. Phase 34J-0 creates
the private-test send preflight and manual approval gate design only. Neither
phase calls Discord APIs, sends a message, calls OpenRouter/LLM again, calls
embeddings, or executes external actions. Phase 34J-1 would require a separate
manual request before any single live private-test send.

Phase 34J-1 adds the one-shot private-test Discord send boundary. Default CLI
reports remain blocked. A live send requires `--allow-rag-evidence-private-test-discord-send`,
the manual approval env gate, `private_test_only` reply mode, and a configured
private test channel ID. It still does not call OpenRouter/LLM again, embeddings,
or external execution.

Phase 34J-2 closes out the observed single private-test send from an embedded
sanitized fixture. Phase 34K adds no-live E2E preflight. Phase 34L-0 adds
no-live/no-api/no-send mock replay. Actual E2E live reply remains deferred to a
separate Phase 34L-1 manual approval request.

Phase 34L-1 adds the manual private-test E2E live reply boundary. Default CLI
reports are blocked and execute no live runtime, no LLM API call, no Discord
send, no embedding API call, and no external execution. The actual live path is
available only through the explicit allow flag and exact manual env gates, and
must process one private-test event, one LLM call, and one private-test reply
before Phase 34L-2 closeout/replay/audit.

Phase 34L-1A fixes safety stage ordering. Prompt/input safety is pre-LLM, while
output safety is post-LLM and may only run when an LLM response packet exists.
The earlier blocked run is classified as safe but legacy-invalid ordering
because it reported `output_safety_blocked` while `llm_api_called=false` and
`discord_message_sent=false`. Next action is to retry Phase 34L-1 manually
after the hotfix.

Phase 34L-1B connects the approved E2E live path to the LLM stage. Prompt safety
passing now reaches `llm_stage_reached=true`; LLM calls are allowed only when
the LLM manual approval gate also passes, and the call count remains capped at
one. Output safety and Discord send remain downstream of a created LLM response
packet. The latest retry was safe: `llm_api_called=false` and
`discord_message_sent=false`. Next action is another Phase 34L-1 live retry.

Phase 34L-1C eliminates the LLM allowed-but-not-attempted no-op. If
`llm_call_allowed=true`, `llm_dispatch_invoked=true` and
`llm_api_call_attempted=true` must follow. If dispatch cannot run, the report
sets `llm_call_allowed=false` with a concrete `llm_dispatch_blocked_reason`.
The previous retry was safe: `llm_api_called=false` and
`discord_message_sent=false`. Next action is Phase 34L-1 live retry.

Phase 34L-1D fixes OpenRouter key detection in that dispatch path. The E2E live
dispatcher now recognizes `OPENROUTER_API_KEY` and
`HERMES_OPENROUTER_API_KEY`; only `openrouter_api_key_present` is reported and
key values remain hidden. The previous retry was safe: `llm_api_called=false`
and `discord_message_sent=false`. Next action is Phase 34L-1 live retry.

Phase 35D adds agent review packet and manual approval packet preview reports.
They are dry/report-only artifacts for human review. They do not generate
approval phrases, grant approval, run Discord live runtime, send Discord
messages, call OpenRouter/LLM, create embeddings/vector indexes, read external
sources, or execute external actions.

Phase 35E-G adds no-live operator rehearsal, operations dashboard lock, and
forbidden behavior sentinel reports. Phase 36 entry gate is added as a
report-only classifier. Phase 36 is not started, live execution remains false,
and explicit user approval is still required before any future live work.

Phase 36A adds a private-test one-shot LLM draft preflight. It only identifies
future candidate agents and manual gate names. It does not call OpenRouter/LLM,
attempt an LLM API call, send Discord messages, generate approval phrases,
activate manual approval, create embeddings/vector indexes, or execute external
actions.

Phase 36B adds a mock one-shot LLM draft packet and output safety rehearsal for
`kasumi`. It performs no OpenRouter/LLM API call or attempt, no Discord send,
no approval phrase generation, no manual approval activation, no embedding or
vector creation, and no external execution.

Phase 36C adds the actual one-shot LLM draft call preflight. It checks
OpenRouter key presence as a boolean and confirms manual approval is still not
actualized. It performs no OpenRouter/LLM API call or attempt and sends no
Discord message.

Phase 36D adds the manually gated actual one-shot LLM draft call path. The
default report is blocked and performs no LLM API attempt. The actual path is
limited to `kasumi`, source `operation`, one OpenRouter call, and review-only
output safety. It never sends Discord messages, enables public/team replies,
creates embeddings/vector indexes, or executes external actions.

Phase 36E closes out the observed Phase 36D one-shot LLM draft call. It is
report-only and locks the result as one LLM call, one review-only response
packet, output safety allowed, and zero Discord sends. It performs no additional
LLM attempt, no Discord runtime, no embeddings, and no external execution.

Phase 36F-G adds the no-send final lock and post-call dashboard/sentinel update.
Phase 36 is locked as one LLM call and zero Discord sends. Phase 37 entry gate
is available as report-only classification, but Phase 37 is not started and
live/send execution remains blocked without explicit approval.

Phase 37A-C adds private-test review, Discord send preflight preview, and send
approval rehearsal reports. These are all report-only: no new LLM call, no
Discord runtime/send, no approval phrase generation, no embeddings, and no
external execution.

Phase 37D-F adds the actual private-test send manual preflight, mock send
rehearsal, and no-send lock. The bundle remains report-only: OpenRouter/LLM API
call attempt is false, Discord live runtime execution is false, Discord API send
is false, Discord message sent is false, approval phrase generation is false,
manual approval actualization is false, embeddings/vector creation is false, and
external execution is false. Phase 38 actual private-test send path is not
started and remains blocked until a separate explicit user approval request.

Phase 38A-E adds report-only actual private-test send contract, final
would-send payload freeze, rollback gate, operator checklist, and live send
entry gate reports. The bundle performs no new OpenRouter/LLM API call or
attempt, no Discord live runtime, no Discord API send, no Discord message send,
no actual private-test send, no approval phrase generation, no manual approval
actualization, no embedding/vector creation, and no external execution. Phase
39 actual private-test send remains not started.

Phase 39A adds the actual private-test one-shot send path, safety gate, and
blocked report as default-blocked implementation scaffolding. It does not run
Discord live runtime, call Discord API send, send a Discord message, execute
actual private-test send, call OpenRouter/LLM, attempt an LLM API call, generate
or actualize an approval phrase, create embeddings/vector indexes, enable
public/team channel replies, enable unattended auto reply, or execute external
actions. Phase 39B manual one-shot actual send has not been run.

Phase 39A Hotfix 1 adds the missing `--allow-actual-private-test-send` parser
flag. The flag is report-only in Phase 39A and only reflects
`allow_flag_present=true`; it does not weaken the no-send policy.

Phase 39B-0 documents the Codex/user PowerShell process-env separation and keeps
the next actual send as a separate user-run action from the same PowerShell
session where token/channel presence is true. It performs no Discord live
runtime, no Discord API send, no message send, no OpenRouter/LLM attempt, no
RAG call, no embedding/vector creation, and no external execution. Phase 39C
closeout remains unavailable because no actual Phase 39B Discord message has
been sent.

Phase 39B Hotfix 2 separates the Phase 39A default blocked report from a Phase
39B manual readiness gate. With allow flag plus all required env/manual gates,
the report can show `ready_for_phase39b_manual_one_shot_send=true`, but
`ready_for_discord_send=false`, `discord_api_send_called=false`, and
`discord_message_sent=false` remain locked. Approval phrase values are never
printed; only presence/exact-match booleans are reported.

Phase 39B Hotfix 3 adds `--execute-actual-private-test-send` as a separate
execution-mode signal. With allow plus execute plus exact manual/env gates, the
report enters `phase39b_actual_send_execution` using
`actual_execution_adapter=mock`. This can set
`ready_for_actual_private_test_send=true`, but `ready_for_discord_send=false`,
`discord_api_send_called=false`, `discord_message_sent=false`, and
`message_sent_count=0` remain locked. The real execution env
`HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION` is reported only as a boolean, and
actual Discord send remains 0.

Phase 39B Final Bundle adds real adapter selection without running it in Codex.
Adapter selection is `none` without execute, `mock` with execute and real env
false, and `real` only with execute, real env true, exact manual approval gates,
token/channel presence, private-test-only scope, public/team blocked,
unattended false, and LLM/RAG/embedding/external flags false. Tests inject a
fake real adapter and verify adapter selection/call metadata while keeping
actual Discord API send, Discord message sent, and message count at zero.

Phase 39C records the operator-observed Phase 39B actual private-test one-shot
send success. Closeout locks the actual Discord send count to 1, records zero
additional Phase 39C sends, verifies gates off, forbids repeat/retry/unattended
send, and prepares push readiness. Codex does not run Discord live runtime,
does not call Discord API send, and does not push.

Phase 40 adds a safe overnight readiness bundle after Phase 39C. It keeps the
Phase 39 actual send count locked at 1 and records Phase 40 additional send
count 0. All Phase 40 reports are report-only: no Discord live runtime, no
Gateway connection, no Discord API send, no Discord message sent, no
OpenRouter/LLM attempt, no RAG call, no embedding/vector creation, and no
external execution. It adds synthetic/replay-only inbound event dry-run checks,
reply decision audit, outbound queue lock, session/idempotency lock, operator
handoff packet, and a live runtime entry gate blocked by default. The next
sensitive step is Phase 40J private-test live runtime manual entry after
separate human confirmation.

Phase 40J-40N prepares that entry without running it. The bundle adds read-only
runtime preflight, a manual-only launch packet, a pre-capture closeout packet,
runtime abort/kill-switch expectations, and a Phase 41 reply runtime entry gate
blocked by default. Codex does not execute the planned read-only command, does
not connect Discord Gateway, does not call Discord API send, and does not send a
message.

Phase 40O-40S adds the next support layer for a future user-run read-only
runtime: manual launcher packet, redacted capture schema, capture review
closeout, Phase 41 reply preflight matrix, and morning operator decision packet.
Codex still does not run the live command, does not create capture/log files, and
does not enable reply/send.

Phase 40T-0 fixes the missing `--run-discord-private-test-readonly` CLI parser
entry and adds a companion preflight report. The command is blocked by default,
prints only sanitized booleans, and keeps `started=false`,
`discord_gateway_connected=false`, `discord_api_send_called=false`,
`discord_message_sent=false`, and `message_sent_count=0` in Codex verification.

Phase 40T-1 adds a user-only `--execute-readonly-live-runtime` flag for the
private-test read-only runtime, plus timeout/max-events controls, redacted
capture writer, and closeout reports. Codex does not run the execute command;
tests use fake adapters only. Send/reply/LLM/RAG/embedding/external execution
remain false.

Phase 40T-2 adds graceful closeout for Discord login failure. A user-observed
invalid token/LoginFailure or HTTP 401 is converted to safe JSON with
`discord_gateway_connected=false`, `discord_api_send_called=false`,
`discord_message_sent=false`, `message_sent_count=0`, `retry_attempted=false`,
and token/channel/approval/API/raw content values not logged. Codex does not
retry Discord login or run the live runtime; the operator must refresh or
correct the Discord bot token manually before the next user-run read-only
runtime attempt.

Phase 40T-3 preserves the preflight snapshot into execute closeouts. This keeps
token/channel presence consistent between a passed preflight and a later
LoginFailure closeout. Missing token or channel presence blocks before login
with `login_attempted=false`; token/channel present plus LoginFailure or HTTP
401 reports `invalid_or_unauthorized_token` while preserving presence true.

Phase 40U-41A closes out the operator-observed Phase 40T read-only live success
without reconnecting. The closeout records Gateway connection success, timeout
exit, zero captured events, a written redacted capture artifact, and zero
messages sent. It also hardens capture review, adds synthetic private-test
fixtures, freezes a would-reply dry-run, syncs operations viewer/dashboard and
sentinel state, and adds a Phase 41 private-test reply preflight that remains
blocked by default. Codex did not run the live runtime, did not call Discord API
send, did not send a message, did not call LLM/RAG or embeddings, and did not
execute external actions.

Phase 41B-45A is the Safe Prep Mega Bundle for the final production-bound path.
It adds report-only preparation for the actual private-test reply one-shot,
actual reply closeout/no-repeat lock, supervised deterministic session, routing
and rate limits, LLM provider preflight, deterministic fake LLM adapter, and the
Phase 45A actual LLM one-shot preflight gate. Codex did not run Discord live
runtime, did not call Discord API send, did not send a Discord message, did not
attempt OpenRouter/LLM, did not call RAG or embeddings, and did not execute
external actions. The next sensitive manual gate is Phase 41B actual
private-test deterministic reply one-shot in a separate approval phase.

Phase 41B-0 hotfix keeps actual reply/send disabled while fixing the one-shot
gate to read process env booleans from the Phase 41B manual reply keys. It also
renames blocked reasons to failure-shaped names and adds a boolean-only
`--phase41b-env-diagnostics` report.

Phase 41B-1 implements the actual private-test deterministic reply runtime path
behind `--allow-actual-private-test-reply`, all manual gates, private-test-only
routing, human-message-only eligibility, one-shot lock, and no LLM/RAG/external
guards. The implementation adds adapter boundaries and fake-adapter tests.
Codex did not run the actual command, did not connect Discord Gateway, did not
call Discord API send, and did not send a Discord message.

Phase 41B-2 hotfix prepares the next manual retry after the first actual
private-test reply attempt detected an eligible human message but failed the
send step with a sanitized `RuntimeError`. The real adapter is now wired to
send through a fresh private-test channel send path instead of reusing the
closed collection message object. Tests remain fake-adapter only. Codex did not
run `--allow-actual-private-test-reply`, did not call Discord API send, and did
not send a Discord message.

Phase 41C closes out the observed Phase 41B actual private-test reply success:
one private-test-only message, previous failed attempt counted as zero sends,
and Phase 41B repeat send locked. It also adds Discord library log redaction for
session IDs emitted by `discord.gateway`. Codex does not run Discord live
runtime, call Discord API send, or send a Discord message in Phase 41C. The next
actual operation must be a separate Phase 42 supervised deterministic session
manual gate.

Safe Mega Bundle 2 prepares Phase 42 and syncs Phase 43 without opening that
manual gate. Phase 42 remains blocked by default with manual approval and exact
phrase required, deterministic/frozen replies only, private-test-only routing,
public/team/self/bot/duplicate guards, session and send-count locks, timeout
safe closeout, and no LLM/RAG/embedding/external execution. Phase 43 records
the routing/rate/session lock posture. Codex does not run actual Discord
runtime, call Discord API send, send messages, or retry Phase 41B.

Phase 42-0 hotfix reads the Phase 42 supervised-session gates from the current
PowerShell process environment for preflight and diagnostics. The report stays
safe: it prints only booleans/counts, never approval phrase values or raw
Discord/session data, and performs no runtime/send/LLM/RAG/external action.

Phase 42-1 adds the missing actual supervised private-test session runtime CLI
behind `--phase42-supervised-private-test-session` and
`--allow-actual-phase42-supervised-session`. Without the allow flag it returns a
blocked report and does not collect events, call Discord API send, or send a
message. Tests use a fake adapter for the one-message private-test success and
blocked public/team/self/bot/duplicate cases. The real adapter boundary is
wired for the next separate Manual Gate 2 operation; Codex did not invoke it in
this bundle.

Safe Mega Bundle 3 closes out the separately executed Manual Gate 2 result:
Phase 42 actual supervised private-test session succeeded with exactly one
private-test message and `session_lock_consumed=true`. Phase 42 repeat
supervised session is locked, Phase 41B repeat send remains locked, and this
bundle performs no new Discord runtime/send/reply. It also prepares Phase 45A
actual LLM one-shot preflight only: key/provider/model/cost/count/manual gates
are booleans, while actual LLM/OpenRouter attempt/call, RAG, embeddings,
external execution, and Discord send remain false. The next actual operation is
Manual Gate 3 for actual LLM one-shot call approval, with Discord send still
disabled.

Phase45-0 fixes Phase 45A env alias handling and gate naming. The preflight
recognizes `HERMES_LLM_API_KEY` plus OpenRouter aliases for key presence, reads
`HERMES_LLM_PROVIDER`, `HERMES_LLM_MODEL`, and `HERMES_LLM_BASE_URL`, and adds
`--phase45-llm-env-diagnostics` for boolean-only checks. Gate checks now use
positive state names and blocked reasons only list failing gates. This fix does
not attempt or call LLM/OpenRouter, does not send Discord messages, and does not
run RAG/embedding/external actions.

Phase45-1 separates Phase 45 readiness from execution in the dashboard lock and
sentinel. `phase45_ready_for_actual_llm_one_shot_call=true` is allowed as a
manual-gate readiness signal when actual attempt/call/count remain false/zero.
The actual command path returns a blocked JSON report without traceback when the
allow gate is absent. Real LLM/OpenRouter calls remain unexecuted in this
hotfix, Discord send remains disabled, and the next action is a separate Manual
Gate 3 retry.

Phase45-2 bridges Phase45A manual approval into the legacy actual LLM one-shot
draft command. The Phase45A keys are authoritative for this path, so an open
Phase45A gate is reflected as `manual_approval.approved=true`; without the
actual allow flag the command still returns blocked JSON with reason
`actual_llm_allow_flag_missing`. Reports keep API key, approval phrase,
provider/model/base URL values, raw IDs, and raw content out of output. This
safe hotfix does not attempt or call LLM/OpenRouter, does not run
RAG/embedding/external actions, and keeps Discord send disabled. The next
actual operation must be a separate Manual Gate 3 retry exactly once with
Discord send disabled.

Phase45-3 closes out that Manual Gate 3 operation. The actual LLM/OpenRouter
one-shot call succeeded exactly once, with `phase45_actual_llm_call_count=1`.
Output safety then blocked the generated draft for `external_action_claim`; no
response packet was created, Discord send remained disabled, and no Discord
message was sent. Phase45 repeat LLM calls are now locked, and repeat
`--actual-one-shot-llm-draft-call` commands return blocked JSON with reason
`phase45_actual_llm_one_shot_already_consumed`. Any future retry requires a
separate Manual Gate with a new explicit approval policy.

Phase46 records a metadata-only review policy for the blocked Phase45 output.
It does not include the full raw LLM output, does not call LLM/OpenRouter, and
does not send Discord messages. Fixture-based classifier calibration verifies
that negated external-action wording is not treated as a positive external
action claim. Automatic retry remains forbidden; Phase47 is the earliest place
to design either human-review-only closeout or a new retry Manual Gate.

Phase47 adds the human-review-only closeout and disabled retry gate design
packet. It does not attempt or call LLM/OpenRouter, does not send to Discord,
does not include full raw blocked output, and does not make retry execution
available. Phase45 repeat LLM call is forbidden, blocked output auto retry is
forbidden, blocked output auto Discord send is forbidden, and raw output dump is
forbidden. Any future retry must be a new explicit Manual Gate with a new
approval policy in a later phase.

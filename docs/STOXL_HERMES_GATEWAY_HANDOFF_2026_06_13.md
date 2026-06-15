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

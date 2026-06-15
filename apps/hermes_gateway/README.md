# STOXL Fresh Hermes Gateway

This folder is a fresh local runtime skeleton for the STOXL Hermes Discord Agent Organization.

It does not replace any NAS or production Hermes Gateway project. It exists so the STOXL registry, prompts, dry-run Discord structure, mock evaluators, replay/approval mock, audit export, and approval review packet can be tested through a safe local boundary before any real Discord work is considered.

## Current Capabilities

- Accept a local text request or a local JSON event.
- Normalize the event into the Phase 12 adapter boundary shape.
- Load `registry/stoxl_agent_registry.example.json`.
- Call the Phase 10 mock evaluator in-process when available.
- Build a local dispatch plan.
- Build an audit payload.
- Replay multiple local mock events in order.
- Create in-memory approval queue items.
- Apply mock approve/reject decisions without external execution.
- Export replay results to local JSON/JSONL logs.
- Build local approval review packets in JSON/Markdown.
- Run read-only Discord readiness checks without calling Discord.
- Normalize local Discord-shaped raw events and render would-send payloads without calling Discord.
- Replay local Discord-shaped raw events with would-send payloads, approval queue, audit trail, and optional review packets.
- Validate local Discord runtime mapping JSON before any future read-only connection.
- Protect and validate ignored local runtime mapping files.
- Build a no-connection preflight report for a future read-only Discord phase.
- Build Phase 23-28 safety scaffold reports without Discord, LLM, RAG, replies, or external execution.
- Build Phase 29 read-only Discord runtime reports.
- Provide an explicitly gated read-only Gateway runtime path for a later manual run.
- Build Phase 30 live event audit records, routing reports, would-send previews, review packets, and daily manifests without sending Discord messages.
- View Phase 30 operations artifacts with a local-only Phase 31A packet viewer.
- Build Phase 31C deterministic agent placeholder responses without LLM, RAG, or Discord replies.
- Build Phase 31B private test channel reply reports and a guarded private-test-only reply path.
- Build Phase 31D private test reply safety reports for cooldown, budget, duplicate, and circuit breaker controls.
- Build Phase 31E private test reply replay reports and operations viewer summaries without Discord sends.
- Build Phase 32A LLM safety preflight, policy, and prompt envelope reports without calling any LLM provider.
- Build Phase 32B private-test-only LLM dry call reports with mock default behavior and no Discord send.
- Build Phase 32C LLM response packets for local review workflows without Discord send.
- Close out Phase 32C-LIVE by writing a gated LLM dry-call artifact, creating the latest local response packet, and exposing it to the operations viewer without Discord send.
- Build Phase 32D guarded private-test-only LLM reply preflight and runtime boundaries.
- Build Phase 32D closeout replay/audit reports without live Discord send or LLM API calls.
- Build Phase 33A RAG preflight reports without retrieval, embeddings, LLM, Discord send, or external execution.
- Build Phase 33B local read-only RAG retrieval reports from repo-local `knowledge/<source>` folders only.
- Build Phase 33C RAG response packets for human review without LLM, embeddings, Discord send, or external execution.
- Build Phase 33D-safe RAG+LLM private test scaffold reports for preflight, context safety, prompt envelope, would-send preview, and replay/audit without live send.
- Build Phase 33D live readiness review reports with go/no-go checklist and rollback planning without live execution.
- Build Phase 33D-1 guarded RAG+LLM private test runtime code with mockable LLM/send adapters and report-only CLI checks.
- Build Phase 33D-2 live preflight closeout reports that confirm default blocking, mock live-ready fixture readiness, runtime option presence, and no live execution.
- Maintain the Phase 33D-3 single live private test runbook for manual user-run execution only.
- Build Phase 33D-4 single live private test closeout reports from an embedded sanitized success fixture without another live run.
- Build Phase 34A-C local knowledge foundation reports for manifest, ingestion boundary, source routing, and evidence packets.
- Build Phase 34D local evidence-to-RAG response packet integration reports without LLM, embeddings, Discord send, or external ingest.
- Build Phase 34E-F private-test review packets and local sample dry-chain reports without LLM, embeddings, Discord send, or external ingest.
- Build Phase 34G-H0 prompt envelope previews and no-API/mock-only LLM dry readiness reports without provider calls.
- Build Phase 34H-1 manually approved RAG evidence LLM dry-call reports. The default path is report-only; an actual provider call requires a separate CLI allow flag and manual env approval, and still never sends Discord messages.
- Build Phase 34H-2 RAG evidence LLM dry-call closeout reports from an embedded sanitized success fixture without another OpenRouter call.
- Build Phase 34I private-test would-send previews without Discord API calls.
- Build Phase 34J-0 private-test send preflight and manual approval gate reports without actual send.
- Build Phase 34J-1 one-shot private-test Discord send boundary with default blocking, explicit allow flag, and manual approval gate.

## Explicit Non-Goals

- No Discord API calls.
- No Discord Gateway connection unless a human explicitly runs the Phase 29 read-only mode.
- No bot token values are printed or returned in reports.
- No `.env` content is printed.
- No LLM, OpenAI, or OpenRouter calls.
- No external DB/RAG reads or copies.
- No external posting, submission, email, contract, or payment actions.
- No approval-to-external-execution conversion.
- No real Discord approval buttons or messages.
- No real Discord readiness check connects to Discord.
- No Phase 30 audit artifact sends a Discord reply or calls LLM/RAG.
- No general Discord reply path exists; Phase 31B permits only a manually enabled private test channel reply.
- No Phase 32A LLM report calls OpenAI, OpenRouter, Anthropic, RAG, Discord send, or external execution.
- No Phase 32B dry call sends Discord messages, reads RAG, or performs external execution.
- No Phase 32C response packet sends Discord messages, reads RAG, or performs external execution.
- No Phase 32C-LIVE closeout sends Discord messages, reads RAG, or performs external execution.
- No Phase 32D LLM reply is allowed outside the configured private test channel ID.
- No Phase 33A-C RAG flow reads external/NAS RAG roots, calls embedding APIs, calls LLM APIs, or sends Discord messages.
- No Phase 33D live RAG+LLM private test reply is implemented here; the current Phase 33D-safe scaffold is review-only.
- No Phase 33D live readiness review starts Discord, calls LLM APIs, calls embeddings, or enables live replies.
- No Phase 33D-1 test runs start Discord, call OpenRouter/LLM APIs, call embeddings, or execute external actions.
- No Phase 33D-2 closeout starts Discord, sends Discord messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions.
- No Phase 33D-3 runbook step starts Discord, sends Discord messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions automatically.
- No Phase 33D-4 closeout starts Discord, sends additional Discord messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions.
- No Phase 34A-C knowledge foundation flow creates embeddings, vector DB indexes, external source ingest, public/team channel replies, additional Discord sends, LLM API calls, or external execution.
- No Phase 34D evidence integration enables LLM prompts, embeddings, vector DB indexes, external source ingest, public/team channel replies, Discord sends, or external execution.
- No Phase 34E-F review packet or dry-chain flow enables LLM prompts, Discord sends, embeddings, external source ingest, vector DB/index creation, or external execution.
- No Phase 34G-H0 prompt readiness flow calls OpenRouter/LLM APIs, sends Discord messages, calls embeddings, ingests external sources, or executes external actions.
- No Phase 34H-1 default report calls OpenRouter/LLM APIs, sends Discord messages, calls embeddings, ingests external sources, or executes external actions. The actual dry-call path is manual-approval gated and does not enable Discord send.
- No Phase 34H-2 closeout calls OpenRouter/LLM APIs, sends Discord messages, calls embeddings, ingests external sources, or executes external actions.
- No Phase 34I would-send preview calls Discord APIs, sends messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions.
- No Phase 34J-0 preflight calls Discord APIs, sends messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions.
- No Phase 34J-1 default report sends Discord messages, calls OpenRouter/LLM APIs, calls embeddings, or executes external actions. Live send requires a separate human-run allow flag and manual approval gate.

## Phase 21 Read-Only Planning Docs

- `docs/STOXL_PRIVATE_SERVER_READONLY_PLAN.md`
- `docs/STOXL_DISCORD_MANUAL_MAPPING_GUIDE.md`
- `docs/STOXL_DISCORD_ROLLBACK_AND_SAFETY.md`
- `apps/hermes_gateway/examples/private_server_readonly_checklist.example.json`
- `apps/hermes_gateway/examples/manual_mapping_fill_guide.example.md`
- `docs/STOXL_LOCAL_MAPPING_PROTECTION.md`
- `docs/STOXL_DISCORD_DEPENDENCY_PLAN.md`
- `docs/STOXL_READONLY_CONNECTION_PREFLIGHT.md`
- `docs/STOXL_DISCORD_TOKEN_HANDLING_RULES.md`
- `docs/STOXL_READONLY_RUNTIME_STUB.md`
- `docs/STOXL_LIVE_CAPTURE_AUDIT_ONLY.md`
- `docs/STOXL_REPLY_PLANNER_DISABLED_BY_DEFAULT.md`
- `docs/STOXL_APPROVAL_INTERACTION_SPEC.md`
- `docs/STOXL_AGENT_RESPONSE_INTERFACE.md`
- `docs/STOXL_PHASE23_28_SAFETY_SCAFFOLD.md`
- `docs/STOXL_ACTUAL_READONLY_DISCORD_CONNECTION.md`
- `docs/STOXL_DISCORD_SEND_BLOCKING_GUARD.md`
- `docs/STOXL_LIVE_EVENT_PIPELINE.md`
- `docs/STOXL_LIVE_EVENT_AUDIT_PERSISTENCE.md`
- `docs/STOXL_WOULD_SEND_PREVIEW.md`
- `docs/STOXL_LIVE_EVENT_REVIEW_PACKET.md`
- `docs/STOXL_PHASE30_AUDIT_OPERATIONS.md`
- `docs/STOXL_OPERATIONS_PACKET_VIEWER.md`
- `docs/STOXL_AGENT_PLACEHOLDER_RESPONSE.md`
- `docs/STOXL_PRIVATE_TEST_CHANNEL_REPLY.md`
- `docs/STOXL_PRIVATE_TEST_REPLY_SAFETY_CLOSEOUT.md`
- `docs/STOXL_PRIVATE_TEST_REPLY_REPLAY_CLOSEOUT.md`
- `docs/STOXL_LLM_SAFETY_PREFLIGHT.md`
- `docs/STOXL_LLM_DRY_CALL_PRIVATE_TEST.md`
- `docs/STOXL_LLM_RESPONSE_PACKET_INTEGRATION.md`
- `docs/STOXL_LLM_RESPONSE_PACKET_LIVE_CLOSEOUT.md`
- `docs/STOXL_LLM_PRIVATE_TEST_REPLY.md`
- `docs/STOXL_LLM_PRIVATE_TEST_REPLY_CLOSEOUT.md`
- `docs/STOXL_RAG_PREFLIGHT.md`
- `docs/STOXL_RAG_LOCAL_READONLY_RETRIEVAL.md`
- `docs/STOXL_RAG_RESPONSE_PACKET.md`
- `docs/STOXL_RAG_PRIVATE_TEST_LLM_REPLY_PLAN.md`
- `docs/STOXL_RAG_LLM_PRIVATE_TEST_REPLY_PREFLIGHT.md`
- `docs/STOXL_RAG_LLM_PROMPT_ENVELOPE.md`
- `docs/STOXL_RAG_LLM_WOULD_SEND_PREVIEW.md`
- `docs/STOXL_RAG_LLM_PRIVATE_TEST_REPLY_REPLAY.md`
- `docs/STOXL_RAG_LLM_LIVE_READINESS_REVIEW.md`
- `docs/STOXL_RAG_LLM_LIVE_ROLLBACK_CHECKLIST.md`
- `docs/STOXL_RAG_LLM_PRIVATE_TEST_RUNTIME.md`
- `docs/STOXL_RAG_LLM_LIVE_PREFLIGHT_CLOSEOUT.md`
- `docs/STOXL_RAG_LLM_SINGLE_LIVE_TEST_RUNBOOK.md`
- `docs/STOXL_RAG_LLM_SINGLE_LIVE_TEST_CLOSEOUT.md`
- `docs/STOXL_KNOWLEDGE_INGESTION_BOUNDARY.md`
- `docs/STOXL_KNOWLEDGE_MANIFEST.md`
- `docs/STOXL_KNOWLEDGE_SOURCE_ROUTING.md`
- `docs/STOXL_KNOWLEDGE_EVIDENCE_PACKET.md`
- `docs/STOXL_RAG_EVIDENCE_INTEGRATION.md`
- `docs/STOXL_RAG_EVIDENCE_REVIEW_PACKET.md`
- `docs/STOXL_KNOWLEDGE_DRY_CHAIN.md`
- `docs/STOXL_RAG_EVIDENCE_PROMPT_ENVELOPE.md`
- `docs/STOXL_RAG_EVIDENCE_LLM_DRY_READINESS.md`
- `docs/STOXL_RAG_EVIDENCE_LLM_DRY_CALL.md`
- `docs/STOXL_RAG_EVIDENCE_LLM_DRY_CALL_CLOSEOUT.md`
- `docs/STOXL_RAG_EVIDENCE_WOULD_SEND_PREVIEW.md`
- `docs/STOXL_RAG_EVIDENCE_PRIVATE_TEST_SEND_PREFLIGHT.md`
- `docs/STOXL_RAG_EVIDENCE_PRIVATE_TEST_SEND.md`

These documents prepare for a later private server read-only connection review. They do not authorize or perform a Discord connection.

## Local Usage

```powershell
python apps\hermes_gateway\main.py
python apps\hermes_gateway\cli.py --text "인스타 업로드 문구 초안 만들어줘" --channel "marin-초안" --author-role "Decision Maker"
python apps\hermes_gateway\cli.py --event apps\hermes_gateway\examples\local_message_event.json --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --approval-actions apps\hermes_gateway\examples\approval_actions.example.json --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --export-log --dry-run-export --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --review-packet --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --approval-actions apps\hermes_gateway\examples\review_packet_actions.example.json --review-packet --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --review-packet --export-review-packet --dry-run-export --json
python apps\hermes_gateway\cli.py --discord-readiness --json
python apps\hermes_gateway\cli.py --discord-readiness --mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --json
python apps\hermes_gateway\cli.py --discord-raw-event apps\hermes_gateway\examples\discord_raw_event_stub.example.json --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --review-packet --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --export-log --dry-run-export --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --strict --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.partial.example.json --json
python apps\hermes_gateway\cli.py --init-local-mapping --json
python apps\hermes_gateway\cli.py --validate-local-mapping --json
python apps\hermes_gateway\cli.py --validate-local-mapping --strict --json
python apps\hermes_gateway\cli.py --connection-preflight --json
python apps\hermes_gateway\cli.py --readonly-runtime-stub --json
python apps\hermes_gateway\cli.py --live-capture-stub --json
python apps\hermes_gateway\cli.py --reply-planner-report --json
python apps\hermes_gateway\cli.py --approval-interaction-spec --json
python apps\hermes_gateway\cli.py --agent-response-interface --json
python apps\hermes_gateway\cli.py --safety-scaffold-report --json
python apps\hermes_gateway\cli.py --discord-token-report --json
python apps\hermes_gateway\cli.py --send-block-report --json
python apps\hermes_gateway\cli.py --live-event-pipeline-report --json
python apps\hermes_gateway\cli.py --discord-readonly-runtime-report --json
python apps\hermes_gateway\cli.py --live-event-audit-report --json
python apps\hermes_gateway\cli.py --would-send-preview-report --json
python apps\hermes_gateway\cli.py --live-event-review-packet-report --json
python apps\hermes_gateway\cli.py --phase30-audit-ops-report --json
python apps\hermes_gateway\cli.py --operations-viewer --json
python apps\hermes_gateway\cli.py --operations-viewer --markdown
python apps\hermes_gateway\cli.py --operations-packet --event-id EVENT_ID --json
python apps\hermes_gateway\cli.py --agent-placeholder-response-report --json
python apps\hermes_gateway\cli.py --agent-placeholder-response-report --markdown
python apps\hermes_gateway\cli.py --private-test-reply-report --json
python apps\hermes_gateway\cli.py --private-test-reply-report --markdown
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --json
python apps\hermes_gateway\cli.py --private-test-reply-safety-report --markdown
python apps\hermes_gateway\cli.py --private-test-reply-replay-report --json
python apps\hermes_gateway\cli.py --private-test-reply-replay-report --markdown
python apps\hermes_gateway\cli.py --llm-preflight-report --json
python apps\hermes_gateway\cli.py --llm-preflight-report --markdown
python apps\hermes_gateway\cli.py --llm-safety-policy-report --json
python apps\hermes_gateway\cli.py --llm-prompt-envelope-report --json
python apps\hermes_gateway\cli.py --llm-prompt-envelope-report --markdown
python apps\hermes_gateway\cli.py --llm-dry-call-report --json
python apps\hermes_gateway\cli.py --llm-dry-call-report --markdown
python apps\hermes_gateway\cli.py --llm-dry-call-report --json --allow-llm-api-call --write-artifact
python apps\hermes_gateway\cli.py --llm-response-packet-report --json
python apps\hermes_gateway\cli.py --llm-response-packet-report --markdown
python apps\hermes_gateway\cli.py --llm-response-packet-report --latest --json
python apps\hermes_gateway\cli.py --llm-response-packet-report --latest --markdown
python apps\hermes_gateway\cli.py --llm-response-packet-live-closeout --json
python apps\hermes_gateway\cli.py --llm-private-test-reply-report --json
python apps\hermes_gateway\cli.py --llm-private-test-reply-report --markdown
python apps\hermes_gateway\cli.py --llm-private-test-reply-replay-report --json
python apps\hermes_gateway\cli.py --llm-private-test-reply-replay-report --markdown
python apps\hermes_gateway\cli.py --rag-preflight-report --json
python apps\hermes_gateway\cli.py --rag-preflight-report --markdown
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --json
python apps\hermes_gateway\cli.py --rag-local-retrieval-report --markdown
python apps\hermes_gateway\cli.py --rag-response-packet-report --json
python apps\hermes_gateway\cli.py --rag-response-packet-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-private-test-reply-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-reply-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-prompt-envelope-report --json
python apps\hermes_gateway\cli.py --rag-llm-prompt-envelope-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-would-send-preview --json
python apps\hermes_gateway\cli.py --rag-llm-would-send-preview --markdown
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-replay-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-live-readiness-review --json
python apps\hermes_gateway\cli.py --rag-llm-live-readiness-review --markdown
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --markdown
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --markdown
python apps\hermes_gateway\cli.py --rag-llm-live-success-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-success-closeout --markdown
python apps\hermes_gateway\cli.py --knowledge-manifest --json
python apps\hermes_gateway\cli.py --knowledge-manifest --markdown
python apps\hermes_gateway\cli.py --knowledge-ingestion-boundary --json
python apps\hermes_gateway\cli.py --knowledge-ingestion-boundary --markdown
python apps\hermes_gateway\cli.py --knowledge-source-routing --json
python apps\hermes_gateway\cli.py --knowledge-source-routing --markdown
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --json
python apps\hermes_gateway\cli.py --knowledge-evidence-packet --markdown
python apps\hermes_gateway\cli.py --rag-evidence-integration --json
python apps\hermes_gateway\cli.py --rag-evidence-integration --markdown
python apps\hermes_gateway\cli.py --rag-evidence-review-packet --json
python apps\hermes_gateway\cli.py --rag-evidence-review-packet --markdown
python apps\hermes_gateway\cli.py --knowledge-dry-chain --json
python apps\hermes_gateway\cli.py --knowledge-dry-chain --markdown
python apps\hermes_gateway\cli.py --rag-evidence-prompt-envelope --json
python apps\hermes_gateway\cli.py --rag-evidence-prompt-envelope --markdown
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-readiness --json
python apps\hermes_gateway\cli.py --rag-evidence-llm-dry-readiness --markdown
python apps\hermes_gateway\cli.py --run-discord-private-test-reply --json
python apps\hermes_gateway\tests\test_local_pipeline.py
python apps\hermes_gateway\tests\test_replay_approval.py
python apps\hermes_gateway\tests\test_persistent_audit_export.py
python apps\hermes_gateway\tests\test_review_packet.py
python apps\hermes_gateway\tests\test_discord_readiness.py
python apps\hermes_gateway\tests\test_discord_adapter_stub.py
python apps\hermes_gateway\tests\test_discord_replay.py
python apps\hermes_gateway\tests\test_mapping_validator.py
python apps\hermes_gateway\tests\test_local_mapping_manager.py
python apps\hermes_gateway\tests\test_connection_preflight.py
python apps\hermes_gateway\tests\test_safety_scaffold.py
python apps\hermes_gateway\tests\test_discord_readonly_runtime.py
python apps\hermes_gateway\tests\test_live_event_pipeline.py
python apps\hermes_gateway\tests\test_live_event_audit_persistence.py
python apps\hermes_gateway\tests\test_would_send_preview.py
python apps\hermes_gateway\tests\test_live_event_review_packet.py
python apps\hermes_gateway\tests\test_operations_packet_viewer.py
python apps\hermes_gateway\tests\test_agent_placeholder_response.py
python apps\hermes_gateway\tests\test_private_test_reply.py
python apps\hermes_gateway\tests\test_private_test_reply_safety.py
python apps\hermes_gateway\tests\test_private_test_reply_replay.py
python apps\hermes_gateway\tests\test_llm_preflight.py
python apps\hermes_gateway\tests\test_llm_safety_policy.py
python apps\hermes_gateway\tests\test_llm_client.py
python apps\hermes_gateway\tests\test_llm_dry_call.py
python apps\hermes_gateway\tests\test_llm_response_packet.py
python apps\hermes_gateway\tests\test_llm_response_packet_live_closeout.py
python apps\hermes_gateway\tests\test_llm_private_test_reply.py
python apps\hermes_gateway\tests\test_llm_private_test_reply_replay.py
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
```

The `--run-discord-readonly` option is intentionally not part of normal local
test usage. It is reserved for a separately approved private server read-only
connection run. Message sending remains blocked in that strict mode.

The `--run-discord-private-test-reply` option is a separate Phase 31B runtime
path for the private-test-only reply exception. It requires
`HERMES_DISCORD_SEND_MESSAGES=true`, `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`,
`HERMES_DISCORD_REPLY_MODE=private_test_only`, and an event channel that exactly
matches `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID`. LLM, RAG, external execution,
self-message replies, duplicate message replies, public replies, and team
channel replies remain blocked.

Phase 31D adds a session-local cooldown, maximum reply budget, duplicate guard,
and circuit breaker around that private-test-only runtime path.

Phase 31E adds local replay and operations viewer summaries for private test
reply states. Replay reports do not connect to Discord and do not send messages.

Phase 32A adds local-only LLM safety preflight reports. These reports check env
flags, provider/model presence, prompt envelope previews, and output policy
without making a provider request, reading RAG, or sending Discord messages.

Phase 32B adds a private-test-only dry call layer. The default CLI path uses a
mock response. The explicit `--allow-llm-api-call` option can attempt one
provider call only when all LLM, private-test, no-send, no-RAG, and no-external
env gates pass.

Phase 32C converts LLM dry call results into local response packets that can be
reviewed in would-send previews, live event review packets, and the operations
viewer. These packets do not send Discord messages or perform external actions.

Phase 32C-LIVE reads the latest local dry-call artifact, writes a local response
packet, and reports whether the operations viewer can see the packet. It is a
local closeout workflow only; Discord send, RAG, and external execution remain
false.

Phase 32D adds a separate guarded runtime for private-test-only LLM replies. It
requires private channel ID match, LLM output safety, response packet safety,
cooldown, reply budget, duplicate guard, and circuit breaker checks. It is not a
general Discord reply mode.

Phase 32D closeout validates the redacted live success fixture and blocked
scenario replay without starting Discord, calling OpenRouter, reading RAG, or
executing external actions.

Phase 33A-C add a local RAG safety ladder:

- Phase 33A reports canonical RAG source readiness and keeps retrieval disabled.
- Phase 33B permits only repo-local, read-only keyword retrieval from `knowledge/<source>`.
- Phase 33C wraps retrieval output in a human-review response packet.
- Phase 33D remains plan-only until a separate review approves guarded RAG+LLM private test behavior.

These phases do not call embedding APIs, LLM APIs, Discord sends, external RAG
roots, or external execution.

Phase 33D-safe adds preflight, context safety, prompt envelope, would-send
preview, and replay/audit reports for a future guarded RAG+LLM private test
reply. It does not implement the live reply path. A separate manual approval is
required before any live RAG+LLM private test implementation.

Phase 33D live readiness review adds go/no-go reporting, manual enable
checklists, and rollback planning. The review result is `go=false` by design;
it only marks the repo ready for a separate manual implementation request.

Phase 33D-1 adds guarded runtime code and the
`--run-discord-private-test-rag-llm-reply` option. The runtime option is not
part of normal local testing and requires separate manual approval before use.

Phase 33D-2 adds a report-only live preflight closeout. It confirms the default
runtime preflight remains blocked, a mock live-ready fixture can pass the gates,
the runtime option is present, and the report itself executes no runtime,
Discord send, LLM API call, embedding API call, or external action. A single
live private test still requires separate manual approval.

Phase 33D-3 adds the single live private test runbook. It documents the
before-run checks, env gates, manual-only live command, expected logs, abort
conditions, rollback commands, and Phase 33D-4 replay/audit closeout handoff.
The runbook itself executes no live runtime.

Phase 33D-3A adds an explicit two-part single live approval env gate. The
runtime start remains blocked unless
`HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED=true` and
`HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE` exactly matches the documented
approval phrase. Reports log only booleans, not the phrase value.

Phase 33D-3B wires the RAG+LLM private-test runtime start adapter. Tests still
use mock adapters or token-missing checks only; the actual live command remains
manual user-run PowerShell only.

Phase 33D-4 closes out the successful single live private test from a sanitized
fixture. It verifies one private-test-channel event, one retrieval path, one
LLM-allowed path, one output-safety-allowed path, one Discord send, and one
self-message skip. It does not start Discord again, send another message, call
OpenRouter again, call embeddings, or execute external actions. The closeout
sets `ready_for_phase34_knowledge_ingestion=true`.

Phase 34A-C adds the local knowledge foundation. It creates canonical
`knowledge/` source folders, a local text-only manifest, ingestion boundary
rules, agent source routing, and citation/evidence packets. `operation` remains
canonical and `operations` remains blocked. Embedding, vector DB/index creation,
external source ingest, LLM calls, Discord sends, and external execution remain
deferred.

Phase 34D integrates the local evidence packet into the RAG response packet. It
adds `evidence_packet` and `citation_summary` fields while keeping full content
out of packets, enforcing relative citations, and keeping `ready_for_llm_prompt`
false. It is ready only for private-test review, not live public/team replies.

Phase 34E-F adds the review-only packet and a local sample dry chain. The sample
chain verifies repo-local `knowledge/operation` files through manifest,
evidence packet, RAG response packet, and review packet outputs. It remains
private-test review only.

Phase 34G-H0 prepares prompt envelope preview and no-API/mock-only LLM dry-call
readiness. It creates a review-only message preview and a mock LLM response
packet, but actual provider calls remain reserved for a later separately
approved phase.

If the registry file is missing, generate it from the repo root:

```powershell
python scripts\load_stoxl_agent_registry.py --out registry\stoxl_agent_registry.example.json
```

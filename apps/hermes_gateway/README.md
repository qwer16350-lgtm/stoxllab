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
```

The `--run-discord-readonly` option is intentionally not part of normal local
test usage. It is reserved for a separately approved private server read-only
connection run, and it still blocks message sending, LLM, RAG, and external
execution.

If the registry file is missing, generate it from the repo root:

```powershell
python scripts\load_stoxl_agent_registry.py --out registry\stoxl_agent_registry.example.json
```

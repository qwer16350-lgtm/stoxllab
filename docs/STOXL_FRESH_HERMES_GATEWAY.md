# STOXL Fresh Hermes Gateway

## Purpose

`apps/hermes_gateway` is a fresh local runtime skeleton for connecting the STOXL Phase 0-12 artifacts into one dry-run pipeline.

This is not a replacement for the NAS/Z-drive Hermes Gateway project. The earlier read-only discovery phases could not reliably access the NAS runtime in the current session, so this skeleton provides a safe local boundary for future integration planning.

## Current Capabilities

- Accept local CLI text input.
- Accept local JSON event files.
- Normalize Discord-shaped events without connecting to Discord.
- Load `registry/stoxl_agent_registry.example.json`.
- Bridge to `scripts/evaluate_stoxl_mock_request.py`.
- Build a dispatch plan.
- Build an in-memory audit payload.
- Run local smoke tests without pytest.

## What It Does Not Do

- It does not connect to Discord.
- It does not call the Discord API.
- It does not require or read a Discord Bot Token.
- It does not read a real `.env` file.
- It does not call OpenAI, OpenRouter, or any LLM provider.
- It does not read or copy external DB/RAG source files.
- It does not ingest or index RAG content.
- It does not post, submit, email, approve contracts, or execute external actions.
- It does not replace production Hermes Gateway code.

## Execution Methods

From `C:\tmp\STOXL_LAB`:

```powershell
python apps\hermes_gateway\main.py
python apps\hermes_gateway\cli.py --text "인스타 업로드 문구 초안 만들어줘" --channel "marin-초안" --author-role "Decision Maker"
python apps\hermes_gateway\cli.py --event apps\hermes_gateway\examples\local_message_event.json --json
python apps\hermes_gateway\tests\test_local_pipeline.py
```

## Local Pipeline

1. `cli.py` receives text or a JSON event.
2. `discord_event_adapter.py` normalizes it into the Phase 12 boundary shape.
3. `registry_loader.py` loads the generated STOXL registry.
4. `evaluator_bridge.py` calls the Phase 10 evaluator.
5. `dispatcher.py` creates a dispatch plan without sending anything.
6. `audit_log.py` creates an in-memory audit payload.

## Safety Rules

The skeleton keeps these rules active:

- `no_external_execution`
- `human_only_execution`
- `no_secret_output`
- `no_rag_source_copy`
- `no_unknown_agent_dispatch`
- `no_junior_direct_approval`
- `no_reze_direct_order`
- `no_discord_api_call`

## Phase 14+ Plan

- Review whether this fresh skeleton should become the integration boundary for the NAS Hermes runtime.
- Decide whether to keep the Phase 10 evaluator as an import or expose it behind a stable internal interface.
- Design a Discord mock test harness before any real gateway work.
- Add a real Discord adapter only after manual approval.
- Keep actual Discord application, token loading, RAG path access, and external execution out of scope until separately approved.

## Values Still Needing User Decision

- Actual production Hermes Gateway path.
- Whether this skeleton should be copied into or imported by the NAS runtime.
- Discord guild/channel/role ID mapping.
- Prompt/config loader strategy for production.
- Audit log destination, if any.
- Real test framework choice.

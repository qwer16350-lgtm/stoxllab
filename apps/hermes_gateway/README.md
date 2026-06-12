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

## Explicit Non-Goals

- No Discord API calls.
- No Discord Gateway connection.
- No bot token loading.
- No `.env` reading.
- No LLM, OpenAI, or OpenRouter calls.
- No external DB/RAG reads or copies.
- No external posting, submission, email, contract, or payment actions.
- No approval-to-external-execution conversion.
- No real Discord approval buttons or messages.

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
python apps\hermes_gateway\tests\test_local_pipeline.py
python apps\hermes_gateway\tests\test_replay_approval.py
python apps\hermes_gateway\tests\test_persistent_audit_export.py
python apps\hermes_gateway\tests\test_review_packet.py
```

If the registry file is missing, generate it from the repo root:

```powershell
python scripts\load_stoxl_agent_registry.py --out registry\stoxl_agent_registry.example.json
```

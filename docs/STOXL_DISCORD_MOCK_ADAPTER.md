# STOXL Discord Mock Adapter

## Purpose

`scripts/evaluate_discord_mock_event.py` evaluates Discord-shaped mock message events without connecting to Discord. It normalizes mock events and passes them into the Phase 10 mock evaluator so routing, approval gates, permissions, handoffs, RAG access, and status guardrails can be reviewed locally.

## Relationship To Phase 10 Mock Evaluator

The adapter reuses the Phase 10 evaluator logic from `scripts/evaluate_stoxl_mock_request.py`. The Discord mock adapter adds:

- channel check
- author role check
- mention check
- Discord-event-to-request normalization
- dispatch plan generation

It does not generate real agent replies.

## Difference From Real Discord API

This adapter reads local JSON only. It does not receive real messages, send messages, create channels, edit roles, use a gateway, or call Discord APIs.

## How To Run

Single text/channel event:

```powershell
python scripts\evaluate_discord_mock_event.py --text "인스타 업로드 문구 초안 만들어줘" --channel "marin-초안" --author-role "Decision Maker"
```

Event JSON:

```powershell
python scripts\evaluate_discord_mock_event.py --event mock\discord_mock_events.example.json
```

Event JSON with output:

```powershell
python scripts\evaluate_discord_mock_event.py --event mock\discord_mock_events.example.json --out mock\discord_mock_results.example.json
```

Explicit root and JSON:

```powershell
python scripts\evaluate_discord_mock_event.py --root C:\tmp\STOXL_LAB --json --text "이 지원사업 제출해줘" --channel "공모전-지원사업" --author-role "Decision Maker"
```

## Options

- `--root`: explicit repo root. Defaults to auto-detection.
- `--json`: JSON output mode. Output is JSON by default.
- `--text`: mock Discord message text.
- `--channel`: mock channel name.
- `--channel-category`: mock channel category.
- `--author-display-name`: mock author display name.
- `--author-role`: mock author role.
- `--author-is-agent`: treat the author as an agent.
- `--mention`: mentioned agent id. Can be repeated.
- `--event`: event JSON file.
- `--out`: write result JSON to a file.

## What The Adapter Evaluates

Each event result includes:

- `channel_check`: whether the channel exists and category matches.
- `author_check`: role and agent author validation.
- `mention_check`: mentioned agent existence and shortcut guardrails.
- `normalized_request`: evaluator-ready request.
- `evaluator_result`: Phase 10 routing/approval/permission/RAG/status result.
- `dispatch_plan`: planned agent/channel dispatch, without sending anything.
- `blocked`, `block_reasons`, `recommended_next_action`, and `notes`.

## What The Adapter Does Not Do

- Does not receive real Discord messages.
- Does not send Discord messages.
- Does not call the Discord API.
- Does not use a Discord Bot Token.
- Does not connect to Discord Gateway.
- Does not run a real bot.
- Does not call an LLM.
- Does not access RAG source files.
- Does not access external DB files.
- Does not post, submit, email, upload, or confirm contracts.
- Does not modify source config, prompt, registry, or dry-run files.

## Phase 12+ TODO

Before designing a real Discord adapter, decide:

- NEEDS_USER_DECISION: Discord Gateway connection method
- NEEDS_USER_DECISION: message intent settings
- NEEDS_USER_DECISION: channel ID mapping
- NEEDS_USER_DECISION: user ID mapping
- NEEDS_USER_DECISION: approval reaction/button design
- NEEDS_USER_DECISION: audit log strategy
- NEEDS_USER_DECISION: whether real dispatch remains mock-only until manual approval

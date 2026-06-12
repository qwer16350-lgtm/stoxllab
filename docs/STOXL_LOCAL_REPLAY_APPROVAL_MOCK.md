# STOXL Local Replay and Approval Mock

## Purpose

This document describes the Phase 14 local replay and approval interaction mock for the fresh Hermes Gateway skeleton.

The goal is to simulate multiple STOXL Discord-shaped events in order, collect dispatch/block decisions, create approval queue items, apply mock approval decisions, and produce an audit trail without connecting to Discord, LLM providers, or external RAG sources.

## Relationship to Phase 13B

Phase 13B created `apps/hermes_gateway` as a fresh local boundary. Phase 14 adds:

- `replay.py` for ordered local event replay.
- `approval_queue.py` for in-memory approval decisions.
- replay and approval example JSON files.
- a direct-run test file for replay and approval behavior.

This still does not replace or modify any NAS Hermes Gateway runtime.

## What Replay Does

Replay reads `apps/hermes_gateway/examples/replay_events.example.json`, then for each event:

1. Normalizes the event with `discord_event_adapter.py`.
2. Evaluates routing and guardrails with `evaluator_bridge.py`.
3. Builds a dispatch plan with `dispatcher.py`.
4. Creates an in-memory audit payload with `audit_log.py`.
5. Adds an approval queue item when `approval_required=true`.

## What Approval Queue Mock Does

The approval queue mock stores pending approval items in memory only. It supports:

- `pending`
- `approved`
- `rejected`
- `expired`

Only the `Decision Maker` role can approve or reject. Unknown approval ids produce warnings. Already decided items are not processed again.

Approval never turns into external execution:

- `human_only_execution=true`
- `external_execution_allowed=false`

## What Approval Does Not Do

Approval does not send Discord messages. It also does not perform:

- SNS posting
- homepage upload
- grant or competition submission
- email sending
- contract confirmation
- price confirmation
- delivery schedule confirmation
- any external execution

## Usage

From `C:\tmp\STOXL_LAB`:

```powershell
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --approval-actions apps\hermes_gateway\examples\approval_actions.example.json --json
python apps\hermes_gateway\tests\test_replay_approval.py
```

## Result JSON Structure

Replay returns:

```json
{
  "replay_id": "",
  "events_processed": 0,
  "events": [],
  "approval_queue": [],
  "approval_actions": [],
  "audit_trail": [],
  "summary": {
    "blocked_count": 0,
    "dispatch_count": 0,
    "approval_required_count": 0,
    "approved_count": 0,
    "rejected_count": 0,
    "human_only_execution_count": 0,
    "external_execution_count": 0
  },
  "safety_assertions": []
}
```

## Safety Assertions

The replay output includes these checks:

- `external_execution_count_is_zero`
- `approved_items_remain_human_only`
- `approved_items_do_not_allow_external_execution`

All approved items must remain human-only and must keep `external_execution_allowed=false`.

## Phase 15+ Plan

Possible later phases, still requiring separate approval:

- local persistent audit log design
- approval UI mock
- read-only Discord connection investigation
- Discord mock-to-real adapter design
- real Discord apply plan after manual review

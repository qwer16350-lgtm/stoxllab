# STOXL Persistent Audit Log

## Purpose

Phase 15 adds local persistent export for Phase 14 replay and approval mock results. It stores dry-run results as JSON and JSONL so replay runs, approval decisions, and audit events can be reviewed later.

This is still a local dry-run feature. It does not connect to Discord, call an LLM, read external RAG sources, or perform external execution.

## Relationship to Phase 14

Phase 14 introduced ordered local replay and an in-memory approval queue. Phase 15 exports those results to files under a configurable local log root.

Default log root:

```text
logs/hermes_gateway/
```

Default folders:

```text
logs/hermes_gateway/replay_runs/
logs/hermes_gateway/approval_decisions/
logs/hermes_gateway/audit_events/
```

## Stored Log Types

- Replay run summary: `.json`
- Approval decisions: `.jsonl`
- Audit events: `.jsonl`

## What Is Not Stored

The exporter must not store:

- Discord token
- API key
- password
- secret
- external DB/RAG originals
- attachment original contents

Sensitive values are replaced with:

```text
[REDACTED]
```

## Usage

```powershell
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --export-log --dry-run-export --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\replay_events.example.json --approval-actions apps\hermes_gateway\examples\approval_actions.example.json --export-log --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\export_replay_events.example.json --export-log --log-root logs\hermes_gateway --json
```

## CLI Options

- `--export-log`: export replay results to local log files.
- `--log-root`: choose the log root. Relative paths resolve from the repo root.
- `--dry-run-export`: build the export plan without creating files.

Existing local options remain available:

- `--text`
- `--event`
- `--replay`
- `--approval-actions`
- `--json`

## Result Structure

Export summary:

```json
{
  "exported": true,
  "log_root": "",
  "replay_run_path": "",
  "approval_decisions_path": "",
  "audit_events_path": "",
  "records": {
    "approval_decisions": 0,
    "audit_events": 0
  },
  "redaction_applied": true,
  "external_execution_count": 0,
  "human_only_execution_preserved": true
}
```

## Safety Assertions

Export is refused when `external_execution_count` is not `0`.

Approved approval items must keep:

```text
human_only_execution=true
external_execution_allowed=false
```

## Git Note

The `.gitignore` file should exclude actual local log outputs before real repeated use. At the time of this phase, `.gitignore` was not modified because only the Phase 15 files were allowed to change.

## Phase 16+ Plan

Possible future phases, still requiring separate approval:

- approval UI mock
- persistent audit viewer
- read-only Discord connection investigation
- audit review workflow

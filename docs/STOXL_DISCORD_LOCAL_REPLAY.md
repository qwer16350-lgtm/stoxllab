# STOXL Discord Local Replay

## Purpose

Phase 19 extends the Phase 18 Discord adapter stub into a local replay runner for Discord-shaped raw event JSON.

This is still local-only. It does not connect to Discord, call Discord APIs, send messages, load a bot token, call an LLM, or access external RAG originals.

## Relationship To Phase 18

Phase 18 handles one raw event at a time:

- raw Discord-shaped event
- normalized request
- evaluator result
- dispatch plan
- would-send payload

Phase 19 runs that same flow over a list of raw events and adds replay-level state:

- approval queue
- approval action replay
- audit trail
- summary
- optional review packet
- optional dry-run export plan

## Input JSON

Example input:

```text
apps/hermes_gateway/examples/discord_raw_event_replay.example.json
```

The input may be a JSON array or an object with an `events` array. Each event is a local JSON object shaped like a Discord message event:

- `event_type`
- `event_id`
- `guild_id`
- `channel_id`
- `channel_name`
- `category_name`
- `author`
- `content`
- `mentions`
- `attachments`
- `timestamp`
- optional expectation metadata such as `expected_blocked`

Discord IDs remain TODO placeholders. Attachment originals are not stored in the replay output.

## Replay Result JSON

Example result:

```text
apps/hermes_gateway/examples/discord_raw_event_replay_results.example.json
```

The replay result includes:

- `replay_type`
- `version`
- `replay_id`
- `created_at`
- `source_event_file`
- `events_processed`
- `events`
- `approval_queue`
- `approval_actions`
- `would_send_payloads`
- `audit_trail`
- `review_packet`
- `summary`
- `safety_assertions`

Each event result includes:

- safe raw event summary
- normalized request
- evaluator result
- dispatch plan
- would-send payload
- approval queue item when applicable
- audit payload
- blocked state and block reasons

## Would-Send Payload

The runner renders local would-send payloads only. These payloads describe what a future adapter might send, but they do not send anything.

Every payload keeps:

- `safety.discord_api_called=false`
- `safety.message_sent=false`
- `safety.external_execution=false`
- `safety.human_only_execution=true`

## Approval Queue

Approval-required events are added to an in-memory approval queue. Approval actions may mark an item as approved or rejected, but approval never becomes external execution.

Approved items still keep:

- `human_only_execution=true`
- `external_execution_allowed=false`

## Audit Trail

The audit trail records normalized request, classification, dispatch, approval, and safety information. Attachments are represented only as redacted metadata.

Sensitive values are redacted before result output and export.

## Review Packet

With `--review-packet`, the replay result includes a local review packet built from the approval queue and blocked sensitive requests.

With `--export-review-packet --dry-run-export`, the CLI returns an export plan only. It does not write review packet files in dry-run mode.

## Not Done In This Phase

Phase 19 does not:

- connect to Discord Gateway
- call Discord APIs
- use a Discord Bot Token
- send real Discord messages
- add `discord.py` or `discord.js`
- call LLM providers
- access external RAG originals
- create RAG ingest or indexes
- perform external posting, submission, email, contract, payment, or other execution
- turn approval into external execution

## Required Safety Counts

The replay summary must keep:

- `message_sent_count=0`
- `external_execution_count=0`

Safety assertions also confirm that would-send payloads do not call Discord, do not send messages, and do not execute external actions.

## Usage

```powershell
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --export-log --dry-run-export --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --review-packet --json
python apps\hermes_gateway\cli.py --discord-replay apps\hermes_gateway\examples\discord_raw_event_replay.example.json --review-packet --export-review-packet --dry-run-export --json
python apps\hermes_gateway\tests\test_discord_replay.py
```

## Phase 20 Candidates

Phase 20 can strengthen the local boundary before any real Discord connection:

- local channel ID mapping validation
- stricter role/channel permission checks against runtime mapping
- read-only private server connection planning
- final dry-run before any real Discord apply
- real Discord connection only after explicit approval, starting in read-only mode

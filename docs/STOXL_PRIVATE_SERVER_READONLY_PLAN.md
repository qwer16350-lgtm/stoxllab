# STOXL Private Server Read-Only Plan

## Purpose

Phase 21 is not an actual Discord connection phase. It is an operating plan for a later private Discord server read-only connection.

This phase does not call Discord APIs, connect to Discord Gateway, run a bot, request a Bot Token, or send Discord messages. It organizes the conditions that must be satisfied before a later read-only connection is considered.

The plan builds on Phase 17 through Phase 20:

- Phase 17 Discord readiness checks
- Phase 18 Discord raw event adapter stub
- Phase 19 local Discord raw event replay
- Phase 20 runtime mapping validator

## Currently Prepared

The repo currently has local-only preparation artifacts:

- config validation
- registry loader
- evaluator bridge
- Discord adapter stub
- local Discord raw event replay
- approval queue mock
- audit export
- review packet export
- Discord readiness checker
- mapping validator

These tools are local dry-run tools. They do not connect to Discord.

## Required Values Before Real Read-Only Connection

The following values must be available in a private runtime mapping or later approved runtime setup:

- `DISCORD_GUILD_ID`
- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`
- actual channel IDs
- actual role IDs
- audit log channel ID
- read-only bot role ID
- private test server confirmation
- bot invite permission scope

Bot Token is not part of the mapping file and is not required in this phase.

## Read-Only Bot Principle

The first real Discord connection must be read-only.

Allowed in the later read-only phase:

- read server metadata needed for mapping confirmation
- read message events only if explicitly approved
- normalize events locally
- build local dispatch plans
- build audit records
- produce local would-send payloads without sending them

Not allowed:

- send Discord messages
- approve actions
- post SNS content
- update a homepage
- submit grants or applications
- send external email
- confirm contracts, prices, or delivery dates
- copy external DB/RAG originals

Approvals remain human-only. Approval must never trigger automatic external execution.

## Discord Intent Review

### `guilds`

Needed to identify the target server and read basic guild metadata.

Current need: likely required for any future read-only connection.

Risk: low, but must be scoped to the private test server only.

### `guild_messages`

Needed only if live message events are captured in a later phase.

Current need: not needed in Phase 21.

Risk: can read message event metadata, so it should wait until a reviewed read-only phase.

### `message_content`

Needed only if the bot must inspect message content.

Current need: not needed in Phase 21.

Risk: high compared to metadata-only access. Enable only after mapping validation, private server confirmation, and explicit approval.

### `reactions`

Later only. Could support manual approval signals in a controlled channel.

Current need: not needed.

Risk: can blur the boundary between review and action if not designed carefully.

### `members`

Later only. Could support role/user validation.

Current need: not needed.

Risk: broader identity visibility. Prefer static mapping first.

### Slash Commands

Later only.

Current need: not needed.

Risk: command interactions can feel executable. Keep disabled until a dedicated command policy exists.

### Approval Buttons

Later only.

Current need: not needed.

Risk: buttons must never trigger external execution. They can only create review records unless a later phase explicitly changes policy.

## Private Server Test Sequence

1. Prepare a private Discord test server.
2. Confirm category, channel, and role structure.
3. Copy the mapping template to a private local mapping file.
4. Fill TODO placeholders with actual Discord IDs.
5. Run mapping validator in non-strict mode.
6. Run mapping validator in strict mode.
7. Run local raw event replay.
8. Build a review packet.
9. Review rollback and safety plan.
10. Confirm final read-only checklist.
11. Move to the next phase only after explicit approval.

## Forbidden During Read-Only Connection

- Discord message sending
- SNS posting
- homepage upload
- grant or application submission
- external email sending
- contract, price, or delivery confirmation
- external DB/RAG original copy
- secret output
- approval-to-external-execution conversion

## Phase 22 And Later Candidates

- Phase 22: actual mapping fill support and validation only
- Phase 23: read-only Discord connection stub with dependency plan
- Phase 24: private server read-only connection
- Phase 25: audit-only live event capture
- Phase 26: controlled bot reply mock in a private channel

No later phase should enable external execution automatically.

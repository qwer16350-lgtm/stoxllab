# STOXL Live Event Pipeline

Phase 29 introduces an audit-only live event pipeline for Discord message events.

## Purpose

The pipeline normalizes a Discord-shaped message, runs the existing local evaluator and dispatch planner, creates an audit payload, builds a would-send payload, and then blocks all outbound action.

## Pipeline Steps

1. Normalize the live message into a local raw event shape.
2. Ignore self or bot-authored messages.
3. Evaluate the request with the local STOXL evaluator.
4. Build a dispatch plan.
5. Build a would-send payload for review only.
6. Build a disabled reply plan.
7. Build an audit payload.
8. Block outbound action through the send blocking guard.

## Visibility Decisions

Every live `on_message` event should produce an audit-only visibility event:

- `ignored_self_message`: the author is the bot or a bot account.
- `ignored_guild_not_allowed`: a target guild is configured and the event is from another guild.
- `ignored_unmapped_channel`: the channel is not in the runtime mapping or known STOXL channel list.
- `content_unavailable_or_empty`: the message content is unavailable or empty.
- `accepted_mapped_channel`: the event is from a mapped channel and can continue through audit-only evaluation.

These decisions are for observation only. They do not authorize any Discord reply or external action.

## Guild And Channel Consistency

`guild_configured` means the event is inside an allowed guild context for read-only processing.

- It is `true` when the target guild ID is configured and the event guild matches it.
- It is also `true` when the event is a guild message and the channel is mapped by the local runtime mapping or known STOXL channel list.
- It is `false` when the target guild is configured but the event guild does not match, or when the event has no guild context.

Decision-specific consistency:

- `accepted_mapped_channel`: `guild_configured=true`, `channel_mapped=true`, `workflow_role` is present.
- `ignored_guild_not_allowed`: `guild_configured=false`, `channel_mapped=false`.
- `ignored_unmapped_channel`: `guild_configured=true`, `channel_mapped=false`.
- `content_unavailable_or_empty`: for a valid guild and mapped channel, `guild_configured=true`, `channel_mapped=true`.

All cases keep `message_sent=false`, `external_execution=false`, `llm_called=false`, and `rag_called=false`.

## Console Output

The runtime prints one redaction-safe line per observed message:

```text
[READONLY_EVENT] accepted_mapped_channel channel=marketing-brief author=discord_id_redacted:1234 content_present=true content_length=24
```

Message content, raw token values, full user IDs, and full channel IDs are not printed.

## JSONL Visibility Log

Observed events are appended to:

```text
logs/hermes_gateway/live_events/readonly_events_YYYYMMDD.jsonl
```

The `logs/hermes_gateway/` folder is ignored by git. Each JSONL line records the decision, reason, channel name, workflow role, content presence/length, and safety assertions.

## Phase 30 Audit Operations

After visibility classification, Phase 30 can create local-only audit artifacts:

```text
visibility event
-> audit record
-> routing report
-> would-send preview
-> review packet
-> daily manifest
```

This flow is still read-only. It does not send a Discord message, call LLM/RAG, or perform external execution.

## Safety Rules

- No Discord write API call.
- No message send.
- No external execution.
- No LLM call.
- No RAG read.
- Long Discord-like IDs are redacted in reports.
- Attachment originals are not stored in audit payloads.

## Report Command

```powershell
python apps\hermes_gateway\cli.py --live-event-pipeline-report --json
```

The report uses a local sample event and does not connect to Discord.

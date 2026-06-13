# STOXL Operations Packet Viewer

Phase 31A adds a local-only viewer for Phase 30 audit artifacts.

## Purpose

Operators can inspect recent live events, review packets, daily manifests, and route summaries without sending Discord messages or calling LLM/RAG.

## Readable Artifacts

```text
logs/hermes_gateway/live_events/
logs/hermes_gateway/live_events/manifests/
exports/hermes_gateway/live_event_packets/
exports/hermes_gateway/would_send_previews/
exports/hermes_gateway/llm_response_packets/
```

The viewer does not read `.env` or local mapping files.

## CLI Usage

```powershell
python apps\hermes_gateway\cli.py --operations-viewer --json
python apps\hermes_gateway\cli.py --operations-viewer --markdown
python apps\hermes_gateway\cli.py --operations-viewer --limit 10 --json
python apps\hermes_gateway\cli.py --operations-viewer --date 20260612 --json
python apps\hermes_gateway\cli.py --operations-viewer --channel marketing-brief --json
python apps\hermes_gateway\cli.py --operations-viewer --workflow-role marketing_intake --json
python apps\hermes_gateway\cli.py --operations-viewer --agent marin --json
python apps\hermes_gateway\cli.py --operations-viewer --decision accepted_mapped_channel --json
python apps\hermes_gateway\cli.py --operations-packet --event-id EVENT_ID --json
python apps\hermes_gateway\cli.py --operations-packet --event-id EVENT_ID --markdown
```

Markdown is printed to stdout only. It is not posted to Discord.

## Filters

- channel name
- workflow role
- agent route candidate
- decision
- date
- limit

## Placeholder Response Summary

When a review packet contains a Phase 31C deterministic placeholder response, the viewer shows:

- `agent_placeholder_response_available`
- `agent_placeholder_title`
- `agent_placeholder_summary`

Markdown output adds an `Agent Placeholder Response` section. It is local stdout only and is not posted to Discord.

## LLM Response Summary

When Phase 32C LLM response packets exist, the viewer can show:

- `llm_response_available`
- `llm_provider`
- `llm_model`
- `llm_output_safety_allowed`
- `llm_cost`
- `llm_message_sent=false`

Markdown output adds an `LLM Response` section. It is local stdout only and is not posted to Discord.

## Safety Boundaries

The viewer does not:

- send Discord replies
- call Discord write APIs
- modify Discord server, channel, or role settings
- call LLM or OpenAI/OpenRouter
- make new LLM calls while viewing response packets
- read RAG sources
- execute external actions
- read `.env`
- read local mapping files
- print raw token values or raw Discord IDs

## Next Phase Candidates

- Phase 31C: deterministic agent placeholder response
- Phase 31B: private test reply design

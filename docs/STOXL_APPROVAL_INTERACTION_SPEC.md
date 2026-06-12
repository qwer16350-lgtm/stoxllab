# STOXL Approval Interaction Spec

## Purpose

This document describes approval interactions as a future spec only.

No Discord reaction, button, slash command, or real interaction is registered in this phase.

## Current Mode

Current mode:

```text
manual_cli_mock_only
```

Runtime interactions are disabled.

## Future Modes

Possible future modes:

- reaction
- button
- slash command

Each future mode requires explicit approval and a separate safety review.

## Approval After-Effect

Approval must not trigger external execution.

The spec keeps:

- `external_execution_allowed=false`
- `human_only_execution=true`
- `message_send_allowed=false`

## Safety Flags

- `discord_api_called=false`
- `interaction_registered=false`
- `message_sent=false`
- `external_execution=false`

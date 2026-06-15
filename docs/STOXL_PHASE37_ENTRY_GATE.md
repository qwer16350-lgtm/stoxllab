# STOXL Phase 37 Entry Gate

Phase 37 is not started. This gate only classifies possible next steps after
the Phase 36 no-send final lock.

## Allowed Next Candidates

- `private_test_llm_draft_review_packet_no_send`
- `private_test_discord_send_preflight_no_send`

## Hold Candidates

- `actual_private_test_discord_send`
- `multi_turn_private_test_runtime`

## Forbidden Candidates

- `public_team_send`
- `public_team_auto_reply`
- `unattended_auto_reply`
- `external_execution`

## Safety State

- Requires explicit user approval: true
- Ready for Phase 37 live execution: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## CLI

```powershell
python apps\hermes_gateway\cli.py --phase37-entry-gate --json
python apps\hermes_gateway\cli.py --phase37-entry-gate --markdown
```

This gate does not call LLM APIs, start Discord, send messages, create
embeddings, or execute external actions.

## Phase 37A-C

Phase 37A-C may create review/preflight/rehearsal reports only:

- private-test LLM draft review packet, no send
- private-test Discord send preflight preview, no API send
- private-test send approval rehearsal, no approval phrase generation

Actual private-test send remains held for a later explicit approval phase.

## Phase 37D-F

Phase 37D-F may create manual preflight, mock send rehearsal, and no-send lock
reports only. It keeps Phase 38 actual private-test send path not started,
locks actual Discord send count to zero, and requires a separate explicit user
approval before any real private-test send path is considered.

## Phase 38A-E

Phase 38A-E creates the final no-send preparation layer: send contract, payload
freeze, rollback gate, operator checklist, and live send entry gate. It keeps
Phase 39 not started and requires a later explicit approval before any actual
private-test send.

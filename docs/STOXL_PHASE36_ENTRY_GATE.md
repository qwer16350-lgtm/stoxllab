# STOXL Phase 36 Entry Gate

Phase 36 has not started. This document and report only classify possible next
work.

## Allowed Next Candidates

- `private_test_one_shot_llm_draft_preflight_no_send`
- `agent_review_packet_to_llm_draft_preview_no_send`

## Hold

- `private_test_multi_turn_runtime`
- `embedding_vector_db`
- `scheduler`

## Forbidden

- `public_team_auto_reply`
- `unattended_auto_reply`
- `external_execution`

## Safety State

- Requires explicit user approval: true
- Ready for Phase 36 live execution: false
- Ready for LLM call: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## Phase 36A

Phase 36A may add a private-test one-shot LLM draft preflight. That preflight is
still no-call and no-send: it does not start live execution, attempt an LLM API
call, generate an approval phrase, or send a Discord message.

## CLI

```powershell
python apps\hermes_gateway\cli.py --phase36-entry-gate --json
python apps\hermes_gateway\cli.py --phase36-entry-gate --markdown
```

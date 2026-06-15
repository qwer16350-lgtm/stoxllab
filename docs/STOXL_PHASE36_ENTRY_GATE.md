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

## Phase 36B

Phase 36B may add a mock LLM draft packet and output safety rehearsal. It still
does not call OpenRouter/LLM, attempt an API call, generate approval phrases,
or send Discord messages.

## Phase 36C

Phase 36C may check actual one-shot LLM draft call prerequisites. It may report
OpenRouter key presence as a boolean, but it does not print key values, attempt
an API call, activate manual approval, or send Discord messages.

## Phase 36D

Phase 36D may add the manually gated actual one-shot LLM draft call path. The
default report remains blocked. A provider call is possible only with an
explicit allow flag, exact manual approval gate, OpenRouter key presence, the
`kasumi` candidate, and source `operation`. It still never sends Discord
messages, creates embeddings/vector indexes, enables public/team replies, or
allows unattended auto reply.

## Phase 36E

Phase 36E may close out an observed Phase 36D one-shot LLM draft result. It is
report-only and must not make another LLM attempt, start Discord, send a
message, generate approval phrases, create embeddings, or execute external
actions.

## Phase 36F-G

Phase 36F-G may lock the Phase 36 result as one LLM draft call and zero Discord
sends, then update dashboard/sentinel visibility. These reports remain
report-only and must not open live/send execution.

## Phase 37

Phase 37 entry gate may classify next candidates, but Phase 37 is not started.
Live/send execution requires a later explicit approval phase.

## CLI

```powershell
python apps\hermes_gateway\cli.py --phase36-entry-gate --json
python apps\hermes_gateway\cli.py --phase36-entry-gate --markdown
```

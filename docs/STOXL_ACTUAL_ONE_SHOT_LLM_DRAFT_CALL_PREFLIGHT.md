# STOXL Actual One-shot LLM Draft Call Preflight

Phase 36C checks whether the future one-shot LLM draft call could be prepared
for manual approval. It does not call OpenRouter or any LLM provider.

## Safety State

- Discord live runtime executed: false
- Discord message sent: false
- Discord API send called: false
- OpenRouter or LLM API called: false
- LLM API call attempted: false
- LLM API call count: 0
- Approval phrase generated: false
- Approval phrase value logged: false
- Manual approval actualized: false
- Embedding/vector created: false
- External execution: false
- Ready for actual LLM call: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## Candidate

- Candidate agent: `kasumi`
- Allowed source: `operation`
- Evidence citation: `knowledge/operation/stoxl_operation_tone_sample.md`

## OpenRouter Key Check

Only presence is checked. Values are never logged.

- `OPENROUTER_API_KEY`
- `HERMES_OPENROUTER_API_KEY`

If a key is present and all dry prerequisites pass,
`preflight_ready_for_manual_llm_call=true`. Even then,
`ready_for_actual_llm_call=false` in Phase 36C because the actual call requires
a later explicit approval phase.

## Phase 36D Follow-up

Phase 36D uses this preflight as a gate before the manually approved one-shot
LLM draft call path. Passing this preflight alone is not enough to call the
provider; Phase 36D also requires the explicit CLI allow flag and exact manual
approval env gate. Discord send remains disabled after any successful LLM draft.

Phase 36E can then close out an observed Phase 36D draft result without another
LLM call and without any Discord send.

Phase 36F-G locks the no-send state, and Phase 37 entry gate remains blocked
for live/send execution until a separate explicit approval phase.

## CLI

```powershell
python apps\hermes_gateway\cli.py --actual-one-shot-llm-draft-call-preflight --json
python apps\hermes_gateway\cli.py --actual-one-shot-llm-draft-call-preflight --markdown
```

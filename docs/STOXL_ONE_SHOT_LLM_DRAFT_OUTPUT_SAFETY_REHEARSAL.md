# STOXL One-shot LLM Draft Output Safety Rehearsal

Phase 36B rehearses output safety against the mock draft packet. It performs no
LLM call and sends no Discord message.

## Checks

- Review-only language
- Evidence citation presence
- No secret value
- No raw Discord ID
- No approval phrase value
- No public/team send instruction
- No unattended auto reply instruction
- No full content inclusion

## Negative Fixtures

The rehearsal verifies that the following cases block:

- secret-like value present
- approval phrase present
- raw Discord-like ID present
- public/team send instruction present
- unattended auto reply instruction present
- full content included

## Readiness

`ready_for_phase36c_actual_llm_call_preflight=true` means a later preflight can
be designed. It does not mean actual LLM calls or Discord sends are allowed in
Phase 36B.

## Phase 36C Follow-up

Phase 36C checks this rehearsal result before any future actual LLM call phase.
The Phase 36C report still keeps `ready_for_actual_llm_call=false`.

## Phase 36D Follow-up

Phase 36D can run the actual one-shot LLM draft call only after explicit manual
approval and the CLI allow flag. The output safety gate is checked again on the
provider response, and Discord send remains false.

## CLI

```powershell
python apps\hermes_gateway\cli.py --one-shot-llm-draft-output-safety-rehearsal --json
python apps\hermes_gateway\cli.py --one-shot-llm-draft-output-safety-rehearsal --markdown
```

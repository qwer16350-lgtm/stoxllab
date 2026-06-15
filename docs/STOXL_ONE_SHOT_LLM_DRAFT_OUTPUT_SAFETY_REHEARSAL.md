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

## CLI

```powershell
python apps\hermes_gateway\cli.py --one-shot-llm-draft-output-safety-rehearsal --json
python apps\hermes_gateway\cli.py --one-shot-llm-draft-output-safety-rehearsal --markdown
```

# STOXL Post-LLM-call Dashboard Lock

Phase 36G adds a dashboard lock for the post-call state. It summarizes Phase
36D/E/F and keeps the forbidden behavior sentinel active after an actual LLM
draft call has been observed.

## Guardrails

- Total Phase 36 LLM calls must equal `1`
- Total Phase 36 Discord messages must equal `0`
- Output safety must be allowed
- Public/team send and reply stay blocked
- Unattended auto reply stays blocked
- Embedding/vector creation stays blocked
- External execution stays blocked
- Secret/API key/token/raw Discord ID/approval phrase values must not be logged
- Full content must not be included

## CLI

```powershell
python apps\hermes_gateway\cli.py --post-llm-call-dashboard-lock --json
python apps\hermes_gateway\cli.py --post-llm-call-dashboard-lock --markdown
```

The report is read-only and performs no new LLM call or Discord action.

## Phase 37A-C Follow-up

Phase 37A-C can use this locked state to create private-test review and
preflight previews. These previews do not open Discord send or perform another
LLM call.

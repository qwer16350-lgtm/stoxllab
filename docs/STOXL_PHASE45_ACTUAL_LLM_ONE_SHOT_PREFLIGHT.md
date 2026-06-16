# STOXL Phase 45A Actual LLM One-shot Preflight

Phase 45A prepares the future actual LLM one-shot call gate. This bundle does not attempt the call.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase45-actual-llm-one-shot-preflight --json
```

The preflight is blocked by default and requires a later manual approval gate, exact approval phrase match, cost guard, call-count guard, provider key presence, and Discord send remaining false. API key and approval phrase values are never logged.

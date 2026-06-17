# STOXL Phase46 LLM Retry Policy

Phase46 forbids automatic retry after the Phase45 output safety block.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase46-llm-retry-policy --json
```

Policy state:

- `automatic_retry_allowed=false`
- `repeat_phase45_call_allowed=false`
- `retry_requires_new_manual_gate=true`
- `retry_requires_new_approval_phrase=true`
- `retry_requires_new_approval_policy=true`
- `retry_requires_cost_guard=true`
- `retry_requires_call_count_guard=true`
- `discord_send_remains_disabled=true`

Phase45 actual LLM/OpenRouter call already succeeded exactly once. Any future
retry must be designed as a separate explicit manual gate, not as a replay of
the consumed Phase45 gate.

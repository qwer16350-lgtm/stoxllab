# STOXL Phase46 Blocked LLM Output Review

Phase46 reviews the Phase45 blocked LLM output as metadata and policy only.
It does not dump the full raw LLM output and does not make another
LLM/OpenRouter call.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase46-blocked-llm-output-review --json
```

Expected state:

- `phase45_actual_llm_call_completed=true`
- `phase45_llm_call_count=1`
- `phase45_repeat_llm_call_allowed=false`
- `output_safety_checked=true`
- `output_safety_blocked=true`
- `blocked_reasons=["external_action_claim"]`
- `safe_disclaimer_detected=true`
- `raw_output_included=false`
- `full_content_included=false`
- `discord_message_sent=false`
- `ready_for_retry=false`
- `retry_requires_new_manual_gate=true`

Classifier calibration is fixture-based only. Negated external-action language
such as "No external action has been taken", "review-only draft", "not sent",
"not published", and "not approved" must not be treated as a positive external
action claim. Positive external-action claims still block.

This review is human-review-only. It does not automatically unblock the Phase45
output, create a response packet, send Discord messages, or retry the LLM call.

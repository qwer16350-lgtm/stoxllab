# STOXL Phase50 Release Blocker Matrix

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase50-release-blocker-matrix --json
```

Release blocker state:

```json
{
  "unattended_auto_reply_blocked": true,
  "automatic_retry_blocked": true,
  "automatic_discord_send_blocked": true,
  "llm_repeat_call_blocked": true,
  "raw_output_dump_blocked": true,
  "production_unattended_ready": false
}
```

Missing before production:

- continuous_readonly_runtime
- review_packet_automation
- agent_router
- rag_evidence_layer
- team_channel_low_risk_policy
- scheduler_safety
- global_kill_switch
- budget_guard
- incident_closeout

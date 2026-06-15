# STOXL Agent Routing Dry Preview

Phase 35B adds rule-only agent routing preview.

Routes:

- `marin`: `marketing`, `brand`
- `lucy`: `marketing`, `brand`, `archive`
- `kasumi`: `operation`
- `meiko`: `operation`, `archive`
- `reze`: `strategy`, `brand`, `archive`
- `decision_maker_review`: `marketing`, `operation`, `strategy`, `brand`, `archive`
- `unrouted`: none

Blocked examples:

- `kasumi -> operations`: forbidden source
- `marin -> operation`: source not allowed for agent

CLI:

```powershell
python apps\hermes_gateway\cli.py --agent-routing-dry-preview --json
python apps\hermes_gateway\cli.py --agent-routing-dry-preview --markdown
```

This preview is rule-only and never calls LLMs or sends Discord messages.

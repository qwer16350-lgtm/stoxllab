# STOXL Evidence Quality Preview

Phase 35B adds a dry evidence quality preview.

It checks:

- Citation sufficiency
- Duplicate evidence suspicion
- Stale document suspicion
- Relative paths only
- No full content inclusion

CLI:

```powershell
python apps\hermes_gateway\cli.py --evidence-quality-preview --json
python apps\hermes_gateway\cli.py --evidence-quality-preview --markdown
```

The preview keeps `ready_for_llm_prompt=false`, `ready_for_embedding=false`, `ready_for_external_sources=false`, and `ready_for_discord_send=false`.

# STOXL Phase50 Manual Gate Matrix

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase50-manual-gate-matrix --json
```

Manual gate types:

- Read-only live runtime gate
- RAG/LLM no-send one-shot gate
- Private-test supervised auto reply gate
- Team-channel low-risk canary gate
- Production unattended limited launch gate
- Emergency kill-switch verification gate

Every gate requires:

- approval phrase required
- cost/count guard required when LLM involved
- channel allowlist required when Discord send involved
- rate limit required
- cooldown required
- no-repeat or bounded-repeat lock required
- secret/raw log forbidden

No manual gate execution is available in Phase50.

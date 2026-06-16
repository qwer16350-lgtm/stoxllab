# STOXL Phase 44 Fake LLM Adapter

Phase 44 includes a deterministic fake LLM adapter for dry-run validation.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase44-llm-fake-reply-dry-run --json
```

The adapter returns the same schema-valid fake reply every run. It does not call OpenRouter or any LLM API, does not send Discord messages, and does not perform RAG, embedding, vector, or external execution.

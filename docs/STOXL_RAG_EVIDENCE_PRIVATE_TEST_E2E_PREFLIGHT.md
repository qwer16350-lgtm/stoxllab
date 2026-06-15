# STOXL RAG Evidence Private-test E2E Preflight

Phase 34K prepares an end-to-end private-test readiness report without running a live Discord runtime.

It links the local knowledge dry chain, prompt envelope, LLM dry-call closeout, would-send preview, and private-test send gate into one preflight report.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-preflight --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-e2e-preflight --markdown
```

## Safety Boundary

- `discord_live_runtime_executed=false`
- `discord_api_send_called=false`
- `discord_message_sent=false`
- `llm_api_called=false`
- `embedding_api_called=false`
- `external_execution=false`
- `ready_for_unattended_auto_reply=false`

Passing this phase only means a later Phase 34L-1 manual E2E live reply can be reviewed separately.

Phase 34L-1 remains manually gated. Its default report is blocked and performs
no live runtime, no LLM API call, and no Discord send.

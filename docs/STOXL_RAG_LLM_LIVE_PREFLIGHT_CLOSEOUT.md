# STOXL RAG+LLM Live Preflight Closeout

Phase 33D-2 is a no-live-execution closeout for the guarded RAG+LLM private test runtime boundary.

It confirms that the default runtime preflight remains blocked, a mock live-ready fixture can satisfy the required gates, and the live runtime option exists for a separately approved single private test. This phase does not start Discord, send Discord messages, call OpenRouter or any LLM provider, call embedding APIs, read external RAG roots, or perform external execution.

## Result

- Default preflight blocked: true
- Mock live-ready fixture passed: true
- Runtime option present: true
- Runtime executed: false
- Ready for single live private test: true
- Actual Discord send: false
- Actual LLM API call: false
- Embedding API called: false
- External execution: false

`ready_for_single_live_private_test=true` means the local safeguards and mock fixture are ready for a separately approved, single private test. It does not authorize running the live runtime.

## CLI

Report only:

```powershell
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --markdown
```

Do not run the live runtime option in this phase:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-rag-llm-reply --json
```

The live runtime option remains reserved for a later, separately approved single private test.

## Required Live Gates

- private test only
- private test channel ID required
- channel ID match required
- canonical `source=operation` required
- `source=operations` forbidden
- local read-only RAG required
- RAG response packet required
- RAG context safety required
- LLM output safety required
- cooldown required
- reply budget required
- duplicate guard required
- self/bot guard required
- public/team channel block required
- separate manual approval required

## Blocked Before Retrieval

The following cases must stop before retrieval, LLM call, or Discord send:

- public channel
- team mapped channel
- self message
- bot message
- duplicate message
- cooldown
- budget exhausted
- invalid source
- `operations` source

## Operations Viewer

The operations viewer exposes a summary section:

```json
{
  "rag_llm_live_preflight_closeout": {
    "available": true,
    "runtime_executed": false,
    "ready_for_single_live_private_test": true,
    "actual_discord_send": false,
    "actual_llm_api_call": false,
    "embedding_api_called": false,
    "external_execution": false
  }
}
```

## Safety Assertions

- Discord live runtime executed: false
- Discord message sent: false
- OpenRouter/LLM actual API call: false
- embedding API call: false
- external execution: false
- token/API key value logged: false
- raw Discord ID logged: false

## Next Step

The next step should be a separately approved single live private test only. That approval must explicitly allow running `--run-discord-private-test-rag-llm-reply`, and it should keep public/team channels, self/bot messages, `source=operations`, external execution, and unbounded retrieval blocked.

## Phase 33D-3 Runbook

The manual runbook is:

```text
docs/STOXL_RAG_LLM_SINGLE_LIVE_TEST_RUNBOOK.md
```

It defines before-run checks, required env gates, expected logs, immediate
shutdown, abort conditions, and the Phase 33D-4 replay/audit closeout handoff.
Codex/agent must not run the live runtime automatically.

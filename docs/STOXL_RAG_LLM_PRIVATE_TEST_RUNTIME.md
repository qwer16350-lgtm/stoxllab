# STOXL RAG+LLM Private Test Runtime

Phase 33D-1 implements guarded runtime code for a future private-test-only
RAG+LLM reply. This phase does not run the live Discord runtime and does not
perform a real OpenRouter/LLM API call in tests.

## Runtime Boundary

- private test channel only
- channel ID match required
- `source=operation` is canonical
- `source=operations` is invalid
- local read-only retrieval only
- context safety required
- RAG response packet required
- LLM output safety required
- cooldown, budget, duplicate guard, and circuit breaker required
- public/team channel blocked before retrieval
- self/bot messages blocked before retrieval

## CLI

Report only:

```powershell
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --json
python apps\hermes_gateway\cli.py --rag-llm-private-test-runtime-report --markdown
```

Phase 33D-2 closeout report only:

```powershell
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-preflight-closeout --markdown
```

Runtime option added for a separately approved future run:

```powershell
python apps\hermes_gateway\cli.py --run-discord-private-test-rag-llm-reply --json
```

Do not run the runtime option without separate manual approval.

The Phase 33D-2 closeout confirms that this runtime option is present but not
executed by the report. It also confirms that the default preflight remains
blocked and that only a mock live-ready fixture passes the gate checks.

## Rollback

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_REPLY_ENABLED="false"
```

## Safety

- Discord live runtime executed in this phase: false
- Discord message sent in tests: false except mock send adapter assertions
- OpenRouter/LLM actual API call in tests: false
- embedding API call: false
- external execution: false
- Phase 33D-2 closeout runtime executed: false
- Phase 33D-2 closeout ready for separately approved single live private test: true

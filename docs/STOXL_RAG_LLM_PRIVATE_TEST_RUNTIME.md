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

Phase 33D-3 documents the single live private test procedure in:

```text
docs/STOXL_RAG_LLM_SINGLE_LIVE_TEST_RUNBOOK.md
```

That runbook is for user-run PowerShell execution only. Codex/agent must not
start the live runtime automatically.

Phase 33D-3A adds an explicit two-part approval env gate. The runtime remains
blocked unless both values are set in the user's PowerShell session:

```powershell
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="true"
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_LLM_REPLY"
```

If either value is missing or wrong, the runtime returns:

```json
{
  "started": false,
  "blocked": true,
  "reason": "live_execution_requires_separate_manual_approval",
  "message_sent": false
}
```

Reports expose only approval booleans. The approval phrase value is not logged.

Phase 33D-3B wires the RAG+LLM private test start adapter. After approval and
preflight pass, the live command resolves the Discord private-test RAG+LLM
adapter instead of returning `rag_llm_private_test_runtime_start_adapter_missing`.
The adapter still blocks before live start if token/private channel prerequisites
are missing.

Phase 33D-4 closes out the observed single live private test success through a
sanitized fixture and local parser:

```powershell
python apps\hermes_gateway\cli.py --rag-llm-live-success-closeout --json
python apps\hermes_gateway\cli.py --rag-llm-live-success-closeout --markdown
```

The closeout verifies exactly one accepted private test event, one retrieval
allowance, one context-safety allowance, one RAG packet, one LLM call allowance,
one output-safety allowance, one Discord send, and one self-message skip. It
does not run Discord again, call OpenRouter again, call embeddings, or execute
external actions.

## Rollback

```powershell
$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_LLM_DISCORD_SEND_ENABLED="false"
$env:HERMES_LLM_PRIVATE_TEST_REPLY_ENABLED="false"
$env:HERMES_DISCORD_RAG_ENABLED="false"
$env:HERMES_LLM_RAG_ENABLED="false"
$env:HERMES_RAG_LLM_REPLY_ENABLED="false"
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVED="false"
$env:HERMES_RAG_LLM_SINGLE_LIVE_TEST_APPROVAL_PHRASE=""
```

## Safety

- Discord live runtime executed in this phase: false
- Discord message sent in tests: false except mock send adapter assertions
- OpenRouter/LLM actual API call in tests: false
- embedding API call: false
- external execution: false
- Phase 33D-2 closeout runtime executed: false
- Phase 33D-2 closeout ready for separately approved single live private test: true
- Phase 33D-3 runbook live runtime executed by Codex/agent: false
- Phase 33D-3A approval phrase value logged: false
- Phase 33D-3B default start adapter wired: true
- Phase 33D-4 closeout sends additional Discord messages: false
- Phase 33D-4 closeout calls OpenRouter/LLM again: false
- Phase 33D-4 closeout calls embeddings: false
- Phase 33D-4 closeout external execution: false
- Phase 33D-4 ready for Phase 34 knowledge ingestion: true

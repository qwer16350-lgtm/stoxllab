# STOXL Private-test One-shot LLM Draft Mock Packet

Phase 36B creates a mock one-shot LLM draft packet for the Phase 36A candidate.
It does not call OpenRouter or any LLM provider.

## Safety State

- Discord live runtime executed: false
- Discord message sent: false
- Discord API send called: false
- OpenRouter or LLM API called: false
- LLM API call attempted: false
- LLM API call count: 0
- Approval phrase generated: false
- Manual approval actualized: false
- Embedding/vector created: false
- External execution: false
- Ready for actual LLM call: false
- Ready for Discord send: false
- Ready for unattended auto reply: false

## Mock Candidate

Only `kasumi` receives a mock response because Phase 36A selected her from the
`operation` evidence citation:

- `knowledge/operation/stoxl_operation_tone_sample.md`

The mock response is review-only and contains citations, not full source
content.

## CLI

```powershell
python apps\hermes_gateway\cli.py --private-test-one-shot-llm-draft-mock-packet --json
python apps\hermes_gateway\cli.py --private-test-one-shot-llm-draft-mock-packet --markdown
```

## Phase 36C Follow-up

The actual LLM draft call preflight consumes this mock packet as a dry
prerequisite. It still does not call an LLM provider or send Discord messages.

## Phase 36D Follow-up

The manually gated one-shot draft call path may use the same `kasumi` and
`operation` scope after explicit approval. Passing output still does not allow
Discord send.

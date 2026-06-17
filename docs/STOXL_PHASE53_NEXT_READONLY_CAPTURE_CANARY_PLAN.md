# STOXL Phase53 Next Read-Only Capture Canary Plan

The next actual operation is a separate Manual Gate for one read-only private
test human message capture.

Canary goal:

- `capture_one_private_test_human_message_readonly`

Recommended guardrails:

- Timeout: `120` seconds.
- Max events: `5`.
- Discord send disabled.
- Reply disabled.
- LLM/OpenRouter disabled.
- RAG disabled.
- Embedding/vector disabled.
- External execution disabled.
- Scheduler live execution disabled.
- Raw content dumps forbidden.
- Raw Discord ID dumps forbidden.
- Secret and approval phrase values forbidden.

Success criteria:

- Gateway connection verified.
- One private-test human message captured as redacted metadata.
- Review packet pipeline consumes the capture metadata.
- Discord send remains false and `message_sent_count=0`.

# STOXL Mock Private-test Send Rehearsal

Phase 37E creates a mock would-send rehearsal for the private-test scope only.

The rehearsal count is locked to one mock rehearsal, while actual Discord send count stays zero. The preview is review-only and does not include full content.

Safety state:

- Mock send rehearsal count: 1
- Actual Discord API send called: false
- Actual Discord message sent: false
- Actual message sent count: 0
- OpenRouter/LLM API call attempted: false
- Discord live runtime executed: false
- Public/team channel send or reply: false
- Embedding/vector created: false
- External execution: false

Any non-private-test scope, actual send flag, full content inclusion, or sensitive value exposure must fail the rehearsal.

Phase 38B may freeze a review-only would-send preview from this chain, but the
payload remains no-send and does not include full content.

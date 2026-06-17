# STOXL Phase 42 Supervised Private-test Session

Phase 42 adds a deterministic supervised private-test session preflight. It is report-only and blocked by default.

The scaffold requires manual approval, exact approval phrase, max session messages, max reply/send counts, timeout, cooldown, private-test-only mode, deterministic/frozen reply mode, session lock, duplicate/self/bot guards, and disabled LLM/RAG/embedding/external execution before a later manual phase can consider a supervised session.

This safe bundle does not open the Phase 42 manual gate, does not run a live runtime, does not call Discord API send, and sends no Discord messages. Phase 41B repeat send remains locked. The next actual operation must be a separate Manual Gate 2 request for the Phase 42 supervised deterministic private-test session.

# STOXL Hermes Production Roadmap

Safe-prep sequence:

1. Phase 41B actual private-test reply one-shot completed exactly once.
2. Phase 41C actual reply closeout and no-repeat lock.
3. Phase 42 supervised deterministic private-test session completed exactly once.
4. Phase 42 actual session closeout and repeat supervised-session lock.
5. Phase 43 routing, rate-limit, cooldown, session lock, and operations stability scaffold.
6. Phase 44 LLM provider preflight, prompt contract, and fake adapter.
7. Phase 45A actual LLM one-shot call preflight gate.
8. Phase 45 actual LLM one-shot call closeout and no-repeat lock.
9. Phase 46 blocked LLM output review policy and no-automatic-retry policy.

Manual Gate 3 is complete: the actual LLM/OpenRouter call succeeded exactly
once, output safety blocked the generated draft, and Discord send stayed
disabled. Phase 41B repeat send, Phase 42 repeat supervised session, and
Phase45 repeat LLM call remain locked. Next sensitive work is Phase46 safe
review of blocked LLM output and retry policy, with no automatic re-call.

Phase46 is now a policy/review stage only. Next possible work is Phase47:
either human-review-only closeout or a new retry Manual Gate design.

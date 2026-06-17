# STOXL Hermes Production Roadmap

Safe-prep sequence:

1. Phase 41B actual private-test reply one-shot completed exactly once.
2. Phase 41C actual reply closeout and no-repeat lock.
3. Phase 42 supervised deterministic private-test session scaffold.
4. Phase 43 routing, rate-limit, cooldown, session lock, and operations stability scaffold.
5. Phase 44 LLM provider preflight, prompt contract, and fake adapter.
6. Phase 45A actual LLM one-shot call preflight gate.

Next sensitive manual step is Manual Gate 2: Phase 42 supervised deterministic private-test session. It must be handled as a separate manual approval phase, outside this safe-prep bundle. Phase 41B repeat send remains locked.

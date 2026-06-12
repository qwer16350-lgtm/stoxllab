# STOXL Agent Placeholder Response

Phase 31C adds deterministic agent placeholder responses.

## Purpose

The placeholder response gives operators a local preview of the agent role and likely next review step without calling an LLM, reading RAG, or sending Discord messages.

## Why Deterministic First

Before private test replies or LLM generation, the system needs a stable response shape that can be audited. Phase 31C verifies that shape with fixed templates only.

## Agent Templates

- Marin: marketing draft intake
- Lucy: marketing senior review
- Kasumi: operations research intake
- Meiko: operations senior review
- Reze: strategy note
- Decision Maker Review: approval or executive review
- Unrouted: route cannot be determined

## Integrations

- Would-send preview can include a placeholder title and summary.
- Review packet can include the same placeholder summary.
- Operations viewer can display placeholder availability, title, and summary.

## Still Disabled

- Discord reply
- Discord write API
- LLM generation
- RAG access
- external execution

## Next Phase Candidates

- Phase 31B: private test channel only reply
- Phase 32: LLM response generation

# STOXL Agent Review Packet

Phase 35D adds a report-only agent review packet layer on top of the Phase 35C agent evidence pack composer and agent prompt preview.

## Purpose

The review packet gives a human reviewer one place to inspect:

- agent name
- allowed sources
- blocked sources
- evidence citation summary
- prompt preview summary
- risk flags
- human review requirement

## Safety State

- Discord live runtime executed: false
- Discord message sent: false
- OpenRouter or LLM API called: false
- Embedding or vector index created: false
- External execution: false
- Public or team channel reply allowed: false
- Unattended auto reply allowed: false
- Full content included: false
- Relative citation paths only: true

## Canonical Source Rule

`operation` is the canonical operations source. `operations` remains forbidden and is reported as a risk if requested or present in blocked sources.

## Risk Flags

- `no_evidence_citations`
- `forbidden_source_requested`
- `unknown_source_requested`
- `broad_source_scope`
- `full_content_requested`
- `not_ready_for_approval`

## Agent Boundary Checks

- `kasumi` uses `operation` only and blocks `operations`.
- `marin` uses `marketing` and `brand`; `operation` and `operations` are blocked.
- `decision_maker_review` may review all canonical sources but is flagged as broad scope.
- `unrouted` has no allowed sources and requires human review.

## CLI

```powershell
python apps\hermes_gateway\cli.py --agent-review-packet --json
python apps\hermes_gateway\cli.py --agent-review-packet --markdown
```

Both commands are report-only and do not call Discord, LLM, RAG, embeddings, or external systems.

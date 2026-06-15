# STOXL Knowledge Source Routing

Phase 34B defines review-only source routing by agent.

This policy is a pre-retrieval check. It is not connected to public/team channel replies and does not enable general automatic responses.

## Policy

- `marin`: `marketing`, `brand`
- `lucy`: `marketing`, `brand`, `archive`
- `kasumi`: `operation`
- `meiko`: `operation`, `archive`
- `reze`: `strategy`, `brand`, `archive`
- `decision_maker_review`: `marketing`, `operation`, `strategy`, `brand`, `archive`
- `unrouted`: none

## Rules

- `operation` is allowed.
- `operations` is blocked for every agent.
- Unknown agents are blocked.
- Decision maker routing is review-only.
- Source routing happens before retrieval.
- Public/team channel reply remains forbidden.

## CLI

```powershell
python apps\hermes_gateway\cli.py --knowledge-source-routing --json
python apps\hermes_gateway\cli.py --knowledge-source-routing --markdown
```

Safety flags remain false for embedding, LLM, Discord send, and external execution.

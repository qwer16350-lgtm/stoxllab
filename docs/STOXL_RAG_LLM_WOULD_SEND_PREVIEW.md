# STOXL RAG+LLM Would-send Preview

Phase 33D-safe would-send preview shows what a future private-test-only reply
would look like after all gates pass. It never sends the preview to Discord.

## Behavior

- `will_send=false`
- `message_sent=false`
- `discord_send_attempted=false`
- public/team channel scope blocks
- self/bot messages block
- invalid source and `operations` block
- output safety is not considered passed because no LLM call is made

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-llm-would-send-preview --json
python apps\hermes_gateway\cli.py --rag-llm-would-send-preview --markdown
```

## Required Before Any Future Live Review

- valid RAG source
- context safety allowed
- LLM API call explicitly enabled
- output safety allowed
- response packet created
- private test channel ID match
- cooldown, budget, duplicate, and circuit breaker checks clear

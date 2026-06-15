# STOXL Agent Prompt Preview

Phase 35C creates agent prompt previews from dry evidence packs.

The preview includes prompt summaries and citation paths, but it does not execute prompts and does not include full source content.

- Rule-only
- `llm_called=false`
- `discord_message_sent=false`
- `ready_for_llm_call=false`
- `ready_for_discord_send=false`
- `ready_for_embedding=false`
- `ready_for_external_sources=false`
- `ready_for_unattended_auto_reply=false`

CLI:

```powershell
python apps\hermes_gateway\cli.py --agent-prompt-preview --json
python apps\hermes_gateway\cli.py --agent-prompt-preview --markdown
```

This report does not run Discord, send messages, call LLMs, create embeddings/vector indexes, or execute external actions.

## Phase 35D Follow-up

The Phase 35D manual review flow uses this preview as a summary only. It does
not execute the prompt, call an LLM, approve a live run, or send a Discord
message.

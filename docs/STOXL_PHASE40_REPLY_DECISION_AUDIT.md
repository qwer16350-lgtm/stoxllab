# STOXL Phase 40D Reply Decision Audit

Phase 40D audits reply decisions without generating reply text and without sending anything.

Decision table:

- Private-test human message: eligible_for_future_manual_reply.
- Self message: skip_self_message.
- Bot message: skip_bot_message.
- Duplicate message: skip_duplicate_message.
- Public channel: block_public_channel.
- Team channel: block_team_channel.

Safety state:

- Reply text generated: false.
- LLM called: false.
- RAG called: false.
- Discord API send called: false.
- Discord message sent: false.

CLI:

```powershell
python apps\hermes_gateway\cli.py --phase40-reply-decision-audit --json
```

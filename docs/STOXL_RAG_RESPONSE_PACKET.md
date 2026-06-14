# STOXL RAG Response Packet

Phase 33C converts a local retrieval report into a human-review packet.

It does not call LLMs, send Discord messages, call embeddings, or execute external actions.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-response-packet-report --json
python apps\hermes_gateway\cli.py --rag-response-packet-report --markdown
```

## Packet Rules

- citations use relative local paths only
- human review is required
- auto reply is disallowed
- public publish is disallowed
- Discord send is disallowed
- external execution is disallowed

## Safety

- embedding_api_called=false
- llm_api_called=false
- discord_message_sent=false
- external_execution=false
- API key/token/raw Discord ID output is forbidden

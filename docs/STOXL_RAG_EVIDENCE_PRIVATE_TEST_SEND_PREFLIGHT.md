# STOXL RAG Evidence Private-test Send Preflight

Phase 34J-0 defines the private-test send preflight and manual approval gate. It does not implement or run an actual Discord send.

## CLI

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send-preflight --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send-preflight --markdown
```

## Manual Gate For Later Phase

The future Phase 34J-1 live send would require a separate manual approval:

```env
HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED=true
HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE=I_APPROVE_ONE_PRIVATE_TEST_RAG_EVIDENCE_SEND
HERMES_DISCORD_SEND_MESSAGES=true
HERMES_DISCORD_PRIVATE_TEST_REPLY=true
HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID=<private test channel id>
```

Phase 34J-0 reports only booleans. It never logs the approval phrase value.

## Current Phase Boundary

Even when future send gates are represented, Phase 34J-0 keeps:

- `discord_api_send_allowed=false`
- `discord_api_send_called=false`
- `discord_message_sent=false`
- `ready_for_actual_private_test_send=false`
- `ready_for_phase34j1_manual_live_send=true`

The next possible step is Phase 34J-1, which must be requested and approved separately before any single private-test live send.

Phase 34J-1 adds the one-shot send boundary, but default execution remains blocked unless the explicit CLI allow flag and manual approval env gate are present.

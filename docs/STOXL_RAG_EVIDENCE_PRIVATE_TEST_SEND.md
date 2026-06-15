# STOXL RAG Evidence Private-test Send

Phase 34J-1 adds a one-shot private-test Discord send boundary from the Phase 34I would-send preview.

Default execution is blocked. A live send is only possible when all gates pass:

- explicit CLI allow flag
- manual approval env gate
- `HERMES_DISCORD_SEND_MESSAGES=true`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY=true`
- `HERMES_DISCORD_REPLY_MODE=private_test_only`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID` present
- would-send preview safety passed

This phase does not call OpenRouter/LLM again, does not call embeddings, does not create vector indexes, does not ingest external sources, and does not perform external execution.

## Default Report

```powershell
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send --json
python apps\hermes_gateway\cli.py --rag-evidence-private-test-send --markdown
```

## Manual Live Send Command

This command is documented for a human-run single private-test send. Codex should not run it during implementation or testing.

```powershell
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED="true"
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE="I_APPROVE_ONE_PRIVATE_TEST_RAG_EVIDENCE_SEND"

$env:HERMES_DISCORD_SEND_MESSAGES="true"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="true"
$env:HERMES_DISCORD_REPLY_MODE="private_test_only"

python apps\hermes_gateway\cli.py --rag-evidence-private-test-send --json --allow-rag-evidence-private-test-discord-send
```

Immediately after the run:

```powershell
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVED="false"
$env:HERMES_RAG_EVIDENCE_PRIVATE_TEST_SEND_APPROVAL_PHRASE=""

$env:HERMES_DISCORD_SEND_MESSAGES="false"
$env:HERMES_DISCORD_PRIVATE_TEST_REPLY="false"
$env:HERMES_DISCORD_REPLY_MODE=""
```

## Success Criteria

- `discord_message_sent=true`
- `message_sent_count=1`
- `sent_channel_scope=private_test_only`
- `sent_message_review_only=true`
- `self_loop_guard_expected=true`
- `ready_for_phase34j2_send_closeout=true`

Public/team channel sends remain forbidden.

## Next Phase

Phase 34J-2 should close out the single send with replay/audit verification.

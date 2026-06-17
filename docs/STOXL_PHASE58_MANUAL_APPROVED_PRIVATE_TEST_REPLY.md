# STOXL Phase58 Manual-Approved Private-Test Reply

Phase58 defines a dedicated actual path for sending the deterministic reply
derived from the captured read-only canary event. Phase58-1 removes the
unconditional `safe_hotfix_no_send` block from the actual command path when all
manual gates pass, while this Lean Safe Hotfix still verifies the success branch
only with a fake sender.

Approval phrase for the later Manual Gate:

```text
I_APPROVE_PHASE58_MANUAL_APPROVED_PRIVATE_TEST_REPLY
```

Required Manual Gate environment keys:

- `HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVED`
- `HERMES_PHASE58_MANUAL_APPROVED_REPLY_APPROVAL_PHRASE`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`

Required reply mode:

```text
private_test_manual_approved_only
```

Current Safe Hotfix behavior:

- Preflight reports actual-path readiness booleans only.
- Blocked actual report is available.
- Actual CLI without the later Manual Gate remains blocked.
- Actual path can enter the send branch only when the allow flag, manual
  approval, exact phrase, reply mode, private-test reply gate, Discord send
  gate, token/channel presence, and all disabled external capability checks pass.
- Unit tests verify successful actual-path behavior with a fake sender only.
- Reply text source is `deterministic_template`.
- Target scope is private-test only.
- Raw user content is not included.
- Approval phrase value is not logged in reports.
- Discord runtime is not executed by this hotfix.
- The required verification commands do not call real Discord API send.
- Report-only and blocked reports keep `message_sent_count=0`.
- LLM/OpenRouter, RAG, embedding/vector, scheduler live execution, and external
  execution are false.

Phase58 closeout state:

- The operator-run actual Phase58 private-test deterministic reply send is
  recorded as metadata only.
- `message_sent_count=1` is fixed as the historical success count.
- Closeout reports do not call Discord API send and do not send a message.
- Repeat send is locked with
  `phase58_actual_manual_reply_already_consumed`.
- `ready_for_repeat_send=false`.
- The next gate is supervised private-test auto-reply Manual Gate prep.

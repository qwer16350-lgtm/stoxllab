# STOXL Phase59 Supervised Private-Test Auto-Reply

Phase59 adds the supervised private-test auto-reply runtime path for a later
Manual Gate. This Lean Safe Hotfix does not execute Discord runtime and does not
perform real Discord send.

Manual Gate environment keys:

- `HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVED`
- `HERMES_PHASE59_SUPERVISED_AUTO_REPLY_APPROVAL_PHRASE`
- `HERMES_PHASE59_MAX_SESSION_SECONDS`
- `HERMES_PHASE59_MAX_REPLY_COUNT`
- `HERMES_PHASE59_MAX_SEND_COUNT`
- `HERMES_PHASE59_COOLDOWN_SECONDS`
- `HERMES_PHASE59_KILL_SWITCH_READY`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_LLM_ENABLED`
- `HERMES_DISCORD_RAG_ENABLED`
- `HERMES_EMBEDDING_ENABLED`
- `HERMES_VECTOR_ENABLED`
- `HERMES_DISCORD_EXTERNAL_EXECUTION`

Reply mode:

```text
private_test_supervised_auto_reply_only
```

Safety properties:

- Runtime scope is `private_test_only`.
- Reply text source is `deterministic_template`.
- Public/team channel events are blocked.
- Self, bot, and duplicate messages are skipped.
- Max session, max reply, max send, cooldown, and kill-switch guards are
  required.
- The real Discord sender adapter is wired for the later Manual Gate only.
  Safe Bundle verification uses fake sender tests and does not run the allow
  command.
- The former `send_adapter_required_for_actual_manual_gate` blocked state is
  resolved by selecting the real sender adapter only after the allow flag and
  all gate conditions pass.
- LLM/OpenRouter, RAG, embedding/vector, scheduler live execution, and external
  execution remain disabled.
- Raw content, raw Discord IDs, raw session IDs, secrets, and approval phrase
  values are not logged.

The next actual operation must be a separate Manual Gate: actual Phase59
supervised private-test auto-reply short session.

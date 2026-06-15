# STOXL Private-test Send Operator Checklist

Phase 38D defines the final human checklist before any later actual send phase.

Required manual checks:

- `working_tree_clean`
- `validator_errors_zero`
- `relevant_tests_passed`
- `discord_token_presence_boolean_checked`
- `private_test_channel_presence_boolean_checked`
- `approval_false_by_default`
- `public_team_forbidden`
- `unattended_auto_reply_false`
- `payload_preview_human_reviewed`
- `final_send_command_not_run`

Safety state:

- Operator checklist ready: true
- Approval phrase generated: false
- Manual approval actualized: false
- Discord API send called: false
- Discord message sent: false
- Ready for Phase 38E live send entry gate: true
- Ready for actual private-test send: false
- Ready for Discord send: false

## Phase 39A Operator Note

Phase 39A introduces a default-blocked one-shot send path, but it does not
activate the operator approval. The checklist remains a review artifact.

- Approval phrase value must not be generated or printed.
- Token, private channel ID, API key, raw Discord ID, and full message content
  must not be printed.
- Actual send path exists for inspection only.
- Discord live runtime must not be started by this phase.
- Discord API send must remain uncalled.
- Discord message sent must remain false.
- Phase 39B manual one-shot actual send remains a separate future step.

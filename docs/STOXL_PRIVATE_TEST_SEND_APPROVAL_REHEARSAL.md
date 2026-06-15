# STOXL Private-test Send Approval Rehearsal

Phase 37C lists future private-test send gate names without generating an
approval phrase or enabling approval.

## Future Gate Names

- `HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVED`
- `HERMES_PRIVATE_TEST_DRAFT_SEND_APPROVAL_PHRASE`
- `HERMES_DISCORD_SEND_MESSAGES`
- `HERMES_DISCORD_PRIVATE_TEST_REPLY`
- `HERMES_DISCORD_REPLY_MODE`
- `HERMES_DISCORD_PRIVATE_TEST_CHANNEL_ID`
- `DISCORD_BOT_TOKEN`

## Safety State

- Approval phrase generated: false
- Approval phrase value logged: false
- Manual approval actualized: false
- Future send scope: `private_test_only`
- Ready for Phase 37D actual private-test send: false
- Ready for Discord send: false
- Ready for unattended auto reply: false
- Phase 37D-F keeps approval rehearsal as non-actualized and does not generate an approval phrase.

Phase 38E may list future manual gate names, but no gate values or approval
phrase values are generated or printed.

## CLI

```powershell
python apps\hermes_gateway\cli.py --private-test-send-approval-rehearsal --json
python apps\hermes_gateway\cli.py --private-test-send-approval-rehearsal --markdown
```

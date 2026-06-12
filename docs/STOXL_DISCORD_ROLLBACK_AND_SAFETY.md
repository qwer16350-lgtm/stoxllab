# STOXL Discord Rollback And Safety

## Basic Principles

Before any real Discord connection:

- commit the repo state
- back up the runtime mapping file
- start with read-only behavior only
- keep message sending disabled
- keep external execution disabled
- preserve `human_only_execution`
- keep approval and execution separate

The first live trial must be on a private test server only.

## Risk Situations

Watch for these risks:

- bot reads an unexpected channel
- private channel permissions are broader than intended
- `message_content` intent is broader than needed
- owner ID mapping is wrong
- role ID mapping is wrong
- approval channel mapping is wrong
- audit log mapping is missing
- secret-like content appears in logs
- unexpected dispatch occurs
- unknown channel is not blocked
- junior direct approval shortcut is not blocked

## Immediate Stop Conditions

Stop immediately if any of these occurs:

- Discord API call happens in a phase where it is not approved
- `message_sent=true`
- `external_execution_count` is not 0
- unknown channel attempts dispatch
- junior direct approval is attempted
- secret redaction fails
- approval attempts external execution
- bot sees channels outside the private test scope

## Rollback Procedure

1. Stop the bot process.
2. Remove or disable the bot role permissions.
3. Revoke the private test server invite if needed.
4. Rotate local env/token values if any exposure is suspected.
5. Inspect audit logs.
6. Back up the mapping file for incident review.
7. Revert or reset the relevant git changes only after confirming ownership of the changes.
8. Re-run local validation and tests before trying again.

## Audit Logs To Inspect

Inspect:

- replay logs
- audit events
- approval review packets
- mapping validation reports

Confirm:

- no raw secrets
- no message sends
- no external execution
- human-only approval state preserved
- unknown channels blocked
- junior shortcuts blocked

## Never Automate These

The STOXL Hermes Discord system must not automatically perform:

- SNS posting
- homepage upload
- grant or application submission
- email sending
- contract confirmation
- price confirmation
- delivery confirmation
- external DB/RAG original copy

Any approved external action remains a human-only action unless a later, explicitly approved policy says otherwise.

## Recovery Before Retry

Before retrying a read-only connection:

- run config validation
- run all local tests
- run mapping validator in strict mode
- confirm rollback plan is still current
- confirm no secret-like values are present
- confirm no Discord message send path is enabled

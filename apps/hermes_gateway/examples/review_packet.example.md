# STOXL Approval Review Packet

## Summary
- total_events: 6
- blocked_count: 4
- approval_required_count: 4
- pending_count: 2
- approved_count: 1
- rejected_count: 1
- human_only_execution_count: 4
- external_execution_count: 0

## Decision Maker Notice

This packet is for review only. It is not a Discord button/message UI, and approval does not trigger SNS posting, homepage upload, grant submission, email, or contract execution.

## Pending / Decided Items

### Item: approval_example_sns

- Requested action: sns_publish
- Source event: rp_evt_sns_publish_001
- Primary agent: marin
- Reviewer:
- Final report channel: 최종-승인요청
- Status: approved
- Risk level: medium
- Risk reasons:
- Public-facing publish/upload action: sns_publish
- Human-only execution: true
- External execution allowed: false
- Recommended decision: manual_review_required
- Decision note template: Approval does not trigger external execution; a human must perform any approved external action separately.

### Item: blocked_example_secret

- Requested action: sensitive_info_request
- Source event: [REDACTED]
- Primary agent:
- Reviewer:
- Final report channel:
- Status: blocked
- Risk level: high
- Risk reasons:
- [REDACTED]
- Human-only execution: true
- External execution allowed: false
- Recommended decision: reject
- Decision note template: Reject. Do not expose tokens, API keys, passwords, or secrets.

## Safety Assertions
- external_execution_count_is_zero: true

## What This Packet Does Not Do

- This packet is for review only.
- It is not an approval button or real Discord message.
- Approval does not automatically trigger external execution.
- SNS posting, homepage upload, grant submission, email sending, and contract confirmation must be performed separately by a human.

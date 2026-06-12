# STOXL Approval Review Packet

## Purpose

Phase 16 adds a local approval review packet for Decision Makers. It converts Phase 14 replay and approval queue results, plus Phase 15 audit metadata, into review-friendly JSON and Markdown.

This is not a Discord interaction UI. It is a local review artifact only.

## Relationship to Prior Phases

- Phase 14 creates replay results and an in-memory approval queue.
- Phase 15 exports replay and audit logs.
- Phase 16 creates a human-readable review packet from the same local replay result.

## What Review Packet Does

- Summarizes replay totals and approval queue status.
- Lists approval items that need review.
- Includes blocked sensitive-information requests for rejection.
- Classifies risk as `low`, `medium`, or `high`.
- Suggests review guidance without auto-approving.
- Preserves `human_only_execution=true`.
- Preserves `external_execution_allowed=false`.

## What Review Packet Does Not Do

- It does not create Discord buttons.
- It does not send Discord messages.
- It does not post to SNS.
- It does not upload to a homepage.
- It does not submit grants or applications.
- It does not send email.
- It does not confirm contracts, prices, or delivery schedules.

## Usage

```powershell
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --review-packet --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --approval-actions apps\hermes_gateway\examples\review_packet_actions.example.json --review-packet --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --review-packet --export-review-packet --dry-run-export --json
python apps\hermes_gateway\cli.py --replay apps\hermes_gateway\examples\review_packet_events.example.json --review-packet --export-review-packet --review-export-root exports\hermes_gateway\review_packets --json
```

## JSON Structure

Top-level fields:

- `packet_id`
- `packet_type`
- `created_at`
- `source_replay_id`
- `summary`
- `decision_maker_notice`
- `items`
- `safety_assertions`
- `recommended_actions`
- `redaction_applied`

Each item contains:

- `approval_id`
- `source_event_id`
- `requested_action`
- `request_summary`
- `primary_agent`
- `reviewer_agent`
- `final_report_channel`
- `status`
- `risk_level`
- `risk_reasons`
- `human_only_execution`
- `external_execution_allowed`
- `decision_options`
- `recommended_decision`
- `decision_note_template`
- `block_reasons`
- `audit_refs`

## Markdown Structure

The Markdown packet contains:

- `Summary`
- `Decision Maker Notice`
- `Pending / Decided Items`
- one section per review item
- `Safety Assertions`
- `What This Packet Does Not Do`

## Risk Level Rules

`high`:

- grant or competition submission
- external email
- contract confirmation
- price confirmation
- delivery schedule confirmation
- official brand direction confirmation
- external collaboration condition confirmation
- secret, API key, password, or token request

`medium`:

- SNS publish
- homepage upload

`low`:

- internal draft creation
- internal review
- strategy review

## Recommended Decision Rules

The packet does not auto-approve.

- Secret/API key/password requests: `reject`
- External submission, contract, price, or schedule confirmation: `manual_review_required`
- SNS/homepage publication: `manual_review_required`

## Redaction Policy

Review packets must not store tokens, API keys, passwords, secrets, or sensitive source content. Matching values are replaced with `[REDACTED]`.

## Safety Assertions

Review packet export is blocked if `external_execution_count` is not zero. Approved items still require:

```text
human_only_execution=true
external_execution_allowed=false
```

## Git Note

Generated export artifacts under `exports/hermes_gateway/` must not be committed. Example packet files under `apps/hermes_gateway/examples/` are documentation examples and may be committed.

## Phase 17+ Plan

- approval UI mock expansion
- read-only Discord connection review packet investigation
- real Discord interaction design after explicit approval

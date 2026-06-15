# STOXL Private-test One-shot LLM Draft Preflight

Phase 36A adds a report-only preflight for a possible future one-shot LLM draft
in the private-test scope. It does not start Phase 36 live execution.

## Safety State

- Discord live runtime executed: false
- Discord message sent: false
- Discord API send called: false
- OpenRouter or LLM API called: false
- LLM API call attempted: false
- LLM API call count: 0
- Approval phrase generated: false
- Approval phrase value logged: false
- Manual approval activated: false
- Embedding/vector created: false
- External execution: false
- Public/team send or reply allowed: false
- Unattended auto reply allowed: false

## Candidate Rules

Candidate selection is conservative. A candidate requires a review packet,
human review, canonical allowed sources, at least one relative evidence
citation, no full content, no critical risk flag, and public/team/unattended
send/reply gates still blocked.

Critical risk flags:

- `forbidden_source_requested`
- `unknown_source_requested`
- `full_content_requested`
- `not_ready_for_approval`

In Phase 36A, `kasumi` is the only candidate because she has an `operation`
evidence citation. `marin` is blocked due to missing evidence citations.
`decision_maker_review` remains human-review-only because of broad source
scope.

## Future Gate Names

The report lists future gate names only. It does not generate or print values:

- `HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED`
- `HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE`
- `OPENROUTER_API_KEY`

## CLI

```powershell
python apps\hermes_gateway\cli.py --private-test-one-shot-llm-draft-preflight --json
python apps\hermes_gateway\cli.py --private-test-one-shot-llm-draft-preflight --markdown
```

## Phase 36B Follow-up

Phase 36B may create a mock draft packet and output safety rehearsal from this
preflight. That follow-up remains no-API and no-send.

## Phase 36C Follow-up

Phase 36C may check actual LLM call prerequisites, including OpenRouter key
presence as a boolean. It still does not attempt an LLM API call.

## Phase 36D Follow-up

Phase 36D may attempt one manually gated review-only LLM draft call for
`kasumi` and `operation` only. Discord send remains disabled.

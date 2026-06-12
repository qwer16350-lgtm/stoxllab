# STOXL Agent Operation Handbook

## Operating Principle

Use Discord channels to route work to the right agent, keep uncertainty visible, and prevent unapproved external execution. Current status is design/configuration/dry-run/documentation; no real Discord server has been applied.

## Where To Ask In Discord

| Request | Start Channel | Flow |
|---|---|---|
| SNS draft | `marketing-brief` or `marin-초안` | 마린 -> 루시 -> 결정권자 |
| Homepage copy | `homepage` | 마린 -> 루시 -> 결정권자 if upload is needed |
| Marketing strategy | `marketing-brief` | 마린 -> 루시, with optional Reze opinion |
| Competition/grant search | `operation-brief` or `kasumi-리서치` | 카스미 -> 메이코 |
| Support decision | `meiko-검토` | 메이코 -> 결정권자 |
| Deadline follow-up | `일정-마감관리` | 카스미 -> 메이코 |
| Strategy/product/business idea | `reze-전략기획`, `product-ideas`, or `new-business` | 레제 -> 결정권자 |
| Cross-team strategy opinion | `대표-회의실`, `marketing-brief`, or `operation-brief` | 레제 -> relevant senior |

## SNS Draft Flow

1. Put the request in `marketing-brief`, `marin-초안`, or `sns-콘텐츠`.
2. Marin prepares draft candidates and marks them as draft/candidate/review-use only.
3. Lucy reviews tone, risk, and publish readiness in `lucy-검토`.
4. If publishing is needed, Lucy prepares `최종-승인요청`.
5. Decision makers approve, hold, or reject.
6. If approved, execution remains human-only.

## Homepage Copy Flow

1. Put the request in `homepage`.
2. Marin prepares section or page copy drafts.
3. Lucy reviews public-facing quality.
4. Upload or real homepage reflection requires `최종-승인요청`.
5. Approved homepage changes are still human-only execution.

## Competition/Grant Search Flow

1. Put the request in `operation-brief`, `kasumi-리서치`, or `공모전-지원사업`.
2. Kasumi searches and captures candidate name, host, due date, eligibility, deliverables, benefits, source URL, and confirmation status.
3. Kasumi sends the result to `meiko-검토`.
4. Meiko evaluates fit, burden, deadline, and risk.

## Support Decision Flow

1. Meiko reviews the candidate.
2. Meiko marks recommendation as recommendation/hold/not recommended.
3. If submission or external contact is needed, Meiko reports to `최종-승인요청`.
4. Decision makers approve, hold, or reject.
5. Even after approval, the bot does not submit or email.

## Strategy/Product/Business Idea Flow

1. Put strategy questions in `reze-전략기획`, `product-ideas`, `new-business`, or `대표-회의실`.
2. Reze provides strategic judgment, reasons, risks, weak points, and next questions.
3. If the idea becomes official direction or external collaboration condition, move it to approval.

## Reze Cross-team Opinion Flow

Reze may provide strategy opinions to marketing or operation, but cannot command practical work.

- Marketing opinion goes to Lucy or `marketing-brief`.
- Operation opinion goes to Meiko or `operation-brief`.
- Reze cannot override Lucy or Meiko.

## Approval Request Flow

Use `최종-승인요청` for:

- SNS publish
- Homepage upload
- Competition/grant submission
- External email
- Price, contract, delivery schedule
- Official brand direction
- External collaboration condition

Approval request reports should include:

- summary
- recommendation_level
- reasons
- risks
- next_actions
- approval_required
- source_links
- uncertainty_notes

## Archive Rules

Use archive channels only after the work has a terminal or near-terminal decision.

- `완료된-안건`: completed work
- `보류된-안건`: held work with reason
- `폐기된-안건`: discarded work with reason

Junior agents cannot directly finalize archive movement.

## Status Tags

Use these status tags consistently:

- 발견됨
- 초안
- 검토중
- 수정필요
- 추천
- 비추천
- 보류
- 승인대기
- 승인됨
- 진행중
- 완료
- 폐기
- 아카이브

Do not jump to `승인됨` without `승인대기`. `완료` and `폐기` should move only to `아카이브`.

## Agent-specific Forbidden Actions

### Lucy

- No SNS publish without approval
- No homepage reflection without approval
- No official brand direction confirmation alone

### Marin

- No final publish copy confirmation
- No direct final approval request without Lucy review
- No treating draft as final

### Meiko

- No submission without approval
- No external contact without approval
- No contract-like confirmation

### Kasumi

- No final support recommendation
- No uncertain facts as confirmed
- No bypassing Meiko review

### Reze

- No direct practical orders to teams
- No overriding Lucy/Meiko judgment
- No official direction confirmation alone

## Human-only Work

People must handle:

- Real SNS posting
- Real homepage upload
- Real competition/grant submission
- Real external email
- Real price/contract/delivery confirmation
- Real Discord server application

## Bot Must Not Do

- Do not execute external actions.
- Do not expose tokens, API keys, passwords, or private IDs.
- Do not copy external DB/RAG source files into the repo.
- Do not use RAG or DB sources outside env-based paths in a later phase.

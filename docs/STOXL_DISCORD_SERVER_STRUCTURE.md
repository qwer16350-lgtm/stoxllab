# STOXL Hermes Discord Server Structure

This document describes the Phase 4 dry-run Discord server structure for the STOXL Hermes agent organization. It is a review document only. It is not an implementation script and does not apply any changes to Discord.

## Purpose

The server structure separates decision making, marketing work, operation work, strategy planning, and archived records. The core workflow is:

- 마린 -> 루시 -> 결정권자
- 카스미 -> 메이코 -> 결정권자
- 레제 -> 결정권자

Only 김태호_STOXL and 이주호_STOXL can approve official external execution.

## Categories

### 00-결정권자

Purpose: final decisions, approval requests, and owner-level discussion.

- `공지-결정사항`: final decisions, approval results, and operating principles.
- `대표-회의실`: owner discussion with senior agents and strategy office.
- `최종-승인요청`: approval requests before external execution, official publishing, homepage upload, submission, email, contracts, prices, delivery schedules, or official brand direction.

### 10-마케팅팀

Purpose: marketing briefs, drafts, review, SNS content, and homepage copy.

- `marketing-brief`: marketing intake and task brief.
- `lucy-검토`: Lucy review and revision guidance.
- `marin-초안`: Marin drafts, references, and content candidates.
- `sns-콘텐츠`: SNS content calendar, post candidates, and hashtags.
- `homepage`: homepage structure, section copy, and product-detail copy drafts.

### 20-운영팀

Purpose: external opportunity research, grant/competition review, and deadline tracking.

- `operation-brief`: operation intake and task brief.
- `meiko-검토`: Meiko review and judgment.
- `kasumi-리서치`: Kasumi external opportunity research.
- `공모전-지원사업`: competition/grant candidate database-style channel.
- `일정-마감관리`: deadline alerts, preparation schedules, and internal schedule tracking.

### 30-전략기획실

Purpose: independent strategy analysis by Reze.

- `reze-전략기획`: Reze brand and strategy analysis.
- `brand-rag`: RAG summaries, source path notes, and index summaries. Original files must not be uploaded here.
- `new-business`: new business direction, collaborations, and pop-up possibilities.
- `product-ideas`: new product groups, items, and experiment-line candidates.

### 90-archive

Purpose: archive closed, held, and discarded work.

- `완료된-안건`: completed work archive.
- `보류된-안건`: held work archive.
- `폐기된-안건`: discarded work archive.

Archive write access is limited to decision makers and related senior/strategy agents. Junior agents cannot directly finalize archive movement.

## Role Summary

| Role | Assigned | Summary |
|---|---|---|
| Decision Maker | 김태호_STOXL, 이주호_STOXL | Can read/write major channels and approve in `최종-승인요청`. |
| Marketing Senior | lucy | Can read/write marketing channels, review Marin output, and report to approval. Cannot approve or execute external actions. |
| Marketing Junior | marin | Can draft in marketing channels. Cannot finalize publishing or request final approval without Lucy review. |
| Operation Senior | meiko | Can read/write operation channels, review Kasumi output, and report support decisions. Cannot submit or contact externally without approval. |
| Operation Junior | kasumi | Can research and organize operation candidates. Cannot finalize recommendations or bypass Meiko review. |
| Strategy Office | reze | Can write strategy channels and report to `대표-회의실`. Can advise marketing/operation but has no command authority. |
| Agent | lucy, marin, meiko, kasumi, reze | Common agent role. Cannot approve or execute external actions. |
| Archive Viewer | agents | Read-focused archive access. |

## Agent Channel Access

### Lucy

- Read/write: `marketing-brief`, `lucy-검토`, `marin-초안`, `sns-콘텐츠`, `homepage`
- Report: `대표-회의실`, `최종-승인요청`
- Archive write: related senior marketing items only
- Cannot publish SNS or update homepage without owner approval.

### Marin

- Read/write: `marketing-brief`, `lucy-검토`, `marin-초안`, `sns-콘텐츠`, `homepage`
- Read: selected strategy references such as `brand-rag`, where configured
- Cannot finalize publishing copy.
- Cannot bypass Lucy review.

### Meiko

- Read/write: `operation-brief`, `meiko-검토`, `kasumi-리서치`, `공모전-지원사업`, `일정-마감관리`
- Report: `대표-회의실`, `최종-승인요청`
- Archive write: related senior operation items only
- Cannot submit applications or contact external organizations without owner approval.

### Kasumi

- Read/write: `operation-brief`, `meiko-검토`, `kasumi-리서치`, `공모전-지원사업`, `일정-마감관리`
- Cannot finalize support recommendations.
- Cannot bypass Meiko review.

### Reze

- Read/write: `reze-전략기획`, `brand-rag`, `new-business`, `product-ideas`
- Report: `대표-회의실`
- May provide strategic opinions on marketing and operation.
- Has no authority to command the marketing or operation teams.
- Cannot approve official direction or external execution.

## Approval Flow

Approval-required actions must go to `최종-승인요청` before any external execution:

- SNS publish
- Homepage upload
- Competition submission
- Grant submission
- External email send
- Price confirmation
- Contract confirmation
- Delivery schedule confirmation
- Official brand direction confirmation
- External collaboration condition confirmation

The approval decision makers are 김태호_STOXL and 이주호_STOXL. Discord user IDs must be referenced only through `.env.example` TODO variables:

- `OWNER_KIM_DISCORD_ID=TODO`
- `OWNER_LEE_DISCORD_ID=TODO`

## Junior -> Senior -> Decision Maker Flow

Marketing:

1. Marin drafts in `marin-초안`, `sns-콘텐츠`, or `homepage`.
2. Lucy reviews in `lucy-검토`.
3. Lucy reports approval-needed items to `최종-승인요청`.
4. Decision makers approve, hold, or reject.

Operation:

1. Kasumi researches in `kasumi-리서치`, `공모전-지원사업`, or `일정-마감관리`.
2. Meiko reviews in `meiko-검토`.
3. Meiko reports support decisions to `최종-승인요청` when approval is needed.
4. Decision makers approve, hold, or reject.

Strategy:

1. Reze analyzes in strategy channels.
2. Reze reports to `대표-회의실`.
3. If official brand direction or external conditions are involved, the item moves to `최종-승인요청`.

## Archive Criteria

- `완료된-안건`: use for completed work.
- `보류된-안건`: use for held work with a reason.
- `폐기된-안건`: use for discarded work with a reason.

Junior agents may provide information for archive decisions, but they cannot directly finalize archive movement.

## TODO Before Real Discord Application

- NEEDS_USER_DECISION: confirm real Discord server/guild target.
- NEEDS_USER_DECISION: confirm final Discord role names if Korean role names are preferred over English dry-run names.
- NEEDS_USER_DECISION: confirm whether Decision Maker should have `can_execute_external_actions=true` as an approval concept only, or whether real execution remains human-only in Discord policy.
- Confirm actual Discord user IDs through `.env` only; never hardcode them.
- Confirm bot permissions before any future apply step.
- Review dry-run JSON files before creating any implementation script.

## Forbidden

- Do not change the real Discord server yet.
- Do not request or use a Discord Bot Token in Phase 4.
- Do not create Discord API calls or apply scripts from this phase.
- Do not treat dry-run files as executable deployment code.
- Agents must not directly perform external publishing, submissions, emails, contracts, prices, or delivery-schedule confirmations.
- Do not create a real `.env` file for this phase.

# STOXL Current Decisions and TODOs

## Confirmed Decisions

| Item | Decision |
|---|---|
| Current repo path | `C:\tmp\STOXL_LAB` |
| Source workbook | `docs/planning/STOXL_Hermes_Discord_Agent_Implementation_Guide.xlsx` |
| External DB/RAG originals | Do not copy into repo |
| Git tracking for external DB/RAG originals | Do not track |
| Repo canonical RAG operation folder | `rag\operation` |
| Operation spelling | Use `operation`, not `operations` |
| Internal role_id style | English snake_case |
| Human-facing role display name | Korean or Korean + English allowed |
| Decision Maker external execution | `can_execute_external_actions=false` |
| External execution policy | human-only |
| Real Discord server application | Not done yet |
| Real `.env` | Not created |
| Discord Bot Token | Not requested |
| External execution by agents | Not allowed |

## Confirmed Organization Rules

- 마린 -> 루시 -> 결정권자
- 카스미 -> 메이코 -> 결정권자
- 레제 -> 결정권자

Decision makers:

- 김태호_STOXL
- 이주호_STOXL

Agent approval and execution boundaries:

- All agents have `L5_External_Execute=false`.
- All agents have `L6_Final_Approval=false`.
- Decision Maker can approve, but does not create bot-based external execution.
- External posting, submission, email, upload, and contract-like actions remain human-only.

## Open TODOs

### Environment and Identity

- NEEDS_USER_DECISION: `DISCORD_GUILD_ID`
- NEEDS_USER_DECISION: `OWNER_KIM_DISCORD_ID`
- NEEDS_USER_DECISION: `OWNER_LEE_DISCORD_ID`
- NEEDS_USER_DECISION: `HERMES_CONFIG_PATH`
- NEEDS_USER_DECISION: real external DB/RAG UNC paths

### Discord Structure

- NEEDS_USER_DECISION: role display name final notation
- NEEDS_USER_DECISION: real Discord server application approval

### Future Test/Runtime Design

- NEEDS_USER_DECISION: test framework selection
- NEEDS_USER_DECISION: Discord mock strategy
- NEEDS_USER_DECISION: config loader implementation decision
- NEEDS_USER_DECISION: prompt loader implementation decision
- NEEDS_USER_DECISION: approval gate evaluator implementation decision
- NEEDS_USER_DECISION: RAG access evaluator implementation decision
- NEEDS_USER_DECISION: status transition evaluator implementation decision

## Current Safety Notes

- The current repo is a design/configuration/dry-run/documentation workspace.
- No real Discord server has been changed.
- No external DB/RAG source files have been copied into the repo.
- No actual external action capability is enabled.
- No real `.env` file exists in this documented phase set.

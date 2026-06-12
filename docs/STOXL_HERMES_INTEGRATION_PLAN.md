# STOXL Hermes Integration Plan

## 1. Current State

Phases 0 through 12 are design, configuration, dry-run, validation, registry, mock evaluator, mock adapter, and boundary documentation phases.

The project has not connected to a real Hermes runtime. It has not connected to Discord Gateway. It has not called Discord APIs. It has not called an LLM. It has not accessed external DB/RAG originals.

Current state should be described as design/configuration/dry-run/mock/boundary documentation, not production implementation.

## 2. Recommended Integration Order

### Phase 13: Runtime Config Schema

Define the schema that a future runtime adapter will consume. Confirm which registry fields are stable and which fields remain dry-run only.

Still forbidden:

- External posting
- Grant or competition submission
- Email sending
- Contract, price, or delivery confirmation
- DB/RAG source copying
- Secret hardcoding

### Phase 14: Discord/Hermes Adapter Stub

Create a stub interface that accepts normalized request objects. It should not connect to Discord or Hermes yet.

Still forbidden:

- Real Discord Gateway connection
- Real Discord API calls
- Bot Token usage
- External execution
- Secret hardcoding

### Phase 15: Local Event Replay Test

Replay stored mock events and confirm the adapter boundary produces stable evaluator and dispatch plans.

Still forbidden:

- Real Discord server changes
- External actions
- RAG source ingest
- Secret hardcoding

### Phase 16: Approval Interaction Mock

Mock approval interactions such as buttons, reactions, or owner confirmation messages without using Discord API.

Still forbidden:

- Real approval button deployment
- Real message sending
- External execution after approval

### Phase 17: Read-only Discord Bot Connection

If approved later, connect a bot in read-only mode to a controlled environment. It should only observe and log.

Still forbidden:

- Channel/role mutation
- Posting generated responses without approval
- External posting/submission/email
- Contract-like execution

### Phase 18: Limited Private Server Test

Test in a private server with mock channels and non-production data.

Still forbidden:

- Real STOXL server apply
- External execution
- Production RAG source ingest
- Secret exposure

### Phase 19: Real STOXL Discord Server Apply

Apply server structure only after explicit manual approval and review of all dry-run outputs.

Still forbidden unless separately approved:

- External posting
- Submission
- Email
- Contract/price/delivery confirmation

### Phase 20: RAG Source Path Connection

Connect external DB/RAG source paths using env-based UNC paths. Do not copy source originals into repo.

Still forbidden:

- Secret ingestion
- Source file copying into repo
- Unfiltered sensitive data exposure

### Phase 21: Scheduler/Notification Connection

Connect deadline and notification scheduling after RAG/source and channel mappings are confirmed.

Still forbidden:

- Automatic submission
- Automatic publish
- Automatic external email
- Automatic contract-like execution

## 3. Hermes Integration Interface Candidates

### inbound_event_adapter

Converts raw Discord, scheduler, CLI, or future RAG events into normalized requests.

### normalized_request

Stable request shape consumed by evaluator logic.

### evaluator_result

Routing, permission, approval, RAG, handoff, and status judgment.

### dispatch_plan

Message plan that says where a response or report should go. This is a plan, not a send operation.

### approval_gate_result

Approval-required action state. Approval after this point still remains human-only.

### audit_log_event

Structured record of input, normalized request, evaluator result, dispatch plan, block reasons, and human review needs.

## 4. Required Values Before Real Code

- NEEDS_USER_DECISION: `DISCORD_GUILD_ID`
- NEEDS_USER_DECISION: `OWNER_KIM_DISCORD_ID`
- NEEDS_USER_DECISION: `OWNER_LEE_DISCORD_ID`
- NEEDS_USER_DECISION: `HERMES_CONFIG_PATH`
- NEEDS_USER_DECISION: actual Discord channel IDs
- NEEDS_USER_DECISION: actual Discord role IDs
- NEEDS_USER_DECISION: actual external DB/RAG UNC paths
- NEEDS_USER_DECISION: runtime log path

## 5. Rollback Plan

Before any real application:

1. Commit all repo changes.
2. Export or back up current Discord server structure.
3. Compare dry-run files with intended real apply output.
4. First run must be read-only mode.
5. If anything behaves unexpectedly, disable the bot.
6. Do not mutate channels or roles until mappings are reviewed.
7. Keep audit logs for every runtime event and evaluator decision.

## 6. Safety Boundary

No integration phase should silently enable external execution. External posting, submissions, emails, uploads, prices, contracts, delivery schedules, and external collaboration conditions require explicit human action.

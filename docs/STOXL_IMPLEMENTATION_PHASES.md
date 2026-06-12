# STOXL Implementation Phases

This document summarizes completed design/configuration/dry-run/documentation phases and proposes possible later phases. Phase 8 and later are proposals only and are not implemented here.

## Completed Phases

### Phase 0: Repository Inspection

Inspected the current repository structure at `C:\tmp\STOXL_LAB`, identified existing folders, and confirmed there was no existing Hermes runtime, Discord gateway, scheduler, RAG runtime, or executable implementation.

### Phase 1: Excel Source-of-Truth Extraction

Read the planning workbook:

`docs/planning/STOXL_Hermes_Discord_Agent_Implementation_Guide.xlsx`

Extracted organization structure, agent roles, permissions, forbidden actions, channels, routing, report formats, RAG access, notifications, status tags, test cases, and environment variables.

### Phase 2: Config Generation

Created machine-readable YAML config and supporting docs:

- `.env.example`
- `ENV_REQUIRED.md`
- `RAG_PATHS_REQUIRED.md`
- `config/stoxl/*.yaml`

No real `.env` was created.

### Phase 3: Agent System Prompts

Created agent prompt markdown files:

- `prompts/agents/lucy.md`
- `prompts/agents/marin.md`
- `prompts/agents/meiko.md`
- `prompts/agents/kasumi.md`
- `prompts/agents/reze.md`

These are prompt documents only, not runtime code.

### Phase 4: Discord Server Dry-run Structure

Created Discord review-only dry-run files and documentation:

- `discord/server_structure.dryrun.json`
- `discord/role_structure.dryrun.json`
- `discord/channel_permissions.dryrun.json`
- `docs/STOXL_DISCORD_SERVER_STRUCTURE.md`

No real Discord server changes were made.

### Phase 5: Routing and Workflow Dry-run

Created routing, approval, and handoff dry-run specs:

- `discord/routing_workflow.dryrun.json`
- `discord/approval_gate.dryrun.json`
- `discord/handoff_rules.dryrun.json`
- `docs/STOXL_ROUTING_AND_WORKFLOW_SPEC.md`

External execution was documented as human-only.

### Phase 6: Guardrail Dry-run Test Specs

Created dry-run test specifications and a test plan:

- `docs/STOXL_TEST_PLAN.md`
- `tests/stoxl/*.dryrun.json`

No executable tests were created.

### Phase 7: Documentation Integration

Created integrated human-readable documentation and the top-level README:

- `README.md`
- `docs/STOXL_HERMES_AGENT_ORG_README.md`
- `docs/STOXL_AGENT_OPERATION_HANDBOOK.md`
- `docs/STOXL_IMPLEMENTATION_PHASES.md`
- `docs/STOXL_CURRENT_DECISIONS_AND_TODOS.md`

## Proposed Later Phases

These are proposals only. Do not treat them as implemented work.

### Phase 8: Config Validation Script Design

Design how config validation should work before writing code. Decide schema format, validation rules, and error reporting.

### Phase 9: Prompt/Config Loader Design

Design how a future runtime might load YAML config and markdown prompts.

### Phase 10: Discord Mock Test Implementation

Implement tests using a Discord mock rather than a real Discord server.

### Phase 11: Approval Gate Evaluator Implementation

Implement logic that evaluates approval-required actions and blocks them before approval.

### Phase 12: RAG Access Evaluator Implementation

Implement logic that checks agent-level RAG source access and sensitive data exclusions.

### Phase 13: Actual Discord Server Apply Script Draft

Draft a script for server setup only after explicit approval. It should support dry-run and review output first.

### Phase 14: Manual Review Before Real Discord Apply

Manually review guild ID, user IDs, role names, channel names, permissions, and safety gates before any real apply.

### Phase 15: Real Discord Server Apply

Apply to the real Discord server only after explicit user approval, confirmed credentials, and a reviewed dry-run.

## Current Boundary

The project is currently at design/configuration/dry-run/documentation. Actual Discord application, bot runtime, external execution, and real test code remain separate future work.

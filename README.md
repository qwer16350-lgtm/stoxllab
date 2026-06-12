# STOXL Hermes Discord Agent Organization

This repository contains the design, configuration, dry-run specifications, and documentation for the STOXL Hermes Discord Agent Organization.

Current status: design/configuration/dry-run/documentation is prepared. The real Discord server has not been changed, no Discord API has been called, and no external execution is enabled.

## Purpose

The project defines a five-agent Discord-based organization for STOXL:

- Lucy / 루시: marketing senior review
- Marin / 마린: marketing junior drafts and research
- Meiko / 메이코: operation senior judgment and deadline risk
- Kasumi / 카스미: operation junior research and condition capture
- Reze / 레제: independent strategy office

The core organizational flows are:

- 마린 -> 루시 -> 결정권자
- 카스미 -> 메이코 -> 결정권자
- 레제 -> 결정권자

Final approval belongs only to the decision makers: 김태호_STOXL and 이주호_STOXL. External execution is human-only.

## Current State

This repo currently contains:

- Source-of-truth planning workbook in `docs/planning/`
- Environment variable documentation and `.env.example`
- Machine-readable config under `config/stoxl/`
- Agent system prompt markdown under `prompts/agents/`
- Discord dry-run structure under `discord/`
- Routing, approval, handoff, and guardrail dry-run specs
- Human-readable operation documents under `docs/`

It does not contain:

- A real `.env` file
- Discord apply scripts
- Discord API integration
- Bot runtime code
- Real test runner code
- External DB/RAG source files

## Folder Structure

| Path | Purpose |
|---|---|
| `docs/planning/` | Source Excel workbook used as the initial planning reference |
| `config/stoxl/` | Generated YAML configuration for agents, departments, permissions, routing, RAG, reports, notifications, and statuses |
| `prompts/agents/` | Agent system prompt markdown files |
| `discord/` | Discord server, roles, permissions, routing, approval, and handoff dry-run JSON |
| `tests/stoxl/` | Dry-run guardrail test specifications, not executable tests |
| `rag/` | Repo-local canonical RAG folder placeholders; `rag/operation` is canonical |
| `scripts/` | Empty; no execution scripts have been created |

## Phase Status

- Phase 0: Repository Inspection - design analysis complete
- Phase 1: Excel Source-of-Truth Extraction - extraction complete
- Phase 2: Config Generation - config/document files created
- Phase 3: Agent System Prompts - prompt markdown files created
- Phase 4: Discord Server Dry-run Structure - dry-run JSON and server structure document created
- Phase 5: Routing and Workflow Dry-run - dry-run routing, approval, handoff specs created
- Phase 6: Guardrail Dry-run Test Specs - dry-run test specs and test plan created
- Phase 7: Documentation Integration - current documentation integration phase

## Do Not Do

- Do not create a real `.env` file.
- Do not request or hardcode Discord Bot Token, OpenAI API Key, Discord server ID, or user IDs.
- Do not call the Discord API.
- Do not change the real Discord server.
- Do not create apply scripts without a later explicit approval phase.
- Do not copy external DB/RAG source files into this repository.
- Do not track external DB/RAG source files in Git.
- Do not enable external posting, submitting, emailing, uploading, or contract-like actions.

## Before Moving To A Later Phase

Confirm the remaining TODO values and decisions:

- `DISCORD_GUILD_ID`
- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`
- `HERMES_CONFIG_PATH`
- Real external DB/RAG UNC paths
- Final role display names
- Explicit approval before any real Discord server apply phase

The only environment example is `.env.example`; a real `.env` has not been created.

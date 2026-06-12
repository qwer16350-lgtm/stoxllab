# STOXL Agent Registry Loader

## Purpose

`scripts/load_stoxl_agent_registry.py` builds a local read-only `stoxl_agent_registry` JSON document from the existing STOXL Hermes config, prompts, and Discord dry-run files.

The loader is intended for Phase 9 dry-run usage. It does not connect to Hermes runtime, Discord, RAG, or external systems.

## Relationship To Validation

Run the validation script first:

```powershell
python scripts\validate_stoxl_configs.py
```

If validation returns errors, stop and fix the source files in an approved phase. The loader assumes the config and dry-run files are already valid.

## How To Run

Print the full registry to stdout:

```powershell
python scripts\load_stoxl_agent_registry.py
```

Use an explicit repo root:

```powershell
python scripts\load_stoxl_agent_registry.py --root C:\tmp\STOXL_LAB
```

Print JSON to stdout:

```powershell
python scripts\load_stoxl_agent_registry.py --json
```

Write the registry to a file:

```powershell
python scripts\load_stoxl_agent_registry.py --out registry\stoxl_agent_registry.example.json
```

Output a single agent:

```powershell
python scripts\load_stoxl_agent_registry.py --agent lucy
```

Unknown agent IDs return exit code `1`.

## Registry Structure

The generated JSON contains:

- `meta`: registry type, phase version, root path, and source files
- `decision_makers`: 김태호_STOXL and 이주호_STOXL with approval-only authority
- `departments`: decision makers, marketing team, operation team, and strategy office
- `agents`: agent config, prompt markdown, RAG access, routing roles, and forbidden shortcuts
- `channels`: Discord dry-run channel registry
- `routing`: request type routing rules
- `approval_gates`: approval-required action gates
- `handoff_rules`: agent-to-agent handoff rules
- `rag_access`: env-key-based source policy and sensitive data exclusion
- `status_tags`: status definitions and allowed transitions
- `warnings`: loader warnings, if any

## What The Loader Does

- Reads YAML config from `config/stoxl/*.yaml`
- Reads prompt markdown from `prompts/agents/*.md`
- Reads Discord dry-run JSON from `discord/*.dryrun.json`
- Builds a local registry JSON
- Writes only to stdout or an explicit `--out` path

## What The Loader Does Not Do

- Does not call the Discord API
- Does not change a Discord server
- Does not request a Discord Bot Token
- Does not run a bot
- Does not access RAG source files
- Does not access external DB files
- Does not create a real `.env`
- Does not post, submit, email, upload, or confirm contracts
- Does not create RAG ingest/index files
- Does not modify YAML, JSON, prompt, or documentation source files

## Future Use

In Phase 10 or later, this registry can be used by mock evaluators or future Hermes runtime design:

- Agent lookup
- Prompt loading
- Routing evaluation
- Approval gate evaluation
- Handoff evaluation
- RAG access evaluation

Those future phases must still preserve the external execution and human-only safety boundaries unless explicitly changed by an approved later phase.

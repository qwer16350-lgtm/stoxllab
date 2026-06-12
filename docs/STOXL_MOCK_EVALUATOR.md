# STOXL Mock Evaluator

## Purpose

`scripts/evaluate_stoxl_mock_request.py` is a local read-only mock evaluator for STOXL Hermes Discord Agent Organization. It uses the Phase 9 agent registry to decide who should handle a request, which approval gate applies, and which guardrails should block unsafe actions.

It does not generate real agent responses and does not call an LLM.

## Relationship To The Registry Loader

The evaluator reads:

`registry/stoxl_agent_registry.example.json`

If the registry is missing, create it first:

```powershell
python scripts\load_stoxl_agent_registry.py --out registry\stoxl_agent_registry.example.json
```

The evaluator does not import the loader and does not rebuild the registry automatically.

## Relationship To Validation

Before using the evaluator, run:

```powershell
python scripts\validate_stoxl_configs.py
```

If validation has errors, fix those first in an approved phase.

## How To Run

Single text input:

```powershell
python scripts\evaluate_stoxl_mock_request.py --text "인스타 업로드 문구 초안 만들어줘"
```

Scenario file:

```powershell
python scripts\evaluate_stoxl_mock_request.py --scenario mock\stoxl_mock_scenarios.example.json
```

Scenario file with output:

```powershell
python scripts\evaluate_stoxl_mock_request.py --scenario mock\stoxl_mock_scenarios.example.json --out mock\stoxl_mock_results.example.json
```

Agent/action permission check:

```powershell
python scripts\evaluate_stoxl_mock_request.py --agent marin --action sns_publish
```

Explicit root and JSON output:

```powershell
python scripts\evaluate_stoxl_mock_request.py --root C:\tmp\STOXL_LAB --json --text "홈페이지 문구 업로드해줘"
```

## Options

- `--root`: explicit repo root. Defaults to auto-detection.
- `--text`: single request text.
- `--scenario`: scenario JSON file.
- `--agent`: actor agent for permission, RAG, or status checks.
- `--action`: requested action.
- `--json`: JSON output mode. Output is JSON by default.
- `--out`: write result JSON to the given path.

## What It Evaluates

The output includes:

- `classification`: keyword-based request type and action type.
- `routing`: primary agent, reviewer, final channel, approval requirement, forbidden shortcuts.
- `approval_gate`: approval-required action policy.
- `permission_check`: whether an agent can perform a requested action.
- `handoff`: required handoff rule.
- `rag_access`: requested source group access and sensitive data blocking.
- `status_transition`: allowed or blocked status transition.
- `guardrails`: major safety rules applied.
- `blocked`, `block_reasons`, `recommended_next_action`, and `notes`.

## What It Does Not Do

- Does not call the Discord API.
- Does not change any Discord server.
- Does not request a Discord Bot Token.
- Does not generate real agent responses.
- Does not call an LLM.
- Does not access RAG source files.
- Does not access external DB files.
- Does not post, submit, email, upload, or confirm contracts.
- Does not create RAG ingest/index files.
- Does not modify registry, config, prompt, dry-run, or docs files.

## Future Integration

In Phase 11 or later, this evaluator can be connected to:

- Discord mock adapter
- Hermes runtime adapter
- Approval gate evaluator
- RAG access evaluator
- Status transition evaluator

Those future adapters must keep the human-only external execution boundary unless a later approved phase changes it.

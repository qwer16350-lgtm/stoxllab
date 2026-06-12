# STOXL Config Validation

## Purpose

`scripts/validate_stoxl_configs.py` is a read-only validator for the STOXL Hermes Discord Agent Organization repository. It checks consistency across config YAML, agent prompts, Discord dry-run JSON, guardrail dry-run specs, and documentation.

The validator does not fix files automatically. If it finds an issue, it prints an error or warning with a guide for what to review.

## How To Run

From the repo root:

```powershell
python scripts/validate_stoxl_configs.py
```

With an explicit root:

```powershell
python scripts/validate_stoxl_configs.py --root C:\tmp\STOXL_LAB
```

With JSON output:

```powershell
python scripts/validate_stoxl_configs.py --json
```

PyYAML is required for YAML parsing. If it is missing, the script prints:

```text
PyYAML is required: pip install pyyaml
```

The script does not install packages.

## Validation Scope

The validator checks:

- Required Phase 2-6 files
- Optional Phase 7 documents
- YAML parsing for `config/stoxl/*.yaml`
- JSON parsing for `discord/*.dryrun.json`
- JSON parsing for `tests/stoxl/*.dryrun.json`
- Agent consistency
- Department consistency
- Permission consistency
- Approval gate consistency
- Discord channel consistency
- Routing and handoff consistency
- RAG access consistency
- Status tag consistency
- Prompt file section consistency
- `.env.example` consistency

## Error vs Warning

Errors fail validation and return exit code `1`.

Examples:

- Missing required Phase 2-6 file
- Invalid YAML or JSON
- Unknown required agent
- Agent has `L5_External_Execute=true`
- Required approval gate missing
- RAG config uses `operations` instead of canonical `operation`

Warnings do not fail validation and return exit code `0` if there are no errors.

Examples:

- Optional Phase 7 document missing
- Real `.env` file exists in the current phase
- `.env.example` secret-like key does not look like a TODO placeholder
- Risky wording found in a prompt and requiring human review

## JSON Output

Use `--json` when another tool needs structured output.

The output object contains:

- `summary`
- `errors`
- `warnings`
- `passed_checks`
- `skipped_checks`
- `next_actions`

## What This Does Not Check

The validator does not check or perform:

- Real Discord API calls
- Real Discord server changes
- Real bot execution
- Real RAG ingest
- Real external DB access
- Real `.env` secret validity
- Network connectivity
- Discord permission bitfields
- External posting, submission, email, or contract execution

## Failure Review Flow

1. Run the validator.
2. Read `[ERROR]` messages first.
3. Open the referenced file.
4. Fix the source manually in an approved implementation phase.
5. Run the validator again.
6. Review `[WARNING]` items after errors are resolved.

The validator is intentionally read-only. It must not auto-correct config, prompt, dry-run, or documentation files.

## Future Integration

In Phase 9 or later, this validator can be connected to real loader/evaluator work:

- Config loader
- Prompt loader
- Approval gate evaluator
- RAG access evaluator
- Status transition evaluator
- Discord mock test runner

Those are future implementation phases. This Phase 8 script is only a read-only consistency checker.

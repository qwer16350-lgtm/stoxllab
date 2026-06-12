# STOXL Discord Mapping Validator

## Purpose

Phase 20 adds a local validator for Discord runtime mapping JSON files.

The validator checks whether a copied runtime mapping file has the required guild, owner, role, channel, approval, audit, intent, and safety fields before any future read-only Discord connection is considered.

## Relationship To Earlier Phases

Phase 17 created the read-only Discord readiness template.

Phase 18 created a local Discord raw event adapter stub that never connects to Discord.

Phase 19 replayed Discord-shaped raw events locally and produced would-send payloads, approval queue entries, audit trail, and optional review packets.

Phase 20 validates the mapping file those later read-only steps would need. It still does not connect to Discord.

## What The Validator Does

The validator:

- parses a mapping JSON file
- checks `mapping_type` and `version`
- checks guild mapping
- checks required owners
- checks required roles
- checks registry and required channel coverage
- checks approval channel mapping
- checks audit channel mapping
- checks intent checklist fields
- checks local-only safety rules
- detects TODO placeholders
- detects missing mappings
- detects secret-like values and redacts them in the report

## What The Validator Does Not Do

The validator does not:

- call Discord APIs
- connect to Discord Gateway
- require or read a Discord Bot Token
- send Discord messages
- modify a Discord server
- import `discord.py` or `discord.js`
- call LLM providers
- access external RAG originals
- perform external posting, submission, email, contract, or payment actions

## Mapping Template

The default template is:

```text
apps/hermes_gateway/examples/discord_runtime_mapping.template.json
```

This template intentionally contains TODO placeholders. It is valid as a structure reference, but it is not ready for read-only connection until real runtime IDs are filled in a private mapping file.

## Partial Mapping Example

The partial example is:

```text
apps/hermes_gateway/examples/discord_runtime_mapping.partial.example.json
```

It intentionally omits:

- one owner
- one role
- two archive channels
- a filled audit channel

This confirms the validator catches missing mappings.

## Non-Strict vs Strict

Non-strict mode:

- TODO placeholders become `manual_required`
- `overall_valid` may remain `true` if the structure is complete
- `ready_for_readonly_connection=false` while placeholders remain

Strict mode:

- TODO placeholders become `fail`
- `overall_valid=false`
- `ready_for_readonly_connection=false`

## Placeholder Rules

The validator treats these as placeholders:

- strings containing `TODO`
- empty strings
- `null`
- strings containing `PLACEHOLDER`
- strings containing `REPLACE_ME`

## Secret-Like Value Detection

Mapping files must not contain token, secret, API key, authorization, bearer, private key, access key, refresh token, `sk-`, `xoxb-`, `mfa.`, or Discord-token-like values.

When detected:

- the report uses `[REDACTED]`
- the raw secret value is not printed
- `overall_valid=false`
- a blocked reason is added

## Required Roles

- `Decision Maker`
- `Lucy`
- `Marin`
- `Meiko`
- `Kasumi`
- `Reze`
- `Human Operator`
- `Read Only Bot`

## Required Owners

- `OWNER_KIM_DISCORD_ID`
- `OWNER_LEE_DISCORD_ID`

## Required Channels

All registry channels must be mapped. The validator also explicitly checks these important channels:

- `최종-승인요청`
- `대표-회의실`
- `marin-초안`
- `lucy-검토`
- `kasumi-리서치`
- `meiko-검토`
- `reze-전략기획`
- `공모전-지원사업`
- `일정-마감관리`
- `완료된-안건`
- `보류된-안건`
- `폐기된-안건`

## Approval And Audit Checks

Approval mapping must preserve:

- final approval channel
- `external_execution_after_approval=false`
- `human_only_execution=true`

Audit mapping must include local log and export roots. A TODO or empty audit channel is accepted only as `manual_required` in non-strict mode.

## Read-Only Connection Gate

`ready_for_readonly_connection` is true only when:

- no failed checks exist
- no TODO placeholders remain
- no manual fields remain
- no warnings remain
- no secret-like values are detected

This flag is only a local readiness signal. It does not connect to Discord.

## Usage

```powershell
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.template.json --strict --json
python apps\hermes_gateway\cli.py --validate-mapping apps\hermes_gateway\examples\discord_runtime_mapping.partial.example.json --json
python apps\hermes_gateway\tests\test_mapping_validator.py
```

## Phase 21 Candidates

Later phases can add:

- private server read-only connection checklist
- actual ID mapping fill in a private runtime file
- read-only connection dry-run
- stronger role/channel permission validation
- explicit review before any real Discord connection

External execution must never be enabled automatically.

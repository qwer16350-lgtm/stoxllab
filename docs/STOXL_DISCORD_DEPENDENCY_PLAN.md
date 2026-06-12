# STOXL Discord Dependency Plan

## Purpose

This document records the future dependency plan for a read-only Discord Gateway phase.

Phase 23 does not install dependencies. It only documents which library should be considered later and why installation is deferred.

## Why No Dependency Is Installed Yet

The current phase does not connect to Discord, call Discord APIs, run a bot, or send messages.

Installing a Discord library now would make the runtime boundary feel closer than the approved scope. Dependency installation should happen only in a later phase where the runtime entrypoint, token handling, and read-only constraints are reviewed together.

## Recommended Library

Recommended future Python library:

```text
discord.py
```

Reason:

- mature Python ecosystem
- Gateway support
- event listener support
- common documentation and examples
- compatible with a small read-only runtime entrypoint

## Alternatives

Possible alternatives:

- `nextcord`
- `py-cord`

These remain alternatives only. Do not install them in Phase 23.

## Required Intents

Planned future intent review:

- `guilds`: required for basic guild metadata
- `guild_messages`: likely required for read-only message event capture
- `message_content`: manual review required because it exposes message text
- `reactions`: later only
- `members`: later only
- `slash_commands`: later only

## Message Content Risk

`message_content` is more sensitive than basic guild metadata. It should be enabled only after:

- private server scope is confirmed
- mapping validator strict mode passes
- token handling rules are accepted
- message send remains disabled
- audit and rollback plans are reviewed

## Read-Only Runtime Principle

The future read-only runtime may:

- connect to a private test server
- read approved event metadata
- normalize events locally
- create local dispatch plans
- create audit records

It must not:

- send Discord messages
- approve external actions
- post SNS content
- update a homepage
- submit grants
- send emails
- confirm contracts, prices, or delivery dates

## Phase 24 Boundary

The first phase that may install a Discord dependency must still keep:

- `send_messages=false`
- `external_execution=false`
- `human_only_execution=true`
- token values never logged

External execution must not be enabled automatically.

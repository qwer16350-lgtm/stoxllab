# STOXL Read-Only Runtime Stub

## Purpose

The read-only runtime stub defines the shape of a future Discord runtime entrypoint without connecting to Discord.

It does not read a Bot Token, read `.env`, connect to Gateway, call Discord APIs, or send messages.

## Current Behavior

- runtime mode is fixed to `readonly_stub`
- Gateway connection is disabled
- message sending is disabled
- external execution is disabled
- token loading is disabled
- dependency installation is not required now
- preflight readiness is read from the local preflight report

## Future Entry Point Shape

A later approved runtime can use this shape to check preflight readiness before any real connection work. That later phase must still keep send messages disabled and external execution disabled.

## Safety Flags

The stub reports:

- `discord_api_called=false`
- `gateway_connected=false`
- `message_sent=false`
- `external_execution_enabled=false`
- `human_only_execution_preserved=true`

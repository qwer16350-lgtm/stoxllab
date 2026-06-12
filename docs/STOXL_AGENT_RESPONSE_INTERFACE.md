# STOXL Agent Response Interface

## Purpose

The agent response interface defines the schema for future agent response generation.

It does not call an LLM, does not call RAG, and does not generate real agent output in this phase.

## Current Behavior

The interface can build:

- a future response request shape
- a deterministic placeholder response
- a safety report

## Disabled Capabilities

- `llm_enabled=false`
- `rag_enabled=false`
- `response_generated=false`

The placeholder content is:

```text
Agent response generation is disabled in this phase.
```

## Future Conditions

A later LLM/RAG phase must separately define:

- prompt loading
- provider selection
- RAG access policy
- source citation policy
- output guardrails
- Discord send boundary

## Safety Flags

- `llm_called=false`
- `rag_called=false`
- `discord_api_called=false`
- `message_sent=false`
- `external_execution=false`

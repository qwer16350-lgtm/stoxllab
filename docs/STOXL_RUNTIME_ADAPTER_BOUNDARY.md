# STOXL Runtime Adapter Boundary

## 1. Purpose

This repository is not a real Discord or Hermes runtime yet. Phase 12 defines the boundary between the current read-only mock system and a possible future runtime adapter.

Phase 12 does not call the Discord API, connect to Discord Gateway, modify Hermes Gateway code, call an LLM, ingest RAG, access external DB/RAG originals, or execute any external action.

The boundary exists so a future runtime can be designed without weakening the current safety rules.

## 2. Current Read-only Pipeline

The current pipeline is fully local and read-only:

1. Config validation  
   `scripts/validate_stoxl_configs.py`

2. Agent registry loader  
   `scripts/load_stoxl_agent_registry.py`

3. Mock request evaluator  
   `scripts/evaluate_stoxl_mock_request.py`

4. Discord mock event adapter  
   `scripts/evaluate_discord_mock_event.py`

The pipeline reads config, prompts, dry-run JSON, and registry files. It writes only explicit example outputs when `--out` is used.

## 3. Runtime Inbound Event Shapes

A future runtime adapter may receive several inbound event types.

### Discord Message Event

Raw Discord-like message event containing author, channel, mentions, message text, attachments, and timestamp.

### Scheduler Event

Internal schedule event for deadlines, reminders, RAG update notifications, or approval waiting reminders.

### Manual CLI Event

Operator-triggered local event for testing, manual replay, or dry-run evaluation.

### Future RAG Query Event

Future query request that asks whether a specific agent may access a specific source group. This event must never include raw secret values or copied source files.

## 4. Normalized Request Shape

The runtime adapter converts raw inbound events into this normalized request shape:

```json
{
  "text": "",
  "actor_role": "",
  "actor_agent": "",
  "author_display_name": "",
  "source_channel": "",
  "source_category": "",
  "mentioned_agents": [],
  "requested_action": "",
  "requested_source": "",
  "current_status": "",
  "requested_next_status": "",
  "attachments": [],
  "timestamp": ""
}
```

The normalized request is the only shape the evaluator should need. Raw Discord or Hermes event details should stay inside the adapter layer.

## 5. Runtime Output Shape

The evaluator and dispatcher boundary should produce this output shape:

```json
{
  "blocked": false,
  "block_reasons": [],
  "dispatch_to_agent": "",
  "reviewer_agent": "",
  "dispatch_channel": "",
  "final_report_channel": "",
  "approval_required": false,
  "human_only_execution": true,
  "required_handoff": "",
  "status_transition": {},
  "rag_policy": {},
  "recommended_next_action": "",
  "audit_log_payload": {}
}
```

## 6. Adapter Boundary Rule

The runtime adapter has one job: convert raw Discord/Hermes events into normalized requests.

The evaluator has one job: judge the normalized request against routing, approval, permission, RAG, status, and handoff rules.

The dispatcher has one job: prepare a message plan based on evaluator output.

Actual send, publish, submit, upload, email, price confirmation, contract confirmation, or delivery confirmation actions are not automatic. They remain human-only even after approval.

## 7. Safety Principles

- No external execution by agents or bot systems.
- Approval does not create automatic execution.
- Human-only execution remains the default after approval.
- Do not output tokens, API keys, passwords, secrets, Discord IDs, or personal sensitive information.
- Do not copy external DB/RAG source files into the repo.
- Unknown channel or unknown agent dispatch must be blocked.
- Junior shortcut to final approval must be blocked.
- Reze direct order to practical teams must be blocked.
- Any future runtime adapter starts in read-only mode.

## 8. Runtime TODO Before Any Real Connection

- NEEDS_USER_DECISION: Discord guild ID
- NEEDS_USER_DECISION: channel ID mapping
- NEEDS_USER_DECISION: role ID mapping
- NEEDS_USER_DECISION: owner user ID mapping
- NEEDS_USER_DECISION: Hermes config path
- NEEDS_USER_DECISION: runtime logging path
- NEEDS_USER_DECISION: approval interaction method
- NEEDS_USER_DECISION: audit log channel
- NEEDS_USER_DECISION: error handling policy
- NEEDS_USER_DECISION: rate limit handling
- NEEDS_USER_DECISION: message intent scope

## 9. Non-goals

Phase 12 does not create runtime code, Discord adapters, Hermes Gateway changes, RAG ingest, or real bot behavior. It only documents the boundary.

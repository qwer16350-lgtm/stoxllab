# STOXL Actual Private-test Send Safety Gate

Phase 39A safety gate lists the conditions that would be required before a
future actual private-test send. In Phase 39A, the gate never allows execution.

Required condition categories include explicit allow flag, manual approval,
exact approval phrase, private-test reply mode, token/channel presence booleans,
Phase 38E gate availability, frozen payload, rollback readiness, operator
checklist readiness, private-test scope, public/team block, and unattended false.

Phase 39A Hotfix 1 wires the explicit allow flag into CLI parsing. This only
lets the safety report observe `allow_flag_present=true`; all other unmet
conditions still block, and the Phase 39A no-execution policy still prevents
send execution.

Phase 39B Hotfix 2 makes the approval phrase check explicit. The phrase must
match the code constant exactly, but reports must never print that phrase value.
The safety gate may report `raw_required_conditions_met=true`, while actual
send remains disallowed in this hotfix.

Phase 39B Hotfix 3 leaves this safety gate intact and adds a separate execution
intent flag at the one-shot send path. Only when raw required conditions, the
allow flag, and `--execute-actual-private-test-send` are present can the
one-shot report expose `ready_for_actual_private_test_send=true`. The adapter is
still `mock`, and the Discord API send flags remain false.

Phase 39B Final Bundle adds one more lock: the real adapter can be selected only
when `HERMES_PHASE39B_REAL_DISCORD_SEND_EXECUTION=true` and LLM/RAG/embedding
and external execution flags are all false. Codex tests use a fake injected real
adapter only. Fake adapter calls are not Discord API calls and must leave
`discord_api_send_called=false`, `discord_message_sent=false`, and
`message_sent_count=0`.

Safety state:

- Conditions met: false
- Actual send allowed: false
- Actual send executed: false
- Discord API send called: false
- Discord message sent: false
- Secret values logged: false
- Approval phrase value logged: false
- Raw Discord IDs logged: false

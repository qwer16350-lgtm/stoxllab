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

Safety state:

- Conditions met: false
- Actual send allowed: false
- Actual send executed: false
- Discord API send called: false
- Discord message sent: false
- Secret values logged: false
- Approval phrase value logged: false
- Raw Discord IDs logged: false

# STOXL Hermes Production Roadmap

Safe-prep sequence:

1. Phase 41B actual private-test reply one-shot completed exactly once.
2. Phase 41C actual reply closeout and no-repeat lock.
3. Phase 42 supervised deterministic private-test session completed exactly once.
4. Phase 42 actual session closeout and repeat supervised-session lock.
5. Phase 43 routing, rate-limit, cooldown, session lock, and operations stability scaffold.
6. Phase 44 LLM provider preflight, prompt contract, and fake adapter.
7. Phase 45A actual LLM one-shot call preflight gate.
8. Phase 45 actual LLM one-shot call closeout and no-repeat lock.
9. Phase 46 blocked LLM output review policy and no-automatic-retry policy.
10. Phase 47 human-review-only closeout and disabled retry gate design packet.
11. Phase 48A human-review-only final closeout and operator handoff packet.
12. Phase 49 production-readiness audit.
13. Phase 50 final automation architecture lock, roadmap, manual gate matrix,
    and release blocker matrix.
14. Phase 51/52 continuous read-only runtime foundation and review packet base
    from synthetic fixtures only.
15. Phase 52B read-only live capture closeout from the separate operator-run
    Manual Gate.
16. Phase 53 capture-to-review-packet replay for the empty capture and next
    read-only capture canary plan.

Manual Gate 3 is complete: the actual LLM/OpenRouter call succeeded exactly
once, output safety blocked the generated draft, and Discord send stayed
disabled. Phase 41B repeat send, Phase 42 repeat supervised session, and
Phase45 repeat LLM call remain locked. Next sensitive work is Phase46 safe
review of blocked LLM output and retry policy, with no automatic re-call.

Phase47 is now a safe closeout/design stage only. It adds human-review-only
project closeout support and documents a disabled retry gate design. It does not
execute a retry, does not implement retry execution, does not send to Discord,
and does not include full raw blocked output.

Next options after Phase47:

- Option A: human-review-only project closeout
- Option B: Phase48 new retry Manual Gate design
- Option C: Phase48 Discord send review gate design

Phase48A finalizes Option A as human-review-only closeout and adds operator
handoff. It does not implement retry, Discord send review, or production
unattended readiness. Next options after Phase48A:

- Option A: archive / human review only finish
- Option B: Phase48B retry Manual Gate design
- Option C: Phase48C Discord send review gate design
- Option D: Phase49 production-readiness audit

Phase49/50 sets the final direction: STOXL Discord Agent OS. Human-review-only
archive is not the final goal; it is the current safe state. Production
unattended mode remains not ready. The next safe implementation is Phase51/52:
continuous read-only runtime foundation plus review packet base.

Phase51/52 completes that foundation without live runtime. Current automation
level is Level 1 foundation: normalized synthetic events, read-only guard,
session context, deterministic review packet composer, and synthetic replay are
ready. Actual Discord runtime, Discord send, LLM/OpenRouter, RAG,
embedding/vector, scheduler live execution, auto reply, and production
unattended mode remain disabled. Next step is a separate Manual Gate for longer
read-only live runtime with Discord send disabled.

Phase51/52-1 fixes the Manual Gate definition for that next step. The approval
phrase and authoritative environment keys are now documented, and the preflight
reads process env readiness while hiding the phrase value. The launch packet
records the user-run command for the later Manual Gate; this hotfix does not
start it.

Phase52B/53 closes out the successful read-only Gateway connection with zero
captured events and connects the empty capture to the review-packet pipeline.
The empty capture produces zero review packets and is treated as a valid
timeout result, not a failure. The next actual operation is a separate Manual
Gate read-only capture canary with one private-test human message and Discord
send disabled.

Phase54-57 records that canary as successful metadata-only closeout with one
private-test human message captured and one review packet prepared. It adds only
manual-approved reply prep, deterministic mock reply packet prep, supervised
private-test auto-reply safety prep, low-risk team auto-ops policy skeleton, and
scheduler dry-run policy skeleton. Actual runtime, Discord send, LLM/OpenRouter,
RAG, embedding/vector, external execution, scheduler live execution, team
auto-ops, and production unattended mode remain disabled.

Phase58 adds the dedicated actual-path gate for a manual-approved deterministic
private-test reply from the captured canary event. It is not a repeat of the old
Phase39/41 send path and does not send in this hotfix. The next production
roadmap step is a separate Manual Gate for exactly one Phase58 private-test
deterministic reply send, followed by a closeout/no-repeat lock.

Phase59 is now closed out after the separate operator-run supervised
private-test auto-reply short session succeeded exactly once. Repeat Phase59
sessions are locked. Current verified level is
`level3_supervised_private_test_auto_reply_verified`; next target level is
`level4_low_risk_team_channel_canary`. Remaining release blockers are team
canary execution, scheduler live approval, RAG/LLM live reply approval,
production kill-switch live test, git index lock resolution, and
refactor/compaction.

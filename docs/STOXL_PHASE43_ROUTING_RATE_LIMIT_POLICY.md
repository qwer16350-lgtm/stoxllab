# STOXL Phase 43 Routing and Rate-limit Policy

Phase 43 defines routing, rate-limit, cooldown, and lock policy for the future supervised private-test session.

Policy summary:

- Private-test human messages are the only eligible input class.
- Self, bot, duplicate, public, and team inputs are not eligible for send.
- Operator commands are separated from reply flow.
- Per-session max replies, cooldown, one-shot/session locks, and crash-recovery lock placeholders are represented.
- External execution remains false.

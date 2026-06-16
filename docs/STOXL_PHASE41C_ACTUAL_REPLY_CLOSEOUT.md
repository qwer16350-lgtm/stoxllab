# STOXL Phase 41C Actual Reply Closeout

Phase 41C prepares the parser/report scaffold for the future actual private-test reply result. In this bundle it uses no-send and mock fixtures only.

Closeout rules:

- `message_sent_count=1` with `private_test` scope is the only success shape.
- `message_sent_count=0` is accepted as no-send closeout and is not ready for supervised session.
- `message_sent_count>1`, public/team scope, or repeat attempts fail.
- Repeat send remains blocked.
- Self-loop, bot, and duplicate messages are ignored.

No secret values, raw Discord IDs, or raw message content are emitted.

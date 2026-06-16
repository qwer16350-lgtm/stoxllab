# STOXL Phase 40Y Phase 41 Reply Preflight Gate

Phase 40Y designs the Phase 41 actual private-test reply gate without executing
reply/send.

The default state is blocked. A future manual reply path would require token and
private-test channel presence, manual approval, exact approval phrase match,
send/reply flags enabled, `HERMES_DISCORD_REPLY_MODE=private_test_only`,
private-test channel scope, self/bot/duplicate guards, one-shot lock available,
and LLM/RAG/embedding/external flags false.

This phase performs no Discord API send and keeps `message_sent_count=0`.

# STOXL Phase 30 Audit Operations

Phase 30 extends the read-only live event flow into local audit operations.

## Flow

```text
live event
-> visibility event
-> audit record
-> routing report
-> would-send preview
-> review packet
-> daily manifest
```

## What This Phase Does

- stores redacted live event audit records
- summarizes route candidates
- builds deterministic would-send previews
- builds local review packets
- updates daily manifests

## What This Phase Still Does Not Do

- no Discord reply
- no Discord server, channel, or role modification
- no LLM call
- no RAG read or ingest
- no SNS post
- no homepage upload
- no application submission
- no email send
- no contract or price decision

## Phase 31 Candidate

A later Phase 31 may design private test reply behavior. That phase should remain opt-in, require explicit safety review, and keep human-only execution for external actions.

## Phase 31A Viewer

Phase 31A adds a local operations packet viewer for the Phase 30 artifacts. It reads only local logs and exports, supports JSON/Markdown stdout, and keeps Discord reply/send, LLM/RAG, and external execution disabled.

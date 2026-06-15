# STOXL Knowledge Manifest

Phase 34A adds a local text-only manifest for the `knowledge/` folder.

The manifest lists source folders and file metadata only. It does not dump file contents, does not include full content previews, and does not read external source roots.

## Folder Layout

```text
knowledge/
  marketing/
  operation/
  strategy/
  brand/
  archive/
```

`operation` is the canonical source. `operations` is forbidden.

## Manifest Content

The manifest may include:

- source name
- relative path
- extension
- extension status
- size in bytes
- file counts

The manifest must not include:

- full file content
- `.env` content
- API keys or tokens
- raw Discord IDs
- absolute paths
- external source contents

## CLI

```powershell
python apps\hermes_gateway\cli.py --knowledge-manifest --json
python apps\hermes_gateway\cli.py --knowledge-manifest --markdown
```

Safety flags remain false for embedding, LLM, Discord send, and external execution.

# STOXL Discord Agent Calling Guide

Command syntax:

- `!lucy <message>`
- `!marin <message>`
- `!meiko <message>`
- `!kasumi <message>`
- `!reze <message>`
- `!agent <agent_id> <message>`
- `!route <message>`
- `!handoff <target_agent> <message>`
- `!agents`
- `!help`

Default routing:

- `marketing-brief`, `sns-콘텐츠`, `homepage`: Marin by default, Lucy for
  review/final/approval messages.
- `marin-초안`: Marin.
- `lucy-검토`: Lucy.
- `operation-brief`, `공모전-지원사업`: Kasumi by default, Meiko for
  judgment/review/schedule messages.
- `kasumi-리서치`: Kasumi.
- `meiko-검토`, `일정-마감관리`: Meiko.
- `reze-전략기획`, `brand-rag`, `new-business`, `product-ideas`: Reze.
- `대표-회의실`: Reze, Lucy, or Meiko depending on message type.
- `최종-승인요청`: Lucy, Meiko, or Reze report-only routing.

Handoff flow:

- Marin -> Lucy.
- Lucy -> `최종-승인요청`.
- Kasumi -> Meiko.
- Meiko -> `최종-승인요청`.
- Reze -> `대표-회의실`.

Handoff format:

```text
[handoff]
from: marin
to: lucy
source_channel: marin-초안
status: 초안
review_required: true
summary: ...
```

Allowed Discord work:

- Drafting.
- Review.
- Metadata-only routing.
- Approval request reports.
- Discord reply/webhook message only when a separate runtime Manual Gate is
  opened.

Not allowed:

- SNS publish.
- Homepage deploy.
- External email send.
- Grant or competition submit.
- Shell command or external execution.
- Public or unknown channel execution.
- Secret, token, webhook URL, API key, approval phrase, raw Discord ID, or raw
  message content logging.

Dry-run examples:

```powershell
python apps\hermes_gateway\cli.py --company-agent-router-dry-run --json --channel marketing-brief --message "SNS draft"
python apps\hermes_gateway\cli.py --company-agent-router-dry-run --json --channel operation-brief --message "지원사업 후보 찾아줘"
python apps\hermes_gateway\cli.py --company-agent-router-dry-run --json --channel reze-전략기획 --message "신제품 방향 아이디어"
```

Runtime:

```powershell
python apps\hermes_gateway\cli.py --run-company-agent-runtime --json
```

The default runtime command is blocked. Actual runtime requires an explicit
operator action:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="deterministic_fallback"
python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

Runtime v0 uses deterministic fallback first. If webhook persona delivery is
not configured, the bot replies as `HERMES_STOXL` with an agent prefix like
`[MARIN_STOXL / 마린]`. External execution, SNS publish, homepage deploy, email
send, grant submit, RAG, embedding/vector creation, and raw secret/Discord ID
logging remain forbidden.

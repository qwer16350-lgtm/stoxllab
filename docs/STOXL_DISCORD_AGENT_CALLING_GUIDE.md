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
- `!review <message>`
- `!approve-draft <message>`
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

Routing priority:

1. Explicit direct command:
   `!lucy`, `!marin`, `!meiko`, `!kasumi`, or `!reze`.
2. Explicit generic command:
   `!agent <agent_id> <message>`.
3. Workflow command:
   `!handoff`, `!review`, or `!approve-draft`.
4. Exact channel default:
   `meiko-검토` -> Meiko, `lucy-검토` -> Lucy, `marin-초안` -> Marin,
   `kasumi-리서치` -> Kasumi, `reze-전략기획` -> Reze.
5. Keyword route when no explicit command exists.

Example: `!meiko 이 지원사업 넣을만한지 판단해줘` in `meiko-검토`
must route to Meiko with reason `explicit_command`. The `지원사업` keyword
must not override the explicit `!meiko` command.

Discord message normalization:

- The router normalizes message content before routing.
- Leading whitespace, blank lines, Discord channel mentions, channel display
  labels, and quoted display lines may appear before a command.
- The first command line in the message is used for explicit command routing
  even when it is not the first line.
- Example:

```text
#operation-brief
!meiko 이 지원사업 넣을만한지 판단해줘
```

This routes to Meiko with reason `explicit_command`; the `지원사업` keyword does
not override `!meiko`.

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

## Workflow v0.1 Calling Notes

Additional command syntax:

- `!review <message>` routes the message to the senior reviewer for the current
  channel.
- `!approve-draft <message>` creates a metadata-only approval draft for
  `최종-승인요청`.
- `!handoff <target_agent_or_channel> <message>` prepares a handoff draft for
  Lucy, Meiko, Reze, or a known target channel.
- `!agents` lists the five company agents and the senior/junior hierarchy.
- `!help` lists the command syntax.

Workflow v0.1 dry-run examples:

```powershell
python apps\hermes_gateway\cli.py --company-agent-workflow-v01-report --json
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel marketing-brief --message "MML test copy"
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel operation-brief --message "support program research"
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel reze-전략기획 --message "STOXL new product direction"
```

Handoff posting:

- Default: `HERMES_COMPANY_AGENT_HANDOFF_ENABLED=false`.
- Enabled only by operator action:
  `HERMES_COMPANY_AGENT_HANDOFF_ENABLED=true`.
- Dry-runs do not call Discord and do not send handoff posts.

Approval drafts:

- Begin with `[APPROVAL_REQUEST]`.
- Include the writing agent, reviewer, related channel, decision need,
  recommendation, risk, and next action.
- Keep `external_execution_performed=false` even when
  `external_execution_requested=true`.

Operator runtime test environment:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="deterministic_fallback"
$env:HERMES_COMPANY_AGENT_HANDOFF_ENABLED="false"

python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

## Workflow v0.2 Handoff And Approval

Workflow v0.2 adds optional real handoff posting for the live runtime.

Dry-run commands:

```powershell
python apps\hermes_gateway\cli.py --company-agent-handoff-dry-run --json --channel marketing-brief --message "!marin MML 인스타 문구 3개 뽑아줘"
python apps\hermes_gateway\cli.py --company-agent-handoff-dry-run --json --channel kasumi-리서치 --message "!kasumi 올해 12월까지 디자인 지원사업 찾아줘"
python apps\hermes_gateway\cli.py --company-agent-handoff-dry-run --json --channel reze-전략기획 --message "!reze 스톡슬 신규 제품 방향 제안해줘"
python apps\hermes_gateway\cli.py --company-agent-approval-dry-run --json --channel lucy-검토 --message "!approve-draft 이 문구 발행 승인 요청서 만들어줘"
```

Default runtime behavior keeps `HERMES_COMPANY_AGENT_HANDOFF_ENABLED=false`:

- The agent replies only in the current channel.
- The handoff target is shown in the report/dry-run.
- No target channel post is made.

When the operator explicitly sets `HERMES_COMPANY_AGENT_HANDOFF_ENABLED=true`:

- Marin replies in the current channel and posts `[HANDOFF]` to `lucy-검토`.
- Kasumi replies in the current channel and posts `[HANDOFF]` to `meiko-검토`.
- Reze replies in the current channel and posts `[HANDOFF]` to `대표-회의실`.
- Lucy or Meiko approval drafts can post `[APPROVAL_REQUEST]` to
  `최종-승인요청`.

Runtime operator command:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="deterministic_fallback"
$env:HERMES_COMPANY_AGENT_HANDOFF_ENABLED="true"

python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

Channel lookup is by channel name only. Reports do not log token values,
webhook URLs, raw Discord IDs, or channel IDs. Publishing, deployment, email,
grant submission, RAG, embedding/vector creation, and external execution remain
forbidden.

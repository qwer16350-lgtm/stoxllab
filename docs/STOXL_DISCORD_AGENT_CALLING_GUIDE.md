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

## Workflow v0.3 Webhook Persona Mode

Workflow v0.3 lets the live runtime send agent replies through Discord webhook
personas so the visible sender can appear as the company agent.

Agent webhook names:

- Lucy -> `LUCY_STOXL`
- Marin -> `MARIN_STOXL`
- Meiko -> `MEIKO_STOXL`
- Kasumi -> `KASUMI_STOXL`
- Reze -> `REZE_STOXL`

Dry-run commands:

```powershell
python apps\hermes_gateway\cli.py --company-agent-webhook-persona-report --json
python apps\hermes_gateway\cli.py --company-agent-webhook-persona-dry-run --json --agent marin --channel marketing-brief --message "MML 인스타 문구 3개 뽑아줘"
python apps\hermes_gateway\cli.py --company-agent-webhook-persona-dry-run --json --agent lucy --channel lucy-검토 --message "이 문구 검토해줘"
python apps\hermes_gateway\cli.py --company-agent-webhook-persona-dry-run --json --agent reze --channel reze-전략기획 --message "제품 방향 제안해줘"
```

Runtime gates:

```powershell
$env:HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED="false"
$env:HERMES_COMPANY_AGENT_WEBHOOK_CREATE_ENABLED="true"
```

Default persona mode is disabled, so bot-message fallback remains the default.
When `HERMES_COMPANY_AGENT_WEBHOOK_PERSONA_ENABLED=true`, the runtime tries the
agent webhook persona first. If lookup, creation, or send fails, it falls back
to the normal bot message without exposing webhook URL, channel ID, raw Discord
ID, token, or secret values.

Webhook creation happens only in actual runtime when persona mode is enabled
and `HERMES_COMPANY_AGENT_WEBHOOK_CREATE_ENABLED=true`. Dry-runs never create
webhooks and never send Discord messages.

## Workflow v0.4 Real Multi-Bot Agent Fleet

Workflow v0.4 supports five real send-only Discord bot clients so the agent
personas can appear in the online member list.

Fleet roles:

- `HERMES_STOXL`: central routing, handoff, and approval workflow.
- `LUCY_STOXL`: Lucy send-only bot.
- `MARIN_STOXL`: Marin send-only bot.
- `MEIKO_STOXL`: Meiko send-only bot.
- `KASUMI_STOXL`: Kasumi send-only bot.
- `REZE_STOXL`: Reze send-only bot.

Dry-run commands:

```powershell
python apps\hermes_gateway\cli.py --company-agent-real-bot-fleet-report --json
python apps\hermes_gateway\cli.py --company-agent-real-bot-send-dry-run --json --agent marin --channel marketing-brief --message "MML 인스타 문구 3개 뽑아줘"
python apps\hermes_gateway\cli.py --company-agent-real-bot-send-dry-run --json --agent lucy --channel lucy-검토 --message "이 문구 검토해줘"
python apps\hermes_gateway\cli.py --company-agent-real-bot-send-dry-run --json --agent reze --channel reze-전략기획 --message "제품 방향 제안해줘"
```

Runtime gates:

```powershell
$env:HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED="false"
$env:HERMES_COMPANY_AGENT_SENDER_MODE="bot_fallback"
```

Sender modes:

- `bot_fallback`: send as `HERMES_STOXL`.
- `webhook`: webhook persona, then bot fallback.
- `real_bot`: real agent bot, optional webhook fallback, then bot fallback.
- `auto`: real agent bot, webhook, then bot fallback.

Agent bot token env keys:

- `HERMES_DISCORD_LUCY_BOT_TOKEN`
- `HERMES_DISCORD_MARIN_BOT_TOKEN`
- `HERMES_DISCORD_MEIKO_BOT_TOKEN`
- `HERMES_DISCORD_KASUMI_BOT_TOKEN`
- `HERMES_DISCORD_REZE_BOT_TOKEN`

The agent bot clients are send-only. They do not respond to `on_message`, and
the HERMES runtime ignores bot authors to prevent loops and duplicate replies.
Reports show token presence as booleans only and never log token values, channel
IDs, raw Discord IDs, webhook URLs, or API keys.

## Workflow v0.5 Per-Agent LLM Response Mode

Workflow v0.5 adds agent-specific LLM response generation behind a manual gate.
The default remains deterministic fallback:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_LLM_MODE="off"
```

Report and dry-run commands do not call the LLM provider and do not send Discord
messages:

```powershell
python apps\hermes_gateway\cli.py --company-agent-llm-report --json
python apps\hermes_gateway\cli.py --company-agent-llm-diagnostics --json
python apps\hermes_gateway\cli.py --company-agent-llm-dry-run --json --agent marin --message "MML 인스타 문구 3개 뽑아줘"
python apps\hermes_gateway\cli.py --company-agent-llm-dry-run --json --agent lucy --message "이 문구 검토해줘"
python apps\hermes_gateway\cli.py --company-agent-llm-dry-run --json --agent reze --message "제품 방향 제안해줘"
```

User-run actual LLM one-shot gate:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="true"
$env:HERMES_COMPANY_AGENT_LLM_MODE="manual_command_only"

python apps\hermes_gateway\cli.py --company-agent-llm-one-shot --json --agent marin --message "MML 인스타 문구 3개 뽑아줘" --allow-company-agent-llm-call
```

User-run Discord runtime with LLM fallback:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="true"
$env:HERMES_COMPANY_AGENT_LLM_MODE="manual_command_only"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="llm_with_deterministic_fallback"
$env:HERMES_COMPANY_AGENT_HANDOFF_ENABLED="true"
$env:HERMES_COMPANY_AGENT_REAL_BOTS_ENABLED="true"
$env:HERMES_COMPANY_AGENT_SENDER_MODE="real_bot"

python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

LLM calls are limited to manual commands such as `!marin`, `!lucy`, `!meiko`,
`!kasumi`, `!reze`, and `!agent <agent_id>`. Plain auto replies stay
deterministic. If the provider call fails, the runtime falls back to the
deterministic template. RAG, embedding/vector creation, external execution,
automatic posting/submission/email/deployment, token/API key logging, webhook
URL logging, and raw Discord ID logging remain forbidden.

The diagnostics command exposes configuration presence as booleans only. A failed
one-shot reports a short reason code such as `api_key_missing`,
`insufficient_quota`, `timeout`, or `provider_exception`, sets
`response_source=deterministic_fallback`, and includes a redacted preview of the
real deterministic reply. Provider error text, API key values, URLs, and raw IDs
are not included.

## Workflow v0.5.1 Agent Voice Tuning

Agent prompts now require concrete role-specific work instead of generic template
advice. Marin returns at least three placed copy options and Lucy review points.
Lucy gives a publish decision, reasons, direct rewrites, and final-approval status.
Kasumi never invents unknown notices and separates candidate, deadline, materials,
and risk with a latestness caveat. Meiko chooses recommend, hold, or do-not-recommend
and separates conditions, owner, deadline, risk, and next action. Reze gives a
compressed representative-meeting critique covering brand direction, `스톡슬 적합성`,
risk, experimentability, and priority.

The deterministic fallback follows the same output contracts. This tuning does not
change routing, handoff, approval, or real-bot sender behavior. It does not enable
Discord sends, RAG, embeddings, vector indexes, or external execution.

## Workflow v0.5.2 Handoff Context Awareness

The runtime keeps the latest handoff for each target channel in memory. References
such as `방금`, `이 지원사업`, `이 문구`, `위 내용`, and `handoff` select that
channel context. A Discord reply to a `[HANDOFF]` or agent output takes priority over
the latest channel context. Context is cleared whenever the runtime process restarts.

```powershell
python apps\hermes_gateway\cli.py --company-agent-context-simulate-handoff --json --source-agent kasumi --target-agent meiko --target-channel meiko-검토 --content "이번 달 지원사업 후보 초안"
python apps\hermes_gateway\cli.py --company-agent-context-dry-run --json --channel meiko-검토 --message "!meiko 이 지원사업 넣을만한지 판단해줘"
```

The simulation stores and immediately verifies one context in its own process. Since
the store is intentionally in-memory, the standalone dry-run uses a clearly labeled
`dry_run_fixture` when no runtime context exists. Actual runtime responses use only
real handoffs or replied messages. Reports never expose raw Discord IDs or secrets.

## Workflow v0.6 Persistent Work Memory

Company work memory is a local JSONL history, not RAG or vector search. Handoffs,
approval requests, and Lucy/Meiko/Reze decisions are written under
`apps/hermes_gateway/local/company_memory/`. The entire local directory is ignored
by Git. Records contain bounded summaries and content only; tokens, API keys,
webhook URLs, raw Discord IDs, and `.env` values are redacted or omitted.

Discord commands:

```text
!memory recent
!memory handoffs
!memory approvals
!memory decisions
!recall <keyword>
```

Local verification:

```powershell
python apps\hermes_gateway\cli.py --company-agent-memory-report --json
python apps\hermes_gateway\cli.py --company-agent-memory-simulate-write --json --record-type handoff --title "지원사업 후보 정리" --content "카스미가 지원사업 후보를 넘김"
python apps\hermes_gateway\cli.py --company-agent-memory-query --json --query "지원사업"
```

After a runtime restart, context resolution checks the latest 20 persisted handoffs
when no in-memory handoff exists. No memory command calls an LLM, Discord API, RAG,
embeddings, vector indexes, or external execution.

## Workflow v0.7 Role-Scoped Read-Only Web Reference

All five agents may use read-only web references for explicit manual commands when
both web-reference environment gates are enabled. Each agent stays inside its role:
Kasumi discovers research candidates, Meiko verifies operational facts, Marin studies
content references, Lucy reviews publication risk, and Reze checks market and strategy
context. The default remains disabled/off.

```powershell
python apps\hermes_gateway\cli.py --company-agent-web-reference-report --json
python apps\hermes_gateway\cli.py --company-agent-web-reference-dry-run --json --agent kasumi --message "이번 달 디자인 지원사업 후보 찾아줘"
python apps\hermes_gateway\cli.py --company-agent-web-reference-dry-run --json --agent reze --message "로우테크 가구 시장 방향성 봐줘"
```

User-approved read-only one-shot:

```powershell
$env:HERMES_COMPANY_AGENT_WEB_REFERENCE_ENABLED="true"
$env:HERMES_COMPANY_AGENT_WEB_REFERENCE_MODE="manual_command_only"
python apps\hermes_gateway\cli.py --company-agent-web-reference-one-shot --json --agent kasumi --message "이번 달 디자인 지원사업 후보 찾아줘" --allow-web-reference
```

Supported providers are configured separately as `serper`, `brave`, or `tavily`.
Provider failures expose only bounded reason codes. Search results include source URLs
and a latestness caveat, are stored as `web_reference` recent items, and flow through
normal handoffs. Generic commands are `!web`, `!search`, `!research`, `!find`, and
`!검증`. Searching and reading are allowed; login, form input, download,
application, submission, email, publish, payment, RAG, embeddings, vectors, and any
external execution remain forbidden.

# STOXL Discord Company Agent OS v0

STOXL Discord Company Agent Layer v0 turns the existing Hermes safety/report
backend into a five-agent company workflow. This is not production unattended
mode.

Agents:

- Marin / 마린 / marketing junior: SNS, homepage, and content drafts.
- Lucy / 루시 / marketing senior: marketing review and final approval request
  reports.
- Kasumi / 카스미 / operation junior: grant, support, and business research.
- Meiko / 메이코 / operation senior: support decision, schedule, and risk
  review.
- Reze / 레제 / strategy lead: strategy planning, brand interpretation, and
  product/business critique.

Hierarchy:

- Marin -> Lucy -> final approval request.
- Kasumi -> Meiko -> final approval request.
- Reze -> decision meeting / decision makers.

Discord channel map:

- `00-결정권자`: `공지-결정사항`, `대표-회의실`, `최종-승인요청`
- `10-마케팅팀`: `marketing-brief`, `lucy-검토`, `marin-초안`, `sns-콘텐츠`, `homepage`
- `20-운영팀`: `operation-brief`, `meiko-검토`, `kasumi-리서치`, `공모전-지원사업`, `일정-마감관리`
- `30-전략기획실`: `reze-전략기획`, `brand-rag`, `new-business`, `product-ideas`
- `90-archive`: `완료된-안건`, `보류된-안건`, `폐기된-안건`
- `99-HERMES-TEST`: `hermes-private-test`, `hermes-canary`

Webhook personas:

- `LUCY_STOXL`
- `MARIN_STOXL`
- `MEIKO_STOXL`
- `KASUMI_STOXL`
- `REZE_STOXL`

Automatic work:

- Marin creates drafts and hands off to Lucy.
- Lucy reviews and creates final approval request reports.
- Kasumi creates candidate/research packets and hands off to Meiko.
- Meiko classifies recommendation, hold, or not recommended and prepares
  approval requests.
- Reze reports strategy opinions to the decision meeting.

Supported work:

- Marin: SNS/homepage/content draft.
- Lucy: marketing review and publish-readiness judgment.
- Kasumi: grant/support/business research.
- Meiko: support judgment, schedule, and risk review.
- Reze: strategy planning, brand analysis, and idea critique.

What is not allowed:

- SNS publish.
- Homepage deploy.
- Email send.
- Grant or competition submit.
- External command execution.
- Secret, webhook URL, raw Discord ID, approval phrase, or API key logging.
- Agent final approval without decision maker approval.

Setup dry-run:

```powershell
python scripts\setup_discord_company_os.py --dry-run --json
```

Dry-run does not call the Discord API.

Actual setup command prepared for the operator:

```powershell
python scripts\setup_discord_company_os.py --execute --allow-actual-discord-setup --json
```

Actual setup requests include `User-Agent: STOXL-Hermes-Gateway (local setup)`
and `Authorization: Bot <token>`. Reports expose token and guild ID presence
only; token values, guild ID values, webhook URLs, and raw Discord IDs are not
logged. HTTPError responses are reported with status and safe blocked reasons
such as `discord_api_unauthorized`, `discord_api_forbidden`,
`discord_guild_not_found_or_inaccessible`, or `discord_rate_limited`.

Runtime report and dry-run:

```powershell
python apps\hermes_gateway\cli.py --company-agent-org-report --json
python apps\hermes_gateway\cli.py --company-agent-router-dry-run --json --channel marketing-brief --message "SNS draft"
```

Actual runtime command prepared for the operator:

```powershell
python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

Default runtime remains blocked without the allow flag. With the allow flag and
`DISCORD_BOT_TOKEN` present, the runtime starts a Discord Gateway loop using the
single `HERMES_STOXL` bot account. The first runtime mode is deterministic
fallback:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="deterministic_fallback"
python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

The bot processes `!lucy`, `!marin`, `!meiko`, `!kasumi`, `!reze`, `!agent`,
`!route`, `!handoff`, `!agents`, and `!help` in known STOXL company channels.
If webhook personas are not configured, v0 replies as a normal bot message with
an agent prefix such as `[MARIN_STOXL / 마린]`. SNS publishing, homepage deploy,
email send, grant submit, RAG, embedding/vector creation, and external command
execution remain disabled.

## Workflow v0.1

Workflow v0.1 adds upgraded deterministic work templates, optional handoff
posting, approval draft reports, and command-level workflow helpers.

Report and dry-run commands:

```powershell
python apps\hermes_gateway\cli.py --company-agent-workflow-v01-report --json
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel marketing-brief --message "SNS draft"
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel operation-brief --message "support program research"
python apps\hermes_gateway\cli.py --company-agent-workflow-dry-run --json --channel reze-전략기획 --message "new product direction"
```

Template upgrades:

- Marin creates draft candidates and hands off to `lucy-검토`.
- Lucy reviews marketing output and prepares final approval drafts when needed.
- Kasumi creates research candidates with deadline, materials, and risk, then
  hands off to `meiko-검토`.
- Meiko returns recommendation, hold, or not recommended with execution
  conditions and risk.
- Reze provides strategy judgment and reports to `대표-회의실`.

Workflow commands:

- `!handoff <target_agent_or_channel> <message>`
- `!review <message>`
- `!approve-draft <message>`
- `!agents`
- `!help`

Handoff posting is supported but disabled by default:

```powershell
$env:HERMES_COMPANY_AGENT_HANDOFF_ENABLED="false"
```

Only an operator-set `HERMES_COMPANY_AGENT_HANDOFF_ENABLED=true` enables a live
runtime handoff post to the target channel. Dry-runs never call Discord and
only report the target channel.

Approval drafts begin with `[APPROVAL_REQUEST]` and remain metadata-only. If a
request asks for publishing, deployment, submission, email, or another external
action, the draft can mark `external_execution_requested=true`, but it keeps
`external_execution_performed=false`.

Recommended operator runtime environment for v0.1:

```powershell
$env:HERMES_COMPANY_AGENT_LLM_ENABLED="false"
$env:HERMES_COMPANY_AGENT_REPLY_MODE="deterministic_fallback"
$env:HERMES_COMPANY_AGENT_HANDOFF_ENABLED="false"

python apps\hermes_gateway\cli.py --run-company-agent-runtime --json --allow-company-agent-runtime
```

The bot command set is `!lucy`, `!marin`, `!meiko`, `!kasumi`, `!reze`,
`!agent`, `!route`, `!handoff`, `!review`, `!approve-draft`, `!agents`, and
`!help`. SNS publishing, homepage deploy, email send, grant submit, RAG,
embedding/vector creation, and external command execution remain disabled.

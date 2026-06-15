# STOXL Actual One-shot LLM Draft Call

Phase 36D adds a manually gated path for one Kasumi review-only LLM draft call.
The default CLI path is blocked and does not call OpenRouter.

## Scope

- Agent: `kasumi`
- Source: `operation`
- Citation: `knowledge/operation/stoxl_operation_tone_sample.md`
- Provider: `openrouter`
- Model: `openai/gpt-5.4-mini`
- Discord send: disabled
- Embedding/vector creation: disabled
- External execution: disabled
- Public/team reply: disabled
- Unattended auto reply: disabled

## Manual Gate

The actual call can be attempted only when all gates pass:

- `--allow-actual-one-shot-llm-draft-call` is present
- `HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVED=true`
- `HERMES_PRIVATE_TEST_ONE_SHOT_LLM_DRAFT_APPROVAL_PHRASE` exactly matches the documented operator phrase
- `OPENROUTER_API_KEY` or `HERMES_OPENROUTER_API_KEY` is present
- Phase 36A candidate is `kasumi`
- Phase 36B output safety rehearsal passed
- Source is `operation`, not `operations`

The approval phrase value and API key value are never printed in reports or
Markdown output. Reports only include boolean gate results.

## CLI

Default blocked report:

```powershell
python apps\hermes_gateway\cli.py --actual-one-shot-llm-draft-call --json
python apps\hermes_gateway\cli.py --actual-one-shot-llm-draft-call --markdown
```

Manual one-call path, to be run only after explicit operator approval:

```powershell
python apps\hermes_gateway\cli.py --actual-one-shot-llm-draft-call --json --allow-actual-one-shot-llm-draft-call
```

## Output Safety

The response must remain review-only, include the operation citation, avoid
secret values, avoid raw Discord IDs, avoid approval phrases, and avoid public
or team channel send instructions. Passing output safety still does not make the
result ready for Discord send.

## Safety Guarantees

- LLM call count is capped at one.
- Discord API send is never called.
- `ready_for_discord_send=false` is preserved after success.
- `ready_for_unattended_auto_reply=false` is preserved after success.
- Response packet content is preview-only; full content dumps are not included.

## Phase 36E Follow-up

Phase 36E records the observed one-shot LLM draft result as a report-only
closeout. It does not call OpenRouter again, attempt another LLM API call, send
Discord messages, or unlock a Discord send phase.

Phase 36F-G then locks the result as a no-send state and updates dashboard /
sentinel visibility. Phase 37 remains gated and report-only.

Phase 37A-C may package the draft for human review and preview send gates, but
does not send the draft to Discord.

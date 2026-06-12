# STOXL Hermes Environment Variables

Phase 2 creates documentation and configuration only. Do not create a real `.env` file in this phase.

| variable_name | required | example_value | purpose | used_by | secret_or_not | notes |
|---|---:|---|---|---|---|---|
| DISCORD_BOT_TOKEN | true | TODO | Discord bot login token | Future Discord gateway | secret | Store only in `.env`; never commit real value. |
| OPENAI_API_KEY | true | TODO | LLM/API calls | Future Hermes agent runtime | secret | Store only in `.env`; never commit real value. |
| DISCORD_GUILD_ID | true | TODO | Discord server identifier | Approval and channel mapping | secret_or_internal_id | TODO placeholder only. |
| OWNER_KIM_DISCORD_ID | true | TODO | Identifies 김태호_STOXL for approval checks | Approval gate | secret_or_internal_id | TODO placeholder only. |
| OWNER_LEE_DISCORD_ID | true | TODO | Identifies 이주호_STOXL for approval checks | Approval gate | secret_or_internal_id | TODO placeholder only. |
| HERMES_CONFIG_PATH | true | TODO | Root for Hermes config loading | Future Hermes runtime | not_secret | NEEDS_USER_DECISION: final config path. |
| STOXL_WORKSPACE_PATH | true | C:\tmp\STOXL_LAB | Current repository workspace | Config and docs | not_secret | Current confirmed repo path. |
| RAG_BASE_PATH | true | TODO | Local canonical RAG workspace root | RAG policy/config | not_secret | Should point to repo-local RAG metadata area, not copied source DB. |
| STOXL_DB_ROOT | true | Z:\TODO | Mapped-drive source DB root | External source lookup | not_secret | User-session dependent; UNC is preferred at runtime. |
| STOXL_DB_ROOT_UNC | true | \\NAS\stoxl\TODO | UNC source DB root | External source lookup | not_secret | Preferred runtime form. |
| STOXL_RAG_SOURCE_ROOT | true | Z:\TODO | Mapped-drive RAG source root | RAG indexing/search | not_secret | Do not copy source files into repo. |
| STOXL_RAG_SOURCE_ROOT_UNC | true | \\NAS\stoxl\TODO | UNC RAG source root | RAG indexing/search | not_secret | Preferred runtime form. |
| STOXL_BRAND_SOURCE_ROOT | true | Z:\TODO | Brand source material root | RAG brand source group | not_secret | External path only. |
| STOXL_MARKETING_SOURCE_ROOT | true | Z:\TODO | Marketing source material root | RAG marketing source group | not_secret | External path only. |
| STOXL_OPERATION_SOURCE_ROOT | true | Z:\TODO | Operation source material root | RAG operation source group | not_secret | Uses singular `operation`. |
| STOXL_STRATEGY_SOURCE_ROOT | true | Z:\TODO | Strategy source material root | RAG strategy source group | not_secret | External path only. |
| STOXL_SHARED_SOURCE_ROOT | true | Z:\TODO | Shared source material root | RAG shared source group | not_secret | External path only. |
| DEFAULT_TIMEZONE | false | Asia/Seoul | Notification and reporting timezone | Scheduler rules | not_secret | Fixed by source workbook. |
| EXTERNAL_EXECUTION_ENABLED | false | false | Global external execution gate | Approval guard | not_secret | Must default to false. |
| SNS_PUBLISH_ENABLED | false | false | SNS publish feature gate | Approval guard | not_secret | Do not implement publishing in Phase 2. |
| HOMEPAGE_DEPLOY_ENABLED | false | false | Homepage deploy feature gate | Approval guard | not_secret | Do not implement deploy in Phase 2. |
| EMAIL_SEND_ENABLED | false | false | External email feature gate | Approval guard | not_secret | Do not implement sending in Phase 2. |
| WEB_SEARCH_ENABLED | false | true | Enables research/search workflows later | Research agents | not_secret | Configuration only in Phase 2. |

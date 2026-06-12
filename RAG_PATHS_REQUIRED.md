# STOXL External DB/RAG Path Policy

The STOXL source database and original RAG materials must remain outside this repository. Do not copy source DB/RAG files into `C:\tmp\STOXL_LAB`, and do not include them in Git tracking.

External source paths must be referenced through environment variables only. Mapped drive paths such as `Z:\` are acceptable for local operator convenience, but they depend on the active Windows user session. Runtime configuration should prefer UNC paths such as `\\NAS\stoxl\...` whenever possible.

Original materials are read from external paths. Any future generated index/cache artifacts must be treated as derived data and should be excluded from Git. Phase 2 does not modify `.gitignore`; add ignore rules later only after the concrete index/cache paths are known.

The canonical repo-local RAG folder for operations is `rag\operation`. Use `operation`, not `operations`, even when older workbook text uses the plural form.

## Source Groups

| source_group | env_key | mapped_drive_example | unc_fallback_env_key | repo_canonical_folder |
|---|---|---|---|---|
| brand | STOXL_BRAND_SOURCE_ROOT | Z:\TODO | STOXL_RAG_SOURCE_ROOT_UNC | rag\brand |
| marketing | STOXL_MARKETING_SOURCE_ROOT | Z:\TODO | STOXL_RAG_SOURCE_ROOT_UNC | rag\marketing |
| operation | STOXL_OPERATION_SOURCE_ROOT | Z:\TODO | STOXL_RAG_SOURCE_ROOT_UNC | rag\operation |
| strategy | STOXL_STRATEGY_SOURCE_ROOT | Z:\TODO | STOXL_RAG_SOURCE_ROOT_UNC | rag\strategy |
| shared | STOXL_SHARED_SOURCE_ROOT | Z:\TODO | STOXL_RAG_SOURCE_ROOT_UNC | rag\shared |

## Agent Access

| agent | allowed_source_groups | notes |
|---|---|---|
| lucy | brand, marketing, shared | Brand tone and marketing review context. |
| marin | brand, marketing, shared | Draft and reference research context. |
| meiko | operation, shared | Grants, competitions, schedules, and operational checks. |
| kasumi | operation, shared | External opportunity research and condition capture. |
| reze | brand, marketing, operation, strategy, shared | Full RAG access for strategy, excluding sensitive material. |

Tokens, passwords, API keys, private IDs, and personal sensitive information must not be exposed in any RAG answer by any agent.

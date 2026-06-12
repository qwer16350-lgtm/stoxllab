# STOXL Routing and Workflow Spec

## 1. 목적

이 문서는 Phase 5의 routing/workflow dry-run spec입니다. 실제 실행 코드가 아니며, Discord 서버에 어떤 변경도 적용하지 않습니다. Discord API 호출, Bot Token 사용, 실제 `.env` 생성, 외부 DB/RAG 원본 접근은 이 Phase 범위가 아닙니다.

Phase 5 기준으로 Phase 4의 결정 필요 항목은 다음처럼 확정합니다.

- 실제 Discord server/guild target은 아직 미확정입니다. `.env.example`의 `DISCORD_GUILD_ID=TODO`를 유지합니다.
- role_id는 영어 snake_case를 사용하고, 사람이 보는 표시명은 한국어 또는 한국어 병기를 허용합니다.
- Decision Maker는 `can_approve=true`만 가지며 `can_execute_external_actions=false`입니다.
- 승인 후에도 봇이 외부 게시, 제출, 발송, 계약성 실행을 직접 하지 않습니다. 외부 실행은 human-only action입니다.

## 2. 전체 흐름 요약

- 마케팅팀: 마린 -> 루시 -> 결정권자
- 운영팀: 카스미 -> 메이코 -> 결정권자
- 전략기획실: 레제 -> 결정권자

후임 에이전트는 초안, 검색, 조건 정리를 담당합니다. 선임 에이전트는 검토, 판단, 보고를 담당합니다. 결정권자는 공식 승인만 담당하며, 실제 외부 실행은 사람이 별도로 수행합니다.

## 3. 요청 유형별 담당자

| 요청 유형 | 1차 담당 | 검토 담당 | 최종 보고 채널 | 승인 필요 |
|---|---|---|---|---|
| SNS 초안 | 마린 | 루시 | 최종-승인요청 | 게시 전 true |
| 홈페이지 문구 | 마린 | 루시 | lucy-검토 또는 최종-승인요청 | 업로드/반영 전 true |
| 마케팅 전략 | 마린 | 루시 | marketing-brief 또는 대표-회의실 | 외부 실행 전 true |
| 공모전/지원사업 검색 | 카스미 | 메이코 | meiko-검토 | 검색 단계 false |
| 지원 여부 판단 | 메이코 | 없음 | 최종-승인요청 | 제출/외부 연락 전 true |
| 일정/마감 관리 | 카스미 | 메이코 | 일정-마감관리 | 외부 약속 전 true |
| 전략/제품/사업 아이디어 | 레제 | 없음 | 대표-회의실 | 공식 방향/외부 실행 전 true |
| 레제의 타부서 전략 의견 | 레제 | 관련 선임 | 대표-회의실 또는 관련 팀 brief | false |

## 4. 승인 게이트

다음 작업은 반드시 김태호_STOXL과 이주호_STOXL의 승인이 필요합니다.

- `sns_publish`
- `homepage_upload`
- `competition_submit`
- `grant_submit`
- `external_email_send`
- `price_confirm`
- `contract_confirm`
- `delivery_schedule_confirm`
- `official_brand_direction_confirm`
- `external_collaboration_condition_confirm`

승인 요청은 `최종-승인요청`으로 올립니다. Discord User ID는 실제 값을 문서나 코드에 쓰지 않고 환경변수 키로만 참조합니다.

- `OWNER_KIM_DISCORD_ID=TODO`
- `OWNER_LEE_DISCORD_ID=TODO`

승인 후에도 봇은 직접 실행하지 않습니다. 다음 행동은 사람이 실행하거나, 나중 별도 수동 실행 Phase에서 다시 검토합니다.

## 5. 금지 Shortcut

- 마린이 루시 검토 없이 `최종-승인요청`으로 직접 올리는 것 금지
- 마린이 최종 발행 문구를 확정하는 것 금지
- 카스미가 메이코 검토 없이 최종 추천하는 것 금지
- 카스미가 source_url 없는 외부 정보를 확정 사실처럼 보고하는 것 금지
- 레제가 마케팅팀/운영팀에 직접 명령하는 것 금지
- 레제가 루시나 메이코의 최종 판단을 덮어쓰는 것 금지
- 루시가 승인 없이 SNS 게시 또는 홈페이지 반영을 진행하는 것 금지
- 메이코가 승인 없이 제출 또는 외부 연락을 진행하는 것 금지
- 어떤 에이전트도 외부 게시, 제출, 이메일 발송, 계약성 확정을 직접 실행하는 것 금지

## 6. 상태 태그 흐름

상태 태그는 다음 값을 사용합니다.

- 발견됨
- 초안
- 검토중
- 수정필요
- 추천
- 비추천
- 보류
- 승인대기
- 승인됨
- 진행중
- 완료
- 폐기
- 아카이브

대표 흐름:

- 리서치 후보: `발견됨` -> `검토중` -> `추천` 또는 `보류` 또는 `비추천`
- 마케팅 초안: `초안` -> `검토중` -> `수정필요` 또는 `승인대기`
- 승인 필요 안건: `승인대기` -> `승인됨` 또는 `보류` 또는 `폐기`
- 종료 안건: `완료` 또는 `보류` 또는 `폐기` -> `아카이브`

`승인됨`은 봇 실행 허가가 아닙니다. 사람의 실행 또는 별도 수동 실행 검토로 넘어갈 수 있다는 의미입니다.

## 7. Archive 흐름

Archive는 완료, 보류, 폐기된 안건을 보관하는 용도입니다.

- `완료된-안건`: 완료된 업무
- `보류된-안건`: 당장 진행하지 않는 업무. 보류 사유 필요
- `폐기된-안건`: 진행하지 않기로 결정한 업무. 폐기 사유 필요

후임 봇은 직접 archive 이동을 확정할 수 없습니다. 마케팅 안건은 루시 또는 결정권자, 운영 안건은 메이코 또는 결정권자, 전략 안건은 레제 또는 결정권자가 archive 기록을 정리합니다.

## 8. RAG와 외부 DB 관련 원칙

이번 Phase에서는 RAG나 외부 DB 원본을 읽지 않습니다.

DB/RAG 원본은 repo 내부로 복사하지 않습니다. 나중 Phase에서 연결하더라도 환경변수 기반 경로로만 접근합니다. `Z:\` 경로는 사용자 세션에 의존하므로 런타임에서는 UNC 경로 사용을 우선 검토합니다.

토큰, 비밀번호, API key, Discord ID, 개인 민감정보는 RAG 응답이나 보고에 노출하지 않습니다.

## 9. 실제 Discord 적용 전 TODO

- NEEDS_USER_DECISION: `DISCORD_GUILD_ID` 확정
- NEEDS_USER_DECISION: `OWNER_KIM_DISCORD_ID` 확정
- NEEDS_USER_DECISION: `OWNER_LEE_DISCORD_ID` 확정
- NEEDS_USER_DECISION: role display name 최종 확인
- NEEDS_USER_DECISION: 실제 서버 적용 승인

## 10. Dry-run 산출물

- `discord/routing_workflow.dryrun.json`: 요청 유형별 라우팅 정의
- `discord/approval_gate.dryrun.json`: 승인 게이트와 human-only execution 원칙
- `discord/handoff_rules.dryrun.json`: 에이전트 간 인계 규칙

이 파일들은 검토용입니다. 실제 Discord 적용 스크립트가 아닙니다.

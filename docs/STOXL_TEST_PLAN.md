# STOXL Hermes Dry-run Test Plan

## 1. 목적

이 문서는 실행 테스트 코드가 아니라 STOXL Hermes Discord Agent Organization의 dry-run 검증 계획입니다. Phase 6에서는 JSON 테스트 명세와 사람이 읽는 계획만 작성하며, 실제 테스트 러너나 `.py`, `.js`, `.ts` 테스트 파일은 만들지 않습니다.

## 2. 테스트 범위

Phase 6의 검증 범위는 다음입니다.

- routing: 요청 유형이 올바른 1차 담당, 검토자, 최종 채널로 흐르는지 확인
- permission: 에이전트 권한과 금지 행동이 지켜지는지 확인
- approval gate: 외부 실행/계약성 행동이 승인대기로 전환되는지 확인
- handoff: 후임 -> 선임 -> 결정권자 인계 payload가 맞는지 확인
- RAG access: 에이전트별 source group 제한과 민감정보 제외 원칙 확인
- tone: 에이전트별 업무용 말투 기준 확인
- status transition: 상태 태그 전이가 허용 범위 안에 있는지 확인

## 3. 테스트하지 않는 것

Phase 6에서는 다음을 테스트하지 않습니다.

- 실제 Discord API 호출
- 실제 Discord 서버 변경
- 실제 봇 실행
- 실제 외부 게시, 제출, 이메일 발송
- 실제 계약, 가격, 납기 확정
- 실제 RAG 원본 접근
- 실제 DB ingest
- 실제 `.env` 생성 또는 비밀값 검증

## 4. 핵심 검증 원칙

### 조직 흐름

- 마케팅팀: 마린 -> 루시 -> 결정권자
- 운영팀: 카스미 -> 메이코 -> 결정권자
- 전략기획실: 레제 -> 결정권자

마린과 카스미는 후임으로서 초안, 검색, 정리를 담당합니다. 루시와 메이코는 선임으로서 검토, 판단, 보고를 담당합니다. 레제는 독립 전략 에이전트이며 전략 의견은 가능하지만 실무 명령은 불가합니다.

### External Execution 금지

모든 agent는 `L5_External_Execute=false`, `L6_Final_Approval=false`입니다. Decision Maker도 `can_execute_external_actions=false`로 유지합니다.

외부 게시, 제출, 이메일, 계약성 행동은 봇이 직접 실행하지 않습니다.

### Human-only Execution

승인 후에도 봇이 실행하지 않습니다. 승인 후 다음 행동은 사람이 실행하거나, 나중 별도 수동 실행 Phase에서 다시 검토합니다.

### RAG Source 제한

- lucy: brand, marketing, shared
- marin: brand, marketing, shared
- meiko: operation, shared
- kasumi: operation, shared
- reze: brand, marketing, operation, strategy, shared

외부 DB/RAG 원본은 repo 내부로 복사하지 않습니다. 나중에 연결하더라도 환경변수 기반 경로로만 연결합니다.

### 민감정보 노출 금지

토큰, 비밀번호, API key, Discord ID, 개인 민감정보는 응답, 보고, RAG 결과에 노출하지 않습니다.

### 에이전트별 말투 차이

- 루시: 차분하고 짧은 존댓말. 느낌표/이모티콘 과사용 금지
- 마린: 밝고 적극적인 존댓말. 초안/후보/검토용 표현 유지
- 메이코: 단호하고 실무적인 존댓말. 마감/리스크를 분명히 말함
- 카스미: 조심스럽고 성실한 존댓말. 확인 상태와 불확실성 분리
- 레제: 부드럽지만 날카로운 존댓말. 전략 의견은 가능하나 실무 명령 금지

## 5. Dry-run Spec Files

- `tests/stoxl/routing_guardrails.dryrun.json`: 라우팅 시나리오
- `tests/stoxl/permission_guardrails.dryrun.json`: 권한 위반 시나리오
- `tests/stoxl/approval_gate_guardrails.dryrun.json`: 승인 게이트 시나리오
- `tests/stoxl/handoff_guardrails.dryrun.json`: 인계 payload 시나리오
- `tests/stoxl/rag_access_guardrails.dryrun.json`: RAG 접근 제한 시나리오
- `tests/stoxl/tone_guardrails.dryrun.json`: 말투 기준 시나리오
- `tests/stoxl/status_transition_guardrails.dryrun.json`: 상태 전이 시나리오

## 6. Phase 7 이후 실제 테스트 코드 전환 TODO

- NEEDS_USER_DECISION: 테스트 프레임워크 선택
- NEEDS_USER_DECISION: Discord mock 방식 선택
- NEEDS_USER_DECISION: config loader 구현 여부
- NEEDS_USER_DECISION: prompt loader 구현 여부
- NEEDS_USER_DECISION: approval gate evaluator 구현 여부
- NEEDS_USER_DECISION: RAG access evaluator 구현 여부
- NEEDS_USER_DECISION: 상태 전이 evaluator 구현 여부

## 7. Current Open Values

- `DISCORD_GUILD_ID=TODO`: 실제 서버 적용 Phase 전까지 유지
- `OWNER_KIM_DISCORD_ID=TODO`: 실제 서버 적용 Phase 전까지 유지
- `OWNER_LEE_DISCORD_ID=TODO`: 실제 서버 적용 Phase 전까지 유지
- 실제 서버 적용 승인: 아직 없음

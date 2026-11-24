# Codex instruction — WI-005: 장비·요소석 추천과 승인 후 원작 장착 통합

Act as the implementation owner for one bounded batch.

## Context

- Repository root: `P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908`
- Work item: `docs/agentic-workflow/work-items/WI-005.md`
- Dependencies: None

Read first:

1. Repository instructions such as `AGENTS.md`.
2. The work-item file above.
3. The exact canonical sections linked by that work item.
4. Existing affected code and tests.

## Objective

모드 토글, 잠금 슬롯, 세 가지 추천 기준, 재고와 취소 보존 및 원작 확인 절차를 최신 빌드에 추가한다

## Scope

Follow the work item's **In scope** and **Out of scope** sections. Do not begin later work items.

## Acceptance and verification

Meet every acceptance criterion and perform every required verification in the work item. Preserve unrelated user changes.

If implementation requires a material architecture or scope change, record the conflict and stop at the smallest safe boundary rather than silently changing the design.

## Completion report

Return:

1. status: implemented, partial, or blocked;
2. changed, created, and deleted files;
3. concise implementation decisions;
4. tests/checks run and exact results;
5. evidence for each acceptance criterion;
6. deviations, known risks, and recommended reviewer focus;
7. before/after commit IDs when Git is used.

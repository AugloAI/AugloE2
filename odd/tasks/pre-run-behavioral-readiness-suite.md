# Build the Pre-Run Behavioral Readiness Tracer

## Intent

Add the smallest executable vertical slice toward the canonical 20-behavior Pre-Run Behavioral Readiness Suite. The slice runs the existing versioned Bounded Session Termination fixture through one `ConversationCandidate`, emits a deterministic readiness result bound to the supplied suite and Behavior Hash identities, and remains `not_ready` while the other 19 canonical behaviors are uncovered.

## Authority and provenance

- Canonical product contract: `project/e2.yaml`.
- Canonical vocabulary: `CONTEXT.md`.
- Previous reviewed boundary: `b73b728` on `feature/executable-e2-bakeoff`.
- Initial tracer branch: `feature/pre-run-readiness-tracer`.
- Current chained work-unit branch: `feature/readiness-evidence-completeness`.
- Native review for the preceding T5 slice closed approved as lineage `review-0fbb2035fde10e28`.

## Confirmed public seam

The founder confirmed this public Interface before TDD:

```python
PreRunReadinessSuite.run(
    candidate: ConversationCandidate,
    request: ReadinessRequest,
) -> ReadinessResult
```

The Module owns the canonical versioned behavior inventory internally. Scenario construction and deterministic assertions remain implementation details. The first slice reuses the existing `ConversationCandidate` Adapter seam and does not add a public scenario Interface.

## Required behavior

- Execute the existing `bounded-session-termination` scenario version `1.0` for one candidate.
- Bind suite version, supplied Behavior Hash, evaluation timestamp, runner identity/version, scenario result, stable evidence references, and coverage into a deterministic evidence digest.
- Report `not_ready` while any canonical behavior lacks a passing mandatory scenario; this slice must name the 19 missing behaviors.
- Preserve mandatory scenario failure as readiness-blocking.
- Preserve diagnostic scenario failure without making diagnostics sufficient for readiness.
- Bind, but do not claim to validate, the supplied Behavior Hash.
- Produce the same result and digest for identical candidate behavior and request data.
- Add `behavior-evidence-completeness` scenario version `1.0` for the existing controlled duration path only.
- Derive evidence-completeness coverage independently from the evaluator-owned named gate, so duration failure does not erase valid evidence coverage and incomplete evidence cannot claim coverage.
- Move successful fake candidates to exactly 2 covered and 18 missing canonical behaviors while remaining `not_ready`.

## Scope decision

The founder confirmed that evidence-completeness v1.0 covers only the currently executable controlled duration path. It does not claim general completeness across future paths or artifacts. Broader use-case and ADR ideation follows this work unit as a separate read-only design phase.

## Non-goals

- No provider, model, voice, transport, deployment, telemetry, storage, or test-framework selection.
- No real telephony, live appointment Adapter, legal sufficiency claim, or production readiness claim.
- No implementation of the other 19 behaviors.
- No winner selection or ranking.
- No CLI/report refactor unless required by the confirmed Interface.
- No sensitive evidence or controlled-storage location in Git.

## Work tasks

- [x] T1 — Implement and verify the readiness tracer as one reviewable vertical slice.
  - Route: delegated bounded writer with strict RED/GREEN through the confirmed public Interface, followed by independent verification.
  - Final edit surfaces: `src/auglo_e2_bakeoff/readiness.py`, `src/auglo_e2_bakeoff/__init__.py`, `tests/test_pre_run_readiness.py`, `README.md`, `project/e2.yaml`, and this task record.
  - TDD evidence: RED first failed because `PreRunReadinessSuite` was absent; GREEN passed the bounded scenario with the exact 19-behavior gap. A second RED exposed an empty evidence digest; GREEN bound candidate and request identities into canonical JSON. A third RED exposed missing diagnostic preservation; GREEN preserved the diagnostic without making it readiness-blocking.
  - Review budget: the planning record was isolated in `08e831d`; the behavior/test/docs commit contains 361 additions and 3 deletions, staying within the 400-line budget without compressing tests or contracts.
  - Final independent verification: focused readiness tests passed 3/3; the full 35-test suite passed twice; repeated bakeoff CLI output was byte-identical at 3,460 bytes with SHA-256 `3261645358d3dfd74e4d27df7835b75c62e8a2cc5da91d615c05c404a4a68dab`; `git diff --check` passed; exact-path staging excluded `.pi/`, `openspec/`, and the task record.
  - Outcome: both fake candidates pass Bounded Session Termination `1.0`; readiness remains `not_ready` with exactly 19 missing behaviors; mandatory failure blocks coverage; diagnostic failure is preserved and nonblocking; the supplied Behavior Hash is bound but explicitly not validated.
  - Commit evidence: `7503ba79eedb3e69e6c118190713e8e6cb0c7e62` (`feat(readiness): add bounded termination tracer`).
  - Native review evidence: lineage `review-56a8b5c08698c18b` approved the committed slice from `08e831dc781595734d437922247eb5778e2d8a91`; exact acknowledgement completed and authority burned.
- [ ] T2 — Add controlled-path Behavior Evidence Completeness v1.0.
  - Route: delegated bounded writer with strict RED/GREEN through the unchanged `PreRunReadinessSuite.run` Interface, followed by independent verification.
  - Expected edit surfaces: `src/auglo_e2_bakeoff/readiness.py`, `tests/test_pre_run_readiness.py`, `README.md`, `project/e2.yaml`, and this task record.
  - RED observed: the focused readiness suite failed 3 tests because passing candidates covered only `bounded-session-termination` instead of both mandatory behaviors.
  - GREEN observed: mapping the evaluator-owned named `evidence_completeness` gate added the second scenario and made all 3 focused tests pass.
  - Second RED observed: the delayed-termination case failed because coverage was empty instead of preserving `behavior-evidence-completeness` independently.
  - Second GREEN observed: deriving each behavior from its own named gate made all 3 focused tests pass.
  - TRIANGULATE: an incomplete-evidence candidate omitting `closure_window_behavior_observed` names that missing requirement, cannot claim either mandatory behavior, changes the digest/evidence references, and passes as the fourth focused test.
  - Required triangulation: both passing fake candidates cover 2/20; delayed termination preserves evidence coverage while losing duration coverage; incomplete controlled-path evidence names missing requirements and cannot cover evidence completeness.
  - First independent verification: all structural and runnable checks passed, but final readiness was blocked solely because this T2 RED/GREEN history had not yet been recorded in the task document.
  - Review budget: 400 changed lines; current complete candidate is 156 changed lines against `650cea56a6bee3f8585dfda717434cb9c28b71fb`.
  - Commit evidence: pending.

## Checks policy

Strict TDD applies. Tests cross only `PreRunReadinessSuite.run`; RED must be observed before the minimal implementation for each behavior increment. Existing public seams remain stable. Final command-running verification is delegated independently.

## Delivery

- One work-unit commit with tests and documentation alongside behavior.
- Conventional Commit message.
- Native review candidate is this work-unit commit against `b73b728`.
- Push, pull request creation, merge, provider activity, and real telephony remain unauthorized.

## Current status

T1 is complete and natively approved. T2 is in progress on `feature/readiness-evidence-completeness`; it is scoped to controlled-duration-path event completeness and must leave the suite explicitly incomplete at 2 of 20 canonical behaviors.

# Build the Pre-Run Behavioral Readiness Tracer

## Intent

Add the smallest executable vertical slice toward the canonical 20-behavior Pre-Run Behavioral Readiness Suite. The slice runs the existing versioned Bounded Session Termination fixture through one `ConversationCandidate`, emits a deterministic readiness result bound to the supplied suite and Behavior Hash identities, and remains `not_ready` while the other 19 canonical behaviors are uncovered.

## Authority and provenance

- Canonical product contract: `project/e2.yaml`.
- Canonical vocabulary: `CONTEXT.md`.
- Previous reviewed boundary: `b73b728` on `feature/executable-e2-bakeoff`.
- Current feature branch: `feature/pre-run-readiness-tracer`.
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

## Non-goals

- No provider, model, voice, transport, deployment, telemetry, storage, or test-framework selection.
- No real telephony, live appointment Adapter, legal sufficiency claim, or production readiness claim.
- No implementation of the other 19 behaviors.
- No winner selection or ranking.
- No CLI/report refactor unless required by the confirmed Interface.
- No sensitive evidence or controlled-storage location in Git.

## Work tasks

- [ ] T1 — Implement and verify the readiness tracer as one reviewable vertical slice.
  - Route: delegated bounded writer with strict RED/GREEN through the confirmed public Interface, followed by independent verification.
  - Expected edit surfaces: `src/auglo_e2_bakeoff/readiness.py`, `src/auglo_e2_bakeoff/__init__.py`, `tests/test_pre_run_readiness.py`, `README.md`, `project/e2.yaml`, and this task record.
  - Review budget: 400 changed lines; do not compress tests, contracts, or documentation to fit.
  - Acceptance checks: focused readiness tests; full existing unittest suite; repeated deterministic readiness result; unchanged deterministic bakeoff command; no provider/runtime selection; exact missing-behavior reporting.
  - Commit evidence: pending.

## Checks policy

Strict TDD applies. Tests cross only `PreRunReadinessSuite.run`; RED must be observed before the minimal implementation for each behavior increment. Existing public seams remain stable. Final command-running verification is delegated independently.

## Delivery

- One work-unit commit with tests and documentation alongside behavior.
- Conventional Commit message.
- Native review candidate is this work-unit commit against `b73b728`.
- Push, pull request creation, merge, provider activity, and real telephony remain unauthorized.

## Current status

T1 is in progress. The public readiness Seam is confirmed; implementation has not started.

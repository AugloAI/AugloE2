# Build the Executable E2 Bakeoff

## Intent

Build the smallest offline, provider-neutral executable harness that runs the same versioned duration scenario through `controlled_cascade` and `audio_native_half_cascade`, records comparable evidence, applies gate-first qualification, and emits a comparison result without selecting a provider or bakeoff winner.

## Authority and provenance

- Canonical product contract: `project/e2.yaml`.
- Canonical vocabulary: `CONTEXT.md`.
- Approved baseline commit: `6507c2fcec2b501d1d784134a4f43ef9fb07d4a5`.
- Preserved SDD exploration: `openspec/changes/executable-e2-bakeoff/exploration.md`.
- SDD execution was explicitly abandoned because the installed native CLI cannot provide authoritative SDD status; OpenSpec artifacts remain reference material, not phase authority.
- Current feature branch: `feature/executable-e2-bakeoff`.

## Decisions

- Workflow: ODD with strict TDD.
- First scenario: `Bounded Session Termination`.
- Duration intervals:
  - normal behavior: `0 <= elapsed < 240s`;
  - graceful closure: `240s <= elapsed < 300s`;
  - forced termination becomes due at the first observation where `elapsed >= 300s`;
  - compliance requires actual media or connection end by 300 seconds, not only a termination request.
- Qualification is gate-first. A failed binary admission gate cannot be offset by quality, cost, latency, or operability scores.
- Synthetic bakeoff results cannot claim that the canonical real-cohort latency gates passed.
- Provider, model, voice, transport, storage, observability, and appointment selections remain deferred.
- Initial implementation stack: Python standard library with Python 3.12-compatible code, executed locally with Python 3.14.
- Initial test runner: `python3 -m unittest discover -s tests -v`.
- Initial serialization: canonical JSON and JSON Lines using the Python standard library; no final storage or telemetry vendor is selected.

## Confirmed public seams for strict TDD

The founder confirmed that tests cross only these four public Interfaces. Helpers, assertion engines, and individual event types remain internal unless a second caller or Adapter proves another seam is necessary.

1. `CandidateEvaluator.evaluate(candidate, qualification_input) -> QualificationResult`
   - Deep external Module hiding fixture execution, evidence validation, binary gates, and comparison-ready aggregation.
2. `ConversationCandidate.execute(execution_context, inbound_stream, ports) -> TerminalResult`
   - Adapter seam implemented by controlled-cascade and audio-native-half-cascade fakes in the first slice.
3. `PreTtsControl.evaluate(proposed_action, policy_state, clock) -> ControlledAction`
   - Shared deterministic policy Module enforcing the 240/300-second contract.
4. `EvidenceRecorder.append(event)` and `EvidenceRecorder.finalize(requirements) -> ManifestRef`
   - Owns ordering, exactly-one terminal event, digest generation, and path-sensitive completeness.

Tests exercise these public seams only. Internal assertion and event helpers will not become public Interfaces without a second caller or Adapter.

## Non-goals

- No real telephony, provider SDK, network access, secrets, PII, recordings, or transcripts.
- No complete 20-behavior readiness suite in the first slice.
- No provider or winner selection.
- No production observability, database, controlled-storage implementation, dashboard, deployment, or multitenancy.
- No claim that synthetic timing proves production latency.
- No refactor of the stale candidate integration map unless a task specifically requires canonical alignment.

## Work tasks

- [x] T1 — Confirm seams and establish the offline Python test harness.
  - Route: delegated bounded writer after founder seam confirmation.
  - RED observed: `python3 -m unittest discover -s tests -v` failed with `ModuleNotFoundError: No module named 'auglo_e2_bakeoff'`.
  - GREEN observed and independently verified: the exact runner passed one public-seam test; candidate identity mismatch is rejected before candidate execution.
  - Checks: Python 3.12-compatible syntax inspected; Python 3.14 execution passed; standard-library-only; no provider or later-task behavior added.
  - Commit evidence: `aae62726cb3dd14ce6c365ba98edeb21919f5c1a` (`feat(bakeoff): establish candidate evaluation harness`).
- [ ] T2 — Implement the evidence contract tracer.
  - Route: delegated writer.
  - RED: reject out-of-order events, missing terminal event, duplicate terminal event, or invalid finalization.
  - GREEN: append-only `EvidenceRecorder` produces deterministic stream and manifest digests plus a path-sensitive completeness verdict.
  - TRIANGULATE: valid minimum duration stream and expected incomplete capture-failure record.
  - Checks: focused unit tests plus full runner.
  - Commit evidence: pending.
- [ ] T3 — Implement deterministic duration control and candidate parity.
  - Route: delegated writer.
  - RED: reject new substantive work at exactly 240 seconds and fail an execution whose real media/connection end exceeds 300 seconds.
  - GREEN: fake monotonic clock and shared `PreTtsControl` produce graceful closure and forced termination behavior through both fake candidate Adapters.
  - TRIANGULATE: immediately before, exactly at, and immediately after both boundaries; mismatched fixture/config/evaluator digests.
  - Checks: focused boundary tests plus full runner.
  - Commit evidence: pending.
- [ ] T4 — Implement gate-first qualification and comparison output.
  - Route: delegated writer.
  - RED: a failed mandatory assertion or incomplete evidence must never receive an admitted or winning result.
  - GREEN: `CandidateEvaluator` emits separate admission outcomes and comparison dimensions with explicit unknown/not-measured values.
  - TRIANGULATE: both admitted, one disqualified, diagnostic-only failure, and missing comparison dimension.
  - Checks: focused evaluator tests plus full runner.
  - Commit evidence: pending.
- [ ] T5 — Verify the slice and align documentation.
  - Route: delegated independent verifier, followed by bounded documentation correction only if needed.
  - Checks: exact full test command, deterministic repeated run, canonical vocabulary, security exclusions, no synthetic overclaim, no provider selection, and diff review.
  - Runtime harness: execute the same frozen scenario through both fake candidates and inspect the emitted qualification/comparison result.
  - Commit evidence: pending.

## Delivery forecast

- Expected total change: approximately 650–950 lines including tests, fixtures, contracts, and documentation.
- Review budget: 400 changed lines.
- Recommended delivery: three reviewable work-unit commits or PR slices:
  1. harness plus evidence tracer;
  2. duration control plus candidate parity;
  3. qualification/reporting plus final documentation.
- Founder-selected delivery: three work-unit commits or PR slices using the recommended boundaries above.
- Never compress or omit tests, evidence, or documentation to fit the budget.
- Push, pull request creation, merge, provider account activity, and real telephony remain unauthorized.

## Current status

T1 is complete in commit `aae62726cb3dd14ce6c365ba98edeb21919f5c1a`: the Python standard-library harness exists, strict RED/GREEN evidence was observed, and an independent verifier passed the exact runner. T2 is next: implement the append-only evidence contract tracer through the confirmed `EvidenceRecorder` seam.

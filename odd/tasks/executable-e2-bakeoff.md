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
- [x] T2 — Implement the evidence contract tracer.
  - Route: delegated writer with two independent verification-driven correction rounds.
  - RED/GREEN evidence: multiple observed cycles covered import absence, ordering, envelope validation, terminal cardinality, deterministic digests, completeness, attempt/event identity, repeated finalization, path-derived requirements, and recursive payload protection.
  - TRIANGULATE: valid duration evidence, no-answer versus threshold-crossed paths, explicit incomplete capture failure, empty identities, and arbitrary nested payload containers.
  - Checks: the exact full runner passed 14 tests; final independent verification passed with no material T2 gap.
  - Review-size exception: founder explicitly accepted one cohesive 521-line T2 work unit; the exception does not apply to later tasks.
  - Commit evidence: `259fa97c953ed553ffc28c2e0b21f21fc256b6e0` (`feat(bakeoff): add canonical evidence recorder`).
- [x] T3 — Implement deterministic duration control and candidate parity.
  - Route: delegated writer plus independent verifier; one failed verifier launch was retried without accepting missing evidence.
  - RED/GREEN evidence: observed cycles covered missing control/candidate Interfaces, negative elapsed time, and parity mismatch handling.
  - TRIANGULATE: immediately before, exactly at, and immediately after 240 and 300 seconds; actual end at 300 versus 300.001; both candidate identities; and independent fixture/configuration/evaluator mismatches.
  - Checks: exact full runner passed 20 tests; independent verification passed; 340 changed lines remained below the 400-line budget.
  - Commit evidence: `23450a8b4771668303bce1844b52c137595e80ea` (`feat(bakeoff): enforce duration control parity`).
- [x] T4 — Implement gate-first qualification and comparison output.
  - Route: delegated writer plus independent verifier.
  - RED/GREEN evidence: observed missing qualification types and incomplete-evidence reason loss before the minimal gate-first result model passed.
  - TRIANGULATE: both candidates admitted independently, mandatory assertion/duration/evidence failures despite maximum scores, diagnostic-only failure, missing dimension, immutability, and identity preflight.
  - Checks: exact full runner passed 24 tests; independent verification found no material gap; 287 changed lines remained below budget.
  - Commit evidence: `0215f358ba08728304ba4492ef0f43c2a5a3c07a` (`feat(bakeoff): enforce gate-first qualification`).
- [x] T5 — Verify the slice and align documentation.
  - Route: delegated independent verifier, bounded writer, and final independent verifier.
  - Checks: the exact suite passed twice with 32 tests; the executable runner passed twice with byte-identical canonical JSON; final verification passed with no material gap.
  - Runtime harness: `PYTHONPATH=src python3 -m auglo_e2_bakeoff` runs the frozen `Bounded Session Termination` fixture through both fake candidates, emits complete execution-owned evidence, derived gates, qualification digests, explicit not-measured dimensions, and no winner selection.
  - Security and integrity: duration requirements are evaluator-owned and unconditional; actual end time derives compliance/outcome; manifests bind candidate and terminal data; qualification digest binds the full qualification basis; recursive sensitive/provider key filtering remains enforced.
  - Documentation: `README.md` and `project/e2.yaml` distinguish the bounded offline harness from production runtime, provider choice, real telephony, full readiness, and real-cohort latency. Contract version is `0.17.4`.
  - Review-size exception: founder explicitly accepted this cohesive T5 work unit at 734 changed lines after final blockers were found. This exception is not reusable.
  - Commit evidence: `22fbde4fb03621fba231a7f4ab735044f13c5349` (`feat(bakeoff): add deterministic qualification runner`).

## Delivery forecast

- Expected total change: approximately 650–950 lines including tests, fixtures, contracts, and documentation.
- Review budget: 400 changed lines.
- Recommended delivery: three reviewable work-unit commits or PR slices:
  1. harness plus evidence tracer;
  2. duration control plus candidate parity;
  3. qualification/reporting plus final documentation.
- Founder-selected delivery began with three work-unit boundaries; T2 received an explicit one-task size exception at 521 lines after implementation, while later tasks remain subject to the 400-line budget.
- Never compress or omit tests, evidence, or documentation to fit the budget.
- Push, pull request creation, merge, provider account activity, and real telephony remain unauthorized.

## Current status

T1–T5 are complete in `aae62726cb3dd14ce6c365ba98edeb21919f5c1a`, `259fa97c953ed553ffc28c2e0b21f21fc256b6e0`, `23450a8b4771668303bce1844b52c137595e80ea`, `0215f358ba08728304ba4492ef0f43c2a5a3c07a`, and `22fbde4fb03621fba231a7f4ab735044f13c5349`. The full suite passes 32 tests and the offline runner produces byte-identical 3,459-byte JSON across repeated runs. The bounded slice is complete; it remains explicitly non-production and does not select a provider or winner.

"""Executable offline qualification for the frozen bounded-duration fixture."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from . import (
    AudioNativeHalfCascadeCandidate,
    CandidateEvaluator,
    CheckOutcome,
    ComparisonDimension,
    ComparisonDimensions,
    ControlledCascadeCandidate,
    EvidenceRecorder,
    ExecutionContext,
    ExecutionPorts,
    ParityIdentities,
    PreTtsControl,
    ProposedAction,
    QualificationInput,
)


@dataclass(frozen=True, slots=True)
class _BoundedSessionTerminationFixture:
    fixture_id: str = "bounded-session-termination"
    name: str = "Bounded Session Termination"
    version: str = "1.0"
    fixture_digest: str = "fixture:bounded-session-termination:v1"
    configuration_digest: str = "config:bounded-duration:v1"
    evaluator_digest: str = "evaluator:gate-first:v1"


_FIXTURE = _BoundedSessionTerminationFixture()
_ACTIONS = (
    ProposedAction("continue_current_task", True),
    ProposedAction("start_new_task", True),
    ProposedAction("continue_current_task", True),
)


class _DeterministicClock:
    def __init__(self) -> None:
        self._observations = iter((239.999, 240.0, 300.0))

    def monotonic(self) -> float:
        return next(self._observations)


def _run_candidate(candidate_type: type, identities: ParityIdentities) -> dict[str, object]:
    candidate = candidate_type(identities)
    recorder = EvidenceRecorder()
    result = CandidateEvaluator().evaluate(
        candidate,
        QualificationInput(
            candidate_id=candidate.candidate_id,
            execution_context=ExecutionContext(identities, 0.0, 300.0, 300.0),
            inbound_stream=_ACTIONS,
            ports=ExecutionPorts(
                PreTtsControl(),
                _DeterministicClock(),
                recorder,
                f"fixture-attempt:{candidate.candidate_id}",
            ),
            diagnostic_outcomes=(
                CheckOutcome(
                    "canonical_real_cohort_latency",
                    False,
                    "not measured by synthetic offline fixture",
                ),
            ),
            comparison_dimensions=ComparisonDimensions(
                semantic_quality=ComparisonDimension.not_measured(),
                estimated_cost=ComparisonDimension.not_measured(),
                solo_founder_operability=ComparisonDimension.not_measured(),
            ),
        ),
    )
    evidence = asdict(result.evidence_ref)
    evidence["completeness"] = evidence.pop("evidence_completeness")
    return {
        "candidate_id": result.candidate_id,
        "qualification": result.outcome,
        "qualification_digest": result.qualification_digest,
        "terminal": asdict(result.terminal_result),
        "gates": [asdict(gate) for gate in result.gate_outcomes],
        "diagnostics": [asdict(item) for item in result.diagnostic_outcomes],
        "dimensions": asdict(result.comparison_dimensions),
        "evidence": evidence,
    }


def main() -> None:
    identities = ParityIdentities(
        _FIXTURE.fixture_digest,
        _FIXTURE.configuration_digest,
        _FIXTURE.evaluator_digest,
    )
    document = {
        "schema": "auglo.e2.offline-qualification",
        "schema_version": "1.0",
        "fixture": {
            "id": _FIXTURE.fixture_id,
            "name": _FIXTURE.name,
            "version": _FIXTURE.version,
        },
        "identities": {
            "fixture": identities.fixture_digest,
            "configuration": identities.configuration_digest,
            "evaluator": identities.evaluator_digest,
        },
        "candidate_results": [
            _run_candidate(ControlledCascadeCandidate, identities),
            _run_candidate(AudioNativeHalfCascadeCandidate, identities),
        ],
        "winner": None,
        "selection_statement": "no_selection_performed",
    }
    print(json.dumps(document, allow_nan=False, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()

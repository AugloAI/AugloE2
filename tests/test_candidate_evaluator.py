from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auglo_e2_bakeoff import (
    AudioNativeHalfCascadeCandidate,
    CandidateEvaluator,
    CandidateIdentityMismatch,
    CheckOutcome,
    ComparisonDimension,
    ComparisonDimensions,
    ControlledCascadeCandidate,
    ExecutionContext,
    ExecutionPorts,
    ManifestRef,
    ParityIdentities,
    PreTtsControl,
    ProposedAction,
    QualificationInput,
)


class UncalledCandidate:
    candidate_id = "audio_native_half_cascade"

    def __init__(self) -> None:
        self.was_executed = False

    def execute(self, execution_context, inbound_stream, ports):
        self.was_executed = True
        raise AssertionError("identity mismatch must be rejected before execution")


class FakeMonotonicClock:
    def __init__(self, *observations: float) -> None:
        self._observations = iter(observations)

    def monotonic(self) -> float:
        return next(self._observations)


IDENTITIES = ParityIdentities(
    fixture_digest="fixture:bounded-session-v1",
    configuration_digest="config:duration-v1",
    evaluator_digest="evaluator:pre-tts-v1",
)
ACTIONS = (
    ProposedAction("continue_current_task", True),
    ProposedAction("start_new_task", True),
    ProposedAction("continue_current_task", True),
)
COMPLETE_EVIDENCE = ManifestRef(
    attempt_id="attempt-001",
    stream_digest="stream-digest",
    manifest_digest="manifest-digest",
    evidence_completeness="complete",
    missing_requirements=(),
)
MEASURED_DIMENSIONS = ComparisonDimensions(
    semantic_quality=ComparisonDimension.measured(0.91),
    estimated_cost=ComparisonDimension.measured(0.82),
    solo_founder_operability=ComparisonDimension.measured(0.87),
)


def qualification_input(candidate_id: str) -> QualificationInput:
    return QualificationInput(
        candidate_id=candidate_id,
        execution_context=ExecutionContext(IDENTITIES, 0.0, 300.0, 300.0),
        inbound_stream=ACTIONS,
        ports=ExecutionPorts(
            PreTtsControl(), FakeMonotonicClock(239.999, 240.0, 300.0)
        ),
        evidence_ref=COMPLETE_EVIDENCE,
        mandatory_assertions=(
            CheckOutcome("bounded_session_termination", True, "all assertions passed"),
        ),
        diagnostic_outcomes=(),
        comparison_dimensions=MEASURED_DIMENSIONS,
    )


class CandidateEvaluatorTests(unittest.TestCase):
    def test_both_candidates_are_individually_admitted_under_identical_inputs(self) -> None:
        candidates = (
            ControlledCascadeCandidate(IDENTITIES),
            AudioNativeHalfCascadeCandidate(IDENTITIES),
        )

        results = [
            CandidateEvaluator().evaluate(
                candidate, qualification_input(candidate.candidate_id)
            )
            for candidate in candidates
        ]

        self.assertEqual(
            ["controlled_cascade", "audio_native_half_cascade"],
            [result.candidate_id for result in results],
        )
        self.assertEqual(["admitted", "admitted"], [result.outcome for result in results])
        self.assertTrue(all(result.terminal_result.duration_compliant for result in results))
        self.assertTrue(
            all(result.evidence_ref == COMPLETE_EVIDENCE for result in results)
        )
        self.assertEqual(MEASURED_DIMENSIONS, results[0].comparison_dimensions)
        self.assertEqual(results[0].gate_outcomes, results[1].gate_outcomes)

    def test_every_mandatory_gate_blocks_high_scoring_candidate(self) -> None:
        high_scores = ComparisonDimensions(
            semantic_quality=ComparisonDimension.measured(1.0),
            estimated_cost=ComparisonDimension.measured(1.0),
            solo_founder_operability=ComparisonDimension.measured(1.0),
        )
        incomplete_evidence = replace(
            COMPLETE_EVIDENCE,
            evidence_completeness="incomplete",
            missing_requirements=("closure_window_behavior_observed",),
        )
        cases = (
            (
                "bounded_session_termination",
                {
                    "mandatory_assertions": (
                        CheckOutcome(
                            "bounded_session_termination",
                            False,
                            "deterministic assertion failed",
                        ),
                    )
                },
                "deterministic assertion failed",
            ),
            (
                "duration_compliance",
                {
                    "execution_context": ExecutionContext(
                        IDENTITIES, 0.0, 300.0, 300.001
                    )
                },
                "hard_duration_violation",
            ),
            (
                "evidence_completeness",
                {"evidence_ref": incomplete_evidence},
                "closure_window_behavior_observed",
            ),
        )

        for failed_gate, changes, expected_reason in cases:
            with self.subTest(failed_gate=failed_gate):
                inputs = replace(
                    qualification_input("controlled_cascade"),
                    comparison_dimensions=high_scores,
                    **changes,
                )
                result = CandidateEvaluator().evaluate(
                    ControlledCascadeCandidate(IDENTITIES), inputs
                )

                self.assertEqual("ineligible", result.outcome)
                failures = {gate.name: gate for gate in result.gate_outcomes if not gate.passed}
                self.assertIn(failed_gate, failures)
                self.assertIn(expected_reason, failures[failed_gate].reason)
                self.assertEqual(high_scores, result.comparison_dimensions)
                self.assertFalse(hasattr(result, "weighted_total"))

    def test_diagnostic_failure_is_reported_without_blocking_admission(self) -> None:
        diagnostic_failure = CheckOutcome(
            "interrupt_reorientation_probe",
            False,
            "optional probe did not recover",
        )
        inputs = replace(
            qualification_input("audio_native_half_cascade"),
            diagnostic_outcomes=(diagnostic_failure,),
        )

        result = CandidateEvaluator().evaluate(
            AudioNativeHalfCascadeCandidate(IDENTITIES), inputs
        )

        self.assertEqual("admitted", result.outcome)
        self.assertEqual((diagnostic_failure,), result.diagnostic_outcomes)
        self.assertFalse(result.diagnostic_outcomes[0].passed)

    def test_missing_comparison_dimension_is_explicitly_not_measured(self) -> None:
        dimensions = ComparisonDimensions(
            semantic_quality=ComparisonDimension.not_measured(),
            estimated_cost=ComparisonDimension.measured(0.82),
            solo_founder_operability=ComparisonDimension.measured(0.87),
        )
        inputs = replace(
            qualification_input("controlled_cascade"),
            comparison_dimensions=dimensions,
        )

        result = CandidateEvaluator().evaluate(
            ControlledCascadeCandidate(IDENTITIES), inputs
        )

        self.assertEqual("not_measured", result.comparison_dimensions.semantic_quality.status)
        self.assertIsNone(result.comparison_dimensions.semantic_quality.value)
        self.assertEqual("measured", result.comparison_dimensions.estimated_cost.status)
        with self.assertRaises(FrozenInstanceError):
            result.outcome = "ineligible"

    def test_rejects_qualification_input_bound_to_another_candidate(self) -> None:
        candidate = UncalledCandidate()
        qualification_input = QualificationInput(candidate_id="controlled_cascade")

        with self.assertRaises(CandidateIdentityMismatch):
            CandidateEvaluator().evaluate(candidate, qualification_input)

        self.assertFalse(candidate.was_executed)


if __name__ == "__main__":
    unittest.main()

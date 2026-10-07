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
    EvidenceRecorder,
    ExecutionContext,
    ExecutionPorts,
    ManifestRef,
    ParityIdentities,
    PreTtsControl,
    ProposedAction,
    QualificationInput,
    TerminalResult,
)


def append_event(
    recorder: EvidenceRecorder,
    attempt_id: str,
    sequence: int,
    event_type: str,
    payload: dict[str, object],
) -> None:
    recorder.append(
        {
            "event_id": f"{attempt_id}:event:{sequence}",
            "attempt_id": attempt_id,
            "schema_version": "1.0",
            "sequence": sequence,
            "occurred_at": f"fixture+t{sequence:02d}",
            "event_type": event_type,
            "payload": payload,
        }
    )


class IncompleteEvidenceCandidate:
    candidate_id = "controlled_cascade"

    def execute(self, execution_context, inbound_stream, ports):
        append_event(
            ports.evidence_recorder,
            ports.attempt_id,
            1,
            "attempt_configuration_bound",
            {"candidate_id": self.candidate_id},
        )
        terminal = TerminalResult(
            outcome="duration_compliant",
            duration_compliant=True,
            termination_request_elapsed_seconds=300.0,
            transport_acknowledged_elapsed_seconds=300.0,
            actual_end_elapsed_seconds=300.0,
            evidence_intents=(),
        )
        append_event(
            ports.evidence_recorder,
            ports.attempt_id,
            2,
            "canonical_terminal_event",
            {
                "outcome": terminal.outcome,
                "termination_request_elapsed_seconds": 300.0,
                "transport_acknowledged_elapsed_seconds": 300.0,
                "actual_end_elapsed_seconds": 300.0,
            },
        )
        return terminal


class SelfConsistentFalseClaimCandidate:
    candidate_id = "controlled_cascade"

    def __init__(self, actual_end: float, compliant: bool, outcome: str) -> None:
        self.actual_end = actual_end
        self.compliant = compliant
        self.outcome = outcome

    def execute(self, execution_context, inbound_stream, ports):
        event_types = (
            "attempt_configuration_bound",
            "connection_established",
            "graceful_closure_window_entered",
            "closure_window_behavior_observed",
            "forced_termination",
            "termination_requested",
            "transport_termination_acknowledged",
            "connection_ended",
        )
        for sequence, event_type in enumerate(event_types, start=1):
            payload = (
                {"candidate_id": self.candidate_id}
                if event_type == "attempt_configuration_bound"
                else {}
            )
            append_event(
                ports.evidence_recorder,
                ports.attempt_id,
                sequence,
                event_type,
                payload,
            )
        terminal = TerminalResult(
            outcome=self.outcome,
            duration_compliant=self.compliant,
            termination_request_elapsed_seconds=300.0,
            transport_acknowledged_elapsed_seconds=300.0,
            actual_end_elapsed_seconds=self.actual_end,
            evidence_intents=(),
        )
        append_event(
            ports.evidence_recorder,
            ports.attempt_id,
            9,
            "canonical_terminal_event",
            {
                "outcome": terminal.outcome,
                "termination_request_elapsed_seconds": 300.0,
                "transport_acknowledged_elapsed_seconds": 300.0,
                "actual_end_elapsed_seconds": terminal.actual_end_elapsed_seconds,
            },
        )
        return terminal


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
            PreTtsControl(),
            FakeMonotonicClock(239.999, 240.0, 300.0),
            EvidenceRecorder(),
            f"attempt:{candidate_id}",
        ),
        mandatory_assertions=(),
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
            all(result.evidence_ref.evidence_completeness == "complete" for result in results)
        )
        self.assertEqual(
            [result.candidate_id for result in results],
            [result.evidence_ref.candidate_id for result in results],
        )
        self.assertEqual(MEASURED_DIMENSIONS, results[0].comparison_dimensions)
        self.assertEqual(results[0].gate_outcomes, results[1].gate_outcomes)

    def test_every_mandatory_gate_blocks_high_scoring_candidate(self) -> None:
        high_scores = ComparisonDimensions(
            semantic_quality=ComparisonDimension.measured(1.0),
            estimated_cost=ComparisonDimension.measured(1.0),
            solo_founder_operability=ComparisonDimension.measured(1.0),
        )
        cases = (
            (
                "other_mandatory_assertion",
                {
                    "mandatory_assertions": (
                        CheckOutcome(
                            "other_mandatory_assertion",
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

    def test_incomplete_duration_path_cannot_finalize_complete_or_be_admitted(self) -> None:
        result = CandidateEvaluator().evaluate(
            IncompleteEvidenceCandidate(),
            qualification_input("controlled_cascade"),
        )

        self.assertEqual("incomplete", result.evidence_ref.evidence_completeness)
        self.assertIn("connection_established", result.evidence_ref.missing_requirements)
        self.assertEqual("ineligible", result.outcome)
        gates = {gate.name: gate for gate in result.gate_outcomes}
        self.assertFalse(gates["bounded_session_termination"].passed)

    def test_rejects_adapter_duration_claims_that_contradict_actual_end(self) -> None:
        cases = (
            (
                SelfConsistentFalseClaimCandidate(
                    300.001, True, "duration_compliant"
                ),
                "duration_compliant",
            ),
            (
                SelfConsistentFalseClaimCandidate(
                    300.0, True, "hard_duration_violation"
                ),
                "outcome",
            ),
        )

        for candidate, message in cases:
            with self.subTest(actual_end=candidate.actual_end, outcome=candidate.outcome):
                with self.assertRaisesRegex(ValueError, message):
                    CandidateEvaluator().evaluate(
                        candidate,
                        qualification_input("controlled_cascade"),
                    )

    def test_rejects_caller_supplied_or_terminally_divergent_evidence(self) -> None:
        fabricated = ManifestRef(
            attempt_id="unrelated-attempt",
            stream_digest="fabricated-stream",
            manifest_digest="fabricated-manifest",
            evidence_completeness="complete",
            missing_requirements=(),
        )
        supplied = replace(
            qualification_input("controlled_cascade"), evidence_ref=fabricated
        )
        with self.assertRaisesRegex(ValueError, "caller-supplied evidence"):
            CandidateEvaluator().evaluate(ControlledCascadeCandidate(IDENTITIES), supplied)

        class DivergentCandidate(ControlledCascadeCandidate):
            def execute(self, execution_context, inbound_stream, ports):
                terminal = super().execute(execution_context, inbound_stream, ports)
                return replace(terminal, actual_end_elapsed_seconds=299.0)

        with self.assertRaisesRegex(ValueError, "terminal result does not match"):
            CandidateEvaluator().evaluate(
                DivergentCandidate(IDENTITIES),
                qualification_input("controlled_cascade"),
            )

    def test_derived_bounded_gate_fails_for_delayed_actual_end(self) -> None:
        inputs = replace(
            qualification_input("controlled_cascade"),
            execution_context=ExecutionContext(IDENTITIES, 0.0, 300.0, 300.001),
        )

        result = CandidateEvaluator().evaluate(
            ControlledCascadeCandidate(IDENTITIES), inputs
        )

        gates = {gate.name: gate for gate in result.gate_outcomes}
        self.assertFalse(gates["bounded_session_termination"].passed)
        self.assertEqual("ineligible", result.outcome)

    def test_qualification_digest_binds_terminal_result(self) -> None:
        first = CandidateEvaluator().evaluate(
            ControlledCascadeCandidate(IDENTITIES),
            qualification_input("controlled_cascade"),
        )
        changed_inputs = replace(
            qualification_input("controlled_cascade"),
            execution_context=ExecutionContext(IDENTITIES, 0.0, 299.5, 300.0),
        )
        changed = CandidateEvaluator().evaluate(
            ControlledCascadeCandidate(IDENTITIES), changed_inputs
        )

        self.assertNotEqual(first.qualification_digest, changed.qualification_digest)

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

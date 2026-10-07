from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auglo_e2_bakeoff import (
    AudioNativeHalfCascadeCandidate,
    ControlledCascadeCandidate,
    ExecutionContext,
    ExecutionPorts,
    ParityIdentities,
    ParityIdentityMismatch,
    PolicyState,
    PreTtsControl,
    ProposedAction,
)


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


class PreTtsControlTests(unittest.TestCase):
    def test_rejects_new_substantive_work_at_240_and_pursues_closure(self) -> None:
        action = PreTtsControl().evaluate(
            ProposedAction(intent="start_new_task", substantive=True),
            PolicyState(connection_started_at=0.0),
            FakeMonotonicClock(240.0),
        )

        self.assertEqual("pursue_graceful_closure", action.disposition)
        self.assertEqual("graceful_closure", action.evidence_intent)
        self.assertFalse(action.substantive_work_allowed)
        self.assertEqual(240.0, action.elapsed_seconds)

    def test_rejects_clock_observation_before_connection_start(self) -> None:
        with self.assertRaisesRegex(ValueError, "elapsed seconds cannot be negative"):
            PreTtsControl().evaluate(
                ProposedAction(intent="continue_current_task", substantive=True),
                PolicyState(connection_started_at=10.0),
                FakeMonotonicClock(9.999),
            )

    def test_applies_half_open_duration_boundaries(self) -> None:
        cases = (
            (0.0, "allow", True),
            (239.999, "allow", True),
            (240.0, "pursue_graceful_closure", False),
            (240.001, "pursue_graceful_closure", False),
            (299.999, "pursue_graceful_closure", False),
            (300.0, "force_termination", False),
            (300.001, "force_termination", False),
        )

        for elapsed, disposition, substantive_allowed in cases:
            with self.subTest(elapsed=elapsed):
                action = PreTtsControl().evaluate(
                    ProposedAction(intent="start_new_task", substantive=True),
                    PolicyState(connection_started_at=10.0),
                    FakeMonotonicClock(10.0 + elapsed),
                )

                self.assertEqual(disposition, action.disposition)
                self.assertEqual(
                    substantive_allowed, action.substantive_work_allowed
                )
                self.assertAlmostEqual(elapsed, action.elapsed_seconds, places=9)


class ConversationCandidateTests(unittest.TestCase):
    def test_actual_end_after_300_is_a_hard_violation_despite_timely_request(self) -> None:
        context = ExecutionContext(
            identities=IDENTITIES,
            connection_started_at=0.0,
            transport_acknowledged_elapsed_seconds=300.0,
            actual_end_elapsed_seconds=300.001,
        )
        ports = ExecutionPorts(
            pre_tts_control=PreTtsControl(),
            clock=FakeMonotonicClock(239.999, 240.0, 300.0),
        )
        actions = (
            ProposedAction("continue_current_task", True),
            ProposedAction("start_new_task", True),
            ProposedAction("continue_current_task", True),
        )

        result = ControlledCascadeCandidate(IDENTITIES).execute(
            context, actions, ports
        )

        self.assertEqual(300.0, result.termination_request_elapsed_seconds)
        self.assertEqual(300.0, result.transport_acknowledged_elapsed_seconds)
        self.assertEqual(300.001, result.actual_end_elapsed_seconds)
        self.assertFalse(result.duration_compliant)
        self.assertEqual("hard_duration_violation", result.outcome)
        self.assertIn("termination_requested", result.evidence_intents)
        self.assertIn("transport_acknowledged", result.evidence_intents)
        self.assertIn("connection_ended", result.evidence_intents)

    def test_fake_adapters_produce_equal_provider_neutral_terminal_results(self) -> None:
        context = ExecutionContext(IDENTITIES, 10.0, 300.0, 300.0)
        actions = (
            ProposedAction("continue_current_task", True),
            ProposedAction("start_new_task", True),
            ProposedAction("continue_current_task", True),
        )
        shared_control = PreTtsControl()
        candidates = (
            ControlledCascadeCandidate(IDENTITIES),
            AudioNativeHalfCascadeCandidate(IDENTITIES),
        )
        results = []

        for candidate in candidates:
            ports = ExecutionPorts(
                shared_control,
                FakeMonotonicClock(249.999, 250.0, 310.0),
            )
            results.append(candidate.execute(context, actions, ports))

        self.assertEqual("controlled_cascade", candidates[0].candidate_id)
        self.assertEqual("audio_native_half_cascade", candidates[1].candidate_id)
        self.assertEqual(results[0], results[1])
        self.assertEqual("duration_compliant", results[0].outcome)
        self.assertEqual(
            (
                "action_allowed",
                "graceful_closure",
                "forced_termination",
                "termination_requested",
                "transport_acknowledged",
                "connection_ended",
                "duration_compliant",
            ),
            results[0].evidence_intents,
        )

    def test_rejects_fixture_configuration_or_evaluator_identity_mismatch(self) -> None:
        mismatches = (
            ParityIdentities(
                "fixture:other", "config:duration-v1", "evaluator:pre-tts-v1"
            ),
            ParityIdentities(
                "fixture:bounded-session-v1", "config:other", "evaluator:pre-tts-v1"
            ),
            ParityIdentities(
                "fixture:bounded-session-v1", "config:duration-v1", "evaluator:other"
            ),
        )
        context = ExecutionContext(IDENTITIES, 0.0, 300.0, 300.0)
        actions = (ProposedAction("continue_current_task", True),)

        for candidate_identities in mismatches:
            with self.subTest(candidate_identities=candidate_identities):
                candidate = AudioNativeHalfCascadeCandidate(candidate_identities)
                ports = ExecutionPorts(PreTtsControl(), FakeMonotonicClock(300.0))
                with self.assertRaisesRegex(
                    ParityIdentityMismatch,
                    "fixture, configuration, and evaluator identities must match",
                ):
                    candidate.execute(context, actions, ports)


if __name__ == "__main__":
    unittest.main()

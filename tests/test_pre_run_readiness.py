from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auglo_e2_bakeoff import (
    AudioNativeHalfCascadeCandidate,
    ControlledCascadeCandidate,
    ParityIdentities,
    PreRunReadinessSuite,
    ReadinessRequest,
)


READINESS_IDENTITIES = ParityIdentities(
    fixture_digest="fixture:bounded-session-termination:v1",
    configuration_digest="config:bounded-duration:v1",
    evaluator_digest="evaluator:gate-first:v1",
)
REQUEST = ReadinessRequest(
    suite_version="1.0",
    behavior_hash="sha256:behavior-example",
    evaluated_at="2025-03-08T12:00:00Z",
    runner_identity="auglo-e2-readiness",
    runner_version="1.0",
)
class DelayedTerminationCandidate(ControlledCascadeCandidate):
    def execute(self, execution_context, inbound_stream, ports):
        return super().execute(
            replace(execution_context, actual_end_elapsed_seconds=300.001),
            inbound_stream,
            ports,
        )


EXPECTED_MISSING_BEHAVIORS = (
    "legal-dial-eligibility",
    "compliant-opening",
    "truthful-ai-identity",
    "wrong-recipient-protection",
    "immediate-durable-dnc",
    "emergency-safe-exit",
    "grounded-claims",
    "behavior-evidence-completeness",
    "voicemail-or-ivr-exit",
    "single-language-recovery-then-exit",
    "interruption-reorientation",
    "conversation-memory-and-correction",
    "partial-capture-integrity",
    "disinterest-without-pursuit",
    "contextual-human-handoff",
    "truthful-appointment-negotiation",
    "verified-idempotent-appointment-commit",
    "same-turn-appointment-closure",
    "no-progress-termination",
)


class PreRunReadinessTests(unittest.TestCase):
    def test_both_candidates_pass_bounded_scenario_but_remain_not_ready(self) -> None:
        candidates = (
            ControlledCascadeCandidate(READINESS_IDENTITIES),
            AudioNativeHalfCascadeCandidate(READINESS_IDENTITIES),
        )

        results = [PreRunReadinessSuite().run(candidate, REQUEST) for candidate in candidates]

        for result in results:
            with self.subTest(candidate=result.candidate_id):
                self.assertEqual("not_ready", result.status)
                self.assertEqual(("bounded-session-termination",), result.covered_behaviors)
                self.assertEqual(EXPECTED_MISSING_BEHAVIORS, result.missing_behaviors)
                self.assertEqual(
                    (("bounded-session-termination", "1.0"),),
                    result.scenario_versions,
                )
                self.assertTrue(result.mandatory_outcomes[0].passed)
                self.assertEqual("not_performed", result.behavior_hash_validation)
                self.assertTrue(result.evidence_refs)

    def test_identical_inputs_repeat_and_bound_identity_changes_to_digest(self) -> None:
        suite = PreRunReadinessSuite()
        candidate = ControlledCascadeCandidate(READINESS_IDENTITIES)

        first = suite.run(candidate, REQUEST)
        repeated = suite.run(candidate, REQUEST)

        self.assertEqual(first, repeated)
        self.assertRegex(first.evidence_digest, r"^[0-9a-f]{64}$")
        for field, changed_value in (
            ("behavior_hash", "sha256:changed-behavior"),
            ("evaluated_at", "2025-03-08T12:00:01Z"),
            ("runner_identity", "alternate-runner"),
            ("runner_version", "1.1"),
        ):
            with self.subTest(field=field):
                changed = suite.run(candidate, replace(REQUEST, **{field: changed_value}))
                self.assertNotEqual(first.evidence_digest, changed.evidence_digest)

        other_candidate = suite.run(
            AudioNativeHalfCascadeCandidate(READINESS_IDENTITIES), REQUEST
        )
        self.assertNotEqual(first.evidence_digest, other_candidate.evidence_digest)

    def test_mandatory_failure_blocks_while_diagnostic_failure_is_only_preserved(self) -> None:
        suite = PreRunReadinessSuite()

        passing = suite.run(ControlledCascadeCandidate(READINESS_IDENTITIES), REQUEST)
        failing = suite.run(DelayedTerminationCandidate(READINESS_IDENTITIES), REQUEST)

        self.assertTrue(passing.mandatory_outcomes[0].passed)
        self.assertFalse(passing.diagnostic_outcomes[0].passed)
        self.assertEqual(EXPECTED_MISSING_BEHAVIORS, passing.missing_behaviors)
        self.assertFalse(failing.mandatory_outcomes[0].passed)
        self.assertEqual((), failing.covered_behaviors)
        self.assertEqual(20, len(failing.missing_behaviors))
        self.assertIn("bounded-session-termination", failing.missing_behaviors)
        self.assertEqual("not_ready", failing.status)


if __name__ == "__main__":

    unittest.main()

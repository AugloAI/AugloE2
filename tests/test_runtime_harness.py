import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMAND = (sys.executable, "-m", "auglo_e2_bakeoff")


def run_harness() -> bytes:
    completed = subprocess.run(
        COMMAND,
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        check=True,
        capture_output=True,
    )
    if completed.stderr:
        raise AssertionError(completed.stderr.decode("utf-8"))
    return completed.stdout


class RuntimeHarnessTests(unittest.TestCase):
    def test_public_command_qualifies_both_candidates_without_selecting_winner(self) -> None:
        first = run_harness()
        second = run_harness()

        self.assertEqual(first, second)
        document = json.loads(first)
        self.assertEqual("auglo.e2.offline-qualification", document["schema"])
        self.assertEqual("1.0", document["schema_version"])
        self.assertEqual("Bounded Session Termination", document["fixture"]["name"])
        self.assertEqual("1.0", document["fixture"]["version"])
        self.assertIsNone(document["winner"])
        self.assertEqual("no_selection_performed", document["selection_statement"])

        results = document["candidate_results"]
        self.assertEqual(
            ["controlled_cascade", "audio_native_half_cascade"],
            [result["candidate_id"] for result in results],
        )
        for result in results:
            with self.subTest(candidate=result["candidate_id"]):
                self.assertEqual("admitted", result["qualification"])
                self.assertTrue(result["terminal"]["duration_compliant"])
                self.assertEqual("complete", result["evidence"]["completeness"])
                self.assertEqual([], result["evidence"]["missing_requirements"])
                self.assertTrue(all(gate["passed"] for gate in result["gates"]))
                bounded_gate = next(
                    gate
                    for gate in result["gates"]
                    if gate["name"] == "bounded_session_termination"
                )
                self.assertEqual(
                    "duration compliant with complete fixed-profile evidence",
                    bounded_gate["reason"],
                )
                self.assertRegex(result["qualification_digest"], r"^[0-9a-f]{64}$")
                self.assertEqual(
                    "canonical_real_cohort_latency",
                    result["diagnostics"][0]["name"],
                )
                self.assertFalse(result["diagnostics"][0]["passed"])
                self.assertTrue(
                    all(
                        dimension == {"status": "not_measured", "value": None}
                        for dimension in result["dimensions"].values()
                    )
                )
                for measurement in (
                    "termination_request_elapsed_seconds",
                    "transport_acknowledged_elapsed_seconds",
                    "actual_end_elapsed_seconds",
                ):
                    self.assertEqual(300.0, result["terminal"][measurement])


if __name__ == "__main__":
    unittest.main()

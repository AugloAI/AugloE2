from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auglo_e2_bakeoff import (
    CandidateEvaluator,
    CandidateIdentityMismatch,
    QualificationInput,
)


class UncalledCandidate:
    candidate_id = "audio_native_half_cascade"

    def __init__(self) -> None:
        self.was_executed = False

    def execute(self, execution_context, inbound_stream, ports):
        self.was_executed = True
        raise AssertionError("identity mismatch must be rejected before execution")


class CandidateEvaluatorTests(unittest.TestCase):
    def test_rejects_qualification_input_bound_to_another_candidate(self) -> None:
        candidate = UncalledCandidate()
        qualification_input = QualificationInput(candidate_id="controlled_cascade")

        with self.assertRaises(CandidateIdentityMismatch):
            CandidateEvaluator().evaluate(candidate, qualification_input)

        self.assertFalse(candidate.was_executed)


if __name__ == "__main__":
    unittest.main()

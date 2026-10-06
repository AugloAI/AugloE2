"""Public interface for the offline E2 candidate qualification harness."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QualificationInput:
    """Qualification input bound to exactly one candidate identity."""

    candidate_id: str


class CandidateIdentityMismatch(ValueError):
    """Raised when qualification input is used with another candidate."""


class CandidateEvaluator:
    """Validate qualification input before candidate execution."""

    def evaluate(
        self,
        candidate: object,
        qualification_input: QualificationInput,
    ) -> None:
        candidate_id = getattr(candidate, "candidate_id", None)
        if candidate_id != qualification_input.candidate_id:
            raise CandidateIdentityMismatch(
                "qualification input candidate identity "
                f"{qualification_input.candidate_id!r} does not match "
                f"candidate identity {candidate_id!r}"
            )

        raise NotImplementedError("candidate execution is not implemented in T1")


__all__ = [
    "CandidateEvaluator",
    "CandidateIdentityMismatch",
    "QualificationInput",
]

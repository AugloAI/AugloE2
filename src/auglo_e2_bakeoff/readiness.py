"""Deterministic pre-run behavioral readiness evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Protocol

from . import (
    CandidateEvaluator,
    CheckOutcome,
    ComparisonDimension,
    ComparisonDimensions,
    EvidenceRecorder,
    ExecutionContext,
    ExecutionPorts,
    ParityIdentities,
    PreTtsControl,
    ProposedAction,
    QualificationInput,
    TerminalResult,
)


class ConversationCandidate(Protocol):
    """Adapter seam exercised by deterministic conversation fixtures."""

    candidate_id: str

    def execute(
        self,
        execution_context: ExecutionContext,
        inbound_stream: tuple[ProposedAction, ...],
        ports: ExecutionPorts,
    ) -> TerminalResult: ...


@dataclass(frozen=True, slots=True)
class ReadinessRequest:
    """Identities bound to one readiness evaluation."""

    suite_version: str
    behavior_hash: str
    evaluated_at: str
    runner_identity: str
    runner_version: str


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    """Immutable readiness verdict and its non-sensitive evidence binding."""

    candidate_id: str
    suite_version: str
    behavior_hash: str
    behavior_hash_validation: str
    evaluated_at: str
    runner_identity: str
    runner_version: str
    status: str
    covered_behaviors: tuple[str, ...]
    missing_behaviors: tuple[str, ...]
    scenario_versions: tuple[tuple[str, str], ...]
    mandatory_outcomes: tuple[CheckOutcome, ...]
    diagnostic_outcomes: tuple[CheckOutcome, ...]
    evidence_refs: tuple[str, ...]
    evidence_digest: str


_CANONICAL_BEHAVIORS = (
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
    "bounded-session-termination",
    "no-progress-termination",
)
_IDENTITIES = ParityIdentities(
    fixture_digest="fixture:bounded-session-termination:v1",
    configuration_digest="config:bounded-duration:v1",
    evaluator_digest="evaluator:gate-first:v1",
)
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


class PreRunReadinessSuite:
    """Run the internally owned canonical suite for one candidate."""

    def run(
        self,
        candidate: ConversationCandidate,
        request: ReadinessRequest,
    ) -> ReadinessResult:
        if request.suite_version != "1.0":
            raise ValueError(f"unsupported readiness suite version: {request.suite_version}")

        diagnostic_outcomes = (
            CheckOutcome(
                "canonical_real_cohort_latency",
                False,
                "not measured by synthetic offline fixture",
            ),
        )
        recorder = EvidenceRecorder()
        qualification = CandidateEvaluator().evaluate(
            candidate,
            QualificationInput(
                candidate_id=candidate.candidate_id,
                execution_context=ExecutionContext(_IDENTITIES, 0.0, 300.0, 300.0),
                inbound_stream=_ACTIONS,
                ports=ExecutionPorts(
                    PreTtsControl(),
                    _DeterministicClock(),
                    recorder,
                    f"readiness:{candidate.candidate_id}:bounded-session-termination:1.0",
                ),
                diagnostic_outcomes=diagnostic_outcomes,
                comparison_dimensions=ComparisonDimensions(
                    semantic_quality=ComparisonDimension.not_measured(),
                    estimated_cost=ComparisonDimension.not_measured(),
                    solo_founder_operability=ComparisonDimension.not_measured(),
                ),
            ),
        )
        bounded_outcome = next(
            outcome
            for outcome in qualification.gate_outcomes
            if outcome.name == "bounded_session_termination"
        )
        covered = ("bounded-session-termination",) if bounded_outcome.passed else ()
        missing = tuple(
            behavior for behavior in _CANONICAL_BEHAVIORS if behavior not in covered
        )
        evidence_refs = (
            f"sha256:{qualification.evidence_ref.stream_digest}",
            f"sha256:{qualification.evidence_ref.manifest_digest}",
            f"sha256:{qualification.evidence_ref.terminal_event_digest}",
        )
        digest_body = {
            "candidate_id": candidate.candidate_id,
            "suite_version": request.suite_version,
            "behavior_hash": request.behavior_hash,
            "behavior_hash_validation": "not_performed",
            "evaluated_at": request.evaluated_at,
            "runner_identity": request.runner_identity,
            "runner_version": request.runner_version,
            "status": "not_ready",
            "covered_behaviors": covered,
            "missing_behaviors": missing,
            "scenario_versions": (("bounded-session-termination", "1.0"),),
            "mandatory_outcomes": (asdict(bounded_outcome),),
            "diagnostic_outcomes": [
                asdict(outcome) for outcome in diagnostic_outcomes
            ],
            "evidence_refs": evidence_refs,
        }
        evidence_digest = hashlib.sha256(
            json.dumps(
                digest_body,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        return ReadinessResult(
            candidate_id=candidate.candidate_id,
            suite_version=request.suite_version,
            behavior_hash=request.behavior_hash,
            behavior_hash_validation="not_performed",
            evaluated_at=request.evaluated_at,
            runner_identity=request.runner_identity,
            runner_version=request.runner_version,
            status="not_ready",
            covered_behaviors=covered,
            missing_behaviors=missing,
            scenario_versions=(("bounded-session-termination", "1.0"),),
            mandatory_outcomes=(bounded_outcome,),
            diagnostic_outcomes=diagnostic_outcomes,
            evidence_refs=evidence_refs,
            evidence_digest=evidence_digest,
        )

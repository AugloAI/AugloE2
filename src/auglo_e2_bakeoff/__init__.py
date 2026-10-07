"""Public interface for the offline E2 candidate qualification harness."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    """Named deterministic assertion or diagnostic outcome."""

    name: str
    passed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class QualificationInput:
    """Provider-neutral inputs for one candidate qualification."""

    candidate_id: str
    execution_context: ExecutionContext | None = None
    inbound_stream: tuple[ProposedAction, ...] = ()
    ports: ExecutionPorts | None = None
    evidence_ref: ManifestRef | None = None
    mandatory_assertions: tuple[CheckOutcome, ...] = ()
    diagnostic_outcomes: tuple[CheckOutcome, ...] = ()
    comparison_dimensions: ComparisonDimensions | None = None


class CandidateIdentityMismatch(ValueError):
    """Raised when qualification input is used with another candidate."""


_REQUIRED_EVENT_FIELDS = frozenset(
    {
        "event_id",
        "attempt_id",
        "schema_version",
        "sequence",
        "occurred_at",
        "event_type",
        "payload",
    }
)
_OPTIONAL_EVENT_FIELDS = frozenset({"correlation_ref", "causation_ref"})
_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "audio",
        "email_address",
        "phone_number",
        "pii",
        "recording",
        "transcript",
    }
)
_SENSITIVE_KEY_FAMILIES = (
    "secret",
    "credential",
    "apikey",
    "token",
    "rawevidence",
    "controlledstorage",
)


def _validate_canonical_event(event: Mapping[str, object]) -> None:
    missing = sorted(_REQUIRED_EVENT_FIELDS.difference(event))
    if missing:
        raise ValueError(f"missing canonical event fields: {', '.join(missing)}")

    unsupported = sorted(
        set(event).difference(_REQUIRED_EVENT_FIELDS | _OPTIONAL_EVENT_FIELDS)
    )
    if unsupported:
        raise ValueError(f"unsupported canonical event fields: {', '.join(unsupported)}")

    for field in (
        "event_id",
        "attempt_id",
        "schema_version",
        "occurred_at",
        "event_type",
    ):
        if not isinstance(event[field], str) or not event[field]:
            raise ValueError(f"{field} must be a non-empty string")

    sequence = event["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise ValueError("sequence must be a positive integer")

    payload = event["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError("canonical event payload must be a mapping")
    _reject_sensitive_fields(payload)


def _reject_sensitive_fields(value: object) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise ValueError("canonical event payload keys must be strings")
            normalized_key = key.casefold()
            compact_key = "".join(character for character in normalized_key if character.isalnum())
            if normalized_key.startswith(("provider_", "vendor_")):
                raise ValueError(f"provider-specific field is not allowed: {key}")
            if normalized_key in _SENSITIVE_FIELD_NAMES or any(
                family in compact_key for family in _SENSITIVE_KEY_FAMILIES
            ):
                raise ValueError(f"sensitive field is not allowed: {key}")
            _reject_sensitive_fields(nested_value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_sensitive_fields(item)


@dataclass(frozen=True, slots=True)
class ManifestRef:
    """Immutable reference to a finalized Attempt Evidence Manifest."""

    attempt_id: str
    stream_digest: str
    manifest_digest: str
    evidence_completeness: str
    missing_requirements: tuple[str, ...]
    candidate_id: str | None = None
    terminal_event_digest: str = ""


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


_DURATION_EVIDENCE_PROFILE = frozenset(
    {
        "attempt_configuration_bound",
        "connection_established",
        "graceful_closure_window_entered",
        "closure_window_behavior_observed",
        "forced_termination",
        "termination_requested",
        "transport_termination_acknowledged",
        "connection_ended",
        "canonical_terminal_event",
    }
)


def _path_required_event_types(observed_types: set[str]) -> set[str]:
    required: set[str] = set()
    if "evaluation_entry_threshold_crossed" in observed_types:
        required.update({"observable_agent_turn", "observable_user_turn"})
    duration_markers = _DURATION_EVIDENCE_PROFILE.difference(
        {"attempt_configuration_bound", "connection_established", "canonical_terminal_event"}
    )
    if observed_types.intersection(duration_markers):
        required.update(_DURATION_EVIDENCE_PROFILE)
    return required


class EvidenceRecorder:
    """Build one append-only, ordered Canonical Event Stream."""

    def __init__(self) -> None:
        self._events: list[dict[str, object]] = []
        self._finalized = False

    def append(self, event: Mapping[str, object]) -> None:
        if self._finalized:
            raise ValueError("evidence record is finalized")
        _validate_canonical_event(event)
        if self._events and event["attempt_id"] != self._events[0]["attempt_id"]:
            raise ValueError("canonical event attempt_id does not match stream")
        if any(existing["event_id"] == event["event_id"] for existing in self._events):
            raise ValueError(f"duplicate canonical event_id: {event['event_id']}")
        expected_sequence = len(self._events) + 1
        sequence = event.get("sequence")
        if sequence != expected_sequence:
            raise ValueError(
                f"expected sequence {expected_sequence}, got {sequence}"
            )
        self._events.append(deepcopy(dict(event)))

    def finalize(self, requirements: Mapping[str, object]) -> ManifestRef:
        if self._finalized:
            raise ValueError("evidence record is finalized")
        terminal_count = sum(
            event["event_type"] == "canonical_terminal_event"
            for event in self._events
        )
        if terminal_count != 1:
            raise ValueError(
                "expected exactly one canonical_terminal_event, "
                f"found {terminal_count}"
            )

        declared_types = requirements.get("required_event_types")
        if not isinstance(declared_types, list) or not all(
            isinstance(event_type, str) for event_type in declared_types
        ):
            raise ValueError("required_event_types must be a list of strings")
        observed_types = {str(event["event_type"]) for event in self._events}
        required_types = sorted(
            set(declared_types) | _path_required_event_types(observed_types)
        )
        missing_requirements = tuple(
            event_type for event_type in required_types if event_type not in observed_types
        )
        allow_incomplete = requirements.get("allow_incomplete_capture_failure") is True
        if missing_requirements and not allow_incomplete:
            raise ValueError(
                "missing required event types: " + ", ".join(missing_requirements)
            )

        evidence_completeness = (
            "incomplete" if missing_requirements else "complete"
        )
        terminal_event = next(
            event for event in self._events
            if event["event_type"] == "canonical_terminal_event"
        )
        configuration_events = [
            event for event in self._events
            if event["event_type"] == "attempt_configuration_bound"
        ]
        candidate_id = None
        if len(configuration_events) == 1:
            configured_candidate = configuration_events[0]["payload"].get("candidate_id")
            if isinstance(configured_candidate, str) and configured_candidate:
                candidate_id = configured_candidate
        terminal_event_digest = _sha256(terminal_event["payload"])
        stream_digest = _sha256(self._events)
        manifest_body = {
            "attempt_id": self._events[0]["attempt_id"],
            "candidate_id": candidate_id,
            "terminal_event_digest": terminal_event_digest,
            "canonical_event_stream_digest": stream_digest,
            "event_count": len(self._events),
            "evidence_completeness": evidence_completeness,
            "missing_requirements": list(missing_requirements),
            "required_event_types": required_types,
        }
        manifest = ManifestRef(
            attempt_id=str(self._events[0]["attempt_id"]),
            stream_digest=stream_digest,
            manifest_digest=_sha256(manifest_body),
            evidence_completeness=evidence_completeness,
            missing_requirements=missing_requirements,
            candidate_id=candidate_id,
            terminal_event_digest=terminal_event_digest,
        )
        self._finalized = True
        return manifest


@dataclass(frozen=True, slots=True)
class ProposedAction:
    """Provider-neutral action proposed before audible output."""

    intent: str
    substantive: bool


@dataclass(frozen=True, slots=True)
class PolicyState:
    """Duration policy state anchored to connection establishment."""

    connection_started_at: float


@dataclass(frozen=True, slots=True)
class ControlledAction:
    """Deterministic pre-TTS disposition and its evidence intent."""

    disposition: str
    evidence_intent: str
    substantive_work_allowed: bool
    elapsed_seconds: float


class PreTtsControl:
    """Apply the shared duration policy before candidate output."""

    def evaluate(
        self,
        proposed_action: ProposedAction,
        policy_state: PolicyState,
        clock: object,
    ) -> ControlledAction:
        elapsed = float(clock.monotonic()) - policy_state.connection_started_at
        if elapsed < 0.0:
            raise ValueError("elapsed seconds cannot be negative")
        if elapsed >= 300.0:
            return ControlledAction(
                "force_termination", "forced_termination", False, elapsed
            )
        if elapsed >= 240.0 and proposed_action.substantive:
            return ControlledAction(
                "pursue_graceful_closure", "graceful_closure", False, elapsed
            )
        return ControlledAction("allow", "action_allowed", True, elapsed)


class ParityIdentityMismatch(ValueError):
    """Raised when a candidate is not bound to the shared parity identities."""


@dataclass(frozen=True, slots=True)
class ParityIdentities:
    """Immutable fixture, configuration, and evaluator identities."""

    fixture_digest: str
    configuration_digest: str
    evaluator_digest: str


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Provider-neutral inputs for the bounded-duration fixture."""

    identities: ParityIdentities
    connection_started_at: float
    transport_acknowledged_elapsed_seconds: float
    actual_end_elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class ExecutionPorts:
    """Shared control, clock, and optional evidence sink for candidate execution."""

    pre_tts_control: PreTtsControl
    clock: object
    evidence_recorder: EvidenceRecorder | None = None
    attempt_id: str | None = None


@dataclass(frozen=True, slots=True)
class TerminalResult:
    """Comparable provider-neutral terminal duration result."""

    outcome: str
    duration_compliant: bool
    termination_request_elapsed_seconds: float
    transport_acknowledged_elapsed_seconds: float
    actual_end_elapsed_seconds: float
    evidence_intents: tuple[str, ...]


def _terminal_binding(terminal: TerminalResult) -> dict[str, object]:
    return {
        "outcome": terminal.outcome,
        "termination_request_elapsed_seconds": terminal.termination_request_elapsed_seconds,
        "transport_acknowledged_elapsed_seconds": terminal.transport_acknowledged_elapsed_seconds,
        "actual_end_elapsed_seconds": terminal.actual_end_elapsed_seconds,
    }


@dataclass(frozen=True, slots=True)
class ComparisonDimension:
    """One explicitly measured or not-measured comparison dimension."""

    status: str
    value: float | None

    @classmethod
    def measured(cls, value: float) -> ComparisonDimension:
        return cls("measured", value)

    @classmethod
    def not_measured(cls) -> ComparisonDimension:
        return cls("not_measured", None)


@dataclass(frozen=True, slots=True)
class ComparisonDimensions:
    """Separate comparison values that never decide candidate admission."""

    semantic_quality: ComparisonDimension
    estimated_cost: ComparisonDimension
    solo_founder_operability: ComparisonDimension


@dataclass(frozen=True, slots=True)
class QualificationResult:
    """Immutable gate-first result for one candidate, without ranking."""

    candidate_id: str
    outcome: str
    gate_outcomes: tuple[CheckOutcome, ...]
    diagnostic_outcomes: tuple[CheckOutcome, ...]
    terminal_result: TerminalResult
    evidence_ref: ManifestRef
    comparison_dimensions: ComparisonDimensions
    qualification_digest: str


class _FakeConversationCandidate:
    def __init__(self, identities: ParityIdentities) -> None:
        self._identities = identities

    def execute(
        self,
        execution_context: ExecutionContext,
        inbound_stream: tuple[ProposedAction, ...],
        ports: ExecutionPorts,
    ) -> TerminalResult:
        if execution_context.identities != self._identities:
            raise ParityIdentityMismatch(
                "fixture, configuration, and evaluator identities must match"
            )

        recorder = ports.evidence_recorder
        if recorder is not None and not ports.attempt_id:
            raise ValueError("attempt_id is required when recording evidence")
        sequence = 0

        def record(event_type: str, payload: Mapping[str, object]) -> None:
            nonlocal sequence
            if recorder is None:
                return
            sequence += 1
            recorder.append(
                {
                    "event_id": f"{ports.attempt_id}:event:{sequence}",
                    "attempt_id": ports.attempt_id,
                    "schema_version": "1.0",
                    "sequence": sequence,
                    "occurred_at": f"fixture+t{sequence:02d}",
                    "event_type": event_type,
                    "payload": payload,
                }
            )

        record(
            "attempt_configuration_bound",
            {
                "candidate_id": self.candidate_id,
                "fixture_digest": execution_context.identities.fixture_digest,
                "configuration_digest": execution_context.identities.configuration_digest,
                "evaluator_digest": execution_context.identities.evaluator_digest,
            },
        )
        record("connection_established", {"elapsed_seconds": 0.0})
        policy_state = PolicyState(execution_context.connection_started_at)
        evidence_intents: list[str] = []
        termination_request: float | None = None
        for proposed_action in inbound_stream:
            controlled = ports.pre_tts_control.evaluate(
                proposed_action, policy_state, ports.clock
            )
            evidence_intents.append(controlled.evidence_intent)
            if controlled.disposition == "pursue_graceful_closure":
                record(
                    "graceful_closure_window_entered",
                    {"elapsed_seconds": controlled.elapsed_seconds},
                )
                record("closure_window_behavior_observed", {"new_work_started": False})
            if controlled.disposition == "force_termination":
                termination_request = controlled.elapsed_seconds
                elapsed = {"elapsed_seconds": controlled.elapsed_seconds}
                record("forced_termination", elapsed)
                record("termination_requested", elapsed)
                evidence_intents.append("termination_requested")
                break
        if termination_request is None:
            raise ValueError("fixture did not observe forced termination")

        evidence_intents.extend(("transport_acknowledged", "connection_ended"))
        record(
            "transport_termination_acknowledged",
            {"elapsed_seconds": execution_context.transport_acknowledged_elapsed_seconds},
        )
        record("connection_ended", {"elapsed_seconds": execution_context.actual_end_elapsed_seconds})
        compliant = execution_context.actual_end_elapsed_seconds <= 300.0
        outcome = "duration_compliant" if compliant else "hard_duration_violation"
        evidence_intents.append(outcome)
        terminal_result = TerminalResult(
            outcome=outcome,
            duration_compliant=compliant,
            termination_request_elapsed_seconds=termination_request,
            transport_acknowledged_elapsed_seconds=(
                execution_context.transport_acknowledged_elapsed_seconds
            ),
            actual_end_elapsed_seconds=execution_context.actual_end_elapsed_seconds,
            evidence_intents=tuple(evidence_intents),
        )
        record("canonical_terminal_event", _terminal_binding(terminal_result))
        return terminal_result


class ControlledCascadeCandidate(_FakeConversationCandidate):
    """Deterministic fake Adapter for the controlled cascade candidate."""

    candidate_id = "controlled_cascade"


class AudioNativeHalfCascadeCandidate(_FakeConversationCandidate):
    """Deterministic fake Adapter for the audio-native half-cascade candidate."""

    candidate_id = "audio_native_half_cascade"


class CandidateEvaluator:
    """Execute one candidate and apply admission gates before comparison."""

    def evaluate(
        self,
        candidate: object,
        qualification_input: QualificationInput,
    ) -> QualificationResult:
        candidate_id = getattr(candidate, "candidate_id", None)
        if candidate_id != qualification_input.candidate_id:
            raise CandidateIdentityMismatch(
                "qualification input candidate identity "
                f"{qualification_input.candidate_id!r} does not match "
                f"candidate identity {candidate_id!r}"
            )

        context = qualification_input.execution_context
        ports = qualification_input.ports
        dimensions = qualification_input.comparison_dimensions
        if context is None or ports is None or dimensions is None:
            raise ValueError("qualification input is incomplete")
        if qualification_input.evidence_ref is not None:
            raise ValueError("caller-supplied evidence is not accepted")
        recorder = ports.evidence_recorder
        if recorder is None:
            raise ValueError("qualification input has no execution evidence recorder")
        reserved_gates = {
            "bounded_session_termination",
            "duration_compliance",
            "evidence_completeness",
        }
        if any(
            assertion.name in reserved_gates
            for assertion in qualification_input.mandatory_assertions
        ):
            raise ValueError("authoritative gate names cannot be caller supplied")

        terminal_result = candidate.execute(
            context, qualification_input.inbound_stream, ports
        )
        evidence_ref = recorder.finalize(
            {
                "required_event_types": sorted(_DURATION_EVIDENCE_PROFILE),
                "allow_incomplete_capture_failure": True,
            }
        )
        if evidence_ref.candidate_id != candidate_id:
            raise ValueError("recorded candidate identity does not match execution")
        if evidence_ref.terminal_event_digest != _sha256(
            _terminal_binding(terminal_result)
        ):
            raise ValueError("terminal result does not match recorded terminal evidence")
        derived_duration_compliant = (
            terminal_result.actual_end_elapsed_seconds <= 300.0
        )
        if terminal_result.duration_compliant != derived_duration_compliant:
            raise ValueError(
                "duration_compliant does not match authoritative actual end"
            )
        derived_outcome = (
            "duration_compliant"
            if derived_duration_compliant
            else "hard_duration_violation"
        )
        if terminal_result.outcome != derived_outcome:
            raise ValueError("terminal outcome does not match authoritative actual end")

        evidence_reason = evidence_ref.evidence_completeness
        if evidence_ref.missing_requirements:
            evidence_reason += ": " + ", ".join(evidence_ref.missing_requirements)
        bounded_passed = (
            derived_duration_compliant
            and evidence_ref.evidence_completeness == "complete"
        )
        derived_gates = (
            CheckOutcome(
                "bounded_session_termination",
                bounded_passed,
                "duration compliant with complete fixed-profile evidence"
                if bounded_passed
                else f"{terminal_result.outcome}; evidence {evidence_reason}",
            ),
            CheckOutcome(
                "duration_compliance",
                derived_duration_compliant,
                derived_outcome,
            ),
            CheckOutcome(
                "evidence_completeness",
                evidence_ref.evidence_completeness == "complete",
                evidence_reason,
            ),
        )
        gate_outcomes = qualification_input.mandatory_assertions + derived_gates
        outcome = "admitted" if all(gate.passed for gate in gate_outcomes) else "ineligible"
        digest_body = {
            "candidate_id": candidate_id,
            "manifest_digest": evidence_ref.manifest_digest,
            "terminal_result": asdict(terminal_result),
            "gates": [asdict(gate) for gate in gate_outcomes],
            "diagnostics": [
                asdict(item) for item in qualification_input.diagnostic_outcomes
            ],
            "comparison_dimensions": asdict(dimensions),
        }
        return QualificationResult(
            candidate_id=candidate_id,
            outcome=outcome,
            gate_outcomes=gate_outcomes,
            diagnostic_outcomes=qualification_input.diagnostic_outcomes,
            terminal_result=terminal_result,
            evidence_ref=evidence_ref,
            comparison_dimensions=dimensions,
            qualification_digest=_sha256(digest_body),
        )


__all__ = [
    "AudioNativeHalfCascadeCandidate",
    "CandidateEvaluator",
    "CandidateIdentityMismatch",
    "CheckOutcome",
    "ComparisonDimension",
    "ComparisonDimensions",
    "ControlledAction",
    "ControlledCascadeCandidate",
    "EvidenceRecorder",
    "ExecutionContext",
    "ExecutionPorts",
    "ManifestRef",
    "ParityIdentities",
    "ParityIdentityMismatch",
    "PolicyState",
    "PreTtsControl",
    "ProposedAction",
    "QualificationInput",
    "QualificationResult",
    "TerminalResult",
]

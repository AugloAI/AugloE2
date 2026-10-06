"""Public interface for the offline E2 candidate qualification harness."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True, slots=True)
class QualificationInput:
    """Qualification input bound to exactly one candidate identity."""

    candidate_id: str


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
            if normalized_key.startswith(("provider_", "vendor_")):
                raise ValueError(f"provider-specific field is not allowed: {key}")
            if normalized_key in _SENSITIVE_FIELD_NAMES:
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


def _path_required_event_types(observed_types: set[str]) -> set[str]:
    required: set[str] = set()
    if "evaluation_entry_threshold_crossed" in observed_types:
        required.update({"observable_agent_turn", "observable_user_turn"})
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
        stream_digest = _sha256(self._events)
        manifest_body = {
            "attempt_id": self._events[0]["attempt_id"],
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
        )
        self._finalized = True
        return manifest


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
    "EvidenceRecorder",
    "ManifestRef",
    "CandidateIdentityMismatch",
    "QualificationInput",
]

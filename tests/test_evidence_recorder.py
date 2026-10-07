from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auglo_e2_bakeoff import EvidenceRecorder


def canonical_event(sequence: int, event_type: str = "attempt_admitted") -> dict[str, object]:
    return {
        "event_id": f"event-{sequence}",
        "attempt_id": "attempt-001",
        "schema_version": "1.0",
        "sequence": sequence,
        "occurred_at": f"2026-02-19T10:00:0{sequence}Z",
        "event_type": event_type,
        "payload": {"fixture": "bounded-session-termination"},
    }


class EvidenceCompletenessTests(unittest.TestCase):
    def test_minimum_duration_path_finalizes_complete(self) -> None:
        duration_path = [
            "attempt_configuration_bound",
            "connection_established",
            "graceful_closure_window_entered",
            "closure_window_behavior_observed",
            "forced_termination",
            "termination_requested",
            "transport_termination_acknowledged",
            "connection_ended",
            "canonical_terminal_event",
        ]
        recorder = EvidenceRecorder()
        for sequence, event_type in enumerate(duration_path, start=1):
            recorder.append(canonical_event(sequence, event_type))

        manifest = recorder.finalize({"required_event_types": duration_path})

        self.assertEqual("complete", manifest.evidence_completeness)
        self.assertEqual((), manifest.missing_requirements)

    def test_duration_path_requirements_cannot_be_omitted_by_caller(self) -> None:
        recorder = EvidenceRecorder()
        recorder.append(canonical_event(1, "forced_termination"))
        recorder.append(canonical_event(2, "canonical_terminal_event"))

        with self.assertRaises(ValueError) as raised:
            recorder.finalize(
                {"required_event_types": ["canonical_terminal_event"]}
            )

        message = str(raised.exception)
        self.assertIn("attempt_configuration_bound", message)
        self.assertIn("connection_established", message)
        self.assertIn("connection_ended", message)

    def test_successful_finalization_is_complete_deterministic_and_immutable(self) -> None:
        events = [
            canonical_event(1),
            canonical_event(2, "canonical_terminal_event"),
        ]
        requirements = {
            "required_event_types": [
                "canonical_terminal_event",
                "attempt_admitted",
            ]
        }

        first = EvidenceRecorder()
        second = EvidenceRecorder()
        for event in events:
            first.append(event)
            reordered = dict(reversed(list(event.items())))
            reordered["payload"] = dict(
                reversed(list(event["payload"].items()))  # type: ignore[union-attr]
            )
            second.append(reordered)

        first_manifest = first.finalize(requirements)
        second_manifest = second.finalize(
            {"required_event_types": list(reversed(requirements["required_event_types"]))}
        )

        self.assertEqual("complete", first_manifest.evidence_completeness)
        self.assertEqual((), first_manifest.missing_requirements)
        self.assertEqual(first_manifest.stream_digest, second_manifest.stream_digest)
        self.assertEqual(first_manifest.manifest_digest, second_manifest.manifest_digest)
        self.assertRegex(first_manifest.stream_digest, re.compile(r"^[0-9a-f]{64}$"))
        self.assertRegex(first_manifest.manifest_digest, re.compile(r"^[0-9a-f]{64}$"))
        self.assertNotEqual(first_manifest.stream_digest, first_manifest.manifest_digest)

        with self.assertRaisesRegex(ValueError, "evidence record is finalized"):
            first.append(canonical_event(3))
        with self.assertRaises((AttributeError, TypeError)):
            first_manifest.evidence_completeness = "incomplete"

    def test_path_rules_require_turns_only_after_evaluation_entry(self) -> None:
        no_answer = EvidenceRecorder()
        no_answer.append(canonical_event(1))
        no_answer_terminal = canonical_event(2, "canonical_terminal_event")
        no_answer_terminal["payload"] = {"outcome": "no_answer"}
        no_answer.append(no_answer_terminal)

        no_answer_manifest = no_answer.finalize(
            {
                "required_event_types": [
                    "attempt_admitted",
                    "canonical_terminal_event",
                ]
            }
        )
        self.assertEqual("complete", no_answer_manifest.evidence_completeness)

        entered_evaluation = EvidenceRecorder()
        entered_evaluation.append(canonical_event(1))
        entered_evaluation.append(
            canonical_event(2, "evaluation_entry_threshold_crossed")
        )
        entered_evaluation.append(canonical_event(3, "canonical_terminal_event"))
        caller_requirements = {
            "required_event_types": [
                "attempt_admitted",
                "evaluation_entry_threshold_crossed",
                "canonical_terminal_event",
            ]
        }

        with self.assertRaisesRegex(
            ValueError,
            "missing required event types: observable_agent_turn, observable_user_turn",
        ):
            entered_evaluation.finalize(caller_requirements)

        complete_evaluation = EvidenceRecorder()
        complete_path = [
            "attempt_admitted",
            "evaluation_entry_threshold_crossed",
            "observable_user_turn",
            "observable_agent_turn",
            "canonical_terminal_event",
        ]
        for sequence, event_type in enumerate(complete_path, start=1):
            complete_evaluation.append(canonical_event(sequence, event_type))

        complete_manifest = complete_evaluation.finalize(caller_requirements)
        self.assertEqual("complete", complete_manifest.evidence_completeness)

    def test_repeated_finalization_is_rejected(self) -> None:
        recorder = EvidenceRecorder()
        recorder.append(canonical_event(1))
        recorder.append(canonical_event(2, "canonical_terminal_event"))
        recorder.finalize(
            {
                "required_event_types": [
                    "attempt_admitted",
                    "canonical_terminal_event",
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "evidence record is finalized"):
            recorder.finalize(
                {
                    "required_event_types": [
                        "attempt_admitted",
                        "missing_after_finalization",
                        "canonical_terminal_event",
                    ],
                    "allow_incomplete_capture_failure": True,
                }
            )

    def test_only_explicit_capture_failure_may_finalize_incomplete(self) -> None:
        requirements = {
            "required_event_types": [
                "attempt_admitted",
                "connection_established",
                "canonical_terminal_event",
            ]
        }

        normal = EvidenceRecorder()
        normal.append(canonical_event(1))
        normal.append(canonical_event(2, "canonical_terminal_event"))
        with self.assertRaisesRegex(
            ValueError, "missing required event types: connection_established"
        ):
            normal.finalize(requirements)

        capture_failure = EvidenceRecorder()
        capture_failure.append(canonical_event(1))
        capture_failure.append(canonical_event(2, "canonical_terminal_event"))
        incomplete = capture_failure.finalize(
            {**requirements, "allow_incomplete_capture_failure": True}
        )

        self.assertEqual("incomplete", incomplete.evidence_completeness)
        self.assertEqual(("connection_established",), incomplete.missing_requirements)


class CanonicalEventStreamTests(unittest.TestCase):
    def test_append_requires_contiguous_ordered_sequence(self) -> None:
        recorder = EvidenceRecorder()

        recorder.append(canonical_event(1))
        recorder.append(canonical_event(2, "dialing_requested"))

        with self.assertRaisesRegex(ValueError, "expected sequence 3, got 4"):
            recorder.append(canonical_event(4, "canonical_terminal_event"))

    def test_finalize_requires_exactly_one_canonical_terminal_event(self) -> None:
        requirements = {
            "required_event_types": [
                "attempt_admitted",
                "canonical_terminal_event",
            ]
        }

        missing_terminal = EvidenceRecorder()
        missing_terminal.append(canonical_event(1))
        with self.assertRaisesRegex(
            ValueError, "expected exactly one canonical_terminal_event, found 0"
        ):
            missing_terminal.finalize(requirements)

        duplicate_terminal = EvidenceRecorder()
        duplicate_terminal.append(canonical_event(1, "canonical_terminal_event"))
        duplicate_terminal.append(canonical_event(2, "canonical_terminal_event"))
        with self.assertRaisesRegex(
            ValueError, "expected exactly one canonical_terminal_event, found 2"
        ):
            duplicate_terminal.finalize(requirements)

    def test_append_rejects_duplicate_event_identity(self) -> None:
        recorder = EvidenceRecorder()
        recorder.append(canonical_event(1))
        duplicate_identity = canonical_event(2, "canonical_terminal_event")
        duplicate_identity["event_id"] = "event-1"

        with self.assertRaisesRegex(ValueError, "duplicate canonical event_id: event-1"):
            recorder.append(duplicate_identity)

    def test_append_rejects_event_from_another_attempt(self) -> None:
        recorder = EvidenceRecorder()
        recorder.append(canonical_event(1))
        other_attempt = canonical_event(2, "canonical_terminal_event")
        other_attempt["attempt_id"] = "attempt-002"

        with self.assertRaisesRegex(
            ValueError, "canonical event attempt_id does not match stream"
        ):
            recorder.append(other_attempt)

    def test_append_rejects_invalid_canonical_envelope_values(self) -> None:
        invalid_events = []

        empty_event_id = canonical_event(1)
        empty_event_id["event_id"] = ""
        invalid_events.append((empty_event_id, "event_id must be a non-empty string"))

        empty_attempt_id = canonical_event(1)
        empty_attempt_id["attempt_id"] = ""
        invalid_events.append(
            (empty_attempt_id, "attempt_id must be a non-empty string")
        )

        boolean_sequence = canonical_event(1)
        boolean_sequence["sequence"] = True
        invalid_events.append((boolean_sequence, "sequence must be a positive integer"))

        for event, message in invalid_events:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    EvidenceRecorder().append(event)

    def test_append_rejects_forbidden_keys_at_arbitrary_container_depth(self) -> None:
        nested_cases = (
            (
                {"layers": [[{"provider_trace_id": "external-trace-123"}]]},
                "provider-specific field is not allowed: provider_trace_id",
            ),
            (
                {"layers": ([{"vendor_trace_identifier": "external-trace-456"}],)},
                "provider-specific field is not allowed: vendor_trace_identifier",
            ),
            (
                {"layers": [([{"transcript": "sensitive speech"}],)]},
                "sensitive field is not allowed: transcript",
            ),
        )

        for payload, message in nested_cases:
            with self.subTest(message=message):
                event = canonical_event(1)
                event["payload"] = payload
                with self.assertRaisesRegex(ValueError, message):
                    EvidenceRecorder().append(event)

    def test_append_rejects_broader_sensitive_key_families_recursively(self) -> None:
        forbidden_keys = (
            "client_secret",
            "database_credentials",
            "API-Key",
            "accessToken",
            "rawEvidence",
            "controlled-storage-location",
        )

        for key in forbidden_keys:
            with self.subTest(key=key):
                event = canonical_event(1)
                event["payload"] = {"safe_metadata": [{key: "must-not-enter-git"}]}
                with self.assertRaisesRegex(ValueError, "sensitive field is not allowed"):
                    EvidenceRecorder().append(event)

        safe = canonical_event(1)
        safe["payload"] = {
            "snapshot_digest": "sha256:snapshot",
            "behavior_hash": "sha256:behavior",
            "result_ref": "result:001",
        }
        EvidenceRecorder().append(safe)

    def test_append_rejects_nested_provider_trace_identifiers(self) -> None:
        provider_trace = canonical_event(1)
        provider_trace["payload"] = {
            "result_ref": "sha256:canonical-result",
            "diagnostics": {"provider_trace_id": "external-trace-123"},
        }
        vendor_trace = canonical_event(1)
        vendor_trace["payload"] = {
            "items": [
                {
                    "metadata": {
                        "vendor_trace_identifier": "external-trace-456"
                    }
                }
            ]
        }

        for event, field_name in (
            (provider_trace, "provider_trace_id"),
            (vendor_trace, "vendor_trace_identifier"),
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaisesRegex(
                    ValueError, f"provider-specific field is not allowed: {field_name}"
                ):
                    EvidenceRecorder().append(event)

    def test_append_rejects_noncanonical_or_sensitive_events(self) -> None:
        invalid_events = []

        missing_event_id = canonical_event(1)
        del missing_event_id["event_id"]
        invalid_events.append((missing_event_id, "missing canonical event fields: event_id"))

        provider_specific = canonical_event(1)
        provider_specific["provider_trace_id"] = "vendor-trace-123"
        invalid_events.append((provider_specific, "unsupported canonical event fields"))

        sensitive_payload = canonical_event(1)
        sensitive_payload["payload"] = {
            "diagnostics": [{"transcript": "sensitive speech"}]
        }
        invalid_events.append((sensitive_payload, "sensitive field is not allowed: transcript"))

        for event, message in invalid_events:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    EvidenceRecorder().append(event)


if __name__ == "__main__":
    unittest.main()

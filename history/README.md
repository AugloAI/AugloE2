# Product Chronicle

`history/events/` is the canonical append-only chronology of E2 product decisions and material milestone changes. It does not replace Git source history or the mutable current contract in `project/e2.yaml`.

## Rules

- Add one immutable event for each material product decision or milestone transition.
- Never edit, reorder, rename, or delete an accepted event.
- Give every event a stable event ID, event time, event type, subject, and non-sensitive payload.
- Treat event time as when the product event occurred, not when a file happened to be committed.
- Keep current state in its canonical owner; chronicles record change and rationale rather than duplicate the latest state.

## Event semantics

An event states that a named product fact became known or a decision took effect. Source edits, formatting changes, and implementation details are not product events unless they change the product contract.

## Corrections and supersession

Do not rewrite an incorrect event. Append a correction that references the original event ID and states the corrected fact. Append a supersession event when a later decision replaces an earlier one; preserve both events and link the replacement to its predecessor.

## Sensitive content

Events must not contain PII, credentials, secrets, rosters, recordings, transcripts, raw call evidence, sensitive configuration, or controlled-storage locations. Refer to controlled evidence only by a stable evidence ID or cryptographic hash. Access, retention, and storage details remain outside Git.

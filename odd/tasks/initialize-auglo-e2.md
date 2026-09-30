# Initialize AugloE2

## Intent

Create a clean, local, authoritative repository for milestone E2 without copying the legacy runtime yet. Establish a minimal current-state contract, an append-only product chronology, and the architectural decisions that govern later extraction and reintegration.

## Decisions already made

- E2 closes as a completed experiment: 20 real outbound calls under one frozen configuration, complete evidence, labeling, failure attribution, and the DR-5 post-run decision.
- AugloE2 is the sole implementation authority for extracted E2 Modules during separation.
- AugloAI remains historical upstream context and the eventual integration destination.
- Sensitive roster, recordings, transcripts, and call evidence live in controlled storage outside Git.
- The canonical product chronicle initially lives in this repository and is append-only.

## Explicit non-goals

- Do not copy or refactor the AugloAI runtime in this work unit.
- Do not create GitHub repositories or issues.
- Do not add CRM/DMS, dashboards, WhatsApp, inbound, multi-agent, multitenant, E3, or E4 scope.
- Do not place sensitive data or secrets in Git.

## Work tasks

- [x] T1 — Bootstrap the local Git repository and this recoverable task record.
  - Route: inline bootstrap; required before a delegated writer can target the independent repository.
  - Evidence: repository root initialized on unborn branch `main`.
- [x] T2 — Create the minimal E2 foundation.
  - Route: delegated to `gentle-ai-worker` because the foundation spans multiple non-trivial files.
  - Outcome: README, glossary, canonical project contract, integration map, chronology rules, two initial ADRs, and repository exclusions created across nine allowed paths.
  - Evidence: writer reported 269 authored lines; YAML parsing, diff check, and Git status checks passed.
- [x] T3 — Verify the initialized repository.
  - Route: delegated to `gentle-ai-verify` because verification commands are required. Native assessment was unavailable because the new files are intentionally untracked, so the candidate was treated as high risk and independently verified.
  - Checks: repository structure, internal references, YAML parseability, contract cardinality, sensitive-content scan, ignored harness-cache status, absence of remotes and commits, and Git status.
  - First verification: failed because this task record contained an absolute host path and the verifier included ignored `.atl/` harness cache files in repository artifacts.
  - Correction: removed the host path, explicitly excluded ignored harness caches, and ignored `.codegraph/` indexing metadata created during incident diagnosis.
  - Final evidence: independent verifier passed; parent spot check printed `contracts-ok` for 10 capabilities and 7 integration Modules.
- [ ] T4 — Create the initial work-unit commit.
  - Route: parent after explicit user authorization.
  - Commit: pending authorization.

## Checks policy

- Effective TDD: not applicable to this documentation/control-plane bootstrap; no runtime behavior is implemented.
- Verification runner: to be derived from tools already available in the new repository environment; do not install dependencies for this work unit.
- Required checks must be observed before T3 can close.

## Delivery

- Strategy: ask-on-risk.
- Forecast: approximately 250 authored changed lines, excluding generated artifacts.
- Current slice: repository foundation only.
- Push, remote creation, pull request, and merge are not authorized.

## Current status

T1–T3 are complete and verified. T4 is waiting for explicit authorization to create the initial commit. No commit or remote exists.

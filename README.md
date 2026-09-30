# Auglo E2

AugloE2 is the standalone authoritative repository for defining and completing the E2 outbound-call experiment while it is separated from AugloAI. E2 means one controlled cohort of 20 real outbound calls, executed serially under one frozen configuration, with complete evidence, labeling, failure attribution, and a post-run decision.

## Current phase

The repository is in the **foundation** phase. It contains contracts, vocabulary, chronology rules, and architectural decisions. It does not contain or imply an executable runtime.

## Canonical source map

| Fact | Canonical owner |
| --- | --- |
| Current E2 scope, gate, capabilities, and gaps | [`project/e2.yaml`](project/e2.yaml) |
| Candidate integration Modules and seams | [`project/integration.yaml`](project/integration.yaml) |
| Domain vocabulary | [`CONTEXT.md`](CONTEXT.md) |
| Product chronology policy | [`history/README.md`](history/README.md) |
| Repository-separation decisions | [`docs/adr/`](docs/adr/) |
| Source change history | Git history |

## Explicit exclusions

This foundation does not include runtime code, package manifests, dependencies, deployment, CRM/DMS, dashboards, WhatsApp, inbound calling, multi-agent or multitenant operation, or E3/E4 scope. AugloAI code is not copied here.

## Security rule

Never commit PII, credentials, secrets, rosters, recordings, transcripts, raw call evidence, or controlled-storage locations. Git may contain only non-sensitive contracts and stable evidence IDs or hashes.

## Where to look

Start with `project/e2.yaml` for the current contract, then `CONTEXT.md` for terminology. Use `project/integration.yaml` for future integration planning, `history/` for product decisions, and `docs/adr/` for durable architectural rationale.

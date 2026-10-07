# Auglo E2

AugloE2 is the standalone authoritative repository for defining and completing the E2 outbound-call experiment while it is separated from AugloAI. E2 means one controlled cohort of 20 real outbound calls, executed serially under one frozen configuration, with complete evidence, labeling, failure attribution, and a post-run decision.

## Current phase

The repository is in the **foundation** phase and now includes one bounded, offline, provider-neutral qualification harness for the frozen **Bounded Session Termination** fixture:

```bash
PYTHONPATH=src python3 -m auglo_e2_bakeoff
```

The deterministic JSON report qualifies both fake candidates without ranking or selecting a winner. Each result carries a digest binding candidate identity, execution-owned evidence, terminal result, derived gates, diagnostics, and dimensions. The evaluator always requires the complete frozen duration evidence profile and independently derives compliance from the actual connection end. Duration evidence separately records the termination request, transport acknowledgement, and actual media/connection end. This synthetic fixture is not production runtime or proof of canonical real-cohort latency.

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

The bounded harness does not provide production runtime, provider integrations, the complete 20-behavior readiness suite, real telephony, or canonical real-cohort latency proof. Deployment, CRM/DMS, dashboards, WhatsApp, inbound calling, multi-agent or multitenant operation, and E3/E4 remain out of scope. AugloAI code is not copied here.

## Security rule

Never commit PII, credentials, secrets, rosters, recordings, transcripts, raw call evidence, or controlled-storage locations. Git may contain only non-sensitive contracts and stable evidence IDs or hashes.

## Where to look

Start with `project/e2.yaml` for the current contract, then `CONTEXT.md` for terminology. Use `project/integration.yaml` for future integration planning, `history/` for product decisions, and `docs/adr/` for durable architectural rationale.

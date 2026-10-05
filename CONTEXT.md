# Auglo E2 Context

Canonical vocabulary for the E2 experiment and its evidence.

## Language

**E2**:
The controlled outbound-conversation milestone that closes only when its Primary Evaluation Cohort, Operational Attempt Ledger, evidence, labels, attribution, and post-run decision satisfy the canonical contract.

**Experiment**:
A bounded evaluation performed under a declared configuration and closure gate to produce a decision.

**Primary Evaluation Cohort**:
Exactly 20 completed/evaluable real outbound conversations assessed for conversational-agent behavior under one arm and one Behavior Hash, with serial dialing. A conversation remains in this cohort after crossing the Evaluation Entry Threshold even if a later agent or infrastructure failure occurs.
_Avoid_: Cohort, call cohort

**Dialing Attempt**:
One admitted effort to establish a real outbound conversation, whether it produces an evaluable conversation, a pre-conversation infrastructure failure, no answer, or another non-evaluable outcome.
_Avoid_: Call, Run

**Operational Attempt Ledger**:
The complete accounting of every admitted Dialing Attempt, including its evidence, outcome, and Failure Attribution when applicable. It is reported separately from the Primary Evaluation Cohort.

**Evaluation Entry Threshold**:
The irreversible boundary crossed after the legal opening has been delivered and the system captures the first intelligible utterance from a live human. A live wrong-contact response crosses it; voicemail, IVR, ambient noise, silence/no-answer, and unintelligible audio do not, and Attempt Evidence must prove whether it was crossed.

**Evaluable Conversation**:
A real outbound conversation that has crossed the Evaluation Entry Threshold and therefore counts toward the Primary Evaluation Cohort, regardless of later agent or infrastructure failure.

**Capability**:
A named E2 outcome the system must support and for which the contract records a current state.

**Attempt Evidence**:
The evidence set required to establish what occurred during a Dialing Attempt, referenced from Git only by stable identifiers or hashes.
_Avoid_: Call Evidence

**Canonical Event Stream**:
The append-only, ordered sequence of provider-neutral lifecycle and observable-behavior events owned by one admitted Dialing Attempt. It is sufficient to interpret the experiment without provider-native or token-level traces.

**Canonical Terminal Event**:
The exactly-once event in a Dialing Attempt's Canonical Event Stream that records its terminal outcome and starts that attempt's 48-hour labeling and initial-triage deadline.

**Attempt Evidence Manifest**:
The non-sensitive record that binds one Dialing Attempt to its Config Snapshot identities, Canonical Event Stream, evidence artifacts, outcome, threshold proof, labels, attribution, optional Detailed Traces, and Evidence Completeness.

**Evidence Completeness**:
A path-sensitive verdict of `complete` or `incomplete` stating whether the Attempt Evidence contains every event and artifact required by what actually occurred. An incomplete verdict names missing or invalid requirements and remains visible in the Operational Attempt Ledger.

**Detailed Trace**:
An optional Adapter-provided runtime or provider trace retained in Controlled Storage and referenced from the Attempt Evidence Manifest. It extends diagnostics but is never required to interpret the experiment.

**Outcome**:
The record of what happened in a Dialing Attempt or conversation. It is distinct from Failure Attribution, which explains where and why an unsuccessful or incomplete attempt failed.

**Outcome Label**:
A founder-confirmed classification of what happened in an admitted Dialing Attempt. Corrections are append-only Outcome Label Revisions, so prior labels and their evidence remain part of the historical record.

**Outcome Label Revision**:
An append-only correction that supersedes an earlier Outcome Label while preserving every prior label and its evidence. The first valid founder-confirmed Outcome Label determines whether the 48-hour requirement was met.

**Failure Attribution**:
The evidence-backed, provider-neutral explanation of where and why an unsuccessful or incomplete Dialing Attempt failed. A resolved attribution has exactly one primary attribution and may have contributing factors across lifecycle stage, causal category, responsibility, retryability/remediation, and confidence.

**Initial Failure Attribution Triage**:
The first Failure Attribution assessment required within 48 hours of an unsuccessful or incomplete Dialing Attempt's Canonical Terminal Event. It may remain unresolved, but records evidence references, candidate causes, investigation status, reviewer or actor identity reference, and triage timestamp.

**Unresolved Attribution**:
A provisional Failure Attribution that preserves Attempt Evidence, candidate causes, and investigation status without inventing a primary cause. Timely unresolved triage satisfies the initial-triage deadline but does not satisfy E2 closure unless DR-5 explicitly accepts and exposes the uncertainty without rewriting it as resolved.

**Attribution Revision**:
An append-only correction to a Failure Attribution that supersedes an earlier attribution while preserving its evidence and history.

**Founder Review Authority**:
The founder is the sole accountable human authority for E2 Outcome labels, initial Failure Attribution triage, corrections, unresolved-cause exceptions, and DR-5. Models and automated audits cannot exercise this authority.

**Model Recommendation**:
A non-authoritative, evidence-referenced proposal for an Outcome label or Failure Attribution that records its Adapter and model identity, model or behavior version, decision schema version, available probabilities or confidence, and generation timestamp.

**Independent Automated Pre-Closure Audit**:
An advisory inspection of a frozen Closure Candidate for missing evidence and contract inconsistencies. It is not human approval and cannot authorize DR-5.

**Closure Candidate**:
An immutable, digest-identified representation of the E2 closure basis presented for review and bound to one DR-5 decision. It identifies the cohort, ledger, evidence manifests, effective labels and attributions, exceptions, and contract-check results as frozen together.

**Closure Amendment**:
An append-only post-DR-5 correction that preserves the historical closure and original decision. An amendment affecting the experiment result, cohort membership, evidence completeness, an unresolved-attribution exception, or any closure predicate requires a superseding DR-5 decision.

**DR-5**:
The founder-authorized post-run decision bound to exactly one frozen Closure Candidate. A closure remains historically true only as of the candidate bound to its DR-5 decision.

**Config Snapshot**:
An immutable, schema-versioned composition of typed Module configuration fragments containing the resolved configuration for a Primary Evaluation Cohort. Every field is classified as behavior, provenance, operational, or secret reference; Attempt inputs and observations are excluded.

**Snapshot Digest**:
A digest of the complete canonical Config Snapshot that establishes its exact identity and integrity.
_Avoid_: Config Hash

**Behavior Hash**:
A digest of the Config Snapshot schema's versioned behavior-affecting projection that establishes experimental comparability and cohort membership.
_Avoid_: Config Hash

**Enrichment Attestation**:
A separate evidence-backed record that adds a proven historical fact by reference to an original Snapshot Digest without rewriting the historical Config Snapshot.

**Observability Adapter**:
A provider-specific mapping between an external observability platform and E2's vendor-neutral configuration, trace/event identity, Attempt Evidence reference, outcome, and correlation contracts. It is not a source of domain truth or sensitive evidence authority.

**Executable Appointment**:
An appointment outcome containing enough validated business and scheduling facts to be acted upon by the destination system.

**Product Chronicle**:
The append-only sequence of product events that records decisions and material milestone changes independently of source changes.

**Controlled Storage**:
Access-restricted storage outside Git for sensitive evidence and configuration material.

**Benchmark Evidence Archive**:
The consent-qualified evidence set retained for future internal comparison against the E2 Primary Evaluation Cohort's frozen Behavior Hash and historical evidence.

**Evidence Retention Attestation**:
An append-only record that exposes a required deletion or restriction of benchmark evidence without rewriting the historical closure facts established before that change.

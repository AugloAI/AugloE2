# Auglo E2 Context

Canonical vocabulary for the E2 experiment and its evidence.

## Language

**E2**:
The controlled outbound-call milestone that closes only when its cohort, evidence, labels, attribution, and post-run decision satisfy the canonical contract.

**Experiment**:
A bounded evaluation performed under a declared configuration and closure gate to produce a decision.

**Cohort**:
The complete set of calls admitted to one Experiment under the same arm and Config Hash.

**Run**:
One controlled execution attempt for an admitted call within a Cohort.

**Capability**:
A named E2 outcome the system must support and for which the contract records a current state.

**Call Evidence**:
The evidence set required to establish what occurred during a Run, referenced from Git only by stable identifiers or hashes.

**Failure Attribution**:
A label assigning an unsuccessful or incomplete outcome to its accountable failure category using available Call Evidence.

**Config Snapshot**:
An immutable representation of all experiment-relevant configuration used for a Cohort.

**Config Hash**:
A stable digest identifying one Config Snapshot without exposing its sensitive contents.

**Executable Appointment**:
An appointment outcome containing enough validated business and scheduling facts to be acted upon by the destination system.

**Product Chronicle**:
The append-only sequence of product events that records decisions and material milestone changes independently of source changes.

**Controlled Storage**:
Access-restricted storage outside Git for sensitive evidence and configuration material.

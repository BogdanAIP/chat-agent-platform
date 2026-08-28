# CAP Mutation Assurance

Status: **CURRENT ASSURANCE DIRECTION / CAP-M0 ACCEPTED / BROADER CATALOG STAGED**.

This document defines mutation-testing and adversarial-verification direction. It does not change production authority, public Chat-facing tools or acceptance semantics by itself.

## Purpose

The important question is not a generic mutation percentage. It is whether a concrete weakening of a verification, provenance, recovery or completion guarantee is detected by an independent test/gate.

Use three complementary layers:

1. generic source mutation experiments for ordinary test weakness;
2. curated **Guarantee Mutation Suite** tied to named architecture guarantees/detectors;
3. adversarial behavioral/fault-injection tests for multi-component failure sequences.

Primary metric for curated critical guarantees is **Verification Guarantee Coverage**, not raw mutation score.

## Current accepted assurance state

CAP-M0 is accepted: the Verification Kernel curated pilot proved its unmutated baseline and killed the accepted curated mutant set using detector tests bound to the actual mutated source overlay.

Representative Browser/Windows physical gates also exposed real acceptance-harness defect classes. Invalid runs were rejected rather than waived.

Stage 26.3C then advanced: PR #124 accepted the L1 WorkingState/typed reconciliation/budget/LoopGuard foundation. Therefore the current CAP-M7 target is **production integration/restart behavior**, not merely designing the WorkingState type from scratch.

## CAP-M0 invariant

A mutant is `KILLED` only when the named detector actually observes the mutated target and fails for the intended guarantee. Import errors, harness failures, timeouts, wrong detector cardinality, wrong-source resolution or compile failures are `ERROR`, never `KILLED`.

The mutated verifier/checker cannot be its own oracle.

## Adversarial test shape

Every behavioral case states:

1. **Guarantee** — architecture promise being tested.
2. **Fault/attack** — minimum weakening/hostile sequence.
3. **Independent oracle** — evidence not controlled by the mutated component.
4. **Required result** — FAIL / UNKNOWN / NOT_DONE / no delivery / no unrelated mutation, as appropriate.

Harness failure is never proof that the guarantee held.

## Current permanent defect families

### Source provenance / executed-byte closure — CAP-M6

| ID | Fault | Required result |
|---|---|---|
| `SRC-001` | wrong exact qualification HEAD | fail before consequence path |
| `SRC-002` | dirty tracked source | fail |
| `SRC-003` | runtime artifact appears in source worktree during qualification | provenance revalidation fail |
| `SRC-004` | installed runtime already differs from independently materialized expected source | fail |
| `SRC-005` | executed runtime helper omitted from attestation | closure meta-test fail |
| `SRC-006` | transitive runtime dependency omitted from complete-tree proof | fail |
| `SRC-007` | committed lock correct but installed dependency bytes modified | fail |
| `SRC-008` | source changes after prepare before Finish Gate | fail / NOT_DONE |
| `SRC-009` | installed semantic runtime changes after prepare | fail / NOT_DONE |
| `SRC-010` | old provenance reused after an invalidating Chat action | reject old evidence; no DONE |

Closure tests should derive/compare actual runtime/install closure rather than maintain fragile allowlists where practical.

### Finish Gate / stale evidence — CAP-M5/M6

| ID | Fault | Required result |
|---|---|---|
| `FINISH-101` | reuse previously valid evidence after invalidating action | NOT_DONE/UNKNOWN |
| `FINISH-102` | authoritative PASS/DONE emitted before required cleanup completes | ordering rejected |
| `FINISH-103` | final-state predicates pass but cleanup fails | no authoritative DONE |
| `FINISH-104` | target mutated then restored | history-sensitive constraint still reports mutation where required |
| `FINISH-105` | non-target mutated then restored | Finish Gate rejects where non-target integrity is required |

### Process / fixture ownership — CAP-M5

| ID | Fault | Required result |
|---|---|---|
| `PROC-101` | recorded PID exits/reuses unrelated process generation | unrelated process never killed |
| `PROC-102` | harness crashes after spawning owned children | owned children cleaned or explicitly unresolved; no false PASS |
| `PROC-103` | transport/fixture restarts between prepare and Finish Gate | generation continuity fails |
| `PROC-104` | cleanup uses stale ownership metadata | fail closed; no kill of unowned generation |
| `PROC-105` | process-start identity relies on locale-sensitive text | deterministic generation identity avoids/rejects ambiguity |

### Fixture freeze / atomic evidence — CAP-M5

| ID | Fault | Required result |
|---|---|---|
| `FIX-101` | late/in-flight mutation races authoritative freeze | blocked/excluded before final snapshot; no split-brain PASS |
| `FIX-102` | final evidence write interrupted | partial snapshot never authoritative |
| `FIX-103` | freeze endpoint replayed with stale/wrong auth | no final-state transition |
| `FIX-104` | checker fixture dead while decoy remains | fixture identity/liveness rejects run |
| `FIX-105` | producer/consumer evidence schema diverges | contract fails before physical acceptance |

### Action / observation timing — CAP-M3/M5

| ID | Fault | Required result |
|---|---|---|
| `OBS-101` | delivered action has delayed postcondition | bounded fresh observation may verify; no blind redelivery |
| `OBS-102` | BEFORE/AFTER non-advancing | UNKNOWN/stale |
| `OBS-103` | subject/capability/stream changes after delivery | UNKNOWN/FAIL |
| `TIME-101` | outer timeout shorter than delivery + verification window | configuration contract rejects ambiguity |

### Public authority — CAP-M4/M5

| ID | Fault | Required result |
|---|---|---|
| `AUTH-101` | raw/generic seventh tool added without accepted consequence contract | public-surface contract fails |
| `AUTH-102` | backend/PID/HWND/selector/raw execution authority leaks into bounded public procedure | schema/authority contract fails |
| `AUTH-103` | evidence object treated as grant | policy/authority test rejects operation |

## CAP-M7 — Stage 26.3C WorkingState / recovery

The L1 foundation now exists; CAP-M7 must prove that production consumers preserve it under real restart/failure composition.

Minimum guarantee families:

- `WS-*` — stale/mismatched WorkingState/provenance cannot authorize another effect;
- `REC-*` — ambiguous delivery reconciles from fresh state before retry;
- `LOOP-*` — repeated equivalent physical intents/budgets fail closed before unbounded redelivery;
- restart cannot replay a proven-applied logical operation;
- durable history cannot attach another actor/environment/generation/evidence stream;
- `candidate_done` and stale success remain non-authoritative after recovery;
- StagnationReport is diagnostic/escalation data, not grant/planner.

For the current draft workspace-artifact production integration, add deterministic cases for:

```text
concurrent duplicate resume -> loser performs zero mutation
process death -> task lock becomes recoverable
prepared intent persisted before delivery
crash after delivery before recovery commit
recovery-commit persistence failure
same-content but different file identity
ABA delete/recreate identity mismatch
unresolved outcome blocks compensation
```

Because that draft changes a real `procedure_run` effect path, deterministic CAP-M7 tests do not replace the required target-Windows physical qualification.

## Meta-tests: prove assurance liveness

Required principles:

- each curated mutant changes exactly the intended source/fault point;
- named detector proves it loaded/observed the mutated target;
- evidence-corpus expected outcome is independent from mutated implementation;
- new runtime dependencies cannot silently escape provenance coverage;
- producer/consumer evidence schemas are checked for parity;
- runtime diagnostics stay in owned state locations rather than source checkout;
- removing/disconnecting a qualification fixture causes a liveness failure rather than a green no-op;
- intentionally weakened references for each major family are rejected by at least one named detector.

## Codex Review -> permanent guarantee workflow

Independent review is additive, not a release oracle and not a substitute for executable assurance.

For a concrete new defect class:

```text
finding
 -> minimal fix
 -> focused regression
 -> named guarantee
 -> curated mutant and/or adversarial case
 -> permanent suite
```

The same applies to physical-gate findings. A gate that catches a harness/runtime defect is useful evidence that the gate is live, but that failed run is not acceptance.

If Codex Review/equivalent independent review is unavailable, do not represent it as completed; follow the merge policy in `AGENTS.md` for whether the change class may proceed without it.

## CI tiers

- **T0 every PR:** ordinary unit/contract tests + fast critical assurance for changed modules.
- **T1 critical-path PR:** relevant CAP-M family, deterministic corpus and provenance closure selected by changed path.
- **T2 scheduled/manual:** broader state-machine/generic mutation/adversarial corpus.
- **T3 release/qualification:** exact-head target-Windows/Browser/application physical gates where real consequences are required.

A conditional/path-filtered check is not automatically a universal merge requirement; use a stable required aggregator if later made merge-critical.

## Planned family progression

```text
CAP-M0 Verification Kernel pilot                         ACCEPTED
CAP-M1 broader Verification Kernel mutants              staged
CAP-M2 observation adapters                             staged
CAP-M3 transition verification/timing                   staged
CAP-M4 authority/registry/reporting guarantees          staged
CAP-M5 acceptance-system behavioral adversarial cases   staged/current source of permanent defects
CAP-M6 source provenance / closure                      accepted physical lessons + further deterministic hardening
CAP-M7 WorkingState/recovery/LoopGuard production use   ACTIVE with Stage 26.3C integration
CAP-M8 assurance CI tiering/aggregation                 future
```

Do not create one new testing framework/workflow per CAP family. Reuse the same assurance mechanisms where possible.

## Independence rule

A mutated verifier/checker cannot be its own oracle. Physical mutation runs are justified only when the guarantee depends on a live delivery/target/freshness/identity consequence that deterministic evidence cannot faithfully represent.

# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

`ROADMAP.md` owns **release order and stage-level completion conditions**, not active PR mechanics, exact accepted SHAs or machine evidence. Use `CURRENT_STATE.md` for the live boundary/active work and `EVIDENCE_INDEX.md` for accepted physical evidence.

## Accepted public semantic surface

Exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal transport is direct stdio through the Secure MCP Tunnel and official tunnel-client. 1MCP remains optional internal Extension Manager infrastructure.

A new registered procedure may extend `procedure_run` only through bounded reviewed schemas. A genuinely new consequence class requires a truthful public-contract/security/physical-acceptance decision rather than generic dispatch.

## Acceptance-depth rule

```text
L1 — primitive / contract proof
 -> L2 — multi-step workflow integration where useful
 -> L3 — ordinary user-task E2E with independent Finish Gate
```

Release-critical physical acceptance also binds executed source/runtime provenance when that is part of the claim. One L3 pass is scoped evidence, not universal reliability.

## Foundation already completed

Relevant accepted progression:

```text
Stage 24/24.1 typed file/browser foundation                 ACCEPTED
Stage 25/25.1/25.2 Browser + local vision                   ACCEPTED
Stage 26.1A-E / 26.2A-E Windows foundation                 ACCEPTED FOR RECORDED SCOPE
Stage 26.3A canonical six-tool Verified Procedure Runtime  ACCEPTED
Transport Supervisor                                       ACCEPTED
Stage 26.3B Verification Kernel + Finish Gate              ACCEPTED / CLOSED FOR RECORDED SCOPE
CAP-M0 Verification mutation pilot                         ACCEPTED
Stage 26.3C WorkingState / reconciliation / LoopGuard L1   ACCEPTED FOUNDATION
```

Exact PR/physical evidence belongs in `CURRENT_STATE.md` / `EVIDENCE_INDEX.md`, not here.

## Current release-critical sequence

```text
26.3C consequence-bearing production integration + restart/reconciliation acceptance
 -> broad real-application physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill / skill lineage
 -> 26.5 Hybrid Computer-Use Integration + selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

Broad real-app coverage is an acceptance objective, not a new architecture family.

Parallel Track M Agent Session / Delegation remains future/non-release-critical. Track P local general planner remains optional future research. UFO³ Galaxy remains deferred until multi-device orchestration is an observed bottleneck.

---

# 26.3B — Verification Kernel + independent Finish Gate — ACCEPTED / CLOSED

Recorded representative scope is complete.

Accepted shared contract includes:

```text
ObservationRef / ObservationSnapshot
same-stream capability + subject identity
monotonic fresh re-observation
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN
independent evidence-batch-bound Finish Gate
separate task-success and safety/policy result dimensions
```

Accepted representative production/evidence slices cover Files, Browser and Windows/application paths. The accepted Browser route is headless Playwright/Chrome on target Windows and does not claim visible headed desktop-browser control.

Do not reopen 26.3B merely to add another variant. New completion predicates or physical gates belong to the stage/capability that introduces the new requirement.

---

# 26.3C — WorkingState + recovery/reconciliation + LoopGuard

## Foundation — ACCEPTED

The L1 project-owned state-machine foundation is already accepted.

WorkingState remains **capability-spanning structured operational state**, not private chain-of-thought and not a vendor procedure/session store.

Accepted foundation covers:

```text
constraints / subgoals / progress
facts + provenance + freshness
evidence refs
stable mutating-operation identity
AttemptIntent / AttemptRecord
verified-applied / not-applied / ack-failed / unknown outcomes
fresh same-stream reconciliation
task / procedure / strategy budgets
LoopGuard
StagnationReport
fail-closed durable history validation
```

The foundation is L1 only; it does not by itself prove restart-safe delivery on every production path.

## Remaining stage work

Integrate the accepted state/reconciliation/LoopGuard semantics into bounded consequence-bearing production consumers and prove the intended restart/failure guarantees without blind duplicate effects.

Any material persistence/recovery/concurrency/identity mechanism used for that work must pass the current `stage-research` gate before implementation and must explicitly compare affected roles against `ARCHITECTURE_REUSE_BASELINE.md`.

Before acceptance of a consequence-bearing integration, require the evidence appropriate to that exact path, including focused deterministic/fault-injection tests, exact-head hosted CI/security, independent review when required/available and target-machine physical qualification when the consequence boundary cannot be represented faithfully in hosted tests.

## 26.3C completion condition

26.3C is ready to leave the critical path when accepted production consumers can use WorkingState/reconciliation/LoopGuard without blind duplicate effects across their declared restart/failure scope and the project has enough evidence to reuse the same semantics across later capabilities.

Do not expand 26.3C into Track M, a generic event bus, scheduler, second planner or new persistence framework without fresh evidence and Stage Research.

---

# Broad real-application physical coverage gate

Representative L3 gates are vertical proofs. Broaden coverage across multiple task/application classes and environmental variants.

Minimum families should include multiple examples from:

- native Windows/Win32;
- Browser;
- Electron;
- office-style applications;
- standard file/dialog flows.

Variants should include DPI, moved/resized windows, focus changes, similar windows/records, unexpected dialogs/overlays/noise and reviewed structure-to-vision fallback where applicable.

Success means a materially broader characterized accepted scope, not universal Windows accuracy.

---

# Pre-26.4 — bounded OpenAdapt integration spike

After the project-owned 26.3C production state/recovery shape is accepted, revalidate selected OpenAdapt roles through `ARCHITECTURE_REUSE_BASELINE.md` and fresh Stage Research rather than assuming prior selection is sufficient.

Target bounded spike:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> upstream effect evidence
 -> project evidence adapter
 -> project ObservationSnapshot / ExpectedEffect
 -> PROJECT Verification Kernel
 -> PROJECT independent Finish Gate
```

No upstream verdict becomes unconditional project `PASS`/`DONE`. No raw workflow catalog, generic desktop executor, shell/Python authority or second planner is introduced merely for the spike.

If upstream mechanics do not fit the exact current failure/authority model, keep them qualified but outside the production path.

---

# 26.4 — Human Demo -> verified candidate skill / lineage

Compile demonstrations into:

```text
subtask goals
verifiable completion criteria
applicability / preconditions
advisory target/action evidence
versioned candidate lineage
```

Live state outranks demonstration history. Blind coordinate/action replay is not accepted. One demonstration creates at most a CANDIDATE; promotion requires independent replay/regression/variant evidence.

Prefer mature selected capture/compile/ProgramGraph/replay/checkpoint/certification mechanics when fresh evidence confirms fit rather than rebuilding them locally.

Project trust still requires project verification and Finish Gate evidence.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows/application mechanisms on common cross-capability semantics without flattening rich native state:

```text
capability-native observation identity
semantic/native vs reviewed GUI routing
grounding identity/confidence/ambiguity evidence
selective visual fallback
cross-app provenance
WorkingState/reconciliation/recovery
independent completion
```

For Office/Windows breadth, evaluate focused UFO/UFO²-derived UIA/Win32/WinCOM/application mechanics one application at a time behind project-owned capability, identity, observation, ExpectedEffect and verification boundaries.

Do not adopt UFO HostAgent/AppAgent planner hierarchy or UFO³ Galaxy as the current production planning layer.

Trusted-site full-browser/JS/CDP authority may be promoted only after its Site Capability/network/security boundary is implemented, reviewed and physically accepted.

---

# Local Execution Kernel — adjacent future consequence class

Arbitrary Python/program execution may be useful later, but it is not Browser authority and must not be hidden in `web_interact` or generic `procedure_run` dispatch.

It requires a separate grant/security/public-contract/physical-acceptance decision.

Generated code remains proposal data; deterministic Control Plane policy remains authoritative.

---

# 27 — Distribution & Maintenance

After core reliability and broad physical scope are credible:

- simplify install/update/repair/uninstall paths;
- remove developer-machine assumptions;
- make dependency/runtime ownership explicit;
- close/reassess release-relevant `TECH_DEBT.md`;
- preserve fail-closed security boundaries.

Current implementation remains primarily Python + Node/MJS + PowerShell/Windows glue. Rust is not a release prerequisite.

---

# 28 — Clean User E2E / stable release

Target:

```text
clean supported Windows machine/account
 -> install
 -> connect/authenticate
 -> approve required capability scope
 -> normal semantic route ready
 -> representative user task succeeds with verification
 -> restart/recovery/update behavior remains understandable
```

Stable release requires accepted core behavior, clean install evidence, current documentation and no known P0/P1 debt required for shipped authority.

---

# Parallel Track M — Agent Sessions / Delegation

Track M is a future work-distribution capability below the ordinary-ChatGPT manager and deterministic Control Plane boundary. It must not displace release-critical Stage 26 prerequisites.

Keep separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Canonical progression remains:

```text
M0 object model + fixture contracts
 -> M1 read-only Session Observer
 -> M2 Manager -> one EXISTING Worker with verified delivery/correlation
 -> M3 WorkingState/HandoffPack + recovery/event monitoring
 -> M4 bounded session lifecycle + operation idempotency/reconciliation
 -> M5 manager-created Worker + ownership/WorkerLease/cleanup
 -> M6 multiple workers + bounded fan-out, default max_spawn_depth=1
 -> M7 separate Project / ExecutionEnvironment lifecycle
 -> M8 broader cross-harness/provider adoption
```

Track M may reuse accepted WorkingState/logical-operation/reconciliation/LoopGuard semantics later; it does not justify broadening 26.3C solely for future orchestration.

---

# Parallel Track P — optional future local planner

A future local general planner is not banned, but it is not release-critical now.

Research order remains:

```text
shadow/proposal-only
 -> measured bounded subtask role
 -> optional local general planner only after parity/safety/resource evidence
```

It always remains above the same deterministic authorization, Verification Kernel and Finish Gate boundaries.

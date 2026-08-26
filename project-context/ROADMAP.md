# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture/contracts: `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `REAL_TASK_ACCEPTANCE.md`, `SOURCE_PROVENANCE_ACCEPTANCE.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `CURRENT_STATE.md`, `PROJECT_RISKS.md`, `TECH_DEBT.md`; ADR-036 future Browser/local-execution direction lives in `BROWSER_HARNESS_ARCHITECTURE.md`.

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

## Acceptance-depth rule

```text
L1 — primitive / contract proof
 -> L2 — multi-step workflow integration where useful
 -> L3 — ordinary user-task E2E with independent Finish Gate
```

L3 receives a natural-language goal rather than a click/type script and verifies independent final state plus important non-target constraints. One L3 pass is scoped evidence, not a universal reliability claim.

Release-critical physical acceptance has an orthogonal source-provenance requirement:

```text
behavior evidence
  L1 / L2 / L3 + independent Finish Gate

source evidence
  exact expected head + clean tree + critical source/driver/lock hash binding
```

`git rev-parse HEAD` alone is not sufficient proof of the bytes actually executed.

## Completed foundation relevant to current work

```text
Stage 24/24.1 typed file/browser foundation       ACCEPTED
Stage 25/25.1/25.2 Browser + local vision         ACCEPTED
Stage 26.1A-E / 26.2A-E Windows foundation       ACCEPTED FOR RECORDED SCOPE
Stage 26.3A canonical six-tool runtime            ACCEPTED / MERGED #92
Transport Supervisor                              ACCEPTED / MERGED #94
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                 PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                    MERGED #110
web_interact postcondition verification           PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                   PHYSICAL ACCEPTED / MERGED #113
```

The Browser L3 run used randomized Case Desk data and an external independent Finish Gate. Accepted evidence included exactly one target save, one target audit mutation and `NON_TARGET_MUTATION=none`.

The later Source Provenance review found that the historical #113 harness proved the named head and independent task result but did not separately prove a clean working tree/source-byte binding. #113 is not retroactively failed; before Stage 26.3B closes, repeat one representative Browser L3 under the stronger provenance methodology.

Windows acceptance remains scoped evidence, not universal Windows accuracy.

## Current release-critical sequence

```text
26.3B Verification Kernel + production adapters   ACTIVE
 -> 26.3C project-owned WorkingState + typed recovery + LoopGuard
 -> Broad real-app physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration / selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The Broad real-app physical coverage gate is an acceptance objective, not a separate architecture stage. Track M multi-chat remains future/parallel. Track P local-planner work remains future only. UFO³ Galaxy remains deferred until multi-device orchestration becomes an observed product bottleneck.

---

# 26.3B — Verification Kernel + independent Finish Gate — ACTIVE

Objective: one reusable verification contract across real production capabilities, with representative real-task evidence rather than only primitive success checks.

Shared foundation:

```text
ObservationRef / ObservationSnapshot
same-stream capability + subject identity
monotonic fresh re-observation
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN
independent evidence-batch-bound Finish Gate
separate task-success and safety/policy results
```

Accepted production/evidence slices:

- file/artifact procedure path through PR #102;
- production `web_open` verification through PR #107;
- production `web_interact` verification through PR #111;
- first Browser L3 real-task acceptance through PR #113 for its historical physical-gate scope.

## Current active slice — PR #114

PR #114 integrates accepted Windows `DesktopState` evidence with the shared Verification Kernel. It is internal and non-authorizing:

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> bounded expected final state
 -> mandatory stable process/native-window continuity
 -> DesktopState AFTER
 -> shared verify_expected_effect
 -> PASS | FAIL | UNKNOWN
```

Stable continuity includes:

```text
Windows session
application identity
executable name
PID
process generation
HWND
coordinate space
```

Process restart/PID-generation drift, HWND drift or application-identity drift therefore cannot satisfy a similar-looking final state.

`window_instance` is snapshot-consistency evidence, not immutable continuity identity, because the accepted Stage 26.2 digest includes window title. PR #114 recomputes it per snapshot, along with control fingerprints and frame digest. It also validates redundant freshness evidence.

PR #114 adds no `desktop_*` Chat tool, no process launch authority, no generic code execution and no new Windows mutation route. It preserves the accepted Stage 26.2 legacy verifier rather than silently changing its semantics.

Required acceptance sequence:

```text
freeze final #114 head
 -> fresh hosted checks
 -> isolated target-Windows source root
 -> SourceProvenanceGate PASS on the same exact head
 -> target-Windows physical verifier qualification
 -> no unresolved review/security finding
 -> merge #114
 -> representative Windows/application L3 with independent Finish Gate + source provenance
 -> repeat representative Browser L3 under SourceProvenanceGate
```

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md` and `SOURCE_PROVENANCE_ACCEPTANCE.md`.

## Remaining 26.3B work

```text
1. hosted + source-provenance-bound physical acceptance and merge of PR #114
2. representative Windows/application L3 using accepted action/observation/verifier mechanisms
3. one representative Browser L3 repeat under the new source-provenance methodology
4. add cross-capability completion predicates only where a real procedure requires them
5. run any additional physical gate required by a production-path change
6. declare 26.3B accepted only when required evidence gaps are closed
```

## ADR-036 relation to 26.3B

ADR-036 does not silently enlarge current authority. Site Capability Profiles / Browser Network Gate remain reviewed future direction and become hard prerequisites before trusted-site JS/CDP/full-browser authority is promoted.

---

# 26.3C — Project-owned WorkingState + typed recovery + LoopGuard

Objective: make long-horizon continuation/recovery reliable before broader authority.

WorkingState v1 remains **project-owned and capability-spanning**. It must not be replaced by OpenAdapt procedure-local checkpoint/resume state.

WorkingState should contain structured operational state only:

```text
user constraints
subgoals + progress vector
verified achievements
facts + provenance + freshness
open ambiguities/questions
evidence references
expected/observed deltas
retry/recovery history
action/time/resource budgets
active capability/grant state
procedure id/version/node + optional external checkpoint reference
```

Never persist private chain-of-thought.

Initial recovery classes include target missing/ambiguous, stale state, action no-effect, partial effect, unexpected dialog, navigation change, tool unavailable, permission denied, unsafe transition and external dynamic change.

Default recovery ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

LoopGuard must terminate/escalate repeated no-effect fingerprints, oscillation and exhausted budgets. Do not implement a second general planner in 26.3C.

An OpenAdapt checkpoint may later be referenced by WorkingState for one compiled procedure, but OpenAdapt does not own cross-capability state, authority, retry budgets or completion.

---

# Broad real-application physical coverage gate

Earlier L3 gates are representative vertical proofs. This later gate broadens coverage across task families, application classes and environment variants.

Minimum classes should include multiple examples from native Windows/Win32, Browser, Electron, office-style applications and standard file/dialog flows. Variants should cover DPI, moved/resized windows, focus changes, multiple similar windows, unexpected dialogs/overlays/noise and reviewed structure-to-vision fallback where applicable.

The success criterion is a materially broader, characterized, repeatable accepted scope — not a universal Windows accuracy claim.

---

# Pre-26.4 — bounded OpenAdapt integration spike

After the project-owned 26.3C core shape is accepted, run a bounded spike rather than rewriting the Control Plane around OpenAdapt:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> OpenAdapt effect-verifier verdict + evidence
 -> project OpenAdaptEffectEvidenceAdapter
 -> project ObservationSnapshot / ExpectedEffect
 -> PROJECT Verification Kernel
 -> PROJECT independent Finish Gate
```

OpenAdapt `CONFIRMED`, `REFUTED` and `INDETERMINATE` are upstream evidence states. They are not unconditional aliases for project `PASS`, `FAIL` and `UNKNOWN`; the project Kernel also checks subject, freshness, selected verifier/effect-contract identity and provenance.

The spike must add no raw per-workflow MCP catalog, `execute_windows`, generic shell/Python authority or second planner. Healthy deterministic replay should require zero model calls where the pinned OpenAdapt substrate supports that path.

If the spike passes, promote selective reuse for 26.4. If it fails these boundaries, keep OpenAdapt qualified but outside the production procedure path.

Canonical boundary: `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`.

---

# 26.4 — Human Demo -> verified candidate skill

Compile demonstrations into subtask goals, verifiable completion criteria, applicability/preconditions, advisory target/action evidence and versioned candidate lineage. Live state outranks demonstration history. Blind coordinate/action replay is not accepted. One demonstration creates at most a candidate; promotion requires independent replay/regression/variant evidence.

If the bounded spike is accepted, prefer pinned OpenAdapt for mature mechanics such as Capture/compile/ProgramGraph/deterministic replay/checkpoint/teach/certification/effect-coverage rather than reimplementing them. OpenAdapt skill/certification status remains upstream evidence; project trust/promotion still requires project verification and Finish Gate evidence.

Generated Browser/local helpers use the same candidate lineage discipline.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows mechanisms on common observation references, capability-aware semantic/native vs GUI routing, common grounding identity/confidence/ambiguity evidence, selective visual fallback, cross-app provenance and verified recovery.

For Office/Windows breadth, evaluate focused UFO²-derived UIA/Win32/WinCOM/application adapters one application at a time behind project-owned capability, identity, observation, ExpectedEffect and verification contracts. Do **not** adopt UFO HostAgent/AppAgent planner hierarchy or UFO³ Galaxy as the current production planning layer.

Trusted-site full-browser/JS/CDP authority may be promoted only after the Site Capability/network boundary is implemented, reviewed, physically accepted and backed by representative L3 evidence.

A future public Windows/computer-use Chat-facing surface still requires its own schema/security/ordinary-Chat physical acceptance.

---

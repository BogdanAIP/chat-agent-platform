# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture/contracts: `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `REAL_TASK_ACCEPTANCE.md`, `SOURCE_PROVENANCE_ACCEPTANCE.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `CURRENT_STATE.md`, `PROJECT_RISKS.md`, `TECH_DEBT.md`; ADR-035 future Agent Session / Delegation direction lives in `CONVERSATION_BRIDGE_ARCHITECTURE.md`; ADR-036 future Browser/local-execution direction lives in `BROWSER_HARNESS_ARCHITECTURE.md`; ADR-037 future capability/event/policy substrate lives in `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md`; mutation/adversarial-assurance direction lives in `MUTATION_ASSURANCE.md`.

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

The six-tool inventory and the closed registered procedure catalog are separate contracts. A new registered procedure may extend `procedure_run` only through a bounded reviewed schema. Any genuinely new consequence class requires a truthful public-contract/security/physical-acceptance decision rather than being hidden behind generic dispatch.

## Acceptance-depth rule

```text
L1 — primitive / contract proof
 -> L2 — multi-step workflow integration where useful
 -> L3 — ordinary user-task E2E with independent Finish Gate
```

L3 receives a natural-language goal rather than a click/type script and verifies independent final state plus important non-target/history constraints. One L3 pass is scoped evidence, not a universal reliability claim.

Release-critical physical acceptance has an orthogonal source-provenance requirement:

```text
behavior evidence
  L1 / L2 / L3 + independent Finish Gate

source evidence
  exact expected head
  + clean tree
  + critical source/driver/lock hash binding
  + installed/runtime binding where applicable
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
Windows DesktopState shared-kernel verification   PHYSICAL ACCEPTED / MERGED #114
Windows/application real-task L3                  PHYSICAL ACCEPTED / MERGED #115
CAP-M0 Verification mutation pilot                ACCEPTED / MERGED #117
Track M + ADR-037 architecture                    MERGED #116 / FUTURE AUTHORITY ONLY
Browser stronger-provenance L3 repeat             PHYSICAL ACCEPTED / MERGED #118
post-26.3B adversarial assurance plan             MERGED #119
```

Historical Browser L3 #113 remains accepted for its original functional/final-state/history scope. PR #118 repeated one representative Browser L3 task under the stronger source/install/full-dependency provenance methodology and closed the remaining recorded Stage 26.3B evidence gap. Exact heads/results belong in `EVIDENCE_INDEX.md`.

All physical acceptance remains scoped evidence, not universal Browser/Windows accuracy.

## Current release-critical sequence

```text
26.3B Verification Kernel + representative production/L3 evidence   ACCEPTED / CLOSED FOR RECORDED SCOPE
 -> 26.3C project-owned WorkingState + typed recovery/reconciliation + LoopGuard   ACTIVE / NEXT
 -> Broad real-app physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration / selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

Broad real-app coverage is an acceptance objective, not a separate architecture stage. Track M Agent Session / Delegation remains future/parallel. Track P local-planner work remains future only. UFO³ Galaxy remains deferred until multi-device orchestration becomes an observed bottleneck.

---

# 26.3B — Verification Kernel + independent Finish Gate — ACCEPTED

Objective achieved for the recorded representative scope: one reusable verification contract across real production capabilities with independent task-level evidence rather than primitive success checks alone.

Accepted shared foundation:

```text
ObservationRef / ObservationSnapshot
same-stream capability + subject identity
monotonic fresh re-observation
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN
independent evidence-batch-bound Finish Gate
separate task-success and safety/policy results
```

Accepted production/evidence slices include:

- file/artifact procedure path through #102;
- production `web_open` verification through #107;
- production `web_interact` verification through #111;
- first Browser L3 real-task acceptance through #113 for its historical scope;
- Windows `DesktopState` shared-kernel verification through #114;
- representative Windows/application L3 through #115;
- representative Browser L3 repeat under stronger Source Provenance through #118.

#118 additionally bound clean exact source, installed semantic runtime, complete exact-lock Node dependency materialization, process generations, frozen final snapshot, target-only mutation history and cleanup around an ordinary-Chat Browser task. Invalid earlier attempts failed closed and exposed defect classes that are now catalogued in `MUTATION_ASSURANCE.md`.

The accepted Browser route is headless Playwright/Chrome on target Windows. It does not claim visible headed desktop-browser control.

No further 26.3B work is required merely to keep the stage “open”. Add cross-capability completion predicates or new physical gates only when a material production-path requirement demands them.

ADR-036 does not silently enlarge current authority. Site Capability Profiles / Browser Network Gate remain future prerequisites before trusted-site JS/CDP/full-browser authority is promoted.

---

# 26.3C — Project-owned WorkingState + typed recovery/reconciliation + LoopGuard — ACTIVE / NEXT

Objective: make long-horizon continuation/recovery reliable before broader authority.

WorkingState v1 remains **project-owned and capability-spanning**. It must not be replaced by OpenAdapt procedure-local checkpoint/resume state or a vendor session/task store.

WorkingState contains structured operational state only:

```text
user constraints
subgoals + progress vector
verified achievements
facts + provenance + freshness
open ambiguities/questions
evidence references
expected/observed deltas
retry/recovery/reconciliation history
action/time/resource budgets
active capability/grant state
procedure id/version/node + optional external checkpoint reference
```

Never persist private chain-of-thought.

## Required first-slice guarantees

Structured failure reasons are mandatory. They must survive handoff/retry and provide enough typed information that the next attempt can choose a materially different safe strategy rather than replaying the same physical action.

LoopGuard is mandatory for repeated physical attempts. It must detect repeated no-effect fingerprints, oscillation and exhausted budgets before unbounded redelivery.

Budget layers are distinct:

```text
task budget
procedure/resumable-run budget
strategy/attempt budget
```

Phases/checkpoint nodes are introduced for `procedure_run` / resumable procedures where useful. Do not turn them into a universal planner hierarchy.

## Track M compatibility guardrail inside 26.3C

26.3C must **not implement Track M**, but WorkingState should avoid a schema that assumes:

```text
one task -> one procedure -> one executor
```

Reserve optional planner-neutral references where useful:

```text
subgoal
  subgoal_id
  status
  actor_ref                    optional
  delegation_ref               optional
  execution_environment_ref    optional
  budget_ref                   optional
  evidence_refs

capability_grant_refs[]
```

Future `actor_ref` may identify the manager, deterministic procedure runtime or admitted worker session without granting authority by identity alone.

## Recovery / ambiguous side-effect foundation

Initial recovery classes include target missing/ambiguous, stale state, action no-effect, partial effect, unexpected dialog, navigation change, tool unavailable, permission denied, unsafe transition and external dynamic change.

Generic mutating outcomes:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` means reconcile the original logical operation from fresh authoritative state before retry.

Default recovery ladder:

```text
re-observe
 -> re-resolve
 -> reconcile ambiguous logical effect where required
 -> retry only when new evidence proves retry safety
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

LoopGuard must terminate/escalate repeated no-effect fingerprints, oscillation and exhausted budgets. StagnationReport passes a structured failure reason/evidence summary to the next planner attempt; it is diagnostic/escalation data, not authorization and not a second planner.

Recovery after process restart must not replay a proven committed effect. Stale WorkingState/evidence must never authorize a new physical mutation.

## Assurance obligation

CAP-M7 cases in `MUTATION_ASSURANCE.md` are designed with the 26.3C guarantees. Deterministic state-machine/fault-injection tests should cover stale state, ambiguous delivery, duplicate attempts, budget exhaustion, actor/evidence mismatch and stale candidate completion before physical qualification is considered.

## Minimal ADR-037 seam during 26.3C

26.3C may introduce only the smallest internal typed-event/read-only capability-descriptor seam needed by WorkingState/recovery/LoopGuard/Finish Gate.

It must not implement connector marketplace, scheduler, arbitrary hooks or Track M runtime merely because ADR-037 exists.

## Planner portability guardrail

After WorkingState v1 stabilizes, define the smallest planner-neutral proposal/escalation contract needed to prevent the lower deterministic Control Plane from depending on ChatGPT-specific planning payloads. A future second planner should first run shadow/proposal-only through that contract.

## Adjacent hardening before/with first runtime slice

Make Playwright/Browser runtime output ownership explicit under project-owned state/log storage rather than inherited arbitrary CWD. Add a regression that source checkouts remain clean after Browser runtime use. This hardening comes from #118 qualification and should not reopen #118 acceptance.

---

# Broad real-application physical coverage gate

Earlier L3 gates are representative vertical proofs. This later gate broadens coverage across task families, application classes and environment variants.

Minimum classes should include multiple examples from native Windows/Win32, Browser, Electron, office-style applications and standard file/dialog flows. Variants should cover DPI, moved/resized windows, focus changes, multiple similar windows, unexpected dialogs/overlays/noise and reviewed structure-to-vision fallback where applicable.

Success means a materially broader, characterized, repeatable accepted scope — not universal Windows accuracy.

---

# Pre-26.4 — bounded OpenAdapt integration spike

After the project-owned 26.3C core shape is accepted, run a bounded spike rather than rewriting the Control Plane around OpenAdapt:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> OpenAdapt effect-verifier verdict + evidence
 -> project evidence adapter
 -> project ObservationSnapshot / ExpectedEffect
 -> PROJECT Verification Kernel
 -> PROJECT independent Finish Gate
```

OpenAdapt evidence states are not unconditional aliases for project PASS/FAIL/UNKNOWN. The project Kernel still checks subject, freshness, verifier/effect identity and provenance.

The spike must add no raw per-workflow MCP catalog, generic desktop executor, shell/Python authority or second planner. If it passes the project boundary, reuse selected mechanics for 26.4; otherwise keep OpenAdapt outside the production procedure path.

---

# 26.4 — Human Demo -> verified candidate skill

Compile demonstrations into subtask goals, verifiable completion criteria, applicability/preconditions, advisory target/action evidence and versioned candidate lineage. Live state outranks demonstration history. Blind coordinate/action replay is not accepted. One demonstration creates at most a candidate; promotion requires independent replay/regression/variant evidence.

If the bounded OpenAdapt spike is accepted, prefer pinned mature mechanics such as capture/compile/ProgramGraph/deterministic replay/checkpoint/teach/certification/effect-coverage rather than reimplementing them. Project trust still requires project verification and Finish Gate evidence.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows mechanisms on common observation references, capability-aware semantic/native vs GUI routing, common grounding identity/confidence/ambiguity evidence, selective visual fallback, cross-app provenance and verified recovery.

For Office/Windows breadth, evaluate focused UFO²-derived UIA/Win32/WinCOM/application adapters one application at a time behind project-owned capability, identity, observation, ExpectedEffect and verification contracts. Do **not** adopt UFO HostAgent/AppAgent planner hierarchy or UFO³ Galaxy as the current production planning layer.

Trusted-site full-browser/JS/CDP authority may be promoted only after the Site Capability/network boundary is implemented, reviewed, physically accepted and backed by representative L3 evidence.

26.5 may supply common app/adapter/ObservationEnvelope seams later reused by Track M, but Track M must not broaden/delay 26.5 merely to add multi-session orchestration.

---

# Local Execution Kernel — adjacent future capability

ADR-036 retains arbitrary Python/program execution as a useful local capability, but **not inside Browser authority** and not as a hidden expansion of `web_interact`/`procedure_run`.

It may begin only after relevant 26.3C state/grant foundations exist and requires a separate consequence-class/security/public-contract/physical acceptance.

Target grant shape:

```text
LocalExecutionGrant
 -> filesystem roots
 -> network scope
 -> executable/program allowlist
 -> environment exposure
 -> runtime/process/resource budgets
 -> task/session lifetime
```

Generated code remains proposal data; deterministic Control Plane policy remains authoritative.

---

# 27 — Distribution & Maintenance

Only after the core loop and broad physical scope are credible:

- simplify installation/update paths;
- reduce developer-environment assumptions;
- make dependency/runtime ownership explicit;
- close/reassess relevant `TECH_DEBT.md` items;
- preserve fail-closed security boundaries.

The implementation remains primarily Python + Node/MJS + PowerShell/Windows glue. Rust is not a current release prerequisite.

---

# 28 — Clean User E2E / stable release

Target user path:

```text
clean machine / supported Windows account
 -> install
 -> connect/authenticate
 -> choose/approve required capability scope
 -> normal six-tool route ready
 -> representative user task succeeds with verification
 -> restart/recovery/update behavior remains understandable
```

Stable release requires accepted core behavior, clean install evidence, current documentation and no known P0/P1 debt required for shipped authority.

---

# Parallel Track M — Agent Sessions / Delegation / Conversation Bridge

Track M is a parallel future work-distribution capability below the ordinary-ChatGPT manager and deterministic Control Plane authority boundary. It must not displace release-critical Stage 26 prerequisites.

## Product target

The primary cross-provider target is authenticated web AI conversations:

```text
ordinary ChatGPT web manager
 -> existing user-owned web worker conversations
 -> ChatGPT / Claude / Gemini / DeepSeek / Qwen / future web AI services
```

Browser Companion remains the primary cross-provider adapter family. Common structural extraction, normalization, capability detection and fallback belong in `GenericChatAdapter` / common Browser Companion layers. Thin provider adapters remain necessary for exact selectors, provider quirks and identity. For an exact target surface with a reviewed stronger official/native host interface, prefer that route for truthful state/effect semantics.

## Object model

Keep distinct:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Session identity is not task identity. Delivery is not completion. Project/worktree lifecycle is not session lifecycle. `HandoffPack` remains bounded task context; capability grants remain Control Plane state outside the message.

## Routing

```text
reviewed official/project-owned harness API / local host protocol when available for the target
 -> validated provider/session native route
 -> Browser Companion + GenericChatAdapter DOM/accessibility
 -> reviewed GUI/visual fallback
 -> ABSTAIN
```

## Track M progression

```text
M0  Object model + fixture contracts
M1  Read-only Session Observer
M2  Manager -> ONE EXISTING Worker with verified delivery/correlation
M3  WorkingState + HandoffPack integration and recovery
M4  Session lifecycle + stable operation_id + reconciliation
M5  Manager-created Worker E2E + WorkerLease/minimum authority
M6  Multiple workers + fan-out/LoopGuard + max_spawn_depth=1 default
M7  Project / ExecutionEnvironment lifecycle as stronger consequence class
M8  Cross-provider / cross-harness adoption and broader adapter matrix
```

Core invariants:

- discoverability != lifecycle ownership;
- worker/session identity != capability authority;
- queued send != steer/interrupt;
- transport accepted != message delivered != worker result;
- result correlates to a concrete DelegationTask/work unit;
- every mutating logical effect has stable `operation_id`;
- `OUTCOME_UNKNOWN` is reconciled before retry;
- events trigger observation but do not prove semantic completion;
- workers receive minimum explicit delegated authority;
- bounded fan-out/LoopGuard applies to workers/messages/session creation/unresolved delegations;
- independent Finish Gate remains task-completion authority.

---

# ADR-037 — CapabilityRegistry + TypedEventBus / PolicyHooks

Future project-owned substrate:

```text
CapabilityRegistry
  = semantic discovery / availability / health / trust metadata
  != authorization
  != generic dispatch

TypedEventBus
  = typed lifecycle events / observation triggers
  != external-effect success proof
  != WorkingState

PolicyHooks
  = registered bounded deterministic policy handlers
  != second planner
  != arbitrary shell/Python
  != Verification Kernel / Finish Gate replacement
```

Preserve `AVAILABLE -> ACTIVE -> AUTHORIZED`. Raw provider/MCP catalogs are not automatically trusted planner-visible semantics. Events cause fresh authoritative re-observation where consequence state matters. Hook output cannot widen grants or upgrade FAIL/UNKNOWN/completion state.

---

# Optional Track P — local planner

Track P remains **future only** research:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general planner
```

No planner may grant itself capability authority; all planners remain above deterministic Control Plane/verifier/Finish Gate boundaries. Track P is not part of the current release-critical path.

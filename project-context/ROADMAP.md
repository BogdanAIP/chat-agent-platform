# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture/contracts: `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `REAL_TASK_ACCEPTANCE.md`, `SOURCE_PROVENANCE_ACCEPTANCE.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `CURRENT_STATE.md`, `PROJECT_RISKS.md`, `TECH_DEBT.md`; ADR-035 future Agent Session / Delegation direction lives in `CONVERSATION_BRIDGE_ARCHITECTURE.md`; ADR-036 future Browser/local-execution direction lives in `BROWSER_HARNESS_ARCHITECTURE.md`; ADR-037 future capability/event/policy substrate lives in `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md`; mutation-assurance direction lives in `MUTATION_ASSURANCE.md`.

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

Track M / ADR-037 architecture work changes no current public tool.

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
```

The Browser L3 run used randomized Case Desk data and an external independent Finish Gate. Historical #113 evidence included exactly one target save, one target audit mutation and `NON_TARGET_MUTATION=none`.

The later Source Provenance review found that the historical #113 harness did not separately prove clean-tree/all-executed-source-byte binding. #113 is not retroactively failed. Before Stage 26.3B closes, **repeat representative Browser L3 under stronger source-provenance methodology**.

Windows #114 was physically accepted on exact clean head `ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e`. It proved the shared Windows verifier against live process/HWND identity, advancing observation time, positive PASS, wrong-postcondition FAIL, process-generation/HWND drift FAIL and stale/non-advancing UNKNOWN.

Windows/application #115 was physically accepted on exact frozen head `5ae5d5ac52f391b1a58662e94a976c6ab8d48c62`. Ordinary Chat completed five bounded Case Desk transitions with kernel PASS, then a frozen independent Finish Gate proved exact target state, unchanged decoys, exactly one intended save/mutation, source/install/runtime provenance and cleanup. #115 merged as `e965e7b5466446c9f065f6b57f438f25168bed9a`.

CAP-M0 #117 was replayed onto post-#115 main and accepted on exact head `e99de4ea89e6a763e3db6671e710cf06c4e5bb17`: dedicated mutation pilot, CI, CodeQL and Secret History Scan passed before merge as `500bfc646a14892ea655369c20c8f8d725fccfeb`.

All physical acceptance remains scoped evidence, not universal Browser/Windows accuracy.

## Current release-critical sequence

```text
26.3B Verification Kernel + representative production/L3 evidence   ACTIVE — final provenance gap
 -> 26.3C project-owned WorkingState + typed recovery/reconciliation + LoopGuard
 -> Broad real-app physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration / selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

Broad real-app coverage is an acceptance objective, not a separate architecture stage. Track M Agent Session / Delegation remains future/parallel. Track P local-planner work remains future only. UFO³ Galaxy remains deferred until multi-device orchestration becomes an observed bottleneck.

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
- first Browser L3 real-task acceptance through PR #113 for its historical physical-gate scope;
- Windows `DesktopState` shared-kernel verification through PR #114;
- representative Windows/application L3 through physically accepted PR #115.

## Accepted representative Windows/application L3 — PR #115

Architecture retained:

```text
ordinary Chat natural-language goal
 -> bounded registered procedure
 -> native/process-window-scoped execution
 -> fresh DesktopState after required effects
 -> shared ExpectedEffect verification
 -> procedure completion != user-task DONE
 -> independent external L3 Finish Gate
```

The procedure accepts user-level case id, note and reviewed status only. PID/HWND/backend/interpreter/command/Python/arbitrary path/audit path/raw action-sequence authority remains unavailable to Chat.

Final acceptance evidence:

```text
status=completed
action_count=5
local_execution_verified=true
all 5 kernel_verification.status=pass
local_goal_verification.status=pass
local_safety_verification.status=pass
EXTERNAL_FINISH_GATE=DONE
TARGET_FINAL_STATE=True
DECOYS_UNCHANGED=True
ONLY_TARGET_EVER_MUTATED=True
AUDIT_TARGET_SAVE_EXACTLY_ONCE=True
PROVENANCE_REVALIDATION=PASS
STAGE26_3B_WINDOWS_APPLICATION_L3=PASS
```

This closes the representative Windows L3 item; do not rerun it merely because unrelated architecture/docs branches move.

## Remaining 26.3B work

```text
1. repeat representative Browser L3 under stronger source-provenance methodology
2. add cross-capability completion predicates only where a real procedure requires them
3. run additional physical gates only for material production-path changes
4. declare 26.3B accepted when the recorded evidence gap is closed
```

## ADR-036 relation to 26.3B

ADR-036 does not silently enlarge current authority. Site Capability Profiles / Browser Network Gate remain reviewed future direction and become hard prerequisites before trusted-site JS/CDP/full-browser authority is promoted.

## Track M relation to 26.3B

Track M adds no session runtime during 26.3B. It reuses the capability-neutral verification foundation later:

```text
ObservationRef
ExpectedEffect
fresh AFTER observation
PASS | FAIL | UNKNOWN
independent Finish Gate
```

Future session/message effects may use operation-scoped observation subjects without vendor-specific logic inside the Kernel.

---

# 26.3C — Project-owned WorkingState + typed recovery/reconciliation + LoopGuard

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

Generic mutating outcomes should support:

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

LoopGuard must terminate/escalate repeated no-effect fingerprints, oscillation and exhausted budgets. StagnationReport should pass a structured failure reason to the next planner attempt rather than merely replaying the same physical action.

An OpenAdapt checkpoint may later be referenced by WorkingState for one compiled procedure, but OpenAdapt does not own cross-capability state, authority, retry budgets or completion.

## Minimal ADR-037 seam during 26.3C

26.3C may introduce only the smallest internal typed-event/read-only capability-descriptor seam needed by recovery/LoopGuard/Finish Gate.

It must not implement connector marketplace, scheduler, arbitrary hooks or Track M runtime merely because ADR-037 exists.

## Planner portability guardrail

After WorkingState v1 stabilizes, define the smallest planner-neutral proposal/escalation contract needed to prevent the lower deterministic Control Plane from depending on ChatGPT-specific planning payloads. A future second planner should first run shadow/proposal-only through that contract.

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

Browser Companion remains the primary cross-provider adapter family. For an exact target surface with a reviewed stronger official/native host interface, prefer that route for truthful identity/state/effect semantics. Coding-agent harnesses are optional adapters/reference inputs, not a replacement for the web-chat product center.

## Object model

Keep distinct:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Session identity is not task identity. Delivery is not completion. Project/worktree lifecycle is not session lifecycle.

`HandoffPack` remains bounded task context; capability grants remain Control Plane state outside the message.

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
    HarnessSession / Conversation / DelegationTask /
    MessageDelivery / ExecutionEnvironment

M1  Read-only Session Observer
    discover/list/read/status of existing sessions/conversations
    web conversations first for product evidence

M2  Manager -> ONE EXISTING Worker
    verified queued delivery
    stable delegation_id
    response/result correlation
    delivered/held/refused/unknown semantics

M3  WorkingState + HandoffPack integration
    typed event/idle observation triggers
    cancel/recovery/reconciliation

M4  Session lifecycle
    create/fork/rename/archive
    stable operation_id
    native idempotency key where supported
    OUTCOME_UNKNOWN reconciliation before retry

M5  Manager-created Worker E2E
    ownership / WorkerLease
    minimum child capability profile
    cleanup with ownership evidence

M6  Multiple workers
    explicit DelegationTasks
    fan-out/worker/message/session-creation budgets
    duplicate-delegation guard
    max_spawn_depth = 1 by default

M7  Project / ExecutionEnvironment lifecycle
    separate stronger consequence/security/acceptance

M8  Cross-provider / cross-harness adoption and broader adapter matrix
```

## Core Track M invariants

- discoverability != lifecycle ownership;
- worker/session identity != capability authority;
- queued send != steer/interrupt;
- transport accepted != message delivered != worker result;
- result must correlate to the concrete DelegationTask/work unit;
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

Rules:

- preserve `AVAILABLE -> ACTIVE -> AUTHORIZED`;
- raw MCP/provider catalogs are not automatically trusted planner-visible semantics;
- events cause fresh authoritative re-observation where consequence state matters;
- hook output cannot widen grants or upgrade FAIL/UNKNOWN or completion status;
- Skills declare capability requirements but do not self-authorize;
- future scheduled runs get independent run/session identity and explicit scheduled-run grants rather than inheriting all interactive authority.

ADR-037 implementation is staged behind current release needs; documentation does not create runtime authority.

---

# Optional Track P — local planner

Track P remains future-only research:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general planner
```

No planner may grant itself capability authority; all planners remain above deterministic Control Plane/verifier/Finish Gate boundaries.

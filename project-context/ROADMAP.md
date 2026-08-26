# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture/contracts: `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `REAL_TASK_ACCEPTANCE.md`, `CURRENT_STATE.md`, `PROJECT_RISKS.md`, `TECH_DEBT.md`; ADR-036 future Browser/local-execution direction lives in `BROWSER_HARNESS_ARCHITECTURE.md`.

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

Windows acceptance remains scoped evidence, not universal Windows accuracy.

## Current release-critical sequence

```text
26.3B Verification Kernel + production adapters   ACTIVE
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> Broad real-app physical coverage gate
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The Broad real-app physical coverage gate is an acceptance objective, not a separate architecture stage. Track M multi-chat remains future/parallel. Track P local-planner work remains future only.

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
- first Browser L3 real-task acceptance through PR #113.

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
 -> target-Windows physical verifier qualification on same head
 -> no unresolved review/security finding
 -> merge #114
 -> representative Windows/application L3 with independent Finish Gate
```

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Remaining 26.3B work

```text
1. physically accept + merge PR #114
2. representative Windows/application L3 using accepted action/observation/verifier mechanisms
3. add cross-capability completion predicates only where a real procedure requires them
4. run any additional physical gate required by a production-path change
5. declare 26.3B accepted only when required evidence gaps are closed
```

## ADR-036 relation to 26.3B

ADR-036 does not silently enlarge current authority. Site Capability Profiles / Browser Network Gate remain reviewed future direction and become hard prerequisites before trusted-site JS/CDP/full-browser authority is promoted.

---

# 26.3C — WorkingState + typed recovery + LoopGuard

Objective: make long-horizon continuation/recovery reliable before broader authority.

WorkingState v1 should contain structured operational state only:

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

---

# Broad real-application physical coverage gate

Earlier L3 gates are representative vertical proofs. This later gate broadens coverage across task families, application classes and environment variants.

Minimum classes should include multiple examples from native Windows/Win32, Browser, Electron, office-style applications and standard file/dialog flows. Variants should cover DPI, moved/resized windows, focus changes, multiple similar windows, unexpected dialogs/overlays/noise and reviewed structure-to-vision fallback where applicable.

The success criterion is a materially broader, characterized, repeatable accepted scope — not a universal Windows accuracy claim.

---

# 26.4 — Human Demo -> verified candidate skill

Compile demonstrations into subtask goals, verifiable completion criteria, applicability/preconditions, advisory target/action evidence and versioned candidate lineage. Live state outranks demonstration history. Blind coordinate/action replay is not accepted. One demonstration creates at most a candidate; promotion requires independent replay/regression/variant evidence.

Generated Browser/local helpers use the same candidate lineage discipline.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows mechanisms on common observation references, capability-aware semantic/native vs GUI routing, common grounding identity/confidence/ambiguity evidence, selective visual fallback, cross-app provenance and verified recovery.

Trusted-site full-browser/JS/CDP authority may be promoted only after the Site Capability/network boundary is implemented, reviewed, physically accepted and backed by representative L3 evidence.

A future public Windows/computer-use Chat-facing surface still requires its own schema/security/ordinary-Chat physical acceptance.

---

# Local Execution Kernel — adjacent future capability

Arbitrary Python/program execution remains a separate future consequence class, not hidden Browser or `procedure_run` authority. It requires scoped grants for filesystem roots, network, executable allowlist, environment exposure, runtime/process/resource budgets and task/session lifetime.

---

# 27 — Distribution & Maintenance

After the core loop and broad physical scope are credible, simplify install/update paths, reduce developer-environment assumptions, make dependency/runtime ownership explicit, close relevant debt, and preserve fail-closed security boundaries. Rust is not a current release prerequisite.

---

# 28 — Clean User E2E / stable release

```text
clean supported Windows machine/account
 -> install
 -> connect/authenticate
 -> approve required capability scope
 -> normal six-tool route ready
 -> representative user task succeeds with independent verification
 -> restart/recovery/update behavior remains understandable
```

Stable release requires accepted core behavior, clean-install evidence, current documentation and no known P0/P1 debt required by shipped authority.

---

# Parallel Track M — Conversation Bridge / multi-chat

Future/parallel only. It must not displace unfinished release-critical capability/state/verification work.

# Optional Track P — local planner

Future only: shadow/proposal-only -> bounded subtask planner -> optional local general planner. No planner may grant itself capability authority; all remain above the deterministic Control Plane/verifier/Finish Gate boundary.

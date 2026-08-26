# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture:

- `ARCHITECTURE.md`
- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`
- `SECURITY_POLICY.md`

Reviewed future Browser/local-execution direction:

- `BROWSER_HARNESS_ARCHITECTURE.md` / ADR-036

Canonical current status:

- `CURRENT_STATE.md`

Canonical ranked engineering risks:

- `PROJECT_RISKS.md`

Canonical existing technical debt:

- `TECH_DEBT.md`

Do not duplicate the full risk or debt ranking here.

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

## Completed foundation relevant to current work

```text
Stage 24/24.1 typed file/browser foundation       ACCEPTED
Stage 25/25.1/25.2 Browser + local vision         ACCEPTED
Stage 26.1A-E / 26.2A-E Windows foundation       ACCEPTED FOR RECORDED SCOPE
Transport Supervisor                              ACCEPTED / MERGED #94
Stage 26.3A canonical six-tool runtime            ACCEPTED / MERGED #92
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                 PHYSICAL ACCEPTED / MERGED #107
```

Windows acceptance is scoped evidence, not universal Windows accuracy.

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

The **Broad real-app physical coverage gate is an acceptance objective, not a new architecture stage**. It exists to stop architecture growth from outrunning proven computer-use capability.

Track M multi-chat remains future/parallel. Track P local-planner work is **future only**. Neither replaces this release-critical sequence.

---

# 26.3B — Verification Kernel + independent Finish Gate — ACTIVE

Objective: one reusable verification contract across real production capabilities.

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

Accepted production integrations:

- file/artifact procedure path through PR #102;
- production `web_open` final-state verification through physically accepted/merged PR #107.

Merged observation foundation:

- Browser observation stream through PR #106.

Current active production slice:

- **draft PR #111 — production `web_interact` click/type postcondition verification**.

PR #111 requires final exact-head hosted CI and target-Windows ordinary-Chat physical evidence before merge. Historical green evidence from the former stacked branch is regression evidence only.

Remaining 26.3B work:

```text
PR #111 final exact-head hosted + physical acceptance
Windows/application/process verification
cross-capability completion predicates where real procedures require them
appropriate physical gates for each changed production path
```

Only then declare 26.3B accepted.

## ADR-036 relation to 26.3B

ADR-036 does **not** silently enlarge the current 26.3B acceptance objective.

The current release gate remains verification correctness for accepted production capabilities. Site Capability Profiles / Browser Network Gate are reviewed architecture and active technical-debt direction, but broader implementation becomes a hard acceptance prerequisite only when trusted-site JS/CDP/full-browser authority is promoted.

TD-001 therefore remains open through current 26.3B unless a separate reviewed PR explicitly promotes/accepts that network boundary earlier.

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

Initial recovery classes:

```text
target_missing
target_ambiguous
stale_state
action_no_effect
partial_effect
unexpected_dialog
navigation_changed
tool_unavailable
permission_denied
unsafe_transition
external_dynamic_change
```

Default recovery ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

LoopGuard must terminate/escalate repeated no-effect state/action fingerprints, oscillation and exhausted budgets.

### ADR-036 alignment

If Site Capability trust or Local Execution Grants are implemented by this point, their `task | session | permanent` lifetime/provenance/budget state should use the same structured WorkingState/control-plane machinery rather than a parallel hidden permission store.

This is an **integration rule**, not a requirement to implement full-browser or Local Execution Kernel during 26.3C.

## Planner portability guardrail

Do **not** implement a second general planner as part of 26.3C.

After WorkingState v1 stabilizes, define the smallest planner-neutral proposal/escalation contract needed to prevent the lower Control Plane from depending on ChatGPT-specific planning payloads. A future second planner should first run shadow/proposal-only through that contract.

---

# Broad real-application physical coverage gate

This is the highest-ranked current engineering risk and must be attacked after 26.3C rather than hidden behind more architecture.

Minimum representative matrix should cover multiple classes, for example:

```text
native Windows / Win32
browser
Electron application
office-style application
standard file/dialog flows
```

Variants should include where applicable:

```text
DPI 100 / 125 / 150%
window moved/resized
foreground/focus changes
multiple similar windows
unexpected modal/dialog
notification/overlay/noisy state
structure miss -> reviewed visual fallback
```

Success criterion is not a marketing claim of universal Windows accuracy. It is a materially broader, characterized, repeatable accepted scope than the current isolated VS Code E2E.

---

# 26.4 — Human Demo -> verified candidate skill

Compile demonstrations into:

```text
subtask goals
verifiable completion criteria
applicability/preconditions
advisory target/action evidence
versioned candidate lineage
```

Live state outranks demonstration history. Blind coordinate/action replay is not accepted.

One demonstration creates at most a candidate. Promotion requires independent replay/regression/variant evidence.

### ADR-036 alignment

Agent-generated Browser/local helpers and site/domain experience enter the same candidate/lineage discipline:

```text
generated helper
 -> CANDIDATE
 -> bounded tests / replay / variants / verifier evidence
 -> promotion or rejection
```

A one-off successful helper is not automatically a trusted durable skill.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows mechanisms on common long-horizon contracts without creating a universal raw-tool gateway.

Targets:

```text
common observation references
capability-aware semantic/native vs GUI routing
common grounding identity/confidence/ambiguity evidence
selective screenshot/ROI fallback
cross-app fact provenance
verified recovery across capability boundaries
component + noisy-state regression corpus
```

### ADR-036 promoted Browser authority

This is the natural integration stage for Browser Harness-derived capabilities **if** they are still justified by measured need:

```text
SiteCapabilityProfile
Browser Network Gate
trusted-site full-browser mode
selected JS/CDP/raw-browser fallback
background tabs
bounded uploads/downloads
Browser Companion / authenticated-user-browser path where separately accepted
```

Before any trusted-site JS/CDP/full-browser authority is accepted:

1. the Site Capability / network boundary must be implemented below those primitives;
2. navigation, redirect, frame, fetch/XHR, WebSocket-like and transfer destinations must respect the reviewed policy;
3. trusted destination must remain distinct from trusted instructions;
4. Browser trust must not grant filesystem/Windows/Python authority;
5. hosted security/regression evidence and ordinary-Chat physical acceptance must pass on the final exact head.

A future public Windows/computer-use Chat-facing surface still requires its own schema/security/ordinary-Chat physical acceptance.

---

# Local Execution Kernel — adjacent future capability

ADR-036 retains arbitrary Python/program execution as a useful local capability, but **not inside Browser authority** and not as a hidden expansion of `web_interact`/`procedure_run`.

It may begin only after the relevant 26.3C state/grant foundations are available and requires a separate consequence-class/security/public-contract/physical acceptance.

Target authority shape:

```text
LocalExecutionGrant
 -> filesystem roots
 -> network scope
 -> executable/program allowlist
 -> environment exposure
 -> runtime/process/resource budgets
 -> task/session lifetime
```

Generated code remains proposal data; the deterministic Control Plane remains authoritative for scope, execution and ExpectedEffect verification.

---

# 27 — Distribution & Maintenance

Only after the core loop and broad physical scope are credible:

- simplify installation/update paths;
- reduce developer-environment assumptions;
- make dependency/runtime ownership explicit;
- close/reassess relevant `TECH_DEBT.md` items;
- preserve fail-closed security boundaries.

The current implementation is primarily Python + Node/MJS + PowerShell/Windows glue. Rust is not a current release prerequisite.

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

Stable release requires accepted core behavior, clean install evidence, current documentation and no known P0/P1 debt whose close condition is required for the shipped authority.

---

# Parallel Track M — Conversation Bridge / multi-chat

Track M remains future/parallel. It may reuse Browser Companion and verified handoff architecture only after the lower capability/state/verification boundaries are ready. It must not displace Stage 26 release-critical prerequisites.

# Optional Track P — local planner

Track P is **future only** optional research:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general planner
```

No planner may grant itself capability authority; all remain above the deterministic Control Plane/verifier/Finish Gate boundary.

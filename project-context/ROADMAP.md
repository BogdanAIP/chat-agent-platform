# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

Canonical architecture:

- `ARCHITECTURE.md`
- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`
- `SECURITY_POLICY.md`

Canonical current status:

- `CURRENT_STATE.md`

Canonical ranked engineering risks:

- `PROJECT_RISKS.md`

Do not duplicate the full risk ranking here.

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

Track M multi-chat and Track P local-planner work are future/parallel and do not replace this release-critical sequence.

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

Accepted production integration:

- file/artifact procedure path through PR #102.

Merged observation foundation:

- Browser observation stream through PR #106.

Current active PR:

- **#107 — production `web_open` final-state verification**.

The pre-documentation-sync head `08671b5a8763d589bcd16da69e8ed70bcb5f9509` had all 11 PR workflows green. Since documentation synchronization changes the branch head, resolve the final exact head and require hosted CI green on it before the ordinary-Chat target-Windows physical Browser gate.

Remaining 26.3B work:

```text
PR #107 final exact-head hosted + physical acceptance
web_interact click/type/control-result verification
Windows/application/process verification
cross-capability completion predicates where real procedures require them
appropriate physical gates for each changed production path
```

Only then declare 26.3B accepted.

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

## Planner portability guardrail

Do **not** implement a second general planner as part of 26.3C.

After WorkingState v1 stabilizes, define the smallest planner-neutral proposal/escalation contract needed to prevent the lower Control Plane from depending on ChatGPT-specific planning payloads. A future second planner should first run shadow/proposal-only through that contract.

This mitigates the current sole-planner dependency without creating premature local-planner complexity.

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

Any future public Windows/computer-use Chat-facing surface still requires its own schema/security/ordinary-Chat physical acceptance.

---

# 27 — Distribution & Maintenance

Only after the core loop and broad physical scope are credible:

- simplify installation/update paths;
- reduce developer-environment assumptions;
- make dependency/runtime ownership explicit;
- preserve fail-closed security boundaries.

The current implementation is primarily Python + Node/MJS + PowerShell/Windows glue. Rust is not a current release prerequisite.

# 28 — Clean User E2E / stable release

Target user path:

```text
download/install
 -> connect ChatGPT
 -> grant reviewed permissions
 -> runtime READY
 -> perform representative task
 -> recover/verify/finish correctly
```

No stable release claim before clean-machine evidence exists.

---

# Parallel Track M — Conversation Bridge / multi-chat

Future only. First target is one verified Manager -> Worker conversation boundary, then provider-open adapters/fallbacks. It must not outrun WorkingState, verification or credential-isolation prerequisites.

# Optional Track P — local planner

Future only:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general planner
```

Every future planner remains above the same deterministic authorization/verifier/Finish Gate boundary and may never grant itself execution authority.

## Roadmap governance

Before adding a new stage, major architecture document or kernel-like subsystem, state:

1. the concrete observed/measured failure it prevents;
2. why an existing shared contract cannot handle it;
3. the physical or automated evidence that will close the work;
4. which ranked risk in `PROJECT_RISKS.md` it reduces.

Prefer improving proven capability over growing taxonomy.

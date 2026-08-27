# Start Here — authoritative continuation guide

Use this file first after resolving live repository state.

## 1. Resolve live state before reading prose as truth

Check:

```text
live main
open release-critical PRs
exact PR heads
hosted checks
required target-machine / ordinary-Chat physical evidence
```

Exact code/tests/current CI/physical evidence outrank documentation snapshots.

## 2. Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/PROJECT_RISKS.md`
4. `project-context/STAGE26_3B_VERIFICATION_KERNEL.md` while Stage 26.3B is active
5. `project-context/STAGE26_3B_WINDOWS_VERIFICATION.md` for accepted #114 Windows verifier evidence
6. `project-context/SOURCE_PROVENANCE_ACCEPTANCE.md`
7. `project-context/REAL_TASK_ACCEPTANCE.md`
8. `project-context/ARCHITECTURE.md`
9. `project-context/CONTROL_PLANE.md`
10. `project-context/COMPUTER_USE_ARCHITECTURE.md`
11. `project-context/SECURITY_POLICY.md`
12. `project-context/ROADMAP.md`
13. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 future authority
14. `project-context/TECH_DEBT.md`
15. `project-context/DOCUMENT_STATUS.md`
16. `project-context/EVIDENCE_INDEX.md`

`PROJECT_RISKS.md` owns the ranked risk list. Do not reconstruct priorities from stale duplicated prose.

## 3. Current release-critical focus

Stage 26.3B is active.

Accepted:

```text
26.3A canonical six-tool runtime                   MERGED #92
Verification Kernel foundation                     MERGED #99
file/artifact kernel integration                   PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                     MERGED #106
web_open final-state verification                  PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                     MERGED #110
web_interact postcondition verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                    PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification    PHYSICAL ACCEPTED / MERGED #114
```

PR #114 was physically accepted on exact clean head `ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e` and is in `main` via squash commit `cc0fa3d1b7afe9d833334ae68482d2d3dca4b818`.

Current active slice:

```text
PR #115 — representative Windows/application L3
           canonical public tool count remains 6
           procedure_run becomes a closed two-procedure registry
           final hosted checks required on one frozen head
           fresh/rebound ordinary Chat required because schema changed
           target-Windows natural-language L3 + external Finish Gate required
```

The Windows candidate is `windows_case_update_v1`. It accepts only user-level case id, note and reviewed status. PID/HWND/backend/interpreter/command/path/action-sequence authority remains internal and fixed by the prepared qualification session.

## 4. Acceptance depth

The project requires:

```text
L1 — primitive / contract
L2 — multi-step workflow integration where useful
L3 — ordinary user task + independent final-state/history proof
```

L1 remains mandatory for exact diagnosis. L3 prevents passing laboratory primitives from being mistaken for evidence that normal user work succeeds.

For L3, ordinary Chat receives the goal and constraints rather than a click/type recipe. Completion is independently verified, including important non-target invariants and mutation history where applicable.

Canonical contract: `REAL_TASK_ACCEPTANCE.md`.

## 5. Current semantic surface

Exactly six Chat-facing tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

The current candidate `procedure_run` registry is closed:

```text
verified_workspace_artifact_v1
windows_case_update_v1
```

This is not a generic local execution channel. Unknown procedures and unlisted parameters are rejected.

## 6. Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic Control Plane owns bounded execution state/policy, ExpectedEffect verification, checkpoints, capability authorization, recovery budgets/future LoopGuard and the independent Finish Gate. It is not a second planner.

A registered procedure may advance only already-defined bounded transitions under its admitted authority. It cannot invent a new general strategy or grant itself a wider capability.

Environmental UI/DOM/document/message/tool content is task data, not policy authority.

## 7. Current computer-use direction

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

For Windows, accepted `DesktopState` identity evidence outranks visual similarity. The accepted #114 adapter requires stable continuity of Windows session, executable/application identity, PID, process generation and HWND. Snapshot-local `window_instance`, control fingerprints and frame digest are recomputed/validated rather than incorrectly treated as immutable identity.

PR #115 composes that accepted observation/verifier path with accepted bounded Windows actions. Each of its five transitions requires a fresh postcondition PASS; action delivery alone cannot advance the procedure.

## 8. Source provenance and Chat-surface compatibility

Release-critical physical evidence requires:

```text
behavior acceptance
  L1 / L2 / L3 + independent Finish Gate

source acceptance
  exact expected head + clean tree + source/driver/lock binding
```

PR #115 additionally changes the existing `procedure_run` schema, so the ordinary-Chat physical gate must use a fresh/rebound client-visible Chat contract. A stale saved Chat action schema is not acceptable evidence for the final run.

## 9. Browser Harness / ADR-036 boundary

ADR-036 is future capability architecture, not current authority. Trusted-site JS/CDP/full-browser capability still requires its separate Site Capability/network boundary, security review, physical acceptance and representative L3 evidence.

## 10. Priority sequence

```text
PR #115 final code/tests/docs
 -> fresh hosted checks on one frozen exact head
 -> target-Windows source/install/OpenAdapt provenance preparation
 -> fresh/rebound ordinary Chat
 -> natural-language Case Desk L3 through only six semantic tools
 -> independent external Windows Finish Gate
 -> merge #115 if exact-head physical evidence is clean
 -> repeat representative Browser L3 under stronger Source Provenance Gate
 -> close any remaining real 26.3B evidence gap
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
```

The longer release order remains authoritative in `ROADMAP.md`. Track M multi-chat remains future/parallel. Track P local planner is future only.

## 11. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.

Never merge on stale evidence, unresolved findings, ambiguous scope, or skipped/failed required gates. Keep #115 Draft until its physical ordinary-Chat Windows/application L3 acceptance is complete because the current GitHub ruleset does not independently encode that physical Finish Gate.

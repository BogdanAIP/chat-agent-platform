# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general intelligence/planning layer**, while the local platform becomes a deterministic execution system with bounded capabilities, persistent verified state, authorization, recovery, procedural memory and selective specialist perception.

```text
ordinary ChatGPT
  = task understanding / strategy / procedure selection / novel adaptation

Chat Agent Platform
  = scoped Files / Browser / Windows capabilities
  + semantic/native state observation
  + selective visual grounding
  + deterministic execution Control Plane
      TaskState / WorkingState
      ProgramGraph progression
      policy / authorization
      ExpectedEffect + transition verification
      checkpoints
      typed recovery + LoopGuard
      action/time/resource budgets
      independent Finish Gate
      safety/policy gate
  + verified procedural memory
  + optional specialist proposals
  + future optional local general planner research
```

The local deterministic Control Plane is not a second planner. It may advance an already-selected known procedure through independently authorized and verified transitions. Novel strategy and incompatible live state escalate to ordinary ChatGPT.

Canonical contracts:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`

Accepted public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal transport is `semantic + direct-stdio`; 1MCP is an optional internal Extension Manager, not a baseline dependency.

---

# Completed foundation

## Stage 21 — Native ChatGPT <-> local MCP — DONE

Secure MCP Tunnel + official tunnel-client + real local MCP round trip accepted.

## Stage 22 — universal core reduction — DONE

Old generic agent/gateway core removed from active architecture.

## Stage 23 — quality-first module selection — DONE

Focused capability/upstream selection and promotion policy accepted.

## Stage 24 / 24.1 — typed semantic file/browser + direct tunnel — DONE

Historical five-tool file/browser foundation accepted for its tested scope. It no longer defines the current public inventory.

## Stage 25 / 25.1 / 25.2 — Browser semantic + local vision — DONE

Structure first, specialist proposal only, deterministic authorization, ABSTAIN on unresolved evidence.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — DONE

Accepted work includes OpenAdapt qualification, bounded capture/executor, window-scoped UIA, production Windows runtime, `DesktopState`, local Grounder, deterministic UIA->vision routing and the first isolated VS Code real-application E2E.

Exact physical evidence belongs in `EVIDENCE_INDEX.md` and historical stage documents.

## Transport Supervisor v1 — ACCEPTED / MERGED #94

Persistent desired state/runtime ownership, layered health, bounded recovery and console-free Scheduled Task persistence are accepted infrastructure.

## Stage 26.3A — canonical six-tool Verified Procedure Runtime — ACCEPTED / MERGED #92

Exact physically accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Merged integration commit:

```text
43ad61384e966ecf089e69a95c166d41da949ebe
```

Physical ordinary-Chat evidence proved one long-horizon task using all six semantic tools, real working-memory files, browser recovery, one completed three-transition `procedure_run`, independent result reread and a second zero-action `ABSTAIN` on protected-target overwrite.

This establishes the first real long-horizon deterministic procedure boundary. It does not authorize arbitrary shell/Python or broad Windows consequences.

---

# Stage 26 — current release-critical sequence

Explicit release order:

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3 Verified Procedure Runtime / Control Plane ACTIVE
    -> 26.3A six-tool verified procedure runtime   ACCEPTED
    -> 26.3B Verification Kernel + Finish Gate     NEXT
    -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The 2026-08-24 Stage 26.3A GUI-agent research is now promoted into this order through `COMPUTER_USE_ARCHITECTURE.md` and ADR-032/033.

## 26.3B — Verification Kernel + independent Finish Gate — NEXT

Primary objective: make verification a reusable cross-capability contract instead of stage-specific ad hoc checks.

Implement deterministic primitives for:

```text
ExpectedEffect / postcondition contract
fresh re-observation reference
PASS | FAIL | UNKNOWN transition result
file/artifact identity/content/structure
browser URL/document/control/result state
process/window/application identity/state
cross-capability goal predicates
candidate_done -> independent Finish Gate -> DONE
```

The Finish Gate must be task-level and independent of planner confidence or action-history plausibility.

Minimum task completion dimensions:

- requested goal predicates hold;
- user constraints remain satisfied;
- required dynamic/authoritative sources are fresh/reconciled;
- no required ambiguity or confirmation remains unresolved;
- safety/policy predicates hold.

Task-success and safety evidence remain separate even if evaluated at the same completion boundary.

Non-negotiable:

```text
action delivered != transition verified
transition verified != task completed
current observed state > remembered procedure state
stale / ambiguous / UNKNOWN -> zero unauthorized continuation
```

## 26.3C — WorkingState + Typed Recovery + LoopGuard

Generalize long-horizon state and recovery before broad GUI authority.

### WorkingState v1

Persist only structured operational state:

```text
user constraints
subgoals / progress vector
verified completed achievements
authoritative facts + provenance + freshness
open ambiguities/questions
evidence references
expected/observed state deltas
retry/recovery history
action/time/resource budgets
```

Never persist private chain-of-thought.

### Initial typed recovery vocabulary

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

Default ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

### LoopGuard

Track repeated/no-progress behavior through:

```text
state + subgoal + action fingerprint
no-effect count
action-family retry count
oscillation A -> B -> A -> B
subgoal/global budgets
recovery escalation level
verified progress vector
```

Identical state/action repetition without new evidence or verified progress must terminate/escalate rather than loop.

## 26.4 — Human Demo -> Transferable Verified Candidate Skill

Use qualified OpenAdapt Capture/Flow substrate, but compile demonstrations into flexible verified procedure guidance rather than macro replay.

Target representation:

```text
demonstration
 -> subtask goals
 -> verifiable completion criteria
 -> advisory target/action evidence
 -> applicability/preconditions
 -> project CANDIDATE
```

Replay rule:

```text
live state > demonstration
```

Historical coordinates/action sequence are not executable authority. One demonstration never becomes permanent trust automatically.

Promotion:

```text
CANDIDATE
 -> same/near-state replay evidence
 -> changed-state/task variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled as evidence degrades
```

Raw human demonstration privacy/retention/redaction/encryption policy is required before broad product capture.

## 26.5 — Hybrid Computer-Use Integration

Purpose: converge accepted Browser/Windows capability-specific mechanisms on common long-horizon contracts without creating a universal raw-tool gateway.

Targets:

```text
ObservationEnvelope references across Browser/Windows
capability-aware semantic-vs-GUI routing
common grounding proposal identity/confidence/ambiguity fields
semantic/native state first
selective screenshot/ROI evidence
cross-app typed fact provenance
component-level interaction regression corpus
recovery/noisy-state E2E
```

The router must choose capabilities from explicit preconditions/evidence. Tool availability alone is not a routing decision.

A truthful Windows/computer-use public Chat-facing surface still requires a separate ADR/schema/security review and physical ordinary-Chat acceptance under ADR-024. Stage 26.5 does **not** promise exact future tool names and does not automatically expand the accepted six-tool surface.

---

# Evaluation track for computer use

External benchmarks are useful diagnostic/evaluation sources, not automatic release gates.

Layer evaluation as:

```text
component/primitive diagnostics
 -> capability integration tests
 -> noisy/recovery fixtures
 -> long-horizon verified procedures
 -> selected reproducible external benchmark runs
```

Reference mechanisms:

- ComponentBench — component-level route/action diagnostics and observation-space sensitivity;
- WebArena / BrowserGym — functional browser correctness and normalized benchmark harness ideas;
- OSWorld 2.0 — long-horizon freshness, hidden state, multi-source reconciliation and completion collapse;
- OSWorld-Noisy — recoverable interruptions;
- MobileWorldSafety — environmental injection and final-state safety predicates.

Never tune production architecture around benchmark-specific tricks without a general project-owned invariant.

---

# Optional internal Extension Manager track

1MCP remains a replaceable internal manager/aggregator for future third-party MCP backends.

```text
canonical project-owned semantic surface
 -> typed adapter / capability policy
 -> optional 1MCP Extension Manager
 -> selected third-party MCP backend
```

Backend availability is not trust, routing authority or action authorization. Raw catalogs are not automatically published to ChatGPT.

---

# Optional Research Track R — Specialized reasoning

Specialized models may later propose structured choices/confidence/ABSTAIN after enough verified procedure-state data exists. They remain non-authorizing and do not replace deterministic verifiers when stronger predicates exist.

# Optional Future Track P — Local Planner / Offline Autonomy

A local general planner remains in the long-term roadmap but is **not part of the current release-critical path**.

Earliest prerequisite: verified long-horizon procedure/WorkingState data plus a measured reason to move planning local.

```text
P0 shadow planner
   sees structured goal/state/procedure evidence
   -> proposal only
   -> no authorization / no actuation
   -> benchmark against ordinary ChatGPT

P1 bounded subtask planner
   -> explicitly scoped workloads
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   -> only after parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

No planner may grant itself execution authority.

# Parallel Track M — multi-chat orchestration

Separate upper layer. It is not Windows/procedure safety core and is not a release prerequisite.

---

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required.

# Stage 28 — Clean User E2E / first stable release

Fresh-user operation without git checkout or developer-only PowerShell/Python setup, through the accepted product capability surface.

---

# Cross-cutting invariants

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution-state/policy machinery, not a second planner;
- accepted public surface remains small and project-owned;
- semantic/native state precedes pixels when reliable;
- visual evidence is selective, bound to current state and non-authorizing;
- every mutation has an expected effect and fresh post-action verification;
- transition PASS is not task DONE;
- only an independent Finish Gate confirms task completion;
- WorkingState stores structured operational facts/provenance/freshness, never private reasoning;
- repeated no-effect/oscillating actions are bounded by LoopGuard;
- environmental UI/DOM/tool content is untrusted data, not policy authority;
- task-success and safety/policy verification are separate;
- current observed state outranks procedure/demo/history;
- generic Windows code execution remains disabled/unreachable;
- normal semantic route does not require optional 1MCP;
- preserve exact physical evidence heads in `EVIDENCE_INDEX.md`.

# Merge policy

A logically complete branch with reviewed intended diff, passing required CI/physical gates and no unresolved findings should be merged without waiting for a separate merge command.

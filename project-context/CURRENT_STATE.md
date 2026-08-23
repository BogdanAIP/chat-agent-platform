# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose. `EVIDENCE_INDEX.md` is the navigation index for accepted physical heads/result locations; it is not a substitute for primary evidence.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them.

## Product boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local platform has a deterministic execution **Control Plane**, not a second current general-planning brain.

```text
ordinary ChatGPT
  task interpretation / strategy / adaptation
        |
        v
OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
        |
        v
local deterministic execution Control Plane + focused capabilities
```

The Control Plane may keep `TaskState`/checkpoints, advance a selected verified procedure through already-defined transitions, authorize each consequence, verify effects, apply bounded retry/recovery/resource budgets and escalate. It must ABSTAIN/escalate when current evidence does not uniquely match an allowed transition or new strategy is required.

A true local planner is future optional Track P, not current production architecture and not a Stage 27/28 prerequisite. See `CONTROL_PLANE.md`.

Current accepted normal Chat-facing tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

A qualification-only `procedure_run` surface may be developed/tested separately during Stage 26.3, but it is not part of the accepted normal profile until an explicit public-contract decision and ordinary-Chat acceptance.

---

# Accepted foundation

Detailed exact SHAs, local evidence paths and scoped measurements are maintained in `EVIDENCE_INDEX.md` and the historical stage documents.

## Stage 24 / 24.1 — semantic surface and direct tunnel — ACCEPTED

Five public semantic tools, Windows lifecycle and direct stdio Secure MCP Tunnel are accepted foundations. 1MCP remains internal diagnostic/adaptive/aggregation infrastructure rather than the normal semantic critical path.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

Semantic/accessibility structure is primary. Local LFM2.5-VL remains bounded proposal/evidence only, with deterministic authorization and fail-closed ABSTAIN behavior.

## Stage 26.1A-E — OpenAdapt qualification + Windows execution foundations — ACCEPTED

Accepted work includes pinned OpenAdapt Flow/Capture qualification, bounded physical capture, hardened typed Windows execution, the measured desktop-wide UIA bottleneck and its window-scoped native UIA replacement.

The accepted 26.1E result is scoped to the controlled WinForms path; it is not universal Windows accuracy.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Maintained `runtime/windows/` owns bounded actuation, verifier foundations and PID/HWND window-scoped UIA.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

`DesktopState` is bounded read-only evidence carrying session/application/process/window identity, native coordinate space, UIA controls, frame/screenshot digests, provenance and freshness inputs. Observation is not authorization.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED / MERGED #89

Grounding is exact-window/evidence-bound and proposal-only.

## Stage 26.2D — deterministic UIA -> vision routing — ACCEPTED / MERGED #90

Structure-first routing, fresh same-window checks, native foreground/hit-test authority and bounded visual fallback were physically accepted on a controlled path. This is not a general desktop-accuracy claim.

## Stage 26.2E — first real application E2E — ACCEPTED / MERGED #91

An isolated VS Code text-edit task was physically accepted with exact process/window/focus binding, one guarded Unicode action, independent saved-file verification, cleanup and rollback.

Durable architectural lesson: a real application keyboard target may be hidden/zero-size (Monaco). Focused semantic identity and top-level native window geometry are separate evidence channels; one must not be fabricated from the other.

---

# Active release-critical work

## Stage 26.3 — Verified Procedure Runtime / deterministic execution Control Plane — ACTIVE

The next product problem is **autonomous verified progression of a known procedure without using the user as a routine PowerShell operator**.

Target flow:

```text
user gives one goal to ordinary ChatGPT
 -> ChatGPT selects an allowed known procedure + parameters
 -> local deterministic Control Plane
      load exact procedure/ProgramGraph version
      bind TaskState/checkpoint
      observe current state
      select exactly one permitted known transition
      authorize action from current evidence
      execute bounded capability
      re-observe
      verify postcondition
      checkpoint + advance
      repeat while state remains known/permitted
 -> verified completion
    OR ABSTAIN/escalation to ChatGPT
```

### Stage 26.3A — candidate-first procedural trust

A successful trajectory may become a project CANDIDATE, never permanent trust from one success.

The first qualification procedure is intentionally narrow and must prove deterministic multi-transition execution, durable checkpoint compatibility/resume, exact ownership/rollback evidence and a truthful typed procedure surface before any broad Windows/UI procedure expansion.

The accepted five-tool profile stays unchanged by default while the procedure surface is qualification-only.

### Stage 26.3B — advanced verifier/postcondition library

Expand deterministic completion evidence for UI, files/artifacts, process/window/application state, browser state and structured outputs.

### Stage 26.3C — checkpoints / bounded recovery / budgets

Longer procedures require explicit checkpoints, retry ceilings, safe known recovery branches, action/time/resource budgets and deterministic escalation reasons.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Human demonstration transfer follows after the verified procedure runtime is accepted. Live re-resolution and verifier-controlled progression are required; macro replay is insufficient.

---

# Cross-cutting transport reliability

## Transport Supervisor — ACTIVE QUALIFICATION / NOT ACCEPTED

`TRANSPORT_SUPERVISOR.md` defines a separate lifecycle/reliability boundary for the Secure MCP Tunnel. It does **not** replace or become the Stage 26.3 procedure Control Plane.

Required invariants include:

```text
local runtime health
 != remote/control-plane health
 != current ChatGPT route health
```

Recoverable local/network failures may self-heal; authentication/permission/conclusive resource-loss states must block destructive restart loops; transient outages must continue low-rate re-probing rather than permanently exhaust recovery.

Operationally, the supervisor should be physically qualified before relying on repeated hosted ordinary-Chat Stage 26.3 E2E, because manual tunnel repair would otherwise reintroduce the user as an operator.

A healthy replacement tunnel/process is not enough to prove a completed recovery transaction: post-recovery receipt/snapshot publication and a later supervisor heartbeat are separate required evidence.

---

# Current critical path

```text
Stage 26.2E real application E2E — ACCEPTED
 -> Transport Supervisor physical recovery qualification — HIGH-PRIORITY CROSS-CUTTING GATE
 -> Stage 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A candidate-first procedure kernel + truthful qualification surface
    -> ordinary-Chat one-goal multi-transition E2E
    -> 26.3B verifier/postcondition expansion
    -> 26.3C checkpoint/recovery/resource-budget expansion
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27 distribution/maintenance
 -> Stage 28 clean-user E2E / stable release
```

Stage 26.3 remains the release-critical autonomy track; Transport Supervisor is a cross-cutting availability prerequisite for trustworthy hosted qualification, not another planner.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance gates are satisfied, merge it without waiting for a separate merge command.

Stop on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Residual risks

- one real VS Code task is not broad real-application coverage;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- Verified Procedure Runtime/Control Plane is not yet physically accepted through ordinary Chat;
- ordinary Chat -> local autonomous procedure execution without intermediate user commands is not yet physically accepted;
- Transport Supervisor kill/recovery transaction and later network/sleep/reboot gates are not yet physically accepted;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- future local planner has not been researched against verified procedure-state data;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane may advance only already-defined authorized+verified procedure transitions;
- new strategy/ambiguity/stale/UNKNOWN -> ABSTAIN/escalate;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- durable checkpoint evidence is not permission to guess across an ambiguous mid-transition crash;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

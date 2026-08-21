# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general intelligence/planning layer**, while the local platform becomes a strong deterministic execution system with bounded capabilities, persistent execution state, authorization, verification, recovery, procedural memory and specialist inference.

```text
ordinary ChatGPT
  = task understanding / strategy / procedure selection / adaptation / escalation

Chat Agent Platform
  = scoped Files / Browser / Windows capabilities
  + deterministic/native observation
  + bounded specialist perception
  + deterministic execution Control Plane
      TaskState
      ProgramGraph progression
      policy / authorization
      checkpoints
      verifier / postconditions
      bounded retry / recovery
      resource budgets
  + non-agentic procedural memory
  + optional specialist reasoning proposals
  + future optional local general planner research
```

The local deterministic Control Plane is **not** a second planner. It may advance an already-selected known procedure through independently authorized and verified transitions without asking ChatGPT after every low-level step. Novel strategy, incompatible state and open-ended adaptation escalate to ChatGPT.

Canonical contract: `project-context/CONTROL_PLANE.md`.

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Current operating constraint: use ordinary ChatGPT + GitHub + project local/connected tools. Do not use Codex or ChatGPT Work unless the user explicitly re-enables them.

---

# Completed foundation

## Stage 21 — Native ChatGPT <-> local MCP — DONE

Secure MCP Tunnel + official tunnel-client + real local MCP round trip accepted.

## Stage 22 — Superseded universal core reduction — DONE

Old generic agent/gateway core removed from the active architecture.

## Stage 23 — Quality-first module selection — DONE

Focused capability/upstream selection rules accepted.

## Stage 24 / 24.1 — Windows lifecycle + stable semantic surface + direct tunnel — DONE

1MCP remains internal diagnostic/adaptive/aggregation infrastructure; normal public transport is direct stdio semantic-projection.

## Stage 25 / 25.1 / 25.2 — Browser semantic + local vision — DONE

Accepted target baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Structure first, specialist proposal only, deterministic authorization, ABSTAIN on unresolved evidence.

---

# Stage 26 — Windows capability + verified procedural execution — ACTIVE

Required order:

```text
bounded capability
 -> real-application evidence
 -> deterministic procedure Control Plane
 -> human demonstration transfer
```

## 26.0 — UI-Mate analysis + procedural architecture — DONE

UI-Mate remains a demonstration/workflow-state reference, not the active general planner.

## 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

## 26.1B — bounded Windows Capture — ACCEPTED

Physical qualification head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

## 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

## 26.1D — warm Windows latency baseline — ACCEPTED / MERGED #84

Desktop-wide UIA was measured at about 184 s/action and identified as the dominant blocker.

## 26.1E — window-scoped UIA — ACCEPTED / MERGED #85

Physical accepted head: `66390aca1dadf57c4f11568ec311ad6fcdbd7596`.

Controlled evidence: 97 scoped resolutions, zero desktop fallback/binding failures/ambiguities/false/unrelated-window actions, p50 3323.570 ms, p95 3720.061 ms.

## 26.1F — land qualification stack — DONE

#83 -> #84 -> #85 landed.

## 26.1G — authoritative context sync — DONE / MERGED #86

## 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Maintained runtime owns bounded actuation, verifier foundation and exact PID/HWND window-scoped UIA.

Physical runtime head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

## 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head: `dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`.

Observation is evidence, not authority.

## 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED / MERGED #89

Exact physically accepted runtime head: `eadf8ff5a873936441891a66b616c83c62736152`.

Grounder remains exact-window proposal/ABSTAIN only. No broad fuzzy matching.

## 26.2D — deterministic UIA -> vision routing — ACCEPTED / MERGED #90

Exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Accepted route:

```text
native/UIA structure first
 -> exact safe target => structural action
 -> explicitly promoted structural miss only
      -> exact current-window screenshot
      -> bounded Grounder proposal
      -> request/UIA/process/window/frame/coordinate evidence gate
      -> fresh exact-window re-observation
      -> foreground + WindowFromPoint/root-HWND/PID guard
      -> guarded backend frame gate
      -> one bounded action OR ABSTAIN
```

Physical evidence proves one controlled WinForms fallback path, not universal Windows accuracy.

## 26.2E — first real application E2E — ACCEPTED / PR #91

Exact physically accepted runtime/qualification head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Accepted physical result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

The isolated VS Code task passed the full contract:

```text
exact TEMP-contained profile/workspace
 -> exact Code.exe PID/HWND/process generation
 -> production DesktopState
 -> exact hidden Monaco textbox identity
 -> deliberate verifier mismatch => FAIL -> ABSTAIN / zero action
 -> fresh same-window/same-focused-fingerprint state
 -> top-level native foreground/root guard
 -> one-shot window-scoped hidden-focus guard
 -> exactly one guarded Unicode delivery
 -> exact saved-file SHA-256 postcondition
 -> same current window identity
 -> only expected workspace artifact
 -> freshly revalidated WM_CLOSE cleanup
 -> natural CLI exit 0
 -> TEMP cleanup / rollback
```

Key accepted counters:

```text
KEYBOARD_FOCUS_GUARD_ARMS=1
KEYBOARD_FOCUS_GUARD_CALLS=1
KEYBOARD_FOCUS_GUARD_PASSES=1
KEYBOARD_FOCUS_GUARD_FAILURES=0
KEYBOARD_ACTION_COUNT=1
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
STAGE26_2E_REAL_APPLICATION_E2E_RESULT=PASSED
QUALIFICATION_EXIT_CODE=0
```

Real VS Code/Monaco taught an important invariant: the real keyboard target may be an intentionally hidden/zero-size accessibility input. Semantic focus identity and top-level native window geometry are separate evidence channels; point-to-control identity is not required for hidden focused inputs.

Read `STAGE26_2E_REAL_APPLICATION_E2E.md` for accepted evidence.

---

# NEXT / ACTIVE — Stage 26.3: Verified Procedure Runtime / deterministic Control Plane integration

The real-app single-action gate is accepted. The next release-critical target is **verified multi-transition procedure execution without making the user operate PowerShell between steps**.

Target runtime:

```text
user
 -> states one goal once
 -> ordinary ChatGPT
      understand goal
      choose applicable known procedure
      bind parameters
 -> deterministic local Control Plane
      load ProgramGraph
      create/bind TaskState
      observe current state
      resolve exactly one permitted known transition
      authorize action from current evidence
      execute bounded capability
      re-observe effect
      verify postcondition
      checkpoint + advance
      repeat while state remains known/permitted and budgets allow
 -> verified completion
    OR deterministic ABSTAIN/escalation to ChatGPT
```

The Control Plane may continue known transitions autonomously. It must never invent a new strategy or treat procedure/model output as authority.

Priority:

```text
current observed state
 > current goal / verifier criteria
 > trusted procedure evidence
 > historical action sequence
```

## First Stage 26.3 end-to-end acceptance

The first vertical slice must explicitly test the autonomy boundary that Stage 26.2E did not test:

```text
ONE user goal
 -> no intermediate PowerShell copy/paste
 -> ordinary Chat selects a bounded known procedure
 -> local Control Plane performs multiple independently authorized+verified transitions
 -> final postcondition is independently verified
 -> result/evidence returned to Chat
```

Negative acceptance must also prove:

```text
unexpected / stale / ambiguous intermediate state
 -> zero unauthorized continuation
 -> deterministic ABSTAIN/escalation
```

This is **not** “ChatGPT gets arbitrary shell access”. Generic Windows code execution remains disabled. The procedure runtime can invoke only typed/scoped capability transitions already authorized by the active ProgramGraph and current evidence.

## 26.3A — candidate-first procedural trust

```text
DEMO / successful trajectory
 -> CAPTURE
 -> COMPILE
 -> CANDIDATE
 -> replay / regression / variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled / rollback as evidence degrades
```

One demonstration never becomes permanent trust automatically.

Initial 26.3A implementation should define at minimum:

- immutable procedure/program identity/version;
- explicit transition ids;
- required current-state evidence;
- capability/action template;
- parameter schema;
- verifier/postcondition per transition;
- checkpoint state;
- failure/ABSTAIN reason;
- candidate/trusted/quarantined/disabled lifecycle evidence.

## 26.3B — advanced verifier/postcondition library

Expand verifier coverage for:

- UI state;
- files/artifact hashes/content;
- process/window/application state;
- browser state;
- structured outputs;
- completion/rollback evidence.

## 26.3C — checkpoint / bounded recovery / resource budgets

Make deterministic continuation practical for longer procedures:

- explicit checkpoints;
- retry ceilings;
- safe known recovery branches;
- action/time/resource budgets;
- deterministic escalation reasons;
- no infinite retry or blind continuation.

This may be folded into 26.3A/B implementation if the code remains cohesive; it is an architectural requirement even if no separate PR number is used.

---

# Stage 26.4 — Human Demo -> Transferable Skill

```text
human demonstration
 -> Capture
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified same/near-state replay
 -> changed-state/task replay
```

Acceptance requires live re-resolution and verifier-controlled progression, not macro replay.

---

# Optional Research Track R — Specialized reasoning

Procedure-state datasets and small structured reasoning experiments begin only when real verified state-transition data exists and measurements justify them.

A `SpecializedReasoningBackend` may propose structured choices/confidence/ABSTAIN. It never authorizes or actuates and is different from a general planner.

# Optional Future Track P — Local Planner / Offline Autonomy

A local general planner is intentionally kept in the long-term roadmap, but **not** in the current release-critical path.

Earliest prerequisite: verified procedure-state data from 26.3/26.4 plus a measured reason to move planning local.

Potential triggers:

- offline operation;
- material planning round-trip latency;
- multi-machine/highly parallel independent work;
- deployment/privacy requirements;
- measured local-model parity on the actual workload.

Progression:

```text
P0 shadow planner
   sees structured goal/state/procedure evidence
   -> proposal only
   -> no authorization / no actuation
   -> benchmark against ordinary ChatGPT manager

P1 bounded subtask planner
   explicitly scoped task families only
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   only after parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

Even in P2 the planner stays **above** the same policy/authorization/verifier Control Plane. No planner can grant itself execution authority.

# Parallel Track M — multi-chat orchestration

Separate upper layer, not the Windows/procedure safety core and not a release prerequisite. Under the current operating constraint it may coordinate ordinary ChatGPT sessions only; Codex/Work remain disabled unless explicitly re-enabled.

---

# Public contract review

The current five tools remain accepted until a dedicated ADR changes them. Desktop/procedure capability must use truthful semantics; never hide native desktop actions behind `web_interact` or add generic `tool_invoke`/`run_anything`/opaque workflow execution.

Stage 26.3 may require a dedicated typed semantic procedure surface. Any public-surface change requires its own explicit contract/ADR and must not expose arbitrary command execution.

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required.

# Stage 28 — Clean User E2E / first stable release

Fresh-user operation without git checkout or developer-only Python/PowerShell setup.

---

# Merge policy

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command.

Do not merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

# Cross-cutting invariants

- ordinary ChatGPT is the only **current general** planner/intelligence;
- deterministic local Control Plane is allowed/desired and is not a general planner;
- semantic/native structure before pixels where reliable;
- observation/model/procedure/planner proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/ambiguous/UNKNOWN causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation and Windows root/junction containment;
- keep `main` as integration line and preserve exact physical evidence heads.

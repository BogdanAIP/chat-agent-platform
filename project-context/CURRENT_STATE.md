# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them.

## Current product boundary

Ordinary ChatGPT is the **only current general planner/intelligence layer**.

The local platform is expected to own a **deterministic execution Control Plane** for task/procedure state, authorization, checkpoints, verification, bounded recovery and resource budgets. This Control Plane is not a second general planner: it can advance already-selected known procedure transitions after live authorization/verification, but it must ABSTAIN/escalate whenever a new strategy is required.

Canonical distinction: `project-context/CONTROL_PLANE.md`.

```text
ordinary ChatGPT
  general goal / strategy / adaptation
        |
        v
local deterministic Control Plane
  TaskState / ProgramGraph progression
  policy / authorization
  checkpoints / verifier / recovery budgets
        |
        v
focused Files / Browser / Windows capabilities
```

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. `semantic-projection` remains a truthful deterministic compatibility boundary, not a workflow brain.

---

# Accepted foundation

## Stage 24 / 24.1 — semantic surface and direct tunnel — ACCEPTED

Five public semantic tools, Windows lifecycle and direct stdio semantic tunnel are accepted foundations.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Vision is structure-first, bounded proposal-only evidence behind deterministic authorization.

---

# Stage 26 accepted evidence

## 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

## 26.1B — bounded Windows Capture — ACCEPTED

Physical head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

## 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

## 26.1D — latency baseline — ACCEPTED / MERGED #84

Desktop-wide UIA was isolated as the dominant ~184 s/action blocker.

## 26.1E — window-scoped UIA — ACCEPTED / MERGED #85

Physical accepted head: `66390aca1dadf57c4f11568ec311ad6fcdbd7596`.

Controlled evidence: 97 scoped resolutions, zero Desktop fallback/binding failures/ambiguities/false/unrelated-window actions, p50 3323.570 ms, p95 3720.061 ms.

## 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Physical runtime head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

Maintained `runtime/windows/` owns bounded actuation, verifier foundation and exact PID/HWND UIA.

## 26.2B — DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is read-only evidence. Observation is not authorization.

## 26.2C — Native Desktop Grounder — ACCEPTED / MERGED #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Grounder remains exact-window proposal/ABSTAIN only. The physical ordinal-label mismatch is handled by one narrowly bounded alias; general fuzzy matching is forbidden.

## 26.2D — deterministic UIA -> vision routing — ACCEPTED / MERGED #90

Integration merge:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted PR head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

Key physical evidence included wrong-window native refusal, no-promotion and role-conflict ABSTAIN, fresh identical exact-window screenshots, one accepted visual-fallback delivery, one coordinate executor call, zero structural executor calls, zero Desktop fallback/binding failures/ambiguities and clean fixture/runtime restore.

This remains controlled WinForms evidence, not broad real-application accuracy.

---

# Active release-critical work

## Stage 26.2E — first real application E2E — ACTIVE

Active branch:

`chat/stage26-2e-vscode-real-app-e2e`

Qualification application: isolated VS Code with a new disposable `.txt` under a specifically prefixed OS TEMP root.

The current physical contract requires:

- TEMP containment in both Python and PowerShell before recursive cleanup;
- isolated VS Code user-data/extensions and no user project/profile mutation;
- exact unique Code.exe PID/HWND/DesktopState;
- enabled/visible focused editor evidence;
- deliberate wrong postcondition -> FAIL -> ABSTAIN while mutation count remains zero;
- fresh pre-action DesktopState with same exact window identity and same focused-editor observation fingerprint;
- native foreground/WindowFromPoint/root-HWND/PID guard immediately before action;
- exactly one guarded Unicode text delivery;
- exact autosaved file size/SHA-256 completion verification;
- workspace snapshot containing only the expected artifact;
- exact qualification window `WM_CLOSE`;
- natural CLI exit; forced terminate/kill is cleanup-only and makes acceptance fail;
- application + TEMP-root rollback PASS.

A physical VS Code qualification has not yet been accepted at this snapshot.

Read `STAGE26_2E_REAL_APPLICATION_E2E.md`.

---

# Current critical path

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
    -> checkpoints/bounded recovery/resource budgets as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E / stable release
```

Stage 26.3 should create the local deterministic execution Control Plane around selected `ProgramGraph` procedures. It should **not** create a current local general planner.

## Future optional planner track

A local general planner remains an explicit future research goal (`ROADMAP.md` Track P): shadow/proposal-only first, then bounded subtask planning, then optional local general-planner mode only if verified data and measured offline/latency/parallel/deployment needs justify it.

Any future planner remains behind the same deterministic authorization/verifier Control Plane and cannot grant itself execution authority.

---

# Residual risks

- Stage 26.2E real application E2E is not yet physically accepted;
- one controlled WinForms routing PASS is not broad application accuracy;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- deterministic procedure Control Plane is architecture, not yet integrated product code;
- verified procedure trust/reuse and human-demo transfer are not accepted;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- future local planner is research only and not accepted;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only **current general** planner/intelligence;
- deterministic local execution Control Plane is permitted/desired and is not a general planner;
- semantic/native structure before pixels where reliable;
- model/procedure/planner/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/uncertain/UNKNOWN evidence causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

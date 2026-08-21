# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the only general intelligence/planning layer while the local platform supplies bounded observation, execution, verification, procedural memory and optional specialist inference.

```text
ordinary ChatGPT
  = task understanding / strategy / adaptation / escalation

Chat Agent Platform
  = scoped files/browser/windows capabilities
  + deterministic/native observation
  + bounded local vision fallback
  + authorization and guarded execution
  + verification
  + non-agentic procedural memory
  + optional specialized local reasoning later
```

The product must not become a second autonomous agent brain, a generic hidden workflow dispatcher or an unbounded local code-execution gateway.

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Any desktop/public-contract change waits for an explicit post-desktop ADR.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

---

# Completed foundation

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed from active architecture.

## Stage 23 — Quality-first module selection — DONE

Focused Filesystem/Playwright/1MCP candidates and selection rules accepted.

## Stage 24 / 24.1 — Windows lifecycle + stable semantic surface + direct tunnel — DONE

1MCP remains internal diagnostic/adaptive/aggregation infrastructure; normal public path is direct semantic-projection.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — DONE

Accepted local visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Structure first, specialist proposal only, deterministic authorization, ABSTAIN on unresolved evidence.

---

# Stage 26 — Windows capability + verified procedural memory — ACTIVE

The required order is capability -> real application evidence -> verified procedures. Do not insert a second local planner.

## Stage 26.0 — UI-Mate analysis + procedural architecture — DONE

UI-Mate remains a demonstration-guided workflow/state reference, not a second GUI planner.

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Physical qualification head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

## Stage 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

## Stage 26.1D — warm Windows latency baseline — ACCEPTED / MERGED #84

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

## Stage 26.1E — window-scoped UIA resolver — ACCEPTED / MERGED #85

Physical accepted head: `66390aca1dadf57c4f11568ec311ad6fcdbd7596`.

```text
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
```

## Stage 26.1F — land qualification stack — DONE

#83 -> #84 -> #85 landed.

## Stage 26.1G — authoritative context synchronization — DONE / MERGED #86

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA.

Physical production head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Observation is read-only evidence, not authorization.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED / MERGED #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Grounder remains exact-window proposal/ABSTAIN only. The physically observed `1. Benchmark start` -> `Benchmark start` case is handled by one bounded ordinal-prefix alias after inventory-absent; no general fuzzy matching exists.

## Stage 26.2D — deterministic UIA -> vision routing + adversarial authorization — ACCEPTED / MERGED #90

Integration main after merge:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Accepted route:

```text
native/UIA structure first
 -> exact safe structural target => deterministic UIA action
 -> explicitly promoted structural miss only
      -> exact current-window screenshot
      -> Stage 26.2C Grounder proposal
      -> request/UIA/process/window/frame/coordinate evidence gate
      -> fresh exact-window re-observation
      -> foreground + WindowFromPoint/root-HWND/PID guard
      -> accepted guarded-coordinate backend frame gate
      -> one physical click OR ABSTAIN
```

Physical evidence includes one real guarded visual-fallback click, correct refusal without vision promotion, correct role-conflict refusal, wrong-window native point-guard refusal, identical pre/post inference screenshots, `POSITIVE_CONSISTENCY_IOU=0.34455881673798816`, one coordinate executor call, zero structural executor calls, zero Desktop fallback/binding failures/ambiguities and clean fixture/runtime restore.

This remains controlled WinForms evidence, not broad application accuracy.

---

# NEXT — Stage 26.2E: first real application E2E

Active branch at this snapshot:

`chat/stage26-2e-vscode-real-app-e2e`

Qualification candidate: isolated VS Code with one disposable text file under a specifically prefixed TEMP root.

Required physical contract:

```text
new isolated TEMP root
 -> isolated VS Code user-data/extensions
 -> unique empty .txt artifact
 -> exact unique Code.exe PID/HWND/window binding
 -> DesktopState + focused editor evidence
 -> native foreground/hit-test guard
 -> deliberate wrong verifier expectation => FAIL -> ABSTAIN, zero action
 -> exactly one guarded Unicode text delivery
 -> independent saved-file size/SHA-256 verification
 -> same current window identity
 -> workspace contains only expected artifact
 -> close exact qualification window
 -> remove isolated TEMP root
 -> rollback PASS
```

No user workspace, normal VS Code profile, extensions, settings or project files are part of the test.

The first physical run should fail closed if VS Code exposes a different UIA focus shape than expected; adjust only from observed evidence.

Acceptance requires current-state verification, completion verification and rollback. A delivery receipt never proves completion.

Read `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`.

---

# Stage 26.3 — Verified Procedure Runtime

Only after Stage 26.2E real-application acceptance:

```text
ordinary ChatGPT
 -> decide whether a known procedure is relevant
 -> load ProgramGraph
 -> observe current state
 -> resolve one applicable abstract transition
 -> deterministic authorization
 -> bounded execution
 -> observe effect
 -> verifier
 -> advance / recover / ABSTAIN
```

Priority:

```text
current observed state
 > current goal/verifier criteria
 > trusted procedural evidence
 > raw historical action sequence
```

Retrieval/procedure selection is non-authorizing. The runtime is procedural support for ordinary ChatGPT, not another planner.

## Stage 26.3A — candidate-first procedural trust

```text
DEMO
 -> CAPTURE
 -> COMPILE
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantined/disabled as evidence degrades
```

One demonstration never becomes permanent trust automatically.

## Stage 26.3B — advanced verifier/postcondition library

Expand the verifier foundation for UI state, files, windows, applications, browser state, artifacts and structured outputs.

---

# Stage 26.4 — Human Demo -> Transferable Skill

Human demonstration -> Capture -> structured trajectory -> ProgramGraph -> project CANDIDATE -> verified replay -> changed-state/task replay.

One demonstration is evidence, not blind macro authority.

---

# Optional Research Track R — not release-critical

Procedure-state datasets and SpecializedReasoningBackend experiments begin only if real verified data and measurements justify them. Any tiny model proposes; authorization/executor/verifier remain authoritative.

# Parallel Track M — multi-chat orchestration

Separate upper layer, not part of Windows/procedure safety core and not a release prerequisite. Under the current constraint it may coordinate ordinary ChatGPT sessions only; Codex and Work remain disabled unless explicitly re-enabled.

---

# Public MCP contract — post-desktop ADR

After real desktop evidence decide whether the five current tools remain sufficient or a few truthful coarse desktop/procedure capabilities are needed. Never hide native desktop actions behind `web_interact`; never add generic `tool_invoke`/`run_anything`/opaque workflow execution.

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required.

# Stage 28 — Clean User E2E / first stable release

Fresh-user flow without git checkout or developer-only Python/PowerShell setup.

---

# Merge policy

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command.

Do not auto-merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

# Cross-cutting invariants

- ordinary ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- observation is not authorization;
- model/procedure proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/ambiguous/UNKNOWN causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation and Windows root/junction containment;
- track browser DNS/redirect/private-network residual risk;
- keep `main` as integration line and preserve exact physical evidence heads.
# Start Here — authoritative continuation guide

Use this file first in a fresh ChatGPT or Codex session.

## 1. Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect the exact PR heads relevant to the task.

At creation of this synchronization branch:

```text
main = def67e45d7a72547c53bcf339d00124f4edca0be
```

Accepted but still stacked/unmerged Windows qualification work:

```text
#83 Stage 26.1C
  head = 4bf08dd9b8d1ff010f14723f9bb0384b97334a2b
  base = main

#84 Stage 26.1D
  head = 114e865090d39d218418958c40cf359b5f6808da
  base = #83 branch

#85 Stage 26.1E
  head = 66390aca1dadf57c4f11568ec311ad6fcdbd7596
  base = #84 branch
```

This docs branch is stacked on exact accepted #85 head. It does **not** mean C/D/E are already in `main`.

## 2. Read current authoritative context

Read in this order:

1. `project-context/CURRENT_STATE.md`
2. `project-context/ROADMAP.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/MODULE_CATALOG.md`
5. `project-context/KNOWN_ISSUES.md`
6. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
7. accepted Stage 26.1 qualification documents/results as needed

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## 3. Product boundary

Ordinary ChatGPT remains the only general planner/intelligence.

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local capabilities
```

Current public semantic tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

Local components may observe, execute bounded actions, verify effects, reuse procedures and run bounded specialist perception. They must not become a second universal planner or expose generic hidden execution.

## 4. Browser foundation already accepted

Stage 25/25.1/25.2 established:

- semantic/accessibility structure before pixels;
- local LFM2.5-VL-450M F16 only on the reviewed visual fallback path;
- model proposal is not authorization;
- stale/unpromoted/ambiguous evidence fails closed;
- 0 false clicks in accepted Stage 25.2 target test.

Accepted local visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
F16 mmproj
CPU 8 threads
ctx 2048
```

## 5. Procedural substrate direction

Target-qualified upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Use Flow `Workflow`/`ProgramGraph`; adapt upstream lifecycle under project candidate-first trust; reuse Capture/Windows mechanics where qualified. Do not build duplicate generic recorder/compiler/skill-store/actuator components without a measured blocker.

## 6. Stage 26.1B Capture — accepted

Exact accepted qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json`

Capture is no longer the next unresolved gate.

## 7. Stage 26.1C executor — accepted on target / PR #83

Exact accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted boundary:

```text
loopback/auth
legacy generic exec absent/disabled
typed bounded actions
stale frame/context refusal
focus/fingerprint checks
bounded keyboard/pointer/scroll
layout-independent Unicode typing
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
```

No new project-owned Windows actuator is justified without later measured evidence.

## 8. Stage 26.1D latency baseline — accepted benchmark / PR #84

Warm action sequence:

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Exact upstream source inspection identified repeated desktop-wide UIA traversal as the dominant blocker.

## 9. Stage 26.1E window-scoped UIA — accepted on target / PR #85

Exact accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Accepted resolution path:

```text
expected PID
 -> bounded EnumWindows
 -> same-process HWNDs only
 -> exact UIA WindowControl
 -> native FindAll inside the bound window only
 -> existing candidate/fingerprint semantics
 -> independent re-resolution before act
```

Physical result:

```text
WINDOW_BINDING_PASS=True
PREFLIGHT_CANDIDATE_COUNT=1
PREFLIGHT_FINGERPRINT_PRESENT=True
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
speedup=55.244x p50 / 49.883x p95
```

Do not call this “100% Windows accuracy”. It is 97/97 controlled fixture evidence for the exercised role+name path. `AutomationId`, custom controls, multiple real applications/windows and visual fallback still need separate evidence.

## 10. Immediate critical path

### A. Land the stacked qualification PRs safely

```text
verify exact #83 -> merge only on explicit authorization
 -> retarget #84 to main
 -> inspect resulting diff + CI
 -> merge only on explicit authorization
 -> retarget #85 to main
 -> inspect resulting diff + CI
 -> merge only on explicit authorization
```

Do not blindly merge the stack.

### B. Retarget authoritative docs sync

After #85 is in `main`, retarget the docs-sync PR to `main`, inspect that only intended documentation remains and re-run CI before merge.

### C. Stage 26.2A — Production Windows Runtime Foundation

Move accepted qualification mechanisms into a maintained runtime boundary:

```text
interactive session identity
application/process identity
PID/HWND exact-window binding
window-scoped UIA
typed guarded execution
stale/focus/fingerprint safety
verifier foundation
lifecycle/health/logging
```

Verifier foundation is required here:

```text
observe before
 -> authorize
 -> act
 -> observe after
 -> PASS | FAIL | UNKNOWN
```

Action delivery alone never means success.

### D. Stage 26.2B — DesktopState/observation

Canonical state must carry identity, coordinate space, freshness/provenance, control fingerprints and screenshot/frame digests. Observation is not authorization.

### E. Stage 26.2C — native desktop F16 Grounder

Do not reuse the browser CSS/Playwright viewport adapter as native Windows coordinates. Create a dedicated window-pixel proposal seam.

### F. Stage 26.2D — semantic/UIA -> vision routing + accuracy suite

Before broad desktop claims, exercise duplicates, disabled/hidden controls, wrong process/window, overlays, focus changes, stale/recreated windows, `AutomationId`, role+name, weak/custom controls, UIA-missing visual fallback and visual ambiguity/ABSTAIN.

### G. Stage 26.2E — one real application E2E

Choose one medium-complexity real user app from task/evidence with disposable data, deterministic postcondition and rollback. Names such as VS Code, OriginPro or Reaper are candidates, not fixed architecture.

### H. Stage 26.3 / 26.4

Only after real desktop E2E:

```text
Verified Procedure Runtime
 -> candidate-first trust
 -> advanced postcondition verifiers
 -> Human Demo -> transferable verified candidate skill
```

## 11. Optional/parallel directions

### Specialized local reasoning

Procedure-state datasets and TRM/STARM/FPRM/small-model benchmarks are optional research. They start only after real verified data and a measured need such as excessive ChatGPT escalation/decision latency. They are not prerequisites for Stage 27/28.

### Multi-Chat / Codex orchestration

Keep it as a separate upper-layer controller over ChatGPT/Codex. It must not enter Windows executor/procedure safety core and is not a release prerequisite.

## 12. Public contract decision

Only after the Windows desktop surface exists, make a separate ADR deciding whether the current five tools remain sufficient or a few truthful coarse desktop/procedure tools are required.

Never hide desktop control behind misleading `web_interact`, and never add a generic `tool_invoke`/`run_anything`/opaque workflow dispatcher.

## 13. Stage 27 / 28

Stage 27: installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI.

Stage 28: clean-user E2E and first stable release without git checkout or developer-only Python/PowerShell setup.

## 14. Non-negotiable rules

- ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation, Windows junction/root containment and browser network residual-risk tracking;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

# Current State

## Repository-state rule

Always resolve live `main` before new work. Do not treat a documentation SHA as permanently current.

At the time this synchronization branch was created:

```text
main = def67e45d7a72547c53bcf339d00124f4edca0be
```

The accepted Stage 26.1C/D/E work is still a stacked open PR chain and is **not yet in main**:

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

This documentation branch is stacked on exact accepted #85 head. It must be retargeted to `main` only after #83 -> #84 -> #85 are safely landed and the resulting diff is rechecked.

## Product boundary

Ordinary ChatGPT remains the only general planner/intelligence layer.

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

Local components may observe, execute bounded actions, verify effects, reuse procedures, or provide bounded specialist inference. They must not become a second autonomous planner.

---

# Accepted foundation

## Stage 24 / 24.1

Five-tool semantic surface, Windows lifecycle and direct stdio semantic tunnel are accepted foundations.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision accepted

Accepted local visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
F16 mmproj
CPU 8 threads
ctx 2048
```

Stage 25 present-target baseline remains 3/5 because repeated-row/tiny classes are intentionally unpromoted.

Stage 25.2 accepted routing remains semantic/native first. Vision starts only on the reviewed zero-exact-candidate path and remains proposal-only behind deterministic authorization/freshness checks.

Final Stage 25.2 target evidence:

```text
semantic_hits=2
visual_hits=1
correct_abstains=2
false_clicks=0
errors=0
semantic_cases_started_vlm=0
acceptance_pass=true
```

---

# Stage 26 accepted evidence

## Stage 26.0 — procedural architecture — DONE

`Tencent/UI-Mate` remains a demonstration-guided workflow/state reference. It is not adopted as a second GUI planner.

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

Pinned target-tested upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Decisions:

- Flow `Workflow` / `ProgramGraph`: ADOPT behind project boundaries;
- `SkillLibrary` / learn / teach: ADAPT with project candidate-first trust;
- Capture: reuse upstream after bounded target qualification;
- Windows backend/agent: reuse typed boundary if hardened qualification passes;
- OpenAdapt Desktop: Stage 27 distribution reference, not runtime baseline.

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Exact target-tested qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json`

Accepted evidence includes raw UIA capture, bounded selected-window behavior, structural suppression outside the selected window, compile success, explicit refusal of unaccepted native replay, zero false/unrelated structural actions and clean local artifact handling.

## Stage 26.1C — hardened typed Windows executor — ACCEPTED ON TARGET / PR #83

Exact physically accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted:

```text
loopback-only agent
auth required
legacy exec absent/disabled
unauthorized input rejected
command/exec-shaped input rejected
stale frame refusal
stale context refusal
interactive session proof
UIA unique target + fingerprint-bound actuation
layout-independent Unicode text delivery
guarded keyboard/pointer/scroll
zero unrelated-window actions
zero false actions
```

Project-owned actuator replacement is not justified without a measured blocker.

## Stage 26.1D — physical Windows latency baseline — ACCEPTED BENCHMARK / PR #84

Measured warm seven-operation cycle:

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Root cause was confirmed in exact pinned OpenAdapt source: desktop-wide `_find_candidates()` traversal starts at `GetRootControl()` and walks the full UIA tree; structural act re-resolves again before fingerprint verification.

## Stage 26.1E — PID/HWND window-scoped UIA — ACCEPTED ON TARGET / PR #85

Exact physically accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Accepted resolution path:

```text
expected process id
 -> bounded EnumWindows
 -> same-process HWND filtering
 -> ControlFromHandle only after PID filter
 -> exact WindowControl name
 -> FindAll only inside bound window
 -> upstream candidate/fingerprint semantics
 -> independent re-resolution before act
```

Physical acceptance:

```text
WINDOW_BINDING_PASS=True
PREFLIGHT_CANDIDATE_COUNT=1
PREFLIGHT_FINGERPRINT_PRESENT=True
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_ENUM_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
LAST_FAILURE_STAGE=<null>
ERROR=<null>
PASS=True
```

Performance:

```text
action p50 = 3323.570 ms
action p95 = 3720.061 ms
p50 speedup = 55.244x
p95 speedup = 49.883x
```

This closes the measured desktop-wide UIA traversal blocker on the qualification fixture.

### Accuracy scope

Do not claim global Windows accuracy from the 97/97 fixture result. The accepted run proves the role+name path on the controlled WinForms fixture. Real applications, broader `AutomationId`, custom controls, multi-window conflict and vision fallback need separate evidence.

---

# Current integration gap

Most strong Windows capabilities still exist as qualification/benchmark assets rather than the normal product runtime:

```text
production today
  semantic-projection
    -> files
    -> browser semantic/vision

accepted beside production
  OpenAdapt Capture qualification
  hardened Windows executor seam
  PID/HWND window-scoped UIA resolver
  benchmark/fixture evidence
```

The next engineering objective is **not more fixture optimization** and not immediate procedural-memory integration. It is to assemble a production Windows runtime from the accepted components.

---

# Next critical path

## 1. Land #83 -> #84 -> #85 safely

The PRs are stacked. Required sequence:

```text
verify/merge #83
 -> retarget #84 to main
 -> verify resulting diff + CI
 -> merge #84
 -> retarget #85 to main
 -> verify resulting diff + CI
 -> merge #85
```

No blind stacked merge.

## 2. Retarget and land authoritative context sync

After the stack is in `main`, retarget this docs branch/PR to `main`, verify only intended documentation changes remain, run CI and then merge.

## 3. Stage 26.2A — Production Windows Runtime Foundation

Extract accepted mechanisms from qualification scripts into a maintained `runtime/windows/` boundary:

```text
session identity
process/application identity
PID/HWND exact window binding
window-scoped UIA
typed UIA/keyboard/pointer/scroll
stale frame/context/focus/fingerprint safety
lifecycle/health/logging
minimal verifier foundation
```

Verifier foundation belongs here:

```text
observe before
 -> authorize
 -> act
 -> observe after
 -> PASS | FAIL | UNKNOWN
```

## 4. Stage 26.2B — Desktop Observation / DesktopState

Create a canonical structured state with explicit provenance/freshness/coordinate-space and control fingerprints. Observation does not imply authorization.

## 5. Stage 26.2C — Desktop LFM2.5-VL Grounder

Create a native-window pixel-space adapter. Existing browser/CSS viewport grounding must not be falsely reused for desktop coordinates.

## 6. Stage 26.2D — semantic/UIA -> vision routing + adversarial accuracy suite

Test duplicates, disabled/hidden targets, wrong window/process, stale state, overlays, focus changes, `AutomationId`, role+name, weak/custom controls and vision ambiguity/ABSTAIN.

## 7. Stage 26.2E — one real application E2E

Use one medium-complexity real user application with a safe disposable artifact and deterministic postcondition/rollback. Candidate names are examples only; selection comes from task/evidence.

## 8. Stage 26.3 — Verified Procedure Runtime

Only after Windows capability is product-tested on a real application, integrate OpenAdapt `ProgramGraph`/procedural reuse behind the ChatGPT-only planner boundary.

## 9. Stage 26.4 — Human Demo -> Transferable Skill

Record, compile, keep candidate-first trust, verify, then replay against a related changed state/task without blind historical coordinates.

---

# Optional / parallel work, not release blockers

## Specialized local reasoning research

Procedure-state dataset and TRM/STARM/FPRM/small-model experiments are optional research after real procedure data exists. They are not prerequisites for Stage 27/28.

A tiny model may only propose a structured next transition and may ABSTAIN. Authorization/execution/verification stay deterministic/guarded.

## Multi-Chat / Codex orchestration

A separate upper-layer controller may coordinate ChatGPT/Codex sessions for research/code/review, but it is not part of `runtime/windows`, procedural authorization or executor safety core and is not a release prerequisite.

---

# Public contract

Keep the current five tool names until the desktop surface exists. Then make a separate ADR deciding whether a few truthful coarse desktop/procedure tools are needed.

Do not add generic `tool_invoke`, `run_anything`, opaque workflow execution, or misleading reuse of `web_interact` for native Windows.

---

# Residual risks

- repeated-row/tiny/icon-only browser visual promotion remains incomplete;
- screenshot -> coordinate action remains a narrow non-atomic TOCTOU boundary;
- PID-bound loopback ownership is not cryptographic endpoint authentication;
- browser DNS/rebinding/redirect/private-network isolation is incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- accepted Windows executor/window-scoped resolver is not yet integrated into product runtime;
- fixture 97/97 is not cross-application accuracy evidence;
- desktop Grounder/routing is not implemented;
- real application Windows E2E is not yet accepted;
- procedural runtime/product trust adapter is not integrated;
- no stable release exists.

---

# Non-negotiable rules

- ordinary ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/uncertain evidence causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- do not duplicate accepted upstream components without a measured blocker;
- keep the public surface small and truthful;
- preserve fail-closed behavior over benchmark hit rate.

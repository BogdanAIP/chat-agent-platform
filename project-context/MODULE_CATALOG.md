# Module / Capability Catalog

Status synchronized through the physically accepted Stage 26.1E qualification stack. This branch is stacked on PR #85 and does not imply #83/#84/#85 are already in `main`.

This is a current capability-status catalog, not a fixed list of future applications.

## Repository-state rule

Resolve live `main` before work. Stable acceptance heads may remain on open PR branches until explicitly landed.

Current accepted stacked Windows heads:

```text
Stage 26.1C / PR #83 = 4bf08dd9b8d1ff010f14723f9bb0384b97334a2b
Stage 26.1D / PR #84 = 114e865090d39d218418958c40cf359b5f6808da
Stage 26.1E / PR #85 = 66390aca1dadf57c4f11568ec311ad6fcdbd7596
```

## Status meanings

- **PRODUCT-ACCEPTED** — accepted normal product/ordinary-Chat path for the scoped contract.
- **ACCEPTED-INFRASTRUCTURE** — accepted internal runtime/lifecycle foundation.
- **ACCEPTED-SPECIALIST** — bounded specialist backend accepted behind a focused boundary.
- **TARGET-QUALIFIED** — exact component/path physically passed its target qualification but is not yet integrated into the normal product runtime.
- **ADAPT-CANDIDATE** — reusable upstream mechanism that still needs project integration/policy wrapping.
- **DIAGNOSTIC** — internal testing/lifecycle infrastructure only.
- **ACTIVE-INTEGRATION** — next product-integration work after target qualification.
- **FUTURE-SCOPED-GATE** — future capability needing explicit evidence.
- **OPTIONAL-RESEARCH** — useful only if later data/measurements justify it; not release-critical.
- **PARALLEL-TRACK** — separate layer not on the core release path.

## Current catalog

| Capability class | Current implementation/direction | Status | Decision |
|---|---|---|---|
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | PRODUCT-ACCEPTED | Normal ordinary-Chat reachability. |
| Public semantic transport | direct stdio secure semantic launcher -> semantic-projection | PRODUCT-ACCEPTED | Normal public path. |
| Internal MCP aggregation/lifecycle | 1MCP | ACCEPTED-INFRASTRUCTURE / DIAGNOSTIC | Internal diagnostics/adaptive lifecycle; not normal public semantic hop. |
| Windows manager ownership | one authoritative runtime owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | Ambiguous/foreign ownership fails closed. |
| Scoped files | official Filesystem backend behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`. |
| Browser | pinned Playwright path behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`. |
| Semantic capability projection | deterministic five-tool compatibility boundary | PRODUCT-ACCEPTED | Small truthful surface; not planner/gateway/workflow engine. |
| Local visual grounding | llama.cpp + LFM2.5-VL-450M F16 | ACCEPTED-SPECIALIST | Local/on-demand/perception-only; replaceable. |
| Browser semantic->vision routing | Stage 25.2 internal escalation | PRODUCT-ACCEPTED | Semantic first; reviewed zero-exact-candidate visual path only. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | TARGET-QUALIFIED | ADOPT behind project policy boundaries. |
| Procedural lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression internals | ADAPT-CANDIDATE | Reuse mechanics; project trust stays candidate-first. |
| Human/desktop capture | OpenAdapt Capture 1.2.2 + Flow adapter | TARGET-QUALIFIED | Stage 26.1B physically accepted; production procedure integration still later. |
| Typed Windows executor | pinned OpenAdapt `WindowsBackend` + hardened interactive-session agent | TARGET-QUALIFIED | Stage 26.1C physically accepted; legacy generic exec excluded; no replacement actuator without blocker. |
| Window-scoped Windows UI resolution | PID -> Win32 HWND -> exact window -> bounded native UIA FindAll | TARGET-QUALIFIED | Stage 26.1E physically accepted; remove desktop-wide traversal in production integration. |
| Production Windows runtime | maintained session/observation/actuation/safety/verification/lifecycle boundary | ACTIVE-INTEGRATION | Next main engineering layer after stacked PR landing/docs sync. |
| Desktop observation | canonical `DesktopState` with identity/freshness/provenance | ACTIVE-INTEGRATION | Build after Windows runtime foundation. |
| Runtime verifier foundation | before/after observation + expected-effect PASS/FAIL/UNKNOWN | ACTIVE-INTEGRATION | Must exist before real-application E2E; delivery is not success. |
| Desktop F16 Grounder | native/window pixel-space adapter | ADAPT-CANDIDATE | Separate from browser CSS viewport; proposal-only. |
| Windows semantic/UIA->vision router | deterministic structure first, bounded visual fallback | FUTURE-SCOPED-GATE | Must pass adversarial accuracy suite before broad desktop claims. |
| Real application Windows E2E | one medium-complexity user application + disposable artifact | FUTURE-SCOPED-GATE | Select from real task/evidence, not a permanently fixed app list. |
| Verified Procedure Runtime | ProgramGraph + live state + authorization + verifier | FUTURE-SCOPED-GATE | Only after real desktop E2E. |
| Human demonstration transfer | Capture -> candidate procedure -> changed-state verified replay | FUTURE-SCOPED-GATE | Not blind macro replay. |
| Procedure-state dataset | structured verified state-transition examples | OPTIONAL-RESEARCH | Not a Stage 27/28 prerequisite. |
| Specialized local reasoning | generic `SpecializedReasoningBackend` | OPTIONAL-RESEARCH | Only if data and measured escalation/latency need justify it. |
| Multi-Chat/Codex orchestration | upper-layer controller over Chat/Codex sessions | PARALLEL-TRACK | Keep outside Windows/procedure safety core; not release prerequisite. |
| Distribution/cockpit reference | OpenAdapt Desktop packaging/Tauri/sidecar patterns | ADAPT-CANDIDATE | Stage 27 reference; verify runtime-version compatibility. |
| Distribution/maintenance | installer/update/repair/doctor/uninstall/rollback/restart recovery | FUTURE-SCOPED-GATE | Stage 27. |

## Current public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

This is an accepted current contract, not permanent dogma. After the Windows desktop surface exists, a separate ADR decides whether a few truthful coarse desktop/procedure capabilities are required.

Never preserve the count by hiding native desktop actions behind `web_interact`, and never add a generic opaque `tool_invoke` equivalent.

## Stage 26.1B Capture evidence

Accepted target qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json`

Key accepted properties: interactive-session capture, bounded selected-window evidence, raw UIA evidence retention, Flow compile success, zero foreign structural-window evidence, explicit refusal of unaccepted native replay, local artifact containment and cleanup.

## Stage 26.1C executor evidence

Exact physically accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted: authenticated loopback agent, legacy exec absent/disabled, typed actions, stale frame/context refusal, focus/fingerprint binding, bounded keyboard/pointer/scroll, layout-independent Unicode typing, zero false/unrelated-window actions.

## Stage 26.1D / 26.1E performance evidence

Baseline:

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Window-scoped resolver:

```text
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
p50 speedup=55.244x
p95 speedup=49.883x
```

The 97/97 result is controlled fixture evidence for the exercised role+name path, not global Windows accuracy.

## Candidate selection rule for future capabilities

```text
actual task + consequence class
 -> deterministic/native/API/MCP/qualified-upstream candidates
 -> prefer mature maintained upstream
 -> reduce/scope authority
 -> target-machine benchmark
 -> negative/security tests
 -> focused project adapter only for a measured gap
 -> public-contract review only if exported
```

Do not promote a backend merely because it appeared in an older plan.

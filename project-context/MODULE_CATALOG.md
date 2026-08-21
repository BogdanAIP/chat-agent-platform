# Module / Capability Catalog

Status synchronized through accepted Stage 26.2D Windows vision routing and active Stage 26.2E real-application qualification. Resolve live `main` and relevant PR heads before work.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

## Status meanings

- **PRODUCT-ACCEPTED** — accepted normal product/ordinary-Chat path for the scoped contract.
- **ACCEPTED-INFRASTRUCTURE** — accepted maintained internal runtime/lifecycle foundation.
- **ACCEPTED-SPECIALIST** — bounded specialist backend accepted behind a focused boundary.
- **TARGET-QUALIFIED** — exact component/path physically passed target qualification but is not yet promoted into the normal maintained product path.
- **ADAPT-CANDIDATE** — reusable upstream mechanism that still needs project integration/policy wrapping.
- **DIAGNOSTIC** — internal testing/lifecycle infrastructure only.
- **ACTIVE-INTEGRATION** — current product-integration work.
- **FUTURE-SCOPED-GATE** — future capability needing explicit evidence.
- **OPTIONAL-RESEARCH** — only if later data/measurements justify it; not release-critical.
- **PARALLEL-TRACK** — separate layer not on the core release path.

## Current catalog

| Capability class | Current implementation/direction | Status | Decision |
|---|---|---|---|
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | PRODUCT-ACCEPTED | Normal ordinary-Chat reachability. |
| Public semantic transport | direct stdio secure semantic launcher -> semantic-projection | PRODUCT-ACCEPTED | Normal public path. |
| Internal MCP aggregation/lifecycle | 1MCP | ACCEPTED-INFRASTRUCTURE / DIAGNOSTIC | Internal diagnostics/adaptive lifecycle; not normal public semantic hop. |
| Windows manager ownership | authoritative runtime owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | Ambiguous/foreign ownership fails closed. |
| Scoped files | official Filesystem backend behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`. |
| Browser | pinned Playwright path behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`. |
| Semantic capability projection | deterministic five-tool compatibility boundary | PRODUCT-ACCEPTED | Small truthful surface; not planner/gateway/workflow engine. |
| Local visual grounding | llama.cpp + LFM2.5-VL-450M F16 | ACCEPTED-SPECIALIST | Local/on-demand/perception-only; replaceable. |
| Browser semantic->vision routing | Stage 25.2 internal escalation | PRODUCT-ACCEPTED | Semantic first; reviewed bounded visual path only. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | TARGET-QUALIFIED | ADOPT behind project policy boundaries. |
| Procedural lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression internals | ADAPT-CANDIDATE | Reuse mechanics; project trust stays candidate-first. |
| Human/desktop capture | OpenAdapt Capture 1.2.2 + Flow adapter | TARGET-QUALIFIED | Stage 26.1B physically accepted; procedure integration remains later. |
| Typed Windows executor | pinned OpenAdapt `WindowsBackend` + hardened agent + production wrapper | ACCEPTED-INFRASTRUCTURE | Stage 26.1C accepted and Stage 26.2A promoted into maintained runtime; no generic exec. |
| Window-scoped Windows UI resolution | PID -> Win32 HWND -> exact window -> bounded native UIA FindAll | ACCEPTED-INFRASTRUCTURE | Stage 26.1E accepted and promoted by Stage 26.2A. |
| Runtime verifier foundation | before/after evidence + `PASS|FAIL|UNKNOWN` | ACCEPTED-INFRASTRUCTURE | Delivery is not success; UNKNOWN does not silently advance. |
| Production Windows runtime | `runtime/windows` bounded observation/actuation/verification foundation | ACCEPTED-INFRASTRUCTURE | Stage 26.2A merged #87. |
| Desktop observation | canonical read-only `DesktopState` | ACCEPTED-INFRASTRUCTURE | Stage 26.2B merged #88; evidence only, never authority. |
| Desktop F16 Grounder | native exact-window pixel-space proposal adapter | ACCEPTED-SPECIALIST | Stage 26.2C merged #89; proposal-only, frame-bound, no action authority. |
| Windows UIA->vision router | deterministic structure first + bounded visual fallback + fresh/native guards | ACCEPTED-INFRASTRUCTURE | Stage 26.2D physically accepted and merged #90. |
| Native visual point guard | foreground HWND + WindowFromPoint/root HWND/PID | ACCEPTED-INFRASTRUCTURE | Stage 26.2D accepted; no focus stealing. |
| Real application Windows E2E | isolated VS Code + disposable TEMP artifact | ACTIVE-INTEGRATION | Stage 26.2E current gate; one guarded keyboard mutation, independent file verifier, rollback. |
| Verified Procedure Runtime | ProgramGraph + live state + authorization + verifier | FUTURE-SCOPED-GATE | Only after real desktop E2E. |
| Human demonstration transfer | Capture -> candidate procedure -> changed-state verified replay | FUTURE-SCOPED-GATE | Not blind macro replay. |
| Procedure-state dataset | structured verified state-transition examples | OPTIONAL-RESEARCH | Not a Stage 27/28 prerequisite. |
| Specialized local reasoning | generic `SpecializedReasoningBackend` | OPTIONAL-RESEARCH | Only if real data and measured escalation/latency need justify it. |
| Multi-chat orchestration | upper-layer controller over ordinary Chat sessions | PARALLEL-TRACK | Keep outside Windows/procedure safety core; no Codex/Work under current constraint. |
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

A separate ADR later decides whether a few truthful coarse desktop/procedure capabilities are required. Never hide native desktop actions behind `web_interact` and never add a generic opaque `tool_invoke` equivalent.

## Accepted Windows evidence

### Stage 26.1B Capture

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Interactive-session capture, bounded selected-window evidence, raw UIA retention, Flow compile, zero foreign structural-window evidence and explicit refusal of unaccepted replay were accepted.

### Stage 26.1C executor

Physical head `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`: authenticated loopback, legacy exec absent/disabled, typed actions, stale frame/context refusal, focus/fingerprint binding, bounded keyboard/pointer/scroll, layout-independent Unicode typing, zero false/unrelated-window actions.

### Stage 26.1D / 26.1E performance

```text
baseline p50 = 183606.855 ms
baseline p95 = 185567.403 ms
window-scoped p50 = 3323.570 ms
window-scoped p95 = 3720.061 ms
97 scoped resolutions
0 Desktop fallback
0 binding failures/ambiguities
0 false/unrelated-window actions
```

The 97/97 result is controlled WinForms evidence, not global Windows accuracy.

### Stage 26.2A production runtime

```text
physical head = 6ae5c3a9e624c8c341857c025625b203b796b41c
production p50 = 3410.031 ms
production p95 = 3630.583 ms
```

### Stage 26.2B DesktopState

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Read-only behavior is established by code/source-boundary tests; historical constant action counters from the first qualification are not treated as measurements.

### Stage 26.2C Desktop Grounder

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical evidence established the observed `1. Benchmark start` -> `Benchmark start` behavior and one valid proposal inside independent UIA bounds. Synthetic tests separately define ambiguity/fuzzy-matching refusal; those are policy tests, not physical observations.

### Stage 26.2D Windows routing

Exact physically accepted PR head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Merged as #90; integration main became:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Physical result directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

```text
NATIVE_POINT_GUARD_PREFLIGHT_PASS=True
NATIVE_POINT_GUARD_WRONG_WINDOW_REFUSAL_PASS=True
NATIVE_POINT_GUARD_DELIVERY_PASS=True
VISION_DISABLED_ABSTAIN_PASS=True
ROLE_CONFLICT_ABSTAIN_PASS=True
NEGATIVE_ZERO_ACTION_PASS=True
POSITIVE_ROUTE_STATUS=delivered
POSITIVE_ROUTE_REASON=vision-zero-exact-delivered
POSITIVE_CONSISTENCY_IOU=0.34455881673798816
FRESH_REOBSERVATION_PASS=True
GUARDED_CLICK_RECEIPT_PASS=True
SINGLE_ACTION_PASS=True
STRUCTURAL_EXECUTOR_CALLS=0
COORDINATE_EXECUTOR_CALLS=1
GROUNDER_CALLS=1
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
PASS=True
```

This is one controlled WinForms routing success, not global application accuracy.

## Active Stage 26.2E evidence model

The real-app gate intentionally avoids invented `false_action_count=0` constants. Its measurable authority/completion evidence is:

```text
one unique Code.exe PID/HWND/window
enabled+visible focused editor evidence
native foreground/hit-test guard
wrong verifier expectation -> FAIL -> ABSTAIN before action
exactly one guarded keyboard delivery
exact saved-file size + SHA-256 postcondition
workspace contains only expected artifact
same current window identity
exact qualification window cleanup
specifically prefixed TEMP root cleanup
rollback PASS
```

VS Code is a qualification application candidate, not a permanent architectural dependency.

## Merge rule

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command. Stop instead on unresolved findings, conflicts, ambiguous scope or failed/skipped required evidence.

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
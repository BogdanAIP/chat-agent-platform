# Module / Capability Catalog

Status synchronized through accepted Stage 26.2C Desktop Grounder work. Resolve live `main` and relevant PR heads before work.

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
| Browser semantic->vision routing | Stage 25.2 internal escalation | PRODUCT-ACCEPTED | Semantic first; reviewed zero-exact-candidate visual path only. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | TARGET-QUALIFIED | ADOPT behind project policy boundaries. |
| Procedural lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression internals | ADAPT-CANDIDATE | Reuse mechanics; project trust stays candidate-first. |
| Human/desktop capture | OpenAdapt Capture 1.2.2 + Flow adapter | TARGET-QUALIFIED | Stage 26.1B physically accepted; procedure integration remains later. |
| Typed Windows executor | pinned OpenAdapt `WindowsBackend` + hardened agent + production wrapper | ACCEPTED-INFRASTRUCTURE | Stage 26.1C accepted and Stage 26.2A promoted into maintained runtime; no generic exec. |
| Window-scoped Windows UI resolution | PID -> Win32 HWND -> exact window -> bounded native UIA FindAll | ACCEPTED-INFRASTRUCTURE | Stage 26.1E accepted and promoted by Stage 26.2A. |
| Runtime verifier foundation | before/after evidence + `PASS|FAIL|UNKNOWN` | ACCEPTED-INFRASTRUCTURE | Delivery is not success; UNKNOWN does not silently advance. |
| Production Windows runtime | `runtime/windows` bounded observation/actuation/verification foundation | ACCEPTED-INFRASTRUCTURE | Stage 26.2A merged #87. |
| Desktop observation | canonical read-only `DesktopState` | ACCEPTED-INFRASTRUCTURE | Stage 26.2B accepted; introduced by #88 with exact physical runtime evidence. |
| Desktop F16 Grounder | native exact-window pixel-space proposal adapter | ACCEPTED-SPECIALIST | Stage 26.2C physically accepted on controlled WinForms target; proposal-only, frame-bound, no action authority. |
| Windows UIA->vision router | deterministic structure first, bounded visual fallback | ACTIVE-INTEGRATION | Stage 26.2D next; must pass freshness/authorization and adversarial accuracy gates before promotion. |
| Real application Windows E2E | one medium-complexity user app + disposable artifact | FUTURE-SCOPED-GATE | Select from real task/evidence; deterministic postcondition and rollback. |
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

After a real Windows desktop surface exists, a separate ADR decides whether a few truthful coarse desktop/procedure capabilities are required. Never hide native desktop actions behind `web_interact` and never add a generic opaque `tool_invoke` equivalent.

## Accepted Windows evidence

### Stage 26.1B Capture

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Interactive-session capture, bounded selected-window evidence, raw UIA retention, Flow compile, zero foreign structural-window evidence, explicit refusal of unaccepted replay and clean local artifact handling were accepted.

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

The 97/97 result is controlled WinForms role+name evidence, not global Windows accuracy.

### Stage 26.2A production runtime

```text
physical head = 6ae5c3a9e624c8c341857c025625b203b796b41c
production p50 = 3410.031 ms
production p95 = 3630.583 ms
```

Production-owned runtime preserved the accepted safety/performance behavior.

### Stage 26.2B DesktopState

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

```text
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
WINDOW_ENUM_CALLS=2
WINDOW_NAME_MATCH_COUNT=2
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CHROME_PROCESS_COUNT_BEFORE=11
CHROME_PROCESS_COUNT_AFTER=11
CHROME_SURVIVAL_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

This proves bounded DesktopState observation on the controlled WinForms fixture. It does not prove cross-application UIA coverage or desktop VLM accuracy.

The initial qualification also printed `ACTION_COUNT=0` and related values that were constants rather than instrumented measurements. Self-review removed them from acceptance evidence and from future harness output. Read-only behavior is instead established by direct code review and CI source-boundary tests proving no executor/actuation channel exists in the observer/driver path.

### Stage 26.2C Desktop Grounder

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json`

```text
POSITIVE_GROUNDER_STATUS=proposal
POSITIVE_GROUNDER_REASON=grounder-accepted-ordinal-alias-proposal-only
POSITIVE_INVENTORY_LABELS_JSON=["Benchmark start","Guarded list click + scroll"]
POSITIVE_PASS2_DETECTION_COUNT=1
TARGET_POINT_INSIDE_UIA_PASS=True
SAME_FRAME_BINDING_PASS=True
COORDINATE_CONTRACT_PASS=True
TARGET_EVIDENCE_BINDING_PASS=True
ABSENT_TARGET_ABSTAIN_PASS=True
STALE_FRAME_REJECTION_PASS=True
PROPOSAL_ONLY_CONTRACT_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
VISION_RESTORED_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

Physical evidence establishes only the observed target behavior: the rendered fixture label was `1. Benchmark start`, while the VLM inventory read the intended button as `Benchmark start`, and the bounded ordinal-prefix policy recovered a unique proposal whose point fell inside independent UIA bounds. Synthetic unit tests separately define policy boundaries such as ambiguity -> ABSTAIN and no broad fuzzy matching; those synthetic cases are not physical observations.

This remains controlled WinForms evidence, not general desktop accuracy. Stage 26.2D must add deterministic structure-first routing, fresh same-window/same-frame authorization and adversarial coverage before any coordinate action path is promoted.

## Merge rule

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable review/acceptance checks should be merged without waiting for a separate merge command. Stop instead on unresolved findings, conflicts, ambiguous scope, failed/skipped required tests or unavailable required review evidence.

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
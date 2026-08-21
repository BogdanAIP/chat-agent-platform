# Module / Capability Catalog

Status synchronized through accepted Stage 26.2D Windows routing and active Stage 26.2E real-application qualification.

Resolve live `main` and relevant PR heads before work.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

## Status meanings

- **PRODUCT-ACCEPTED** — normal product/ordinary-Chat path for the scoped contract.
- **ACCEPTED-INFRASTRUCTURE** — maintained internal runtime/lifecycle foundation.
- **ACCEPTED-SPECIALIST** — bounded specialist backend behind a focused boundary.
- **TARGET-QUALIFIED** — exact component/path physically passed target qualification but is not yet in normal product execution.
- **ADAPT-CANDIDATE** — reusable upstream mechanism needing project integration/policy wrapping.
- **ACTIVE-INTEGRATION** — current product-integration work.
- **FUTURE-SCOPED-GATE** — planned capability requiring explicit evidence.
- **OPTIONAL-RESEARCH** — only if later measurements justify it; not release-critical.
- **PARALLEL-TRACK** — separate layer not on the core release path.
- **DIAGNOSTIC** — internal test/lifecycle infrastructure.

## Current catalog

| Capability class | Current implementation/direction | Status | Decision |
|---|---|---|---|
| General planner / manager | ordinary ChatGPT | PRODUCT-ACCEPTED | Only current open-ended task/strategy/planning layer. |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | PRODUCT-ACCEPTED | Normal ordinary-Chat reachability. |
| Public semantic transport | direct stdio secure launcher -> semantic-projection | PRODUCT-ACCEPTED | Truthful deterministic compatibility path. |
| Internal MCP aggregation/lifecycle | 1MCP | ACCEPTED-INFRASTRUCTURE / DIAGNOSTIC | Internal diagnostics/adaptive lifecycle; not normal public semantic hop. |
| Windows manager ownership | authoritative runtime owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | Lifecycle/config/diagnostics only; not procedure Control Plane. |
| Scoped files | official Filesystem backend behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`. |
| Browser | pinned Playwright path behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`. |
| Semantic capability projection | deterministic five-tool compatibility boundary | PRODUCT-ACCEPTED | Not planner, workflow engine or procedure Control Plane. |
| Local visual grounding | llama.cpp + LFM2.5-VL-450M F16 | ACCEPTED-SPECIALIST | Local/on-demand/perception-only; replaceable. |
| Browser semantic -> vision routing | Stage 25.2 internal escalation | PRODUCT-ACCEPTED | Semantic first; bounded visual fallback only. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | TARGET-QUALIFIED | ADOPT behind project boundaries. |
| Procedural lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression mechanics | ADAPT-CANDIDATE | Reuse mechanics; project trust stays candidate-first. |
| Human/desktop capture | OpenAdapt Capture 1.2.2 + Flow adapter | TARGET-QUALIFIED | Stage 26.1B physically accepted; transfer integration remains later. |
| Typed Windows executor | pinned OpenAdapt `WindowsBackend` + hardened agent + production wrapper | ACCEPTED-INFRASTRUCTURE | No generic exec; bounded typed actions. |
| Window-scoped Windows UI resolution | PID -> Win32 HWND -> exact window -> bounded native UIA | ACCEPTED-INFRASTRUCTURE | Stage 26.1E accepted and promoted. |
| Runtime verifier foundation | before/after evidence + `PASS|FAIL|UNKNOWN` | ACCEPTED-INFRASTRUCTURE | Delivery is not success; UNKNOWN never silently advances. |
| Production Windows runtime | `runtime/windows` bounded observation/actuation/verification | ACCEPTED-INFRASTRUCTURE | Stage 26.2A merged #87. |
| Desktop observation | canonical read-only `DesktopState` | ACCEPTED-INFRASTRUCTURE | Stage 26.2B merged #88; evidence only. |
| Desktop F16 Grounder | native exact-window proposal adapter | ACCEPTED-SPECIALIST | Stage 26.2C merged #89; proposal-only. |
| Windows UIA -> vision router | deterministic structure first + bounded visual fallback + freshness/native guards | ACCEPTED-INFRASTRUCTURE | Stage 26.2D physically accepted/merged #90. |
| Native visual point guard | foreground HWND + WindowFromPoint/root HWND/PID | ACCEPTED-INFRASTRUCTURE | Stage 26.2D accepted; no focus stealing. |
| Real application Windows E2E | isolated VS Code + disposable TEMP artifact | ACTIVE-INTEGRATION | Stage 26.2E gate. |
| Deterministic execution Control Plane | TaskState + ProgramGraph progression + policy/authorization + checkpoint/verifier/recovery/budgets | FUTURE-SCOPED-GATE / AUTHORITATIVE DIRECTION | Implement in Stage 26.3 after real-app E2E; not a general planner. |
| Verified Procedure Runtime | selected ProgramGraph + live state + deterministic Control Plane | FUTURE-SCOPED-GATE | May advance known verified transitions locally; escalates novel strategy to ChatGPT. |
| Human demonstration transfer | Capture -> candidate procedure -> changed-state verified replay | FUTURE-SCOPED-GATE | Stage 26.4; not blind macro replay. |
| Procedure-state dataset | structured verified state-transition examples | OPTIONAL-RESEARCH | Supports later evaluation/training; not a release prerequisite. |
| Specialized local reasoning | `SpecializedReasoningBackend` proposal-only | OPTIONAL-RESEARCH | Structured specialist decisions only; not a general planner. |
| Future local general planner | Track P: shadow -> bounded subtask -> optional local mode | OPTIONAL-RESEARCH / FUTURE | After verified data + measured offline/latency/parallel/deployment need; always behind deterministic Control Plane. |
| Multi-chat orchestration | upper-layer controller over ordinary Chat sessions | PARALLEL-TRACK | Outside Windows/procedure safety core. |
| Distribution/cockpit reference | OpenAdapt Desktop packaging/Tauri/sidecar patterns | ADAPT-CANDIDATE | Stage 27 reference; verify runtime compatibility. |
| Distribution/maintenance | installer/update/repair/doctor/uninstall/rollback/restart recovery | FUTURE-SCOPED-GATE | Stage 27. |

## Planner / Control Plane terminology

Do not use `Control Plane` as a synonym for `planner`.

```text
general planner
 = open-ended goal/strategy/adaptation
 = ordinary ChatGPT today

local deterministic Control Plane
 = execution state/policy/procedure/verifier/recovery
 = Stage 26.3 direction

future local planner
 = optional Track P research
 = not current product path
```

## Current public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

A later ADR decides truthful desktop/procedure capabilities. Never hide native desktop actions behind `web_interact` and never add generic opaque `tool_invoke` merely to preserve a small count.

## Accepted Windows evidence lineage

### 26.1B Capture

Physical head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

### 26.1C executor

Physical head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

Authenticated loopback, legacy exec absent/disabled, typed actions, stale frame/context refusal, focus/fingerprint binding and bounded input were accepted.

### 26.1D / 26.1E

Desktop-wide p50/p95 ~183.6/185.6 s was reduced by exact-window UIA to 3.324/3.720 s, with 97 controlled scoped resolutions and zero Desktop fallback/binding failures/ambiguities/false/unrelated-window actions.

### 26.2A

Physical production runtime head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

### 26.2B

Exact physically tested DesktopState runtime head: `dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`.

Historical constant action counters from the first observer qualification are not accepted measurements; read-only behavior is established by code/source-boundary tests.

### 26.2C

Exact physically accepted Grounder head: `eadf8ff5a873936441891a66b616c83c62736152`.

The physical `1. Benchmark start` -> `Benchmark start` case supports one narrow ordinal-prefix policy, not broad fuzzy matching.

### 26.2D

Exact physically accepted PR head: `1c74713edcd6321d5583a39234929169e68b5ac1`.

Merged #90 integration main: `42d4130d59e23e2c2b1771ac428467efe27a4b98`.

Physical evidence proves one bounded structure-first Windows visual fallback and negative refusal cases, not global application accuracy.

## Active 26.2E evidence model

Do not fabricate `false_action_count=0` constants. Current measurable contract is:

```text
specific TEMP containment
unique Code.exe PID/HWND/DesktopState
focused editor evidence
wrong verifier expectation -> FAIL -> ABSTAIN before action
fresh pre-action same-window + same-focused-editor fingerprint
native foreground/hit-test guard
exactly one guarded keyboard delivery
exact saved-file size + SHA-256
expected-only workspace
same current window identity
exact qualification window close
natural CLI exit
TEMP cleanup / rollback PASS
```

Forced CLI termination is cleanup-only and must make acceptance fail.

## Future planner acceptance rule

Do not promote a local planner because a model exists. Track P requires verified procedure-state data, a measured need and comparative evaluation against ordinary ChatGPT manager behavior. First mode is shadow/proposal-only. Capability authorization and verifier remain independent regardless of planner source.

## Merge rule

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command. Stop on unresolved finding, conflicts, ambiguous scope or failed/skipped evidence.

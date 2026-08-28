# Module / Capability Catalog

Status: **CURRENT CAPABILITY CATALOG**.

This is a concise inventory/reference. It does not own release order (`ROADMAP.md`), live accepted state (`CURRENT_STATE.md`), exact evidence (`EVIDENCE_INDEX.md`) or prior reuse lineage (`ARCHITECTURE_REUSE_BASELINE.md`). Resolve live repository state before acting.

## Operating boundary

Ordinary ChatGPT is the only current general planner. The project may use Codex Review/equivalent independent review as an assurance layer under `AGENTS.md`; that is distinct from using Codex/Work as an alternate runtime planner or default implementation workspace.

## Status meanings

- **PRODUCT-ACCEPTED** — accepted normal product path for recorded scope.
- **ACCEPTED-INFRASTRUCTURE** — maintained internal runtime/lifecycle foundation.
- **ACCEPTED-SPECIALIST** — bounded specialist backend behind project authority.
- **ACCEPTED-L1** — accepted state/contract foundation not yet sufficient for every production consequence path.
- **TARGET-QUALIFIED** — exact component/path qualified but not promoted to general production use.
- **ACTIVE-INTEGRATION** — current production-integration work; details live in `CURRENT_STATE.md`.
- **FUTURE-SCOPED-GATE** — future capability requiring explicit research/acceptance.
- **PARALLEL-TRACK** — future layer not on current release-critical path.
- **OPTIONAL-RESEARCH** — only if later evidence justifies it.

## Current catalog

| Capability / role | Current implementation/direction | Status | Boundary |
|---|---|---|---|
| General planner / manager | ordinary ChatGPT | **PRODUCT-ACCEPTED** | Only current open-ended goal/strategy/planning layer. |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | **PRODUCT-ACCEPTED** | Normal ordinary-Chat reachability. |
| Transport supervision | Transport Supervisor v1 | **ACCEPTED-INFRASTRUCTURE** | Desired-state/runtime ownership and bounded recovery; not planner/Control Plane. |
| Public semantic transport | direct stdio launcher -> canonical six-tool projection | **PRODUCT-ACCEPTED** | Normal semantic route. |
| Internal MCP aggregation/lifecycle | optional 1MCP Extension Manager | **ACCEPTED-INFRASTRUCTURE / OPTIONAL** | Discovery/lifecycle only; not baseline transport/trust/authorization. |
| Scoped Files | project semantic Files capability | **PRODUCT-ACCEPTED** | `workspace_read` / `workspace_write`. |
| Browser semantic execution | pinned Playwright path behind project Browser capability | **PRODUCT-ACCEPTED** | `web_open` / `web_observe` / `web_interact`; accepted representative backend is isolated/headless. |
| Browser semantic -> local vision routing | bounded structure-first escalation | **PRODUCT-ACCEPTED** | visual evidence only when structural route is insufficient. |
| Local visual specialist | llama.cpp + LFM2.5-VL family | **ACCEPTED-SPECIALIST** | local proposal/evidence only; never authorization/planner. |
| Windows typed executor/runtime | bounded project Windows runtime | **ACCEPTED-INFRASTRUCTURE** | generic exec absent; scoped typed actions only. |
| Windows observation | `DesktopState` + exact PID/HWND/native evidence | **ACCEPTED-INFRASTRUCTURE** | evidence, not authority. |
| Windows native/visual grounding | structure-first UIA/native + bounded F16/vision fallback | **ACCEPTED-INFRASTRUCTURE / SPECIALIST** | proposals remain target/freshness/identity guarded. |
| Representative Windows application E2E | isolated accepted application tasks | **PRODUCT-ACCEPTED scoped** | vertical evidence only; not broad app accuracy. |
| Deterministic execution Control Plane | project-owned authorization/state/verification/recovery/finish boundary | **PRODUCT-ACCEPTED foundation** | not a second planner. |
| Registered Verified Procedure Runtime | bounded registered procedures via `procedure_run` | **PRODUCT-ACCEPTED scoped** | no generic shell/Python/backend selector. |
| Verification Kernel | `ObservationRef`/fresh same-stream evidence + `ExpectedEffect` -> `PASS/FAIL/UNKNOWN` | **ACCEPTED-INFRASTRUCTURE** | Stage 26.3B accepted for recorded representative scope. |
| Independent Finish Gate | fresh goal/safety/constraint evidence -> `DONE/NOT_DONE/UNKNOWN` | **ACCEPTED-INFRASTRUCTURE** | planner/procedure self-report is not completion. |
| WorkingState v1 | capability-spanning structured operational state | **ACCEPTED-L1 / ACTIVE-INTEGRATION** | L1 foundation merged #124; production consequence-path integration continues in 26.3C. |
| Typed recovery/reconciliation | stable operation identity + fresh reconciliation + fail-closed ambiguous outcomes | **ACCEPTED-L1 / ACTIVE-INTEGRATION** | L1 foundation accepted; production restart behavior still requires path-specific proof. |
| LoopGuard / budgets / StagnationReport | repeat/no-effect/oscillation guard + task/procedure/strategy budgets | **ACCEPTED-L1 / ACTIVE-INTEGRATION** | diagnostic/escalation only; no planner/authority expansion. |
| Procedure compiler / workflow IR | OpenAdapt Flow `Workflow` / `ProgramGraph` | **TARGET-QUALIFIED** | selected upstream role; production consumer must be revalidated through Stage Research. |
| Procedure-local checkpoint/resume | OpenAdapt Flow where exact semantics fit | **TARGET-QUALIFIED / REVALIDATE** | below project WorkingState/recovery authority. |
| Procedure/effect evidence | OpenAdapt effect-verifier mechanics through project adapter | **TARGET-QUALIFIED / REVALIDATE** | upstream verdict is evidence, never unconditional project PASS/DONE. |
| Human desktop demonstration capture | OpenAdapt Capture + Flow adapter | **TARGET-QUALIFIED** | privacy/trust/promotion remain future gates. |
| Human demonstration -> candidate skill | live-state re-resolved candidate lineage | **FUTURE-SCOPED-GATE** | Stage 26.4; no blind macro replay. |
| Selective Office/Windows native adapters | UFO/UFO²-derived UIA, Win32, WinCOM and app mechanics | **FUTURE-SCOPED-GATE / SELECTIVE REUSE** | focused adapters only; no UFO planner hierarchy/Galaxy authority. |
| Hybrid cross-capability computer use | common observation/recovery/routing semantics | **FUTURE-SCOPED-GATE** | Stage 26.5; do not flatten rich native state prematurely. |
| Site Capability / broader Browser authority | restricted-by-default -> explicitly scoped trusted-site profiles | **FUTURE-SCOPED-GATE** | requires network/security/public-contract/physical acceptance. |
| Local Execution Kernel | task-scoped Python/program grant | **FUTURE-SCOPED-GATE** | separate consequence class; not hidden Browser/procedure authority. |
| Agent Sessions / Delegation | HarnessSession/Conversation/DelegationTask/MessageDelivery/ExecutionEnvironment | **PARALLEL-TRACK** | ADR-035; no current public/runtime authority. |
| Conversation Bridge / Browser Companion | cross-provider authenticated web-chat adapter family | **PARALLEL-TRACK** | one Agent Session adapter route; provider UI never core authority. |
| CapabilityRegistry / TypedEventBus / PolicyHooks | descriptive discovery + typed trigger/policy substrate | **FUTURE-SCOPED-GATE** | ADR-037; discovery/event != authorization/effect proof. |
| Specialized local reasoning | proposal-only specialist | **OPTIONAL-RESEARCH** | not release prerequisite or general planner. |
| Future local general planner | Track P shadow -> bounded subtask -> optional local mode | **OPTIONAL-RESEARCH** | always behind deterministic authorization/verifier/Finish Gate. |
| Distribution/maintenance | installer/update/repair/uninstall/rollback | **FUTURE-SCOPED-GATE** | Stage 27. |

## Accepted public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no accepted five/six runtime mode. Historical five-tool projection is private regression/implementation history.

Six is not an eternal maximum. Any new public consequence class must use a truthful schema/security/ordinary-Chat acceptance decision rather than being hidden behind generic dispatch.

## Current planner / Control Plane terminology

```text
general planner
 = open-ended goal/strategy/adaptation
 = ordinary ChatGPT today

local deterministic Control Plane
 = execution state/policy/authorization/verification/reconciliation/recovery/finish
 = accepted project-owned boundary

future local planner
 = optional Track P research
 = not current product path
```

Do not use `Control Plane` as a synonym for planner, agent host or unrestricted orchestrator.

## Current Stage 26.3 status

```text
26.3A six-tool Verified Procedure Runtime               ACCEPTED
26.3B Verification Kernel + independent Finish Gate     ACCEPTED / CLOSED FOR RECORDED SCOPE
26.3C WorkingState/LoopGuard L1 foundation              ACCEPTED / MERGED #124
26.3C consequence-bearing production/restart use        ACTIVE-INTEGRATION / NOT YET ACCEPTED
```

Live integration PR/design/check state belongs in `CURRENT_STATE.md`.

## Reuse / architecture lineage

This catalog says **what role exists**. It does not replace `ARCHITECTURE_REUSE_BASELINE.md`, which records the prior selected source/project-owned owner and must be used by applicable Stage Research.

When a current task touches a baseline role, do not silently:

- write custom code that duplicates selected upstream mechanics;
- replace a prior component because a newer option exists;
- delegate a project-owned authority boundary to an external component.

Use the baseline + fresh evidence to decide `KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT`.

## Future-track detail owners

- Agent Sessions / Delegation: `CONVERSATION_BRIDGE_ARCHITECTURE.md` / ADR-035.
- Browser Harness-derived broader authority: `BROWSER_HARNESS_ARCHITECTURE.md` / ADR-036.
- Capability Registry / Event / Policy hooks: `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` / ADR-037.
- external OpenAdapt/UFO detail: `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`.
- release order: `ROADMAP.md`.

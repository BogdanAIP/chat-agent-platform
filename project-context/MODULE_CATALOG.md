# Module / Capability Catalog

Status synchronized through accepted Stage 26.3A / PR #92, the promoted computer-use architecture direction, and provisional ADR-035 / Track M Conversation Bridge direction.

Resolve live `main` and relevant PR heads before work.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.

## Status meanings

- **PRODUCT-ACCEPTED** — normal product/ordinary-Chat path for the scoped accepted contract.
- **ACCEPTED-INFRASTRUCTURE** — maintained internal runtime/lifecycle foundation.
- **ACCEPTED-SPECIALIST** — bounded specialist backend behind a focused boundary.
- **TARGET-QUALIFIED** — exact component/path physically passed target qualification but is not yet in normal accepted product execution.
- **ACTIVE-INTEGRATION** — current product-integration work.
- **FUTURE-SCOPED-GATE** — planned capability requiring explicit evidence.
- **OPTIONAL-RESEARCH** — only if later measurements justify it; not release-critical.
- **PARALLEL-TRACK** — separate layer not on the core release path.
- **DIAGNOSTIC** — internal test/lifecycle infrastructure.

## Current catalog

| Capability class | Current implementation/direction | Status | Decision |
|---|---|---|---|
| General planner / manager | ordinary ChatGPT | PRODUCT-ACCEPTED | Only current open-ended goal/strategy/planning layer. |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | PRODUCT-ACCEPTED | Normal ordinary-Chat reachability. |
| Transport supervision | Transport Supervisor v1 | PRODUCT-ACCEPTED / ACCEPTED-INFRASTRUCTURE | Persistent desired state/runtime owner, bounded recovery, console-free Windows persistence. |
| Public semantic transport | direct stdio launcher -> canonical six-tool semantic projection | PRODUCT-ACCEPTED | Stage 26.3A physically accepted/merged. |
| Internal MCP aggregation/lifecycle | optional 1MCP Extension Manager | ACCEPTED-INFRASTRUCTURE / DIAGNOSTIC | Optional extension discovery/lifecycle; not baseline route, trust or authorization. |
| Windows manager ownership | authoritative runtime owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | Lifecycle/config/diagnostics only; not planner or procedure Control Plane. |
| Scoped files | official Filesystem backend behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`. |
| Browser | pinned Playwright path behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`; current accepted backend is isolated/headless. |
| Semantic capability projection | exact six-tool canonical boundary | PRODUCT-ACCEPTED | Five file/browser semantics + bounded typed `procedure_run`; no 5/6 mode. |
| Deterministic execution Control Plane | TaskState + registered procedures + authorization/checkpoints/verifier/budgets | PRODUCT-ACCEPTED first slice / ACTIVE-INTEGRATION broader contracts | Stage 26.3A proves first slice; 26.3B/C broaden verification/state/recovery. |
| Verified Procedure Runtime | `verified_workspace_artifact_v1` | PRODUCT-ACCEPTED scoped | Three verified transitions, durable checkpoints, fail-closed ABSTAIN/no-overwrite. |
| Verification Kernel | ExpectedEffect + fresh re-observation + `PASS|FAIL|UNKNOWN` + cross-capability predicates | ACTIVE-INTEGRATION | Stage 26.3B; transition delivery/result separation becomes reusable contract. |
| Independent Finish Gate | `candidate_done` -> fresh goal-level predicates -> `DONE` | ACTIVE-INTEGRATION | Stage 26.3B; planner self-assessment is not task completion. |
| WorkingState v1 | constraints/subgoals/facts+provenance+freshness/progress/evidence/recovery/budgets | FUTURE-SCOPED-GATE / NEXT-AFTER-26.3B | Stage 26.3C; structured operational state, never private chain-of-thought. |
| Typed recovery + LoopGuard | failure taxonomy, no-effect/repeat/oscillation detection, bounded escalation | FUTURE-SCOPED-GATE / NEXT-AFTER-26.3B | Stage 26.3C; no blind infinite retry. |
| Local visual grounding | llama.cpp + LFM2.5-VL-450M F16 | ACCEPTED-SPECIALIST | Local/on-demand/perception-only; replaceable. |
| Browser semantic -> vision routing | Stage 25.2 bounded internal escalation | PRODUCT-ACCEPTED | Semantic/AX first; bounded visual fallback only. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | TARGET-QUALIFIED | Candidate IR/mechanics behind project boundaries. |
| Procedural lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression mechanics | FUTURE-SCOPED-GATE | Reuse lifecycle mechanics only after project trust/verification integration. |
| Human/desktop capture | OpenAdapt Capture 1.2.2 + Flow adapter | TARGET-QUALIFIED | Capture foundation accepted; demo transfer Stage 26.4. |
| Human demonstration transfer | demo -> subtask goals/verifiers -> CANDIDATE -> live-state verified replay | FUTURE-SCOPED-GATE | Stage 26.4; not blind macro replay. |
| Typed Windows executor | hardened Windows backend/agent + production wrapper | ACCEPTED-INFRASTRUCTURE | No generic exec; bounded typed actions. |
| Window-scoped Windows UI resolution | PID -> HWND -> exact window -> bounded native UIA | ACCEPTED-INFRASTRUCTURE | Stage 26.1E accepted/promoted. |
| Production Windows runtime | `runtime/windows` bounded observation/actuation/verification | ACCEPTED-INFRASTRUCTURE | Stage 26.2A accepted/merged. |
| Desktop observation | canonical read-only `DesktopState` | ACCEPTED-INFRASTRUCTURE | Capability-native evidence, not authority. |
| Desktop F16 Grounder | native exact-window proposal adapter | ACCEPTED-SPECIALIST | Proposal-only. |
| Windows UIA -> vision router | deterministic structure first + bounded visual fallback + freshness/native guards | ACCEPTED-INFRASTRUCTURE | Stage 26.2D physically accepted scoped path. |
| Native visual point guard | foreground HWND + WindowFromPoint/root HWND/PID | ACCEPTED-INFRASTRUCTURE | Prevents unbound coordinate consequence. |
| Real application Windows E2E | isolated VS Code + disposable TEMP artifact | PRODUCT-ACCEPTED scoped foundation | Stage 26.2E accepted one task; not broad app accuracy. |
| ObservationEnvelope | small reference envelope over capability-native Browser/Windows/file/app state | FUTURE-SCOPED-GATE | Stage 26.5 target; do not flatten rich native state prematurely. |
| Capability-aware router | reviewed semantic/native vs visual/GUI route from preconditions/evidence | FUTURE-SCOPED-GATE | Stage 26.5; backend availability alone is not a route decision. |
| Common grounding proposal fields | target identity/source/frame/confidence/ambiguity + coordinates when required | FUTURE-SCOPED-GATE | Stage 26.5 integration direction; capability-specific grounders remain valid. |
| Environmental-content trust classification | UI/DOM/email/docs/OCR/tool output/worker-chat output treated as untrusted task data re policy/authority | ACCEPTED SECURITY INVARIANT | ADR-033; provenance survives cross-capability/session transfer. |
| Task-success vs safety verification | separate result dimensions | ACCEPTED DIRECTION / ACTIVE-INTEGRATION | Stage 26.3B and later safety evaluation. |
| Conversation Bridge | normalized AI-chat session observation + bounded message actuation below Control Plane | PARALLEL-TRACK / FUTURE-SCOPED-GATE | ADR-035 / Track M; no current public-tool expansion and not a planner. |
| Browser Companion | project-owned extension in user's authenticated browser session | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M1; credentials remain inside browser boundary; starts read-only. |
| ConversationSnapshot | stable platform/session/conversation/message identity + active branch + hashes + generation state + provenance/freshness | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M0/M1 operational observation contract; Markdown is not source of truth. |
| HandoffPack | bounded task-specific context derived from WorkingState + selected conversation evidence | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M2/M3; avoid whole-transcript replay. |
| Procedure-state dataset | structured verified state-transition examples | OPTIONAL-RESEARCH | Supports later evaluation/training; not release prerequisite. |
| Specialized local reasoning | proposal-only specialist interface | OPTIONAL-RESEARCH | Not a general planner or authorization source. |
| Future local general planner | Track P: shadow -> bounded subtask -> optional local mode | OPTIONAL-RESEARCH / FUTURE | Only after verified data + measured need; always behind Control Plane/verifier/Finish Gate. |
| Multi-chat orchestration | one Manager ChatGPT -> verified worker handoff -> later explicit multi-worker session/task ownership | PARALLEL-TRACK | Track M; first prove one-manager/one-worker identity, delivery, response freshness and recovery. |
| Distribution/maintenance | installer/update/repair/doctor/uninstall/rollback/restart recovery | FUTURE-SCOPED-GATE | Stage 27. |

## Planner / Control Plane terminology

```text
general planner
 = open-ended goal/strategy/adaptation
 = ordinary ChatGPT today

local deterministic Control Plane
 = execution state/policy/procedure/verification/recovery/finish
 = accepted first slice + active Stage 26.3 expansion

future local planner
 = optional Track P research
 = not current product path
```

Do not use `Control Plane` as a synonym for `planner`.

Track M also does not change this terminology: Conversation Bridge transports/observes bounded worker-session state and effects; it does not choose open-ended strategy.

## Accepted public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray switch between five and six tools.

The historical five-tool file/browser projection remains internal implementation/regression only. The normal semantic startup guard refuses READY unless live inventory equals the exact six canonical names.

`procedure_run` may invoke only registered bounded procedures and exposes no generic shell/Python/path/backend/tool selector.

ADR-035 / Track M adds no current public tool. Any later truthful new consequence class still requires its own public-contract/security/physical acceptance.

## Computer-use direction

Canonical formula from ADR-032:

```text
semantic/native state first
 -> selective visual evidence
 -> capability-aware bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> WorkingState
 -> independent Finish Gate
 -> safety/policy gate
```

This direction does not authorize a screenshot-only loop, unrestricted program-state/code access, generic raw-tool dispatcher or new public Windows tool names.

Track M reuses the same state-first rule for authenticated AI-chat sessions: validated platform-native read when available, then DOM/accessibility, then selected GUI/visual fallback.

## Stage order

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3 Verified Procedure Runtime               ACTIVE
    -> 26.3A canonical six-tool runtime           ACCEPTED / MERGED #92
    -> 26.3B Verification Kernel + Finish Gate    ACTIVE
    -> 26.3C WorkingState + recovery + LoopGuard
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27/28 release work
```

Parallel Track M is non-release-critical and starts only when its verification/state dependencies are useful; canonical progression is defined in `CONVERSATION_BRIDGE_ARCHITECTURE.md` / `ROADMAP.md`.

## Accepted Windows evidence lineage

Exact Stage 26.1/26.2 physical heads, result directories and scoped measurements live in `EVIDENCE_INDEX.md` and accepted historical stage documents. Do not duplicate them here as current planning state.

## Future planner acceptance rule

Do not promote a local planner merely because a model exists. Track P requires verified long-horizon state data, measured need and comparative evaluation against ordinary ChatGPT behavior. First mode is shadow/proposal-only. Capability authorization, transition verification, Finish Gate and safety policy remain independent regardless of planner source.

## Merge rule

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command. Stop on unresolved finding, conflicts, ambiguous scope or failed/skipped evidence.

# Module / Capability Catalog

Status synchronized through accepted Stage 26.3A / PR #92, the promoted computer-use architecture direction, and provisional ADR-035 / Track M Agent Session & Delegation direction.

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
| Windows manager ownership | authoritative runtime owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | Lifecycle/config/diagnostics only; not planner or procedure/delegation Control Plane. |
| Scoped files | official Filesystem backend behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`. |
| Browser | pinned Playwright path behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`; current accepted backend is isolated/headless. |
| Semantic capability projection | exact six-tool canonical boundary | PRODUCT-ACCEPTED | Five file/browser semantics + bounded typed `procedure_run`; no 5/6 mode. |
| Deterministic execution Control Plane | TaskState + registered procedures + authorization/checkpoints/verifier/budgets | PRODUCT-ACCEPTED first slice / ACTIVE-INTEGRATION broader contracts | Stage 26.3A proves first slice; 26.3B/C broaden verification/state/recovery. Future Track M remains beneath this boundary. |
| Verified Procedure Runtime | `verified_workspace_artifact_v1` plus separately accepted bounded procedures as they land | PRODUCT-ACCEPTED scoped | Registered procedures only; durable checkpoints and fail-closed verification boundaries. |
| Verification Kernel | ExpectedEffect + fresh re-observation + `PASS|FAIL|UNKNOWN` + cross-capability predicates | ACTIVE-INTEGRATION | Stage 26.3B; transition delivery/result separation becomes reusable contract. |
| Independent Finish Gate | `candidate_done` -> fresh goal-level predicates -> `DONE` | ACTIVE-INTEGRATION | Stage 26.3B; planner/worker self-assessment is not task completion. |
| WorkingState v1 | constraints/subgoals/facts+provenance+freshness/progress/evidence/recovery/budgets + planner-neutral optional actor/delegation/environment refs | FUTURE-SCOPED-GATE / NEXT-AFTER-26.3B | Stage 26.3C; structured operational state, never private chain-of-thought; must not hard-code one executor. |
| Typed recovery + LoopGuard | failure taxonomy, no-effect/repeat/oscillation detection, reconciliation and bounded escalation | FUTURE-SCOPED-GATE / NEXT-AFTER-26.3B | Stage 26.3C; no blind infinite retry; future Track M reuses the same logical-operation/idempotency/reconciliation machinery. |
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
| ObservationEnvelope | small reference envelope over capability-native Browser/Windows/file/app/session state | FUTURE-SCOPED-GATE | Stage 26.5 target; do not flatten rich native state prematurely. |
| Capability-aware router | reviewed semantic/native vs visual/GUI route from preconditions/evidence | FUTURE-SCOPED-GATE | Stage 26.5; backend availability alone is not a route decision. Future Track M applies the same native-harness-first rule. |
| Common grounding proposal fields | target identity/source/frame/confidence/ambiguity + coordinates when required | FUTURE-SCOPED-GATE | Stage 26.5 integration direction; capability-specific grounders remain valid. |
| Environmental-content trust classification | UI/DOM/email/docs/OCR/tool output/worker-session output treated as untrusted task data re policy/authority | ACCEPTED SECURITY INVARIANT | ADR-033; provenance survives cross-capability/session transfer. |
| Task-success vs safety verification | separate result dimensions | ACCEPTED DIRECTION / ACTIVE-INTEGRATION | Stage 26.3B and later safety evaluation. |
| Agent Session capability family | first-class session/chat/delegation/message/environment observation + bounded future effects below Control Plane | PARALLEL-TRACK / FUTURE-SCOPED-GATE | ADR-035 / Track M; replaces the narrower Browser-child interpretation of multi-chat without adding current runtime authority. |
| HarnessSession | durable harness/host session identity separate from chat/task/environment | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M0/M1 normalized session state; ownership and lifecycle are explicit. |
| Conversation / Chat | normalized message-history/branch state within a HarnessSession | PARALLEL-TRACK / FUTURE-SCOPED-GATE | One session may contain one or multiple chats; do not assume `session == conversation`. |
| DelegationTask / DelegationRecord | explicit manager-assigned work unit separate from session identity | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Stable `delegation_id`, subgoal, HandoffPack hash, expected result contract, status and evidence/correlation refs. |
| MessageDelivery / DeliveryReceipt | one concrete cross-session message effect | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Separate prepared/delivered/held/refused/unknown states from worker start/completion; preserve stable delivery/correlation identity. |
| ExecutionEnvironment | workspace/worktree/project/host environment separate from session lifecycle | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Initial Track M workers bind only to already-authorized environments; environment/project lifecycle is a later separate consequence class. |
| Session Observer | discover/list/read/status over agent sessions/chats | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M1 begins read-only; observation is evidence only. |
| Session Message Transport | bounded queued message delivery + separately admitted steer/interrupt semantics | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M2; queued/non-interrupting is preferred default where supported; delivery != completion. |
| Session Lifecycle Actuator | create/fork/rename/archive/stop for admitted sessions | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M4+ only after existing-worker handoff/recovery is proven; uses stable logical operation id and reconciliation. |
| Worker ownership / WorkerLease | manager/user/parent/adopted/read-only ownership + task/lifetime/capability/budget binding | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Discoverability is not lifecycle authority; destructive cleanup requires ownership proof. |
| Delegation authority profile | minimum explicitly delegated child capability set | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Worker does not inherit manager harness lifecycle privileges; initial `max_spawn_depth = 1`. |
| Agent Session Adapter Registry | open-ended harness/provider/surface adapters selected by current evidence/capabilities | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Prefer official/project-owned harness API/host protocol, then validated provider/session route, Browser Companion DOM/A11y, reviewed GUI fallback, ABSTAIN. |
| Conversation Bridge | browser/web-chat adapter family inside Agent Session capability | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Retained from CtxPort work; no longer modeled as a child of general Browser capability. |
| Declarative conversation profiles | URL/origin matching + capability declarations + semantic hints + optional small hooks | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Default browser-chat extension path; avoid a duplicate backend per vendor. |
| GenericChatAdapter | provider-agnostic DOM/accessibility chat observation/action fallback | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Unknown/stale browser profile degrades here before visual fallback or ABSTAIN. |
| Conversation visual fallback | selected GUI/visual grounding after semantic routes are insufficient | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Same state-first authority rule; visual route is fallback, not a second authority. |
| Browser Companion | project-owned extension in user's authenticated browser session | PARALLEL-TRACK / FUTURE-SCOPED-GATE | One Track M adapter route, not the architecture root; credentials remain inside browser boundary. |
| ConversationSnapshot | normalized chat/message state with stable IDs where available | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Explicit unknown fields allowed; Markdown is not source of truth. |
| HandoffPack | bounded task-specific context derived from WorkingState + selected conversation evidence | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Task data only, never authority; avoid whole-transcript replay. |
| Session operation idempotency/reconciliation | stable logical `operation_id` + native idempotency key where supported + `OUTCOME_UNKNOWN` reconciliation | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Prevent duplicate session/message/delegation effects after ambiguous transport/ack failures. |
| Session event monitoring | idle/completion/change subscription -> fresh re-observation | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Event is an observation trigger, never semantic completion proof. |
| Agent-session adapter acceptance | discovered -> fixture-tested -> read/message/lifecycle verified -> physically accepted/degraded | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Adapter presence or read success does not grant mutation/lifecycle authority. |
| Multi-worker orchestration | one Manager -> multiple explicit DelegationTasks with bounded fan-out | PARALLEL-TRACK | Future M6; only after one existing-worker and one manager-created-worker E2E; initial nested spawn disabled. |
| Project / environment lifecycle | project/workspace/worktree create/bind/move/delete | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M7 separate consequence/security/acceptance from session lifecycle; do not hide inside harness/session CRUD. |
| Cross-harness adoption/handoff | Codex/Claude/VS Code/web-chat/future provider session adapters under one contract | PARALLEL-TRACK / FUTURE-SCOPED-GATE | Future M8; harness/provider names remain adapters, not core enums. |
| Procedure-state dataset | structured verified state-transition examples | OPTIONAL-RESEARCH | Supports later evaluation/training; not release prerequisite. |
| Specialized local reasoning | proposal-only specialist interface | OPTIONAL-RESEARCH | Not a general planner or authorization source. |
| Future local general planner | Track P: shadow -> bounded subtask -> optional local mode | OPTIONAL-RESEARCH / FUTURE | Only after verified data + measured need; always behind Control Plane/verifier/Finish Gate. |
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

Do not use `Control Plane` as a synonym for `planner`, `agent host` or unrestricted `orchestrator`.

Track M does not change this boundary: Manager/worker agents propose/execute bounded work, while the project Control Plane owns authority, logical operation/delegation state, verification, recovery and completion.

## Track M identity terminology

Keep these distinct:

```text
HarnessSession      durable harness/host agent session
Conversation/Chat   message-history unit within a session
DelegationTask      one explicit manager-assigned work unit
MessageDelivery     one concrete message transport effect
ExecutionEnvironment workspace/worktree/project/host environment
```

`session_id` is not a substitute for `delegation_id`, and neither is environment/project identity.

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

ADR-035 / Track M adds no current public tool. Any later truthful session/message/lifecycle/environment consequence class requires its own public-contract/security/physical acceptance. Do not export raw vendor `thread_*`/`project_*` catalogs or generic `harness_execute` simply because an adapter supports them.

## State-first direction

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

This direction does not authorize a screenshot-only loop, unrestricted program-state/code access, generic raw-tool dispatcher or new public Windows/session tool names.

Track M reuses the same rule:

```text
official/project-owned harness API / host protocol
 -> validated provider/session native route
 -> Browser Companion / GenericChatAdapter DOM/accessibility
 -> selected GUI/visual fallback
 -> ABSTAIN when state remains ambiguous/unsafe
```

Undocumented private web APIs are optional accelerators, not sole security boundaries. A provider UI/API change should degrade one route rather than require a core architecture rewrite.

## Stage order

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3 Verified Procedure Runtime
    -> 26.3A canonical six-tool runtime           ACCEPTED / MERGED #92
    -> 26.3B Verification Kernel + Finish Gate
    -> 26.3C WorkingState + recovery + LoopGuard
 -> broad real-app physical coverage
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27/28 release work
```

Parallel Track M is non-release-critical and starts only when its verification/state/recovery dependencies are useful. Stage 26.3C should reserve planner-neutral optional actor/delegation/environment references and general ambiguous-effect reconciliation, but must not implement Track M merely to prepare for it.

Canonical Track M progression is defined in `CONVERSATION_BRIDGE_ARCHITECTURE.md` / `ROADMAP.md`.

## Accepted Windows evidence lineage

Exact Stage 26.1/26.2 physical heads, result directories and scoped measurements live in `EVIDENCE_INDEX.md` and accepted historical stage documents. Do not duplicate them here as current planning state.

## Future planner acceptance rule

Do not promote a local planner merely because a model exists. Track P requires verified long-horizon state data, measured need and comparative evaluation against ordinary ChatGPT behavior. First mode is shadow/proposal-only. Capability authorization, transition verification, Finish Gate and safety policy remain independent regardless of planner source.

Track M does not require Track P. Multi-session transport/delegation can remain managed by ordinary ChatGPT while all effects continue through the deterministic Control Plane.

## Merge rule

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command. Stop on unresolved finding, conflicts, ambiguous scope or failed/skipped evidence.
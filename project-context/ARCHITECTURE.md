# Architecture

## Repository-state rule

Resolve live `main` and relevant open PR heads before new work. Historical acceptance SHAs are evidence, not substitutes for the current integration line.

Stage 26.3A was merged through PR #92 into:

```text
43ad61384e966ecf089e69a95c166d41da949ebe
```

The exact physically accepted Stage 26.3A runtime head remains:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

The later integration line has continued through Browser verification/L3 and Windows shared-kernel verification. At the base of the Track M architecture update branch, live `main` is `cc0fa3d1b7afe9d833334ae68482d2d3dca4b818` with PR #114 merged; PR #115 is the open Windows/application L3 slice. Always resolve live GitHub state rather than treating this sentence as permanently current.

## Product boundary

`chat-agent-platform` is the local capability and deterministic execution-support layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = current general intelligence
  + task interpretation
  + strategy
  + procedure selection
  + novel-state adaptation / escalation
  + future bounded delegation proposals

local platform
  = scoped capabilities
  + deterministic/native observation
  + selective specialist perception
  + deterministic execution Control Plane
  + authorization
  + ExpectedEffect / verification
  + checkpoints
  + WorkingState
  + typed bounded recovery / LoopGuard
  + independent Finish Gate
  + safety/policy gate
  + verified procedural memory
```

### General planner vs deterministic Control Plane

**General planner** means open-ended semantic strategy: interpreting the user's goal, selecting materially different approaches and adapting to novel state. Ordinary ChatGPT is the only **current general planner**.

**Deterministic Control Plane** means execution-state/policy machinery for an already selected bounded goal/procedure/effect: TaskState/WorkingState, ProgramGraph progression, authorization, expected effects, transition verification, checkpoints, typed recovery, LoopGuard, budgets, finish predicates and escalation.

The Control Plane may autonomously advance a predeclared transition only when current evidence uniquely matches it and authorization + verifier gates pass. It must ABSTAIN/escalate instead of inventing a new strategy.

Canonical detail:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`

A future local general planner is optional Track P research and remains above the same deterministic authority/verification/Finish Gate boundaries.

A future Agent Session / Delegation work-distribution layer is separate parallel Track M. It is governed by ADR-035 and `CONVERSATION_BRIDGE_ARCHITECTURE.md`; it does not change the current planner boundary or public tool inventory.

---

# Accepted ordinary-Chat path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> canonical six-tool semantic projection
  -> deterministic Control Plane / focused task capabilities
```

Current canonical public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no normal runtime/profile/tray choice between five and six tools. The historical five-capability file/browser projection is private implementation/regression infrastructure only.

The current six-tool count is not an eternal maximum. A genuinely new consequence class requires a truthful public-contract ADR/schema/security/ordinary-Chat physical acceptance; never preserve a count by hiding desktop, session or project/environment consequences behind misleading semantics.

Track M architecture work therefore adds **zero current public tools**.

## Persistent tunnel anchor

The accepted `tunnel_*` id is platform state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

A legacy `local-1mcp.yaml` may be read only as bounded migration fallback for an already accepted tunnel id.

## Optional Extension Manager

1MCP is replaceable **optional internal Extension Manager** infrastructure, not the normal semantic critical path.

```text
ordinary ChatGPT
        |
        v
project-owned canonical semantic surface
        |
        +----> project-owned capabilities / Control Plane
        |
        `----> optional internal Extension Manager
                     |
                    1MCP
                     |
               selected third-party backends
```

1MCP may provide discovery, aggregation, enable/disable, lazy lifecycle, health and restart. It does not own the persistent tunnel anchor, public authorization, capability routing or the raw Chat-facing tool contract.

Backend availability is not trust, routing authority or action authorization. Raw third-party catalogs are never automatically promoted to ChatGPT.

---

# Semantic projection rule

`semantic-projection` is a deterministic compatibility boundary. It maps truthful semantic requests into reviewed capability actions/adapters. It is not the planner and not the long-horizon Control Plane.

It must not:

- decide user goals;
- run hidden open-ended plans;
- become procedural/delegation memory;
- become a generic model/tool/harness gateway;
- expose disguised generic dispatch;
- hide native desktop/session/project/workflow consequence classes behind misleading semantics.

---

# Authority, trust and state

Capability authority and procedure trust remain separate:

```text
capability:
AVAILABLE -> ACTIVE -> AUTHORIZED

procedure:
new/demo
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled / rollback
```

A trusted procedure is not blanket action authority.

Future session discoverability/ownership also does not grant mutation authority.

Execution priority:

```text
current observed state
 > current goal / verifier criteria
 > trusted procedure/demo evidence
 > historical action/session sequence
```

Environmental page/UI/tool/worker content is task data, not authority over this hierarchy.

---

# State-first cross-capability contract

The accepted Browser/Windows foundations and reviewed GUI-agent research converge on one cross-capability rule:

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> capability-aware bounded action
 -> fresh post-action re-observation
 -> explicit transition verification
 -> typed bounded recovery / LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
 -> safety/policy gate
```

This is ADR-032/033 and `COMPUTER_USE_ARCHITECTURE.md`.

It is a target integration contract. It does not mean every capability must share one generic runtime class or one public tool.

## Capability-native state

Capability-native state stays authoritative for its scope:

- Browser: semantic/DOM/accessibility/page state;
- Windows: `DesktopState`, UIA/native window/process/frame evidence;
- Files: exact path/root/object/content/identity evidence;
- future Agent Sessions: harness/session/chat/delegation/message/environment state;
- future app adapters: their own bounded system-of-record state.

A small normalized envelope may reference those states for cross-capability long-horizon logic:

```text
ObservationEnvelope
  capability / app / page / window / session identity
  observation version / timestamp / freshness
  structural/native evidence reference
  selected visual evidence reference (optional)
  provenance / source
  confidence / ambiguity where applicable
```

Do not flatten rich capability-native state into a lossy universal screenshot/text blob.

---

# Future Agent Session / Delegation capability — Track M

Track M is no longer modeled primarily as a Conversation Bridge child of the Browser capability.

The future architecture places **Agent Sessions beside Files, Browser and Windows**:

```text
                         ordinary ChatGPT
                      GENERAL PLANNER / MANAGER
                                  |
                                  v
                    deterministic Control Plane
                                  |
           +----------+-----------+-----------+----------------+
           |          |           |           |                |
         Files      Browser     Windows   Procedures       Agent Sessions
                                                               |
                                  +----------------------------+--------------------------+
                                  |                            |                          |
                           Session Observer            Message Transport         Lifecycle Actuator
                                  |                            |                          |
                                  +--------------------+-------+--------------------------+
                                                       |
                                                Delegation Ledger
                                                       |
                                                Adapter Registry
                         +-----------------------------+------------------------------+
                         |                             |                              |
              official/project-owned             provider/session               Browser Companion
               harness/host API                     native route                        |
                                                                                 DOM/accessibility
                                                                                       |
                                                                                 reviewed GUI fallback
                                                                                       |
                                                                                      ABSTAIN
```

Conversation Bridge / Browser Companion remains important for authenticated web-chat surfaces, but is one adapter family beneath the Agent Session capability.

## Track M object model

Keep distinct:

```text
HarnessSession
  durable agent-session/host unit

Conversation / Chat
  message-history unit inside a session

DelegationTask
  one explicit manager-assigned work unit

MessageDelivery
  one concrete cross-session message transport effect

ExecutionEnvironment
  workspace/worktree/project/host environment
```

Core identity rule:

```text
Session != Chat != DelegationTask != MessageDelivery != ExecutionEnvironment
```

One session may contain one or multiple chats. One worker session may process several delegations over time. A late/latest response from the same session is not a sufficient correlation rule.

## Session ownership and authority

Future session state records ownership such as:

```text
user_owned
manager_owned
parent_owned
adopted
external_read_only
```

Discoverability is not lifecycle authority. Destructive cleanup/archive requires current ownership evidence.

A future `WorkerLease` may bind a manager-owned worker to task, manager, lifetime, capability set, budget and cleanup policy.

Workers do not inherit manager session/harness lifecycle authority by default.

Initial topology:

```text
Manager
  -> Worker A
  -> Worker B
  -> Worker C

max_spawn_depth = 1
```

Recursive delegation is later/optional and requires measured need plus explicit cycle/budget/authority controls.

## HandoffPack and delegation

`HandoffPack` is retained as bounded task context from WorkingState and selected evidence:

```text
HandoffPack      = task/environmental data
DelegationGrant  = deterministic Control Plane authority
```

Worker-readable text cannot grant permission/capability authority.

Future `DelegationRecord` preserves a stable `delegation_id`, manager/worker refs, subgoal, HandoffPack hash, expected result contract, status, budget and evidence/correlation refs.

## Message delivery semantics

Track M distinguishes:

```text
transport accepted
message delivered / held / refused / unknown
worker turn/work-unit started
worker turn/work-unit settled
result correlated to this DelegationTask
```

Default send should be queued/non-interrupting where the harness exposes that distinction. `steer` and `interrupt` are stronger separately authorized effects.

## Idempotency and reconciliation

Every logical mutating session/message effect uses a stable `operation_id`. Where a native harness offers an idempotency key, the same logical id is used.

A mutating timeout/error is classified:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

For `OUTCOME_UNKNOWN`, reconcile the original operation from fresh authoritative state before retry. If effect existence cannot be proven, remain `UNKNOWN` and stop/escalate.

Entity creation may use an operation-scoped observation subject such as:

```text
capability = agent_sessions
subject = session-create:<operation_id>
```

so the existing Verification Kernel can verify BEFORE/AFTER without embedding vendor-specific thread logic.

## Native-harness-first routing

Preferred Track M route:

```text
1. official/project-owned harness API / local host protocol
2. validated provider/session SDK/native route
3. Browser Companion + GenericChatAdapter DOM/accessibility
4. reviewed GUI/visual fallback
5. ABSTAIN
```

A documented/project-owned harness API may be the preferred read/write route after scope/identity/verification review. Undocumented private web APIs remain optional accelerators and never the sole security boundary.

## Browser Conversation Bridge retained

For browser-only surfaces retain the useful CtxPort-derived architecture:

```text
open-ended adapter registry
 -> declarative provider/application profiles
 -> small reviewed hooks for real platform differences
 -> GenericChatAdapter DOM/accessibility fallback
 -> selected GUI/visual fallback
 -> ABSTAIN
```

Provider/application/harness IDs are open-ended strings. Application/surface identity remains distinct from optional model identity.

`ConversationSnapshot` is operational state; Markdown transcript export is not source of truth. Unknown stable IDs remain explicitly unknown rather than invented.

Browser cookies/tokens remain inside Browser Companion. Native harness/provider credentials similarly stay inside adapter/runtime boundaries and never become planner/WorkingState/HandoffPack payload data.

## Event-driven monitoring

Native harness/session events or Browser Companion page-change events may trigger observation efficiently:

```text
event
 -> fresh re-observation
 -> Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

Event delivery is never semantic completion proof by itself.

## Project/environment lifecycle is separate

A harness may expose project/workspace/worktree lifecycle, but that is a stronger consequence class affecting roots/repository/workspace/runtime state.

Initial Track M session creation may bind only to an already-authorized existing `ExecutionEnvironment`.

Future project/environment create/bind/move/delete requires separate policy, ExpectedEffect contracts, public-contract decision if exposed, and physical acceptance.

## Track M current status

This is future parallel architecture only. It adds no current runtime module/public tool and is not Stage 26 release-critical work.

Canonical detail: ADR-035 and `CONVERSATION_BRIDGE_ARCHITECTURE.md`.

---

# Capability-aware routing

Routing follows reviewed capability/precondition evidence:

```text
exact safe semantic/native operation available
 -> semantic/native route

reviewed structural miss / spatial requirement
 -> selected visual/GUI grounding evidence

uncertain / ambiguous / high-consequence target
 -> stronger evidence or ABSTAIN
```

Tool/backend existence alone never determines route selection.

## Grounding/identity evidence

Coordinate/spatial proposals preserve when available:

```text
semantic target identity
role/name/state
bounding region / coordinates
source = structural | visual | hybrid
observation/frame binding
confidence
ambiguity evidence
```

Coordinates alone are not durable identity or authority.

Session capability state similarly preserves harness/session/chat/delegation/delivery/environment identities where available rather than using titles/content as durable identity.

---

# Observe -> Act -> Verify

The verifier foundation is the cross-capability transition contract.

```text
before = observe()
expected = bind_expected_effect(goal, transition, before)
authorized = authorize(before, requested_action, expected)
delivery = act(authorized)
after = reobserve(relevant_scope)
verification = verify(before, after, expected)
```

Every state-changing transition defines:

```text
current-state preconditions
logical operation identity when needed
ExpectedEffect / postcondition predicates
one bounded authorized action
re-observation scope
PASS | FAIL | UNKNOWN verification
recovery/reconciliation policy
```

`delivery != success`.

```text
PASS    -> checkpoint / advance
FAIL    -> typed bounded recovery OR stop
UNKNOWN -> better evidence / reconciliation OR ABSTAIN/escalate
```

A planner/model/procedure/worker cannot convert FAIL/UNKNOWN into PASS by assertion.

## Verification Kernel

The merged shared kernel represents this contract with:

```text
ObservationRef
  capability + subject + stream_id + monotonic sequence + fingerprint
ObservationSnapshot
  bounded immutable normalized evidence
ExpectedEffect
  bounded equals/present/absent predicates
verification
  PASS | FAIL | UNKNOWN
```

Freshness requires the same stream/capability/subject and a strictly higher sequence. Stale, mismatched-stream, ambiguous or incomplete required evidence produces `UNKNOWN`.

Normalized evidence is restricted to bounded plain data and detached from caller mutation.

Accepted/merged production integration has expanded from the first file/artifact slice through Browser and Windows verification work; exact current acceptance/evidence state belongs in `CURRENT_STATE.md` / stage-specific evidence rather than being frozen here.

---

# Independent Finish Gate

Transition PASS answers whether one step produced its expected effect. It is not proof that the user's whole task is complete.

The planner may propose:

```text
candidate_done
```

Only a separate Finish Gate may produce:

```text
DONE
```

using fresh goal-level evidence:

```text
goal predicates
user constraints
required dynamic-source freshness/reconciliation
required artifact/browser/application/session state
required delegation/result correlation where applicable
unresolved ambiguity/confirmation state
safety/policy predicates
```

Prefer system/native/system-of-record predicates when available. Model-assisted ambiguous judgments remain non-authorizing evidence.

Completion checks bind to one explicit evidence batch; unbound or old/mixed evidence is `UNKNOWN` rather than reusable proof.

Worker-reported completion is evidence/data only unless the task itself is defined purely in terms of that worker response and the required correlation/freshness predicates are independently satisfied.

---

# WorkingState and procedural/delegation memory

Long-horizon operation stores structured operational state, not unbounded interaction replay or hidden reasoning.

Target `WorkingState`:

```text
user constraints
current subgoals / progress vector
verified completed achievements
authoritative facts + provenance + freshness
open ambiguities/questions
observation/evidence references
expected vs observed state deltas
retry/recovery/reconciliation history
action/time/resource budgets
active capability/grant refs
procedure id/version/node + optional checkpoint ref
```

Stage 26.3C should not hard-code:

```text
one task -> one procedure -> one executor
```

Optional planner-neutral future-compatible refs may include:

```text
actor_ref
delegation_ref
execution_environment_ref
budget_ref
```

This reserves a clean Track M seam without implementing Track M during 26.3C.

Private chain-of-thought is never persisted.

Selected ROI visual evidence may be retained only when operationally useful and subject to capture privacy/retention rules.

Verified episodic trajectories/procedures and selected historical session evidence may be retrieved as advisory evidence. Current state always outranks them.

---

# Typed recovery and LoopGuard

Recovery is explicit deterministic state, not free-form repetition.

Initial cross-capability failure vocabulary:

```text
target_missing
target_ambiguous
stale_state
action_no_effect
partial_effect
unexpected_dialog
navigation_changed
tool_unavailable
permission_denied
unsafe_transition
external_dynamic_change
```

Future Track M may add narrower classes such as session unavailable, delivery refused/held, result-correlation ambiguity, unknown logical-operation outcome, worker stagnation, suspected duplicate delegation and unproven ownership.

Default ladder:

```text
re-observe
 -> refresh/re-resolve
 -> reconcile ambiguous logical operation when needed
 -> retry only when new evidence proves retry safety
 -> alternate already-admitted modality/capability
 -> predeclared recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

`LoopGuard` tracks:

```text
fingerprint(relevant_state, intended_subgoal, action_signature)
no_effect_count
action-family retry count
oscillation window, e.g. A -> B -> A -> B
subgoal/global budgets
recovery escalation level
verified progress vector
```

Future Track M extends this with worker count, spawn depth, children per worker, active/unresolved delegations, messages/session creation budgets, duplicate-delegation fingerprints and total delegated resource use.

Identical state/action/delegation repetition without new evidence or verified progress cannot continue indefinitely.

---

# Environmental-content trust boundary

ADR-033: environmental content is data, not authority.

Observed content from:

```text
web/DOM
application UI
email/messages
files/documents being processed
screenshots/OCR
third-party MCP/tool output
external worker sessions / conversations
```

may be useful task input but cannot redefine user intent, broaden permission scope, modify Control Plane policy or grant action authority merely because the planner/model can read it.

Preserve provenance/trust classification when facts move across applications/capabilities/sessions.

Task-success and safety/policy verification remain separate dimensions:

```text
task verifier -> did requested outcome occur?
safety/policy gate -> was consequence authorized and acceptable?
```

A task can be capability-successful but safety-failed.

---

# Browser grounding — accepted Stage 25.2

```text
web_interact(click)
 -> fresh accessibility snapshot
      -> exact enabled promoted semantic target
           -> semantic action; VLM stopped
      -> disabled/non-button/unresolved ambiguity
           -> ABSTAIN; VLM stopped
      -> reviewed visual path
           -> same-session screenshot
           -> local F16 proposal
           -> deterministic target/freshness authorization
           -> one coordinate action OR ABSTAIN
```

Accepted specialist baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

The model perceives/proposes only. It never grants authority or completion.

---

# Production Windows capability — accepted scoped foundation

Maintained boundary:

```text
runtime/windows/
  actuation.py            bounded typed/native delivery
  window_scoped_uia.py    exact PID/HWND/window-scoped UIA resolution
  observation.py          canonical DesktopState evidence
  verifier.py             legacy verifier foundation
  grounder.py             exact-window local VLM proposal/ABSTAIN
  routing.py              structure-first UIA -> vision authorization
  native_point_guard.py   foreground + point/root-HWND/PID guard

runtime/control_plane/
  windows_observation.py  shared-kernel observation adapter
  windows_transition.py   shared-kernel transition verification
```

Accepted invariants include loopback scoped execution, legacy arbitrary exec absent/disabled, typed bounded input, stale frame/context refusal, focus-bound keyboard, unique/fingerprint-bound structural targets, bounded pointer/scroll, Unicode text delivery and no generic `/execute_windows` public authority.

Delivery receipts remain separate from verified outcome.

Stage 26.1E accepted PID -> bounded HWND -> same-process exact window -> native UIA inside the bound window. `DesktopState` remains the Windows capability-native state model.

The existing structure-first Windows route remains:

```text
current DesktopState/UIA
 -> exact safe structural target
      -> fresh structural re-resolution
      -> native UIA delivery

 -> reviewed structural miss only
      -> current exact-window screenshot
      -> Grounder proposal
      -> deterministic evidence gate
      -> fresh exact-window re-observation
      -> foreground/root-HWND/PID/frame guard
      -> one bounded action OR ABSTAIN
```

This is one implementation of the broader state-first rule.

Real-app Windows evidence remains scoped, not universal desktop authority.

---

# Procedural substrate

Pinned target-qualified upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Reuse/adapt:

```text
Flow compiler + Workflow/ProgramGraph
Capture
SkillLibrary/learn/teach lifecycle mechanics
Windows typed backend/agent mechanics
```

A stored demonstration/procedure may retain structural/native and bounded visual evidence, but blind historical coordinate replay is never authority or primary identity.

Stage 26.4 should compile demonstrations into subtask goals + completion criteria + advisory target/action evidence, then re-resolve every step against live state.

---

# Stage 26.3A — Verified Procedure Runtime — ACCEPTED / MERGED #92

The normal six-tool route includes bounded `procedure_run` and has physical ordinary-Chat acceptance.

The first accepted registered procedure was:

```text
verified_workspace_artifact_v1
```

It proved a three-transition deterministic procedure, independent final reread and zero-action ABSTAIN on pre-existing target overwrite.

Later bounded procedure additions do not imply arbitrary procedures or desktop authority.

---

# Current release-critical implementation

## Stage 26.3B — Verification Kernel + Finish Gate / representative evidence — ACTIVE

The reusable kernel foundation is merged. Production integrations now include file/artifact, Browser and Windows shared-kernel paths for accepted recorded scopes. Current representative Windows/application L3 work is tracked separately in current PR/state documents.

Do not freeze exact current PR details here; `CURRENT_STATE.md`, GitHub and stage-specific evidence remain authoritative.

## Stage 26.3C — WorkingState + typed recovery + LoopGuard

Generalize structured long-horizon state, provenance/freshness, progress vectors, typed recovery/reconciliation, repeated/no-effect detection, oscillation detection and budgets.

Reserve optional planner-neutral actor/delegation/environment references, but do not implement Track M merely to prepare for it.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Compile demonstrations into candidate procedure structure and replay under current-state re-resolution + verifier control, never macro authority.

## Stage 26.5 — Hybrid Computer-Use Integration

Converge Browser/Windows on shared control-loop contracts:

```text
ObservationEnvelope references
capability-aware routing
common grounding identity/confidence/ambiguity evidence
state-first + selective visual fallback
cross-app fact provenance
component/noisy recovery evaluation
```

This stage does not automatically change the public six-tool surface. Public Windows/computer-use semantics require separate acceptance.

Parallel Track M may later reuse these state/app-adapter contracts but is not a Stage 26 acceptance requirement.

---

# Track M progression summary

Canonical detail is in `CONVERSATION_BRIDGE_ARCHITECTURE.md` / `ROADMAP.md`.

```text
M0 object model + fixtures
 -> M1 read-only Session Observer
 -> M2 Manager -> one EXISTING Worker verified handoff/correlation
 -> M3 WorkingState/HandoffPack + event monitoring/recovery
 -> M4 session lifecycle + idempotency/reconciliation
 -> M5 manager-created Worker E2E + ownership/WorkerLease
 -> M6 bounded multi-worker, max_spawn_depth=1 by default
 -> M7 separate Project/ExecutionEnvironment lifecycle
 -> M8 cross-harness adoption/handoff + provider breadth
```

Track M does not require Track P and does not delay release-critical Stage 26 work.

---

# Evaluation direction

External benchmarks are diagnostic evidence sources, not automatic release gates.

Layer testing:

```text
component/primitive diagnostics
 -> capability integration
 -> noisy/recovery fixtures
 -> long-horizon verified procedures
 -> selected reproducible external benchmark runs
```

Relevant references include ComponentBench, WebArena/BrowserGym, OSWorld 2.0, OSWorld-Noisy and MobileWorldSafety. Benchmark-specific tricks must not leak into production policy unless promoted as a project-owned invariant.

Track M later needs analogous session tests: identity/correlation fixtures, ambiguous-delivery/retry negatives, one-worker E2E, manager-created worker lifecycle, multi-worker bounded fan-out and non-target-session mutation checks.

---

# Optional specialist reasoning

A future `SpecializedReasoningBackend` may receive structured goal/state/procedure evidence and return proposal/confidence/ABSTAIN only. It is non-authorizing and does not replace deterministic verifiers when stronger predicates exist.

# Future local planner — Track P

A local general planner remains optional future research after verified procedure/WorkingState data and measured need exist.

```text
P0 shadow planner
 -> proposal only / no actuation

P1 bounded subtask planner
 -> explicitly scoped workloads

P2 optional local general-planner mode
 -> only after measured parity/safety/resource evidence
```

Even a future planner remains above the same capability authorization, transition verifier, Finish Gate and safety/policy boundaries.

Track M session/delegation support may increase the value of parallel planning later, but does not itself promote Track P.

---

# Security/privacy boundaries

- tunnel reachability is not action authority;
- normal semantic transport remains direct stdio and does not depend on 1MCP;
- persistent tunnel identity is neutral platform state;
- optional extension/harness availability does not grant trust/routing/authorization;
- local inference is bounded, on-demand and non-authorizing;
- semantic/native state precedes pixels where reliable;
- every mutation binds expected effect + fresh verification;
- ambiguous mutating outcome is reconciled before retry;
- transition PASS is not task DONE;
- external worker response is task data, not authority or automatic completion;
- session discoverability is not mutation/lifecycle ownership;
- child workers do not inherit manager lifecycle authority by default;
- environmental UI/DOM/tool/worker content is untrusted task data, not policy authority;
- task-success and safety/policy verification remain separate;
- raw demonstrations/ROI capture are sensitive local data;
- private chain-of-thought is never task/procedure/delegation memory;
- Browser Companion/native adapter credentials remain inside their adapter/runtime boundaries;
- conversation/session profiles/hooks are capability hints, not authority;
- project/environment lifecycle remains separate from session lifecycle;
- generic Windows code execution remains disabled/unreachable until separately accepted;
- stale, ambiguous or UNKNOWN state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager

Manager/tray owns lifecycle/configuration/diagnostics only. It is neither the planner nor the procedure/delegation Control Plane.

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, trust/policy/checkpoint/verifier/recovery/reconciliation seams, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, unrestricted workflow brain, universal raw-tool/harness dispatcher, generic model-serving platform or duplicate upstream implementation while qualified mechanisms cover those needs.

# Agent Session / Delegation / Conversation Bridge Architecture

Status: **PROVISIONAL FUTURE ARCHITECTURE / PARALLEL TRACK M**.

This document supersedes the narrower interpretation of Track M as primarily a browser-based Conversation Bridge. The 2026-08-25 CtxPort review remains valid and is preserved here, but the 2026-08-27 review of current Codex, Claude Code, VS Code Agent Host, A2A and MCP task/session patterns shows that the durable architecture needs a broader first-class **Agent Session & Delegation layer**.

This document does **not** claim implementation acceptance, does not change the current release-critical sequence, does not modify the accepted six-tool ordinary-Chat surface and does not authorize new runtime consequences.

The current product boundary remains:

```text
ordinary ChatGPT
  = only current general planner / manager

local deterministic Control Plane
  = execution state / policy / authorization / verification / recovery / finish
```

Track M adds a future capability family for observing and controlling bounded agent sessions, delegating explicit work units, correlating message delivery with worker results and adapting multiple harness/provider surfaces without bypassing the Control Plane.

Named systems such as ChatGPT, Codex, Claude Code, VS Code Agent Host, Gemini, DeepSeek, Qwen, Grok, Doubao, Kimi, Perplexity, Poe, Open WebUI or LibreChat are adapter/reference examples, not architecture boundaries.

---

# 1. External architecture inputs

The broadened design is informed by several current patterns. These are architecture evidence, not imported authority.

## 1.1 Codex harness / App Server

OpenAI documents Codex as one harness shared across CLI, IDE, web and desktop clients, with App Server exposing lifecycle/state operations for agent threads and related product entities.

Current relevant patterns include:

```text
thread lifecycle
  start / list / read / resume / fork / archive / delete

thread work/message queue
  add / list / update / delete / reorder / start

project lifecycle
  list / read / create / import / update / move / delete

thread -> project binding
```

Project create/import operations use idempotency keys, reinforcing an important project rule: a retryable transport call and a logical side effect are different things.

Relevant sources:

- https://openai.com/index/unlocking-the-codex-harness/
- https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md

Public Codex issue reports additionally show important failure modes: a message operation can report an error after delivery, a spawned worker can exist without actually starting useful work, child agents can accidentally inherit lifecycle authority and create user-owned root tasks, and thread identity alone may be insufficient to correlate a later response with one delegation. Treat those reports as failure evidence, not stable API specification.

## 1.2 Claude Code cross-session messaging and Agent Teams

Claude Code exposes cross-session discovery/messaging with delivery states such as delivered/held/refused and supports event-style notification when a target session becomes idle. A received cross-session message does not inherit permission authority from the sender.

Agent Teams further separates:

```text
lead session
teammate sessions
shared task list
mailbox
```

and currently prevents nested teams. This is useful evidence for a bounded initial topology: one manager may own several workers, while workers do not recursively create more workers by default.

Relevant sources:

- https://code.claude.com/docs/en/cross-session-messaging
- https://code.claude.com/docs/en/agent-teams

## 1.3 VS Code Agent Host

VS Code distinguishes:

```text
Agent Harness
Execution Environment
Session
Chat
Model
```

A long-lived session can contain multiple chats that share an execution environment/worktree. The Agent Host is persistent independently from one UI client, and session-management capabilities can list/read/create/message sessions across supported harnesses.

This is direct evidence that `session == conversation` is too weak an object model.

Relevant sources:

- https://code.visualstudio.com/docs/agents/concepts/agent-host
- https://code.visualstudio.com/docs/agents/concepts/agent-harnesses
- https://code.visualstudio.com/docs/agents/run/sessions/manage-sessions

## 1.4 A2A and MCP Tasks

A2A separates long-lived context identity from concrete task identity. MCP Tasks similarly gives a long-running work unit a durable task id/lifecycle rather than treating one message/session as the task.

Relevant sources:

- https://a2a-protocol.org/dev/specification/
- https://modelcontextprotocol.io/extensions/tasks/overview

Project consequence:

```text
Session identity != Task identity != Message delivery identity
```

---

# 2. Why Track M exists

The project needs to support work such as:

```text
Manager ChatGPT
 -> discover an existing worker session
 -> read enough fresh context
 -> delegate one bounded subgoal
 -> prove the intended message reached the intended target
 -> observe worker progress/completion
 -> correlate the result with exactly that delegation
 -> record verified result/evidence in WorkingState
 -> decide the next strategy
```

Later it may additionally:

```text
create/fork a bounded worker session
 -> bind it to an already-authorized execution environment
 -> delegate work
 -> monitor/reconcile failures
 -> archive/cleanup manager-owned worker state
```

The architecture must work whether the target session is exposed through:

```text
official/project-owned harness API
provider/session SDK
local host protocol
browser-native/profile adapter
DOM/accessibility
reviewed GUI/visual fallback
```

The accepted isolated/headless Browser remains useful for ordinary browser automation, but it is not the architecture root for agent-session control.

---

# 3. Target placement

Agent Sessions become a capability family beside Files, Browser and Windows.

```text
                         ordinary ChatGPT
                      GENERAL PLANNER / MANAGER
                                  |
                       current semantic surface
                                  |
                                  v
                    deterministic Control Plane
                                  |
             +----------+----------+-----------+-------------+
             |          |          |           |             |
           Files      Browser    Windows   Procedures   Agent Sessions
                                                              |
                                +-----------------------------+-----------------------------+
                                |                             |                             |
                       Session Observer              Message Transport            Lifecycle Actuator
                                |                             |                             |
                                +----------------------+------^------+----------------------+
                                                       |             |
                                                Delegation Ledger    |
                                                       |             |
                                                  Adapter Registry <-+
                                  +--------------------+--------------------+
                                  |                    |                    |
                           native harness/API    provider/session SDK   Browser Companion
                                                                          |
                                                                   DOM / accessibility
                                                                          |
                                                                   reviewed GUI fallback
                                                                          |
                                                                         ABSTAIN
```

Conversation Bridge / Browser Companion is therefore retained, but it becomes one adapter family beneath the Agent Session capability rather than a child of the general Browser capability.

The current six public tools remain unchanged. A future truthful public session/environment consequence class requires its own ADR/schema/security/ordinary-Chat physical acceptance.

---

# 4. First-class object model

Track M must not collapse several distinct identities into one `session_id`.

## 4.1 HarnessSession

A durable agent working session/host-side unit.

```text
HarnessSession
  schema_version

  harness_id
  provider_id
  adapter_id / adapter_version

  session_id
  lifecycle_state
    active | idle | generating | blocked | archived | unavailable | unknown

  ownership
    user_owned | manager_owned | parent_owned | adopted | external_read_only

  parent_session_id        optional
  fork_origin              optional

  execution_environment_ref
  project_ref              optional

  title                    optional
  created_at               optional
  last_activity_at         optional

  chat_refs[]
  current_chat_ref         optional

  observation_ref
  provenance
```

A session can outlive one UI and may contain one or multiple chats depending on the harness.

## 4.2 Conversation / Chat

Message history within a session.

```text
ConversationSnapshot
  schema_version

  harness_session_ref
  chat_id / conversation_id
  title

  surface/application identity
  provider identity
  optional model identity

  active_branch

  messages[]
    platform_message_id
    parent_id
    role
    kind
    content
    timestamp
    content_hash
    attachments
    visibility

  generation_state
    idle | generating | stopped | unknown

  observed_at
  observation_ref
  adapter_route
  provenance
```

A provider may expose `session_id == chat_id`; another may expose several chats per session. The normalized model must not assume either shape.

## 4.3 DelegationTask

A concrete unit of manager-assigned work. This is intentionally separate from session and message identity.

```text
DelegationRecord
  delegation_id

  manager_session_ref
  worker_session_ref
  worker_chat_ref          optional

  subgoal_id
  handoff_pack_ref
  handoff_hash

  status
    prepared
    dispatched
    acknowledged
    running
    blocked
    candidate_complete
    verified_complete
    failed
    cancelled
    unknown

  expected_result_contract

  dispatch_id
  target_turn_id           optional

  budget_ref
  deadline                 optional

  created_at
  updated_at
  evidence_refs[]
```

One worker session may execute several delegations over time. A late response from the same session must not be accepted as the result of the wrong delegation.

## 4.4 MessageDelivery

Transport state for one concrete message/effect.

```text
DeliveryReceipt
  delivery_id
  client_message_id
  delegation_id            optional

  target_session_ref
  target_chat_ref           optional

  delivery_mode
    queued | steer | interrupt

  status
    prepared | delivered | held | refused | expired | unknown

  target_turn_id            optional
  sent_at                   optional
  observed_at               optional

  observation_refs[]
```

`delivered` proves transport/postcondition only. It does not prove that the worker started, completed or produced a valid result.

## 4.5 ExecutionEnvironment

Workspace/worktree/project/host environment is distinct from the agent session.

```text
ExecutionEnvironment
  environment_id
  environment_kind
  roots / worktree / workspace refs
  project_ref              optional
  capability/grant refs
  lifecycle_state
  provenance
```

Initial Track M session lifecycle should create workers only inside an already-authorized environment. Project/worktree/workspace creation is a separate future consequence class and must not be hidden inside session creation.

---

# 5. HandoffPack remains task data, not authority

CtxPort-style full transcript serialization is useful for manual export/diagnostics but should not become the operational handoff protocol.

Track M keeps `HandoffPack` as compact task context derived from WorkingState plus selected conversation evidence:

```text
HandoffPack
  schema_version
  task_id
  delegation_id

  from_session
  to_session

  goal
  subgoal
  user_constraints

  verified_completed
  authoritative_facts + provenance/freshness
  open_questions / ambiguities

  artifact_refs
  evidence_refs

  selected_context
  recent_messages
  context_budget
```

Important boundary:

```text
HandoffPack      = environmental/task data visible to worker
DelegationGrant  = Control Plane authority outside the message
```

Never encode permission/capability grants as worker-readable text and then treat that text as authority. ADR-033 remains binding.

The complete historical transcript remains an evidence source that may be re-read on demand after context compaction. It is not automatically replayed into every worker.

---

# 6. Observer, Message Transport and Lifecycle Actuator are separate

Read and write consequence classes must remain explicit.

## 6.1 Session / Conversation Observer

Read-only responsibilities may include:

```text
identify_harness()
identify_surface()
identify_provider_if_known()
list_sessions()
observe_session()
list_chats()
observe_conversation()
observe_latest_message()
observe_generation_state()
observe_delegation_correlation_state()
```

Observation is evidence only.

## 6.2 Message Transport

Bounded mutating operations may include:

```text
submit_message(mode=queued)
steer_message(...)       separately authorized
interrupt(...)           separately authorized where admitted
cancel_delivery(...)     where supported
subscribe_idle/event(...) read/event registration
```

Default semantics should be non-interrupting/queued where the harness can preserve that distinction. `steer` and `interrupt` are stronger effects and must not be silently inferred from ordinary send intent.

## 6.3 Lifecycle Actuator

Later Track M stages may admit bounded lifecycle operations such as:

```text
create_session()
fork_session()
rename_session()
archive_session()
stop/cancel_manager_owned_session()
```

Delete and project/environment lifecycle remain stronger later consequences.

No generic `execute`, arbitrary selector, JavaScript, shell, Python, raw HTTP or backend dispatcher belongs in this contract.

---

# 7. Adapter and routing architecture

Track M must prefer the strongest truthful native state/action path, then degrade safely.

## 7.1 Adapter Registry

Conceptual contract:

```text
AgentSessionAdapter
  adapter_id
  adapter_version

  can_handle(harness/surface/environment) -> confidence/capabilities

  observe_session(...)
  observe_conversation(...)
  optional message_transport(...)
  optional lifecycle(...)
  optional event_subscription(...)
```

Harness/provider/application identifiers are open-ended strings, not a closed vendor enum.

## 7.2 Route order

```text
1. official/project-owned harness API / local host protocol
        ↓ unavailable/incompatible
2. validated provider/session SDK or reviewed native/profile route
        ↓ unavailable/incompatible
3. Browser Companion + GenericChatAdapter DOM/accessibility
        ↓ insufficient/ambiguous
4. selected reviewed GUI/visual route
        ↓ still insufficient/unsafe
5. ABSTAIN
```

This differs from the earlier CtxPort-derived architecture in one important way: a **documented/owned harness API is not merely a read optimization**. It is the preferred semantic/native route when its identity, consequence and verification contract are reviewed.

Undocumented private web APIs remain optional accelerators only and are never the sole security boundary.

## 7.3 Declarative browser profiles remain useful

For ordinary web-chat surfaces the preferred extension mechanism remains:

```text
profile_id
match
  origins / URL patterns

capabilities
  conversation_list
  stable_session_id
  stable_conversation_id
  stable_message_id
  branching
  attachments
  generation_state

semantic hints
  session/conversation containers
  message regions
  role markers
  composer
  submit control
  busy/generation markers

optional reviewed native read path
quirks / small hooks
```

A stale profile must fall back to fresh generic structural observation rather than force remembered selectors/actions.

## 7.4 GenericChatAdapter is mandatory for browser surfaces

An unknown web chat should attempt bounded DOM/accessibility extraction of:

```text
conversation regions
message roles
composer
submit control
generation/busy state
session/title/URL identity when observable
```

Unknown stable IDs remain unknown; they are never invented.

---

# 8. Browser Companion and credentials

The Browser Companion remains a small project-owned extension for the user's authenticated browser session when no stronger harness/host interface exists.

Keep:

```text
platform/session detection
adapter registry
profiles/hooks
bounded conversation observation
response/event detection
generic DOM/accessibility fallback
normalized snapshots
```

Exclude:

```text
clipboard as agent transport
Markdown as source of truth
generic page-script execution
arbitrary browser/backend dispatch
```

Credential rule:

```text
browser session
  cookies / access tokens / private auth headers
          |
          X never exported to planner / MCP / WorkingState / HandoffPack
          |
          v
  normalized bounded session/conversation evidence
```

The same local-secret isolation principle applies to native harness adapters: planner/session content receives normalized evidence and bounded commands, not reusable credentials.

---

# 9. Idempotency and operation-scoped verification

Session/message lifecycle has an important ambiguity: the target entity may not have an ID until after a mutating operation.

Track M therefore needs stable logical operation IDs.

```text
operation_id
  = caller-generated stable id for one logical side effect
```

Where a native harness supports an idempotency key, pass the same logical operation id through that interface.

## 9.1 Session creation example

Before creation:

```text
ObservationRef
  capability = agent_sessions
  subject = session-create:<operation_id>
  stream_id = <operation observation stream>
  sequence = N

state
  exists = false
```

After creation:

```text
same capability / subject / stream_id
sequence = N + 1

state
  exists = true
  session_id = ...
  ownership = manager_owned
  parent_session_id = ...
  execution_environment_ref = ...
```

The existing Verification Kernel can then verify the effect using the normal same-stream fresh observation contract.

## 9.2 Delivery example

Use:

```text
subject = delivery:<client_message_id or delivery_id>
```

and verify that exactly the intended target/session/chat contains the expected normalized message identity/hash and delivery state.

## 9.3 Retry rule

A timeout/error after delivery must not cause blind retry.

Classify at minimum:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

For `OUTCOME_UNKNOWN`:

```text
reconcile(operation_id)
 -> authoritative effect found
      -> treat original logical operation as committed
 -> authoritative evidence proves absent
      -> retry may be safe under the same operation id
 -> cannot establish
      -> UNKNOWN / stop / escalate
```

This is an extension of the existing invariant:

```text
delivery != success
UNKNOWN -> zero unauthorized continuation
```

---

# 10. Delegation/result correlation

Session identity alone cannot prove which delegated work a later assistant response belongs to.

Every dispatch should preserve where supported:

```text
delegation_id
client_message_id / delivery_id
worker session id
worker chat id
target turn/work-unit id
handoff hash
```

A response is eligible for a delegation only when fresh evidence can bind it to the expected post-dispatch work unit or an equivalent reviewed correlation rule.

Do not accept:

```text
"latest message from session S"
```

as sufficient proof when session S has processed multiple delegations or unrelated user activity.

---

# 11. Event-driven monitoring

Polling should not be the primary orchestration primitive when a reliable local event/subscription exists.

Preferred pattern:

```text
dispatch delegation
 -> register/receive bounded idle/completion/change event
 -> event arrives
 -> fresh re-observation
 -> Verification Kernel evaluates actual state
```

Event delivery is only a trigger to observe. It is not completion evidence.

For browser adapters, `MutationObserver` or equivalent bounded page-change signals may provide the event. Native host/harness adapters should use official session/status events where available.

---

# 12. Ownership and WorkerLease

Discoverability is not authority.

A session observed in the user's harness may have one of several ownership states:

```text
user_owned
manager_owned
parent_owned
adopted
external_read_only
```

Default policy examples:

```text
user_owned existing session
  read          policy/grant dependent
  send          policy/grant dependent
  rename        denied by default
  archive       denied by default
  delete        denied

manager_owned worker
  read          allowed within task scope
  send          allowed within delegation scope
  stop/archive  allowed under lifecycle policy
  cleanup       allowed with ownership proof
```

A future explicit `WorkerLease` may bind:

```text
worker_session_ref
task_id
manager_session_ref
allowed lifetime
allowed consequence set
budget allocation
cleanup policy
```

Ownership proof is required for destructive cleanup. Similar-looking titles/content are not ownership proof.

---

# 13. Delegation authority and topology

Worker sessions must not automatically inherit the manager's harness/session lifecycle capabilities.

Initial rule:

```text
child/session grant
 = intersection(
     task requirements,
     explicitly delegated capability set,
     platform policy
   )
```

Initial topology should be intentionally shallow:

```text
Manager
  -> Worker A
  -> Worker B
  -> Worker C

max_spawn_depth = 1
```

Workers may return results and use task capabilities explicitly granted to them. They do not create/fork/archive arbitrary sessions or message unrelated workers merely because the manager can.

Recursive delegation/nested teams are a later capability only after measured need, explicit authority semantics, budgets, cycle prevention and physical acceptance.

No model prompt such as "only spawn when appropriate" is a substitute for runtime capability filtering.

---

# 14. Orchestration budgets and LoopGuard extension

Existing typed recovery/LoopGuard remains authoritative and must extend across the delegation graph.

Additional state should include where applicable:

```text
worker_count
spawn_depth
children_per_worker
active_delegations
unresolved_worker_count
messages_per_worker
cross_session_message_budget
session_creation_budget
duplicate_delegation_fingerprints
total delegated action/time/resource cost
```

A useful duplicate fingerprint may include:

```text
worker_session_ref
subgoal_id
handoff_hash
expected_result_contract
```

Repeating the same logical delegation after an ambiguous acknowledgement must enter reconciliation first, not automatically send again.

Cycle/oscillation detection should cover both effect repetition and orchestration paths such as A -> B -> A or repeated create/archive/create behavior.

---

# 15. WorkingState integration

Stage 26.3C WorkingState must remain useful before Track M exists, but its schema should not hard-code `one task -> one procedure -> one executor`.

Planner-neutral future-compatible fields should allow:

```text
WorkingState
  task_id

  subgoals[]
    subgoal_id
    status
    actor_ref              optional
    delegation_ref         optional
    execution_environment_ref optional
    budget_ref             optional
    evidence_refs[]

  delegations[]            optional Track M records
  capability_grant_refs[]

  progress_vector
  global budgets
```

`actor_ref` may later identify current ChatGPT manager, a procedure runtime, an external worker session or another admitted actor without changing the Control Plane's authority model.

This is a compatibility guardrail only. Stage 26.3C must not implement Track M or a second planner merely to reserve the references.

---

# 16. Project / environment lifecycle is separate

External harnesses may expose project/workspace/worktree CRUD. Track M must not generalize that into one unrestricted harness CRUD interface.

Separate consequence classes:

```text
Agent Session Capability
  session observe / message / bounded lifecycle

Execution Environment / Project Capability
  project/workspace/worktree creation/binding/move/delete
```

The latter may affect filesystem, repository identity, roots, permissions and process/runtime state. It requires separate policy, ExpectedEffect contracts and acceptance.

Initial session creation may bind only to an already-authorized existing environment.

---

# 17. Public semantic surface direction

The current public surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Do not copy a large vendor-specific `thread_*` or `project_*` catalog directly into ordinary Chat.

Do not introduce generic:

```text
harness_execute(operation, target, arbitrary_args)
```

If a later accepted user-facing session consequence class requires public tools, prefer a small truthful semantic grouping whose read/message/lifecycle consequences are explicit, for example conceptually:

```text
session_observe
session_message
session_manage
```

Names/schemas are intentionally not fixed by this architecture document. A public contract requires its own ADR/security/physical acceptance.

Project/environment management remains separate.

---

# 18. CtxPort adoption boundary retained

CtxPort remains MIT-licensed architecture/code evidence for browser conversation extraction.

Good candidates to adapt:

```text
adapter/plugin registry pattern
open-ended provider/application identifiers
declarative manifest/profile + small hooks pattern
platform URL/conversation identification
ChatGPT active-branch tree linearization
separation of fetch/acquisition mechanism from normalization
message/content flatteners where semantically appropriate
optional fetch-by-conversation-id read path
MutationObserver dynamic-page pattern
conversation token-budget estimation idea
```

Do not adopt as architecture:

```text
CtxPort as required runtime dependency
clipboard as agent transport
Markdown as authoritative state
copy-button/sidebar UI
raw private APIs as sole route/security boundary
credentials outside browser/native adapter boundary
one combined read/write generic plugin authority
closed provider enum
one full duplicate backend per vendor
```

If substantial upstream source is copied, retain required MIT attribution.

---

# 19. Acceptance direction

Track M must distinguish adapter existence, read reliability, mutation authority and orchestration correctness.

Possible adapter status:

```text
DISCOVERED
FIXTURE_TESTED
READ_VERIFIED
MESSAGE_VERIFIED
LIFECYCLE_VERIFIED
PHYSICALLY_ACCEPTED
DEGRADED / INCOMPATIBLE
```

An adapter may be read-accepted without being allowed to mutate sessions.

Each real authenticated consequence path needs appropriate physical acceptance. L3-style tests should use a natural manager goal plus independent evidence proving:

```text
correct worker/session identity
exactly intended message/delegation
no unintended worker mutation
correct result correlation
bounded number of sessions/messages
task-level Finish Gate
source/runtime provenance where applicable
```

---

# 20. Revised Track M progression

Track M remains parallel/non-release-critical.

Dependencies:

```text
26.3B Verification Kernel / Finish Gate
 -> 26.3C WorkingState + provenance/freshness + typed recovery + LoopGuard
 -> Track M implementation becomes safe/useful
```

Revised progression:

```text
M0  object model + fixture contracts
    HarnessSession / Conversation / DelegationTask / MessageDelivery /
    ExecutionEnvironment

M1  read-only Session Observer
    discover/list/read/status
    native-host first, Browser Companion fallback

M2  Manager -> ONE EXISTING Worker
    verified delivery
    stable delegation_id
    response correlation
    delivered/held/refused/unknown semantics

M3  WorkingState + HandoffPack integration
    event/idle subscription
    cancel/recovery/reconciliation

M4  Session Lifecycle
    create / fork / rename / archive
    operation_id + idempotency + unknown-outcome reconciliation

M5  Manager-created Worker E2E
    WorkerLease / ownership
    minimum child capability profile
    cleanup with ownership evidence

M6  multiple Workers
    explicit DelegationTasks
    fan-out/delegation budgets
    duplicate-delegation guard
    max_spawn_depth = 1 by default

M7  Project / ExecutionEnvironment lifecycle
    separate consequence/policy/acceptance

M8  cross-harness handoff/adoption + provider matrix
    Codex / Claude / VS Code / web-chat services / future adapters
```

M7/M8 order may change if product evidence shows stronger value in cross-harness read/message support before environment creation. The invariants do not change.

---

# 21. First target E2E

The first Track M physical E2E should stay deliberately asymmetric and reuse an **existing** worker session:

```text
Manager chooses bounded subtask
 -> WorkingState/HandoffPack creates delegation_id
 -> Session Observer identifies exact existing worker
 -> Control Plane authorizes queued message
 -> adapter delivers one message
 -> fresh observation verifies exact delivery/correlation
 -> event or bounded status observation notices worker progress
 -> fresh settled worker result
 -> correlate result to delegation
 -> record evidence/result in WorkingState
 -> Manager decides next strategy
```

Only after this path is reliable should Track M create its own worker sessions.

---

# 22. Non-goals / invariants

Track M does not authorize:

- replacing ordinary ChatGPT as the current general planner;
- turning the deterministic Control Plane into an open-ended planner;
- treating `session_id` as `task_id`;
- treating message delivery as worker start/completion;
- accepting the latest worker message without delegation correlation;
- blind retry after an ambiguous mutating result;
- worker inheritance of manager lifecycle authority;
- recursive worker spawning by default;
- worker messages granting capability/permission authority;
- exposing raw cookies/tokens/session secrets;
- generic arbitrary JavaScript, shell, Python, HTTP or backend dispatch;
- treating private web APIs as the only route/security boundary;
- replaying every transcript into every worker;
- mixing project/environment lifecycle with session lifecycle;
- adding public MCP tools merely because an internal adapter exists;
- making CtxPort or any one vendor harness a required product dependency;
- treating provider brand, model, harness, session, chat, task and environment as one identity.

The project-wide rule remains authoritative:

```text
above proposes; deterministic infrastructure below decides
current observed state outranks remembered adapter/procedure/history
delivery != verified effect
transition PASS != task DONE
UNKNOWN -> zero unauthorized continuation
```

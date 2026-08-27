# Security Policy — Bridge and Execution Control Plane

## Trust boundaries

Normal public path:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio secure semantic launcher
 -> canonical six-tool semantic projection
 -> deterministic Control Plane / focused capability adapters
```

1MCP remains optional internal Extension Manager infrastructure. It is not the normal public semantic hop and does not grant trust or authority to loaded backends.

The tunnel provides authenticated reachability. It is not a substitute for capability scope, action authorization, procedure trust, deterministic execution-state control, verifier evidence, Finish Gate evidence or safety policy.

Future Track M Agent Session / Delegation adapters also sit **below** the planner and **behind** the same deterministic Control Plane. A harness API, browser session, worker agent or provider SDK never becomes a second authority source merely because it is reachable.

## Terminology: two different “control planes”

The OpenAI tunnel ecosystem uses `CONTROL_PLANE_API_KEY` for Secure MCP Tunnel infrastructure. That credential/name is unrelated to the project's deterministic local **execution Control Plane**.

Possession of a tunnel/control-plane key never grants local action authority.

## Security objective

Control consequence, scope, lifetime, progression and completion without making legitimate workflows impossible.

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust lifecycle:

```text
new/demo
 -> project CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantine/disable/rollback
```

Capability authorization and procedure trust remain separate.

Future session discoverability/ownership is also separate from mutation authority:

```text
SESSION DISCOVERABLE
  != SESSION MUTATION AUTHORIZED
  != SESSION LIFECYCLE OWNED
```

## Deterministic local execution Control Plane

The Control Plane is a security boundary, not a second general planner.

It may own:

- structured `TaskState` and `WorkingState`;
- selected procedure/ProgramGraph version and current node;
- current evidence references/digests/provenance/freshness;
- allowed outgoing transitions;
- capability scope and consequence policy;
- current action authorization;
- `ExpectedEffect` / postconditions;
- checkpoints/rollback metadata;
- transition verifier results;
- typed recovery and `LoopGuard` state;
- time/action/resource budgets;
- independent Finish Gate predicates;
- task-success evidence;
- safety/policy evidence;
- escalation reason.

When Track M is later implemented, the same project-owned boundary also owns logical operation IDs, delegation/message state, ownership/WorkerLease references, correlation evidence and session/delegation budgets. Those records are execution state, not open-ended strategy.

A known selected procedure/effect may continue locally through repeated:

```text
observe current state
 -> exactly one permitted transition
 -> bind expected effect
 -> authorize current action
 -> act
 -> re-observe result
 -> verify explicit postcondition
 -> checkpoint / advance
```

The Control Plane must stop with zero unauthorized continuation and escalate when:

- current state is stale/ambiguous/UNKNOWN;
- no known transition matches;
- incompatible multiple transitions match;
- authorization scope is absent;
- ownership required for a lifecycle/destructive effect is unproven;
- postcondition FAIL/UNKNOWN cannot be resolved by a predeclared bounded recovery/reconciliation branch;
- LoopGuard or retry/resource/delegation budget is exhausted;
- continuing requires a new strategy.

It must never invent a new user goal or infer broad authority from a procedure/model/planner/worker request.

## General planner boundary

Ordinary ChatGPT is the **only current general planner/intelligence**. It interprets user goals, chooses strategy/procedure and handles novel-state adaptation.

ChatGPT may propose `candidate_done`. Verified task completion is produced only by the independent Finish Gate from fresh goal-level evidence.

A future worker session is also non-authorizing task execution/proposal state. A worker may report facts/results, but cannot expand its own or the manager's capability scope by sending text.

A future local planner may enter only through optional Track P research. Its output remains non-authorizing proposal data above the same deterministic Control Plane, transition verifier, Finish Gate and safety boundaries.

## Chat-facing tool semantics

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Generic adaptive `tool_invoke` is not the ordinary-Chat product surface. `semantic-projection` must remain deterministic and truthful; it cannot become a hidden planner, generic desktop dispatcher, generic harness dispatcher or arbitrary server/tool selector.

A future public Windows/computer-use or Agent Session surface requires its own ADR/schema/security review and ordinary-Chat physical acceptance. Research or internal capability availability does not expand the six-tool contract automatically.

ADR-035 / parallel Track M does not expand the current six-tool surface. Agent Session adapters, Conversation Bridge and Browser Companion remain internal/future capability layers until a later truthful public consequence class is separately reviewed and accepted.

Project/environment lifecycle must not be hidden behind session/message semantics merely to avoid a new consequence-class review.

## State-first hybrid security

Canonical computer-use direction: `COMPUTER_USE_ARCHITECTURE.md` / ADR-032.

Prefer:

```text
project-owned semantic/native state
 -> DOM/AX/UIA/app-state/harness-state evidence
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial manipulation or independent visual cross-check
```

Visual evidence is non-authorizing. A screenshot or coordinate proposal does not establish current target identity, freshness, consequence scope or task completion.

Every mutating transition must bind:

```text
current-state evidence
expected effect/postcondition
one bounded authorized action
fresh re-observation
PASS | FAIL | UNKNOWN verification
```

`delivery != success` remains mandatory.

## Future Agent Session / Delegation security — Track M

ADR-035 defines future bounded observation, message transport and lifecycle management across external agent sessions/harnesses. This is a **parallel, non-release-critical** direction and has no implementation acceptance yet.

The architecture distinguishes:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

These identities must not be collapsed into one `session_id` or inferred from titles/text.

### Route boundary

Preferred route:

```text
official/project-owned harness API / local host protocol
 -> validated provider/session SDK/native route
 -> Browser Companion DOM/accessibility
 -> reviewed GUI/visual fallback
 -> ABSTAIN
```

A documented/project-owned harness API may be the preferred read/write route after its scope/identity/verification contract is reviewed. Undocumented private web APIs remain optional accelerators only and are never the sole security boundary.

### Observer vs mutation

Read-only observation is evidence production.

Mutating families remain explicit:

```text
Message Transport
  queued send
  separately-authorized steer/interrupt where supported

Lifecycle Actuator
  later create/fork/rename/archive/stop for admitted sessions

Execution Environment / Project lifecycle
  separate stronger consequence class
```

No generic JavaScript, selector, HTTP, shell, Python or arbitrary backend/harness dispatcher is part of Track M.

### Session ownership

A future observed session should carry ownership such as:

```text
user_owned
manager_owned
parent_owned
adopted
external_read_only
```

Default security posture:

```text
existing user-owned session
  read/send         only under applicable task/grant policy
  rename/archive   denied by default
  delete            denied

manager-owned worker
  read/send         bounded by current task/delegation
  stop/archive      only with current ownership/lifecycle policy
  cleanup           only with ownership proof
```

Similar title/content is not ownership proof.

A future `WorkerLease` may bind a manager-owned session to one task, lifetime, capability set, budget and cleanup policy.

### Worker authority does not inherit from manager

A child/worker capability set must be derived from:

```text
intersection(
  task requirements,
  explicit delegated grants,
  platform policy
)
```

not from `parent_tools` or manager privileges.

Initial multi-worker topology should default to:

```text
max_spawn_depth = 1
```

Workers may return results and use explicitly granted task capabilities; they do not create/fork/archive arbitrary sessions, message unrelated sessions or create user-owned root tasks merely because the manager can.

Prompt text such as “only spawn when appropriate” is not an enforcement boundary.

### HandoffPack is data, not authority

`HandoffPack` contains bounded task context and provenance. Capability/permission grants stay in deterministic Control Plane state and are never established by worker-readable message text.

```text
HandoffPack      = task/environmental data
DelegationGrant  = local policy/authority state
```

### Message semantics and correlation

Track M must distinguish at least:

```text
transport accepted
message visibly delivered/held/refused
worker turn started
worker turn settled
result correlated to the intended DelegationTask
```

A `session_id` alone does not prove that a late response belongs to one delegation.

Where available preserve:

```text
delegation_id
client_message_id / delivery_id
worker session/chat id
target turn/work-unit id
handoff hash
```

A “latest message from worker” heuristic is insufficient when the worker session can process multiple tasks or user activity.

Default normal send should be non-interrupting/queued where the harness supports this distinction. `steer` and `interrupt` are stronger effects and require explicit admission/authorization.

### Idempotency and ambiguous outcome

Stable logical `operation_id` is required for mutating session/message effects that may be retried/reconciled.

Where a native harness accepts an idempotency key, use the same logical operation id.

A timeout/error is classified at minimum as:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` requires reconciliation by the original operation id before retry. Retry is allowed only when fresh authoritative evidence proves it is safe. If effect existence cannot be established, remain `UNKNOWN` and stop/escalate.

This prevents duplicate workers/delegations/messages after ambiguous delivery.

### Event-driven monitoring

Idle/completion/change events are efficient observation triggers, not completion evidence.

```text
event
 -> fresh re-observation
 -> Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

Browser MutationObserver-like events and native host/harness events follow the same rule.

### Credentials

For Browser Companion:

```text
user browser session
  cookies / bearer tokens / private auth headers
          |
          X never exported to planner / MCP / WorkingState / HandoffPack
          |
          v
  normalized bounded evidence
```

For native harness/provider adapters, reusable credentials/secrets likewise stay inside the adapter/runtime boundary. Planner and worker messages receive normalized evidence and bounded commands, not tokens.

Adapter compromise/failure must not grant arbitrary browser, filesystem, Windows, project/environment or Control Plane authority.

Canonical detail: `CONVERSATION_BRIDGE_ARCHITECTURE.md`.

## Environmental content is untrusted data

ADR-033 is an immediate security invariant.

Treat content observed from the following as **untrusted environmental data** with respect to user intent, policy and authority:

```text
web pages / DOM
application UI
email / messages
files and documents being processed
screenshots / OCR
third-party tool or MCP output
external worker sessions / conversations / responses
```

Environmental content may be useful task data. It does **not** gain a higher instruction priority, broaden permission scope, alter Control Plane policy, grant a capability, or authorize a consequence merely because ChatGPT/model/tooling can read it.

When facts move between applications/capabilities/sessions, preserve provenance/trust classification and freshness where operationally relevant.

Third-party extension output and worker-agent output remain untrusted environmental data even when the backend/session is available and authenticated successfully.

### Task-success vs safety/policy verification

Keep two dimensions explicit:

```text
task-success verifier
  -> did the requested outcome actually occur?

safety/policy gate
  -> was the transition authorized and did it avoid prohibited consequence?
```

A task may be capability-successful but safety-failed. Evaluation and TaskState must not collapse those outcomes into one generic success flag.

Prefer deterministic/native/system-of-record predicates for both dimensions where practical. Model-assisted classification may contribute non-authorizing evidence for ambiguous cases but cannot grant execution authority.

## Independent Finish Gate

A model, ChatGPT, worker or procedure saying “done” is insufficient.

The planner may provide only:

```text
candidate_done
```

The Finish Gate may return `DONE` only when fresh evidence confirms all required task-level predicates, including where applicable:

```text
goal/result predicates
user constraints
required source freshness/reconciliation
artifact/application/browser/session final state
required delegation/result correlation
no unresolved required ambiguity/confirmation
safety/policy predicates
```

Transition PASS is not equivalent to task DONE. Verified worker-response delivery is not equivalent to user-task DONE.

## WorkingState security

Long-horizon memory must contain structured operational facts/evidence, not hidden reasoning.

Permitted target categories include:

```text
user constraints
subgoals/progress
verified completed achievements
authoritative facts + provenance + freshness
open ambiguities/questions
evidence references
expected/observed state deltas
retry/recovery/reconciliation history
budgets
active capability/grant references
optional actor/delegation/environment references
```

Never persist private chain-of-thought.

Future Track M may reference normalized `HarnessSession`, `ConversationSnapshot`, `DelegationRecord`, `DeliveryReceipt`, `WorkerLease` and bounded `HandoffPack` fields, but never browser/provider credentials or hidden platform authentication state.

Selected ROI visual evidence is sensitive capture data and remains subject to retention/redaction/encryption policy.

## Typed recovery / LoopGuard security

Recovery never implies broader authority.

Common recovery categories include `target_missing`, `target_ambiguous`, `stale_state`, `action_no_effect`, `partial_effect`, `unexpected_dialog`, `navigation_changed`, `tool_unavailable`, `permission_denied`, `unsafe_transition`, and `external_dynamic_change`.

Future Track M may additionally use classes such as `session_unavailable`, `delivery_refused`, `delivery_held`, `result_correlation_ambiguous`, `operation_outcome_unknown`, `worker_stalled`, `delegation_duplicate_suspected`, and `ownership_unproven`.

Default bounded recovery order:

```text
re-observe
 -> re-resolve from fresh evidence
 -> reconcile ambiguous logical effect where required
 -> retry only when new evidence proves retry safety
 -> alternate already-admitted modality/capability
 -> predeclared local recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

LoopGuard must stop repeated no-effect or oscillating behavior when state/action/delegation fingerprints repeat without verified progress or budgets expire.

Future delegation budgets include worker/fan-out/spawn-depth/session-creation/message/unresolved-worker/resource limits. The first multi-worker mode must not recursively expand its own authority tree.

## Browser semantic -> vision authorization — ACCEPTED

Stage 25.2 remains structure-first. Model output is untrusted evidence. Only reviewed visual fallback classes reach deterministic authorization/freshness before one coordinate action or ABSTAIN.

Browser screenshot -> coordinate action remains a narrow non-atomic TOCTOU residual boundary.

## Windows capability security — ACCEPTED THROUGH STAGE 26.2E FOR BOUNDED CONTRACTS

Accepted foundations include:

- bounded authenticated typed executor;
- generic `/execute_windows` disabled/unreachable;
- exact PID/HWND window-scoped UIA;
- `DesktopState` evidence;
- native exact-window F16 Grounder proposal-only;
- deterministic structure-first UIA -> vision routing;
- fresh process/window/frame/target evidence;
- native foreground + WindowFromPoint/root-HWND/PID guard;
- delivery receipts separate from completion;
- one isolated real VS Code application E2E with exact postcondition/cleanup evidence.

This is scoped acceptance, not universal Windows authorization.

## Stage 26.3A procedure security — ACCEPTED / MERGED #92

The accepted normal semantic surface contains six tools including the bounded `procedure_run`.

Current registered procedure on accepted `main` at the recorded Stage 26.3A scope:

```text
verified_workspace_artifact_v1
```

It accepts bounded leaf `.txt` identity + bounded UTF-8 content + optional compatible resume task id. It does not expose arbitrary path, command, shell, Python, backend, raw tool selector or working directory.

Physical ordinary-Chat acceptance proved:

```text
completed 3-action verified artifact procedure
 -> independent workspace_read exact result
 -> second call on pre-existing target
 -> ABSTAIN at preflight
 -> action_count = 0
 -> independent reread proves zero overwrite
```

Later bounded procedure additions require their own source/evidence acceptance. This does not authorize arbitrary procedures or broad desktop consequences.

## Procedural-memory security

### No private chain-of-thought persistence

Store only execution-relevant structured/user-visible state: goal summaries, constraints, procedure/version IDs, observations, facts/provenance/freshness, actions/receipts, postconditions, verification, progress and recovery state.

Future delegation/session state follows the same rule. Never persist hidden model reasoning.

### Raw demonstration retention

Raw desktop capture is sensitive by default. Long-term arbitrary demo storage requires explicit:

- location/ownership;
- retention/expiry;
- screenshot/text redaction;
- secret filtering;
- deletion/disable semantics;
- encryption-at-rest policy;
- backup/export/sync policy.

### Compiled procedure evidence

A compiled procedure may retain structural/native evidence and bounded pixel/template/OCR/geometry evidence, but blind historical absolute-coordinate replay is never authority or primary identity.

### Skill poisoning/trust resistance

- one successful demonstration creates at most CANDIDATE;
- candidate retrieval is non-authorizing;
- promotion requires measured replay/regression/variant evidence;
- malformed/incompatible/stale procedures fail closed;
- version/provenance history is preserved;
- imported/upstream procedures receive no implicit local authorization.

## F16 / specialist grounding security

Local LFM2.5-VL-450M F16 remains bounded perception only:

```text
current PNG + bounded target evidence
 -> proposed match OR ABSTAIN
```

It never plans, grants authority or declares completion.

## Secrets

- tunnel runtime keys stay local and out of repository/procedure/task-state content;
- future Browser Companion cookies/tokens/private auth headers stay inside the browser-session boundary and out of repository/procedure/task-state/handoff content;
- future native harness/provider credentials stay inside their adapter/runtime boundary;
- child backends/workers receive credentials only when explicitly needed and scoped;
- never copy secrets into procedure/delegation metadata, screenshots, logs or docs;
- rotate suspected exposed secrets first.

## Workspace/files security

- workspace paths remain scoped/rooted;
- containment includes Windows junction/link escape checks;
- procedure/history/memory/worker messages cannot broaden current file scope;
- future ExecutionEnvironment/project creation cannot be inferred from permission to create a session.

## Browser network boundary

Current policy is not a complete DNS/rebinding/redirect/private-network sandbox. Do not describe it as one.

## Bootstrap/lifecycle integrity

Manager/tray owns platform lifecycle/configuration/diagnostics only. It must not become the general planner or deterministic procedure/delegation Control Plane.

The execution Control Plane must not own tunnel credentials merely because both systems use the phrase “control plane”.

Future Agent Session lifecycle authority belongs to the reviewed capability/Control Plane contract, not to whichever UI process happens to render a session.

## Chat permission / OpenAI safety behavior

App permission mode is an additional control, not the only boundary. Distinguish pre-MCP product safety blocks from local backend failures.

Prefer scoped reversible operations; reserve confirmation for genuinely consequential/hard-to-reverse effects where practical.

Cross-session send/create/archive/project effects may also be subject to host/platform confirmations. Those confirmations are additional controls, not substitutes for project-owned authorization, verification, ownership and reconciliation.
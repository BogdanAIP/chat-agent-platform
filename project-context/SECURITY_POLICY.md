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

A known selected procedure may continue locally through repeated:

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
- postcondition FAIL/UNKNOWN cannot be resolved by a predeclared bounded recovery branch;
- LoopGuard or retry/resource budget is exhausted;
- continuing requires a new strategy.

It must never invent a new user goal or infer broad authority from a procedure/model/planner request.

## General planner boundary

Ordinary ChatGPT is the **only current general planner/intelligence**. It interprets user goals, chooses strategy/procedure and handles novel-state adaptation.

ChatGPT may propose `candidate_done`. Verified task completion is produced only by the independent Finish Gate from fresh goal-level evidence.

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

Generic adaptive `tool_invoke` is not the ordinary-Chat product surface. `semantic-projection` must remain deterministic and truthful; it cannot become a hidden planner, generic desktop dispatcher or arbitrary server/tool selector.

A future public Windows/computer-use surface requires its own ADR/schema/security review and ordinary-Chat physical acceptance. Research or internal capability availability does not expand the six-tool contract automatically.

ADR-035 / parallel Track M also does not expand the current six-tool surface. A Conversation Bridge or Browser Companion may remain an internal capability/app-adapter layer unless a later truthful public consequence class is separately reviewed and accepted.

## State-first hybrid computer-use security

Canonical direction: `COMPUTER_USE_ARCHITECTURE.md` / ADR-032.

Prefer:

```text
project-owned semantic/native state
 -> DOM/AX/UIA/app-state evidence
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

## Future Conversation Bridge / Browser Companion security — Track M

ADR-035 defines a future bounded bridge to the user's already-authenticated AI-chat sessions. This is a **parallel, non-release-critical** direction and has no implementation acceptance yet.

The accepted Browser backend is isolated/headless. A future project-owned Browser Companion may run inside the user's normal authenticated browser only for explicitly reviewed conversation/session capabilities.

Required boundary:

```text
user browser session
  cookies / bearer tokens / private auth headers
          |
          X  never exported to planner / MCP payload / WorkingState
          |
          v
  normalized ConversationSnapshot / bounded event
          |
          v
  deterministic Control Plane verification
```

Rules:

- browser/session credentials stay inside the Browser Companion boundary;
- no cookie, bearer token, organization/session secret or private auth header is persisted in `TaskState`, `WorkingState`, `HandoffPack`, procedure memory, logs or ordinary-Chat messages;
- `ConversationObserver` is read-only evidence production; observation never grants authority;
- `ConversationActuator` remains narrowly bounded, initially to reviewed operations such as `activate_session` and `submit_message` rather than arbitrary JavaScript, selector, HTTP or browser dispatch;
- `submit_message` is a mutating external consequence and must pass the normal `observe -> ExpectedEffect -> authorize -> act -> re-observe -> PASS|FAIL|UNKNOWN` path;
- platform-native/private conversation APIs are optional read fast paths only, never the sole security boundary or authority source;
- adapter/API failure must degrade to bounded structural/GUI recovery or ABSTAIN rather than encouraging credential export or generic browser control;
- a change notification such as `MutationObserver` is only an event signal; fresh re-observation verifies message identity, response state and completion;
- compromise/failure of one platform adapter must not grant arbitrary browser, filesystem, Windows or Control Plane authority;
- raw full-transcript replay is not required for handoff; use bounded `HandoffPack` context and preserve source/provenance.

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
external worker-chat conversations / responses
```

Environmental content may be useful task data. It does **not** gain a higher instruction priority, broaden permission scope, alter Control Plane policy, grant a capability, or authorize a consequence merely because ChatGPT/model/tooling can read it.

When facts move between applications/capabilities/sessions, preserve provenance/trust classification and freshness where operationally relevant.

Third-party extension output and worker-chat output remain untrusted environmental data even when the backend/session is available and authenticated successfully.

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

A model, ChatGPT, procedure or future planner saying “done” is insufficient.

The planner may provide only:

```text
candidate_done
```

The Finish Gate may return `DONE` only when fresh evidence confirms all required task-level predicates, including where applicable:

```text
goal/result predicates
user constraints
required source freshness/reconciliation
artifact/application/browser final state
no unresolved required ambiguity/confirmation
safety/policy predicates
```

Transition PASS is not equivalent to task DONE.

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
retry/recovery history
budgets
```

Never persist private chain-of-thought.

Selected ROI visual evidence is sensitive capture data and remains subject to retention/redaction/encryption policy.

Future Track M may reference normalized `ConversationSnapshot` evidence and bounded `HandoffPack` fields from WorkingState, but never browser credentials or hidden platform authentication state.

## Typed recovery / LoopGuard security

Recovery never implies broader authority.

Common recovery categories include `target_missing`, `target_ambiguous`, `stale_state`, `action_no_effect`, `partial_effect`, `unexpected_dialog`, `navigation_changed`, `tool_unavailable`, `permission_denied`, `unsafe_transition`, and `external_dynamic_change`.

Default bounded recovery order:

```text
re-observe
 -> re-resolve from fresh evidence
 -> retry only when new evidence justifies it
 -> alternate already-admitted modality/capability
 -> predeclared local recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

LoopGuard must stop repeated no-effect or oscillating behavior when state/action fingerprints repeat without verified progress or budgets expire.

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

Current registered procedure:

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

This does not authorize arbitrary procedures or broad desktop consequences.

## Procedural-memory security

### No private chain-of-thought persistence

Store only execution-relevant structured/user-visible state: goal summaries, constraints, procedure/version IDs, observations, facts/provenance/freshness, actions/receipts, postconditions, verification, progress and recovery state.

Never persist hidden model reasoning.

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
- child backends receive credentials only when explicitly needed;
- never copy secrets into procedure metadata, screenshots, logs or docs;
- rotate suspected exposed secrets first.

## Workspace/files security

- workspace paths remain scoped/rooted;
- containment includes Windows junction/link escape checks;
- procedure/history/memory cannot broaden current file scope.

## Browser network boundary

Current policy is not a complete DNS/rebinding/redirect/private-network sandbox. Do not describe it as one.

## Bootstrap/lifecycle integrity

Manager/tray owns lifecycle/configuration/diagnostics only. It must not become the general planner or deterministic procedure Control Plane.

The execution Control Plane must not own tunnel credentials merely because both systems use the phrase “control plane”.

## Chat permission / OpenAI safety behavior

App permission mode is an additional control, not the only boundary. Distinguish pre-MCP product safety blocks from local backend failures.

Prefer scoped reversible operations; reserve confirmation for genuinely consequential/hard-to-reverse effects where practical.

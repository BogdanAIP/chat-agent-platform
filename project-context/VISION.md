# Vision

Let ordinary ChatGPT use the user's own Windows computer as a modular professional capability surface without requiring a custom cloud backend or a competing current general AI planner.

The product stays ChatGPT-first while becoming substantially more autonomous in execution:

```text
ordinary ChatGPT
  = current general reasoning
  + task planning / strategy
  + procedure selection
  + adaptation to novel state
  + future bounded work delegation

local companion
  = scoped Files / Browser / Windows capabilities
  + future Agent Session capability
  + semantic/native observation
  + selective specialist perception
  + deterministic execution Control Plane
  + TaskState / WorkingState
  + authorization / ExpectedEffect verification
  + checkpoints / typed recovery / LoopGuard / budgets
  + independent Finish Gate
  + safety/policy gate
  + verified procedural memory
```

The key distinction is **general planning vs deterministic execution control**.

The local Control Plane may continue an already-selected known procedure/effect through multiple independently authorized and verified transitions without asking ChatGPT after every low-level action. When live state is novel, ambiguous, stale, incompatible or requires new strategy, it stops and escalates to ChatGPT.

Canonical contracts:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`
- `CONVERSATION_BRIDGE_ARCHITECTURE.md` for future Track M Agent Sessions / Delegation

Track M does not change the current planner boundary or release-critical sequence.

## Replaceable local foundation

The bridge should remain boring and replaceable where possible:

- official Secure MCP Tunnel;
- small truthful Chat-facing semantic contract;
- replaceable focused backends/adapters;
- task-driven component/model activation;
- qualified upstream procedural components;
- project-owned deterministic state/policy/verification seams only where product safety/integration requires them.

Capability growth must not become plugin/tool explosion or permanent process growth.

Future agent-session breadth should likewise come primarily from replaceable harness/provider adapters, not one duplicated orchestration backend per vendor.

## Accepted public capability direction

The accepted current ordinary-Chat surface is exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Six is not an eternal maximum. A future Windows/computer-use or Agent Session public consequence class requires its own truthful ADR/schema/security/physical ordinary-Chat gate. Do not hide native consequences behind web semantics, generic dispatch, shell/Python, raw backend catalogs or generic harness CRUD.

Track M does not add a current public tool merely because an internal session adapter, Conversation Bridge or Browser Companion exists.

## State-first hybrid direction

The project explicitly targets:

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> capability-aware bounded action
 -> fresh re-observation
 -> explicit ExpectedEffect verification
 -> typed bounded recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
 -> separate safety/policy gate
```

This extends the already accepted Browser/Windows structure-first foundations. It does not mean screenshot-only operation and does not require one universal low-level agent runtime.

For future Agent Sessions the same rule becomes:

```text
official/project-owned harness API / local host protocol
 -> validated provider/session native route
 -> Browser Companion / DOM/accessibility
 -> reviewed GUI/visual fallback
 -> ABSTAIN
```

### Observation and grounding

Prefer DOM/accessibility/UIA/app-native/harness-native state where reliable. Use screenshots/ROI for spatial/visual-only or structural-miss cases. Grounding should preserve identity/source/frame/confidence/ambiguity evidence rather than return coordinates alone where stronger identity exists.

Track M additionally preserves session/chat/delegation/message/environment identities separately rather than resolving work from titles or “latest message” heuristics.

### Completion

Planner/procedure/worker confidence is not completion. The planner may propose `candidate_done`; fresh goal-level predicates determine `DONE` through an independent Finish Gate.

Cross-session message delivery is likewise not worker completion, and worker completion is not automatically user-task completion.

### Recovery

Long tasks need typed bounded recovery and no-effect/oscillation detection rather than repeated blind retries.

Mutating operations whose outcome becomes ambiguous after timeout/restart require stable logical operation identity and reconciliation before retry. This principle is useful in the core Control Plane and later prevents duplicate session/message/delegation effects in Track M.

### Environmental content

Pages/DOM, UI, email/messages, documents/files, screenshots/OCR, third-party tool/MCP output and future external worker-session responses are task data, not authority over user intent, permission scope or Control Plane policy. Task-success and safety/policy verification remain separate.

## User-teachable direction

Successful work or a human demonstration should become a versioned **candidate** procedure, not a macro with automatic authority.

```text
successful work / human demo
 -> structured trajectory
 -> subtask goals + verifier criteria
 -> ProgramGraph / candidate procedure
 -> replay/regression/variant evidence
 -> trusted reusable procedure
 -> future ChatGPT task
 -> live state re-resolution
 -> independently authorized + verified transitions
```

Historical coordinates/action sequences remain advisory evidence. Current state is authoritative.

## Windows desktop direction

The Windows desktop foundation is accepted through Stage 26.2E for scoped contracts: production runtime, DesktopState, native Grounder, structure-first UIA -> vision routing and one isolated VS Code real-app E2E.

Stage 26.3A then physically accepted the first ordinary-Chat multi-transition procedure runtime and six-tool surface. The Windows Verification Kernel path has subsequently progressed through PR #114, with representative application L3 continuing separately.

Next work deliberately improves long-horizon correctness before broadening GUI authority:

```text
26.3B Verification Kernel + Finish Gate / representative evidence
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-app evidence
 -> 26.4 human demonstration -> verified candidate skill
 -> 26.5 hybrid computer-use integration
```

## Memory direction

Do not replay every screenshot/action forever. WorkingState stores structured operational facts, constraints, provenance/freshness, progress, evidence references and recovery/budget state.

Stage 26.3C should not hard-code `one task -> one procedure -> one executor`. It may reserve optional planner-neutral `actor_ref`, `delegation_ref` and `execution_environment_ref` seams so future Track M can attach verified external-worker work without redesigning the authority model.

Verified episodic trajectories/procedures and selected historical session evidence may later be retrieved under applicability/trust rules. Learned memory selection is optional later work after enough verified traces exist.

Private chain-of-thought is never task/procedure/delegation memory.

## Agent Sessions / external worker direction — Track M

Future Track M is a **parallel** work-distribution layer, not a replacement for the current manager ChatGPT and not a second local planner.

The architecture distinguishes five first-class identities:

```text
HarnessSession      durable agent session/host unit
Conversation/Chat   message-history unit inside a session
DelegationTask      one explicit manager-assigned work unit
MessageDelivery     one concrete cross-session message effect
ExecutionEnvironment workspace/worktree/project/host environment
```

This separation is fundamental:

```text
session identity != task identity
message delivery != delegation completion
session lifecycle != project/environment lifecycle
```

### Target architecture

```text
ordinary ChatGPT Manager
 -> structured subgoal / HandoffPack
 -> deterministic Control Plane
 -> Agent Session capability
      -> Session Observer
      -> Message Transport
      -> later Lifecycle Actuator
 -> Adapter Registry
      -> official/project-owned harness/host API
      -> provider/session native adapter
      -> Browser Companion / GenericChatAdapter
      -> reviewed GUI fallback
 -> selected Worker session
 -> fresh verified delivery/result correlation
 -> evidence/result back into WorkingState
 -> Manager decides next strategy
```

Browser Companion remains important because ordinary web-chat sessions may exist only in the user's authenticated browser, while the accepted general Browser backend is isolated/headless. But Browser Companion is now one Agent Session adapter route, not the architecture root of Track M.

### Handoff and authority

Task transfer uses bounded `HandoffPack` rather than replaying entire transcripts.

```text
HandoffPack      = task/environmental data
DelegationGrant  = deterministic Control Plane authority
```

Worker-readable text cannot grant capability authority.

### Ownership and child authority

Session discoverability is not lifecycle authority. Future normalized ownership includes user-owned, manager-owned, parent-owned, adopted and read-only external states.

Workers do not automatically inherit manager session/harness lifecycle tools. Initial multi-worker topology is deliberately shallow:

```text
Manager
  -> Worker A
  -> Worker B
  -> Worker C

max_spawn_depth = 1
```

Recursive delegation is a later capability only after measured need and explicit cycle/budget/authority controls.

### Delivery and idempotency

Track M distinguishes transport accepted, delivered/held/refused/unknown, worker work-unit state and final delegation correlation.

Mutating session/message operations use stable logical operation IDs and native idempotency keys where available. Ambiguous outcomes are reconciled before retry to prevent duplicate workers/messages/delegations.

Event/idle/completion notifications trigger fresh observation; they are never proof of semantic completion by themselves.

### Project/environment lifecycle

A harness may expose project/workspace/worktree lifecycle. This is a separate stronger consequence class, not generic session CRUD. Initial worker creation binds only to an already-authorized execution environment.

### Track M progression

```text
M0 object model + fixture contracts
 -> M1 read-only Session Observer
 -> M2 Manager -> one EXISTING Worker verified handoff/correlation
 -> M3 WorkingState/HandoffPack + event monitoring/recovery
 -> M4 session create/fork/rename/archive + idempotency/reconciliation
 -> M5 manager-created Worker E2E + ownership/WorkerLease/cleanup
 -> M6 multiple workers + explicit DelegationTasks + bounded fan-out; no nested spawn by default
 -> M7 separate Project / ExecutionEnvironment lifecycle
 -> M8 cross-harness adoption/handoff + provider matrix
```

Multiple workers therefore come only after identity, delivery, correlation, verification and recovery are physically proven for simpler paths.

CtxPort remains an MIT implementation/reference source for browser conversation adapter mechanisms, not a required product dependency. Codex/Claude/VS Code/A2A/MCP patterns are architecture evidence, not dependencies.

## Future local planner direction

A local general planner is explicitly retained as optional future **Track P — Local Planner / Offline Autonomy** after verified long-horizon state data and measured need exist.

Potential reasons include offline operation, planning round-trip latency, parallel/multi-machine work or deployment/privacy constraints.

```text
shadow/proposal-only
 -> bounded subtask planner
 -> optional local general-planner mode
```

Even then, planner output never bypasses deterministic capability policy, transition verification, Finish Gate or safety gates.

Track P and Track M are distinct: Track P concerns who performs open-ended planning; Track M concerns verified session/task/message transport and delegation among external workers. Track M does not require a local general planner.

## Product-ready direction

A stable product requires:

- broader real-app evidence beyond one VS Code path;
- reusable Verification Kernel and independent Finish Gate;
- structured WorkingState + LoopGuard / bounded recovery/reconciliation;
- verified candidate-first human-demo transfer;
- hybrid computer-use integration without raw-tool explosion;
- environmental-injection/safety evaluation;
- normal installation/update/repair/rollback/restart recovery;
- clean-user E2E;
- release-grade dependency/model/procedure artifact reproducibility;
- explicit privacy/security boundaries for task state, procedural memory and desktop capture;
- optional future planner and Agent Session / multi-worker research kept separate from release-critical safety evidence.

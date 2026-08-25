# Vision

Let ordinary ChatGPT use the user's own Windows computer as a modular professional capability surface without requiring a custom cloud backend or a competing current general AI planner.

The product stays ChatGPT-first while becoming substantially more autonomous in execution:

```text
ordinary ChatGPT
  = current general reasoning
  + task planning / strategy
  + procedure selection
  + adaptation to novel state

local companion
  = scoped Files / Browser / Windows capabilities
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

The local Control Plane may continue an already-selected known procedure through multiple independently authorized and verified transitions without asking ChatGPT after every low-level action. When live state is novel, ambiguous, stale, incompatible or requires new strategy, it stops and escalates to ChatGPT.

Canonical contracts:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`

Future parallel multi-chat/session transport is Track M and is defined by ADR-035 / `CONVERSATION_BRIDGE_ARCHITECTURE.md`. It does not change the current planner boundary or release-critical sequence.

## Replaceable local foundation

The bridge should remain boring and replaceable where possible:

- official Secure MCP Tunnel;
- small truthful Chat-facing semantic contract;
- replaceable focused backends;
- task-driven component/model activation;
- qualified upstream procedural components;
- project-owned deterministic state/policy/verification seams only where product safety/integration requires them.

Capability growth must not become plugin/tool explosion or permanent process growth.

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

Six is not an eternal maximum. A future Windows/computer-use public consequence class requires its own truthful ADR/schema/security/physical ordinary-Chat gate. Do not hide native consequences behind web semantics, generic dispatch, shell/Python or raw backend catalogs.

Track M does not add a current public tool merely because a conversation adapter or Browser Companion exists.

## State-first hybrid computer-use direction

The project now explicitly targets:

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

### Observation and grounding

Prefer DOM/accessibility/UIA/app-native state where reliable. Use screenshots/ROI for spatial/visual-only or structural-miss cases. Grounding should preserve identity/source/frame/confidence/ambiguity evidence rather than return coordinates alone where stronger identity exists.

### Completion

Planner/procedure confidence is not completion. The planner may propose `candidate_done`; fresh goal-level predicates determine `DONE` through an independent Finish Gate.

### Recovery

Long tasks need typed bounded recovery and no-effect/oscillation detection rather than repeated blind retries.

### Environmental content

Pages/DOM, UI, email/messages, documents/files, screenshots/OCR, third-party tool/MCP output and future external worker-chat responses are task data, not authority over user intent, permission scope or Control Plane policy. Task-success and safety/policy verification remain separate.

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

Stage 26.3A then physically accepted the first ordinary-Chat multi-transition procedure runtime and six-tool surface.

Next work deliberately improves long-horizon correctness before broadening GUI authority:

```text
26.3B Verification Kernel + Finish Gate
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 human demonstration -> verified candidate skill
 -> 26.5 hybrid computer-use integration
```

## Memory direction

Do not replay every screenshot/action forever. WorkingState stores structured operational facts, constraints, provenance/freshness, progress, evidence references and recovery/budget state.

Verified episodic trajectories/procedures may later be retrieved under applicability/trust rules. Learned memory selection is optional later work after enough verified traces exist.

Private chain-of-thought is never task/procedure memory.

## Multi-chat / external worker direction — Track M

Future multi-chat is a **parallel** work-distribution layer, not a replacement for the current manager ChatGPT and not a second local planner.

The first target is deliberately small:

```text
ordinary ChatGPT Manager
 -> bounded HandoffPack from WorkingState
 -> deterministic Control Plane
 -> Conversation Bridge
 -> project-owned Browser Companion in the user's authenticated browser
 -> one selected ChatGPT Worker conversation
 -> fresh verified worker response
 -> result/evidence back into WorkingState
 -> Manager decides next strategy
```

The Browser Companion is needed because the accepted Browser backend is isolated/headless and is not the user's already-authenticated browser session.

Conversation state should be normalized into `ConversationSnapshot` with stable platform/session/conversation/message identity, active branch, content hashes, generation state and provenance/freshness. Platform-private APIs may be optional read fast paths, with DOM/accessibility and then selected GUI/visual fallback when needed.

Task transfer should use `HandoffPack` rather than replaying entire transcripts. Browser cookies/tokens/private auth headers stay inside the Browser Companion boundary and are never planner, MCP or WorkingState data.

Multiple workers come only after one Manager -> one Worker identity, delivery, response freshness, verification and recovery are physically proven. CtxPort is an MIT implementation/reference source for selected adapter mechanisms, not a required product dependency.

## Future local planner direction

A local general planner is explicitly retained as optional future **Track P — Local Planner / Offline Autonomy** after verified long-horizon state data and measured need exist.

Potential reasons include offline operation, planning round-trip latency, parallel/multi-machine work or deployment/privacy constraints.

```text
shadow/proposal-only
 -> bounded subtask planner
 -> optional local general-planner mode
```

Even then, planner output never bypasses deterministic capability policy, transition verification, Finish Gate or safety gates.

Track P and Track M are distinct: Track P concerns who performs open-ended planning; Track M concerns verified transport/state handoff among external chat sessions. Track M does not require a local general planner.

## Product-ready direction

A stable product requires:

- broader real-app evidence beyond one VS Code path;
- reusable Verification Kernel and independent Finish Gate;
- structured WorkingState + LoopGuard / bounded recovery;
- verified candidate-first human-demo transfer;
- hybrid computer-use integration without raw-tool explosion;
- environmental-injection/safety evaluation;
- normal installation/update/repair/rollback/restart recovery;
- clean-user E2E;
- release-grade dependency/model/procedure artifact reproducibility;
- explicit privacy/security boundaries for task state, procedural memory and desktop capture;
- optional future planner and multi-chat research kept separate from release-critical safety evidence.

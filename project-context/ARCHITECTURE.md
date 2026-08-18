# Architecture

## Product boundary

`chat-agent-platform` is a thin Windows companion that lets ordinary ChatGPT use scoped local capabilities. Ordinary ChatGPT remains the only planner/orchestrator. Local components may provide deterministic execution, bounded specialist inference and non-agentic procedural memory; they must not become a second agent brain.

Current accepted `main` after Stage 25.2:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused task-active backends/adapters
```

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments and aggregation where useful. The normal public `semantic` path is direct stdio.

## Capability projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic operation to one reviewed backend action or a small bounded deterministic sequence. It must not:

- decide user goals;
- execute arbitrary hidden plans;
- become procedural memory or a workflow planner;
- expose generic `tool_invoke` behavior under another name;
- dynamically route to arbitrary unreviewed models/endpoints;
- become a general process supervisor/model manager;
- hide new desktop/workflow consequence classes behind misleading existing schemas merely to avoid adding a truthful capability later.

## Capability lifecycle

Use independent capability states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

A backend/model may exist on disk without running. Start it only when a task needs it. Concurrent backends are allowed when a real workflow requires them, but idle heavyweight processes should not remain loaded without measured need.

Procedural-memory trust is separate from capability lifecycle:

```text
CANDIDATE -> VERIFIED -> PROMOTED
     |          |          |
     +-------> STALE / DISABLED
```

A stored skill being promoted does not itself authorize every action it mentions; normal capability authorization still applies at execution time.

## Browser grounding architecture — Stage 25.2 accepted

Deterministic semantic DOM/accessibility grounding is preferred whenever reliable structure exists.

Accepted Stage 25.2 behavior:

```text
web_interact(click)
  -> fresh accessibility snapshot
       -> exact enabled button
            -> act semantically; VLM stays stopped
       -> same-name buttons with exactly one enabled + disabled alternatives
            -> act semantically; VLM stays stopped
       -> disabled/non-button/unresolved ambiguity
            -> ABSTAIN; VLM stays stopped
       -> zero exact candidates
            -> SAME Playwright page/session capture
            -> reviewed local F16 text-labeled grounder
            -> deterministic authorization
            -> exact freshness proof
            -> one coordinate action OR ABSTAIN
```

This supersedes the earlier Stage 25.1 design wording that treated semantic ambiguity as a possible vision-escalation case. **Current accepted policy does not visually escalate unresolved semantic ambiguity.** Generic semantic click failures also do not invoke vision.

### Same-session invariants

Automatic visual browser interaction is forbidden unless all applicable invariants are proven:

1. capture and action belong to the same Playwright page/session;
2. coordinate space is explicit and deterministic;
3. viewport/layout state required by the verifier is known;
4. no navigation/page replacement invalidated the capture;
5. stale/ambiguous visual evidence produces ABSTAIN;
6. action cannot silently fall back to a different page/browser instance;
7. page mutation is zero when grounding returns ABSTAIN/error.

`targetText` is the semantic/visual authorization anchor. Planner `target`, free-form `instruction` and planner-supplied `kind` cannot redirect the visual target.

## Local vision boundary

Accepted target-laptop baseline:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LiquidAI LFM2.5-VL-450M F16
projector = F16
CPU = 8 threads
ctx = 2048
```

The model is bounded perception. It never plans the user's workflow and never clicks by itself. Product code keeps runtime/model identity replaceable behind provider-neutral/focused interfaces.

Final Stage 25.2 public target gate proved semantic-first routing, one real F16 visual hit, correct ABSTAIN cases, zero false clicks/errors and deterministic runtime cleanup.

## Procedural-memory architecture — Stage 26 design

Procedural memory is a local **memory/state substrate**, not an agent.

```text
ordinary ChatGPT
  planner / task interpretation / adaptation
        |
        | bounded candidate workflow guidance
        v
procedural-memory substrate
  raw trajectory recorder
  Demo Compiler
  versioned skill store
  retrieval/ranking evidence
  workflow progress state
  completion verifier
        |
        v
accepted capability layer
```

Detailed active contract: `STAGE26_PROCEDURAL_MEMORY.md`.

### Raw evidence vs compiled skill

Never treat a recorded low-level action sequence as the reusable procedure.

```text
raw trajectory
  observations/actions/results/verification evidence
        |
        v
Demo Compiler
        |
        v
compiled skill
  purpose/applicability
  subtasks/goals
  completion criteria
  prior milestones
  recovery hints
  evidence statistics
```

Compiled skills must not contain actionable replay coordinates.

Do not persist private chain-of-thought. Procedural memory stores structured/user-visible intent summaries and operational evidence only.

### Current-state priority

```text
current observed state
  > completion criteria / current subtask goal
  > prior successful milestones
  > raw historical action sequence
```

A remembered procedure may guide exploration but cannot override contradictory current evidence.

### Completion verification

A model/Chat report that a subtask is complete is a proposal, not sufficient evidence:

```text
completion proposal
  -> native/deterministic verifier where possible
       PASS -> advance workflow pointer
       FAIL -> stay on current subtask
       UNKNOWN -> observe / ABSTAIN / user input as appropriate
```

Retrieval and workflow progress are non-authorizing. Every actual capability action still passes through its normal scope/authorization boundary.

## Windows desktop surface — explicit planned boundary

Stage 26.3 introduces a scoped Windows desktop surface. This is intentionally separate from browser Playwright and must not be forgotten.

Preferred layering:

```text
Windows task
  -> native/deterministic UI observation where available
  -> screen capture only where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse actuation
  -> post-action verification / ABSTAIN
```

Concrete local programs/capabilities are selected from real tasks and evidence when this stage is benchmarked; architecture does not preselect a fixed list.

True arbitrary human demonstration capture should be built at or after this desktop surface exists, because the current browser semantic bridge does not observe arbitrary user interaction across Windows.

## Public contract decision after desktop surface

Current five public tool names are an accepted **current contract**, not a dogmatic permanent limit.

Only after the Windows desktop surface exists, make an explicit ADR and ordinary-Chat acceptance decision between:

- preserving the existing small semantic philosophy with a few coarse truthful capabilities; or
- adding a small number of new public tool names if required for truthful semantics/safety.

Do not add a generic opaque workflow dispatcher, and do not overload current tools with unrelated desktop/workflow behavior solely to keep the count at five.

## Security boundaries

- tunnel reachability is outbound from the user machine;
- normal semantic transport is direct stdio;
- secrets live outside repository content and tunnel keys use Windows DPAPI;
- Filesystem roots and browser capability exposure remain explicitly scoped;
- raw unrestricted browser execution/network/file-upload surfaces stay out of ordinary Chat;
- local inference remains loopback/focused and does not expose arbitrary endpoint/model/prompt control;
- workspace containment accounts for Windows links/junctions;
- browser DNS/rebinding/redirect isolation remains an explicit residual boundary;
- child backends must not inherit tunnel credentials unless required;
- procedural-memory storage requires redaction/retention rules before long-term storage of screenshots/sensitive observations;
- private chain-of-thought must never be written into skills;
- stale/malformed/incompatible skills fail closed and can be disabled deterministically.

## Windows management

The public manager/tray owns lifecycle/configuration/diagnostics only. It does not become workflow memory, a planner or a desktop agent brain. Installed/source copies coordinate through one authoritative runtime owner; ambiguous/unowned shared runtime state fails closed.

## Testing direction

Stage 25.2 browser semantic→vision integration is already accepted; do not describe it as the next gate.

Stage 26 gates now focus on:

1. raw/compiled procedural schemas and redaction;
2. coordinate-free candidate skill generation;
3. verifier-controlled subtask advancement;
4. same/related changed-task adaptation without blind replay;
5. incompatible/stale skill fail-closed behavior;
6. Windows desktop observation/actuation acceptance when Stage 26.3 begins;
7. later human demonstration capture and transfer;
8. explicit post-desktop public contract decision.

Changing exported Chat actions still requires explicit Refresh/review and fresh ordinary-Chat acceptance.

## Ownership

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, focused missing-boundary adapters, procedural-memory schemas/state/verifiers, tests and project context. It does not own a generic AI gateway, registry, vault, autonomous workflow brain or general model-serving platform.

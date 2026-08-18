# Stage 26 — Procedural Memory / Demo2Workflow

Status: **ACTIVE DESIGN / NOT PRODUCT-ACCEPTED YET**

Stage 26.0 (upstream analysis + authoritative contract/context synchronization) is **DONE** through PR #78. The next implementation step is **Stage 26.1 — Procedural data foundation**.

This document is the authoritative design contract for the stage after merged Stage 25.2. It does not declare a working end-user teach-by-demonstration feature.

## Goal

Let ordinary ChatGPT reuse previously successful procedures without adding a second planner or turning local execution into blind macro replay.

```text
current user task
  -> ordinary ChatGPT remains the only planner/intelligence
  -> relevant prior procedure may be supplied as bounded guidance
  -> current observed state remains authoritative
  -> existing deterministic/semantic capabilities are preferred
  -> bounded perception is used only where needed
  -> completion is verified
  -> act / continue / ABSTAIN
```

A stored procedure is advice and evidence, not an autonomous agent and not authorization to perform an action.

## Upstream reference — Tencent/UI-Mate

Technical analysis was performed against public `Tencent/UI-Mate` main commit:

`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a` (2026-08-18).

License: Apache-2.0 for UI Mate inference-enabling code/parameters/weights, with third-party components retaining their original terms.

Relevant upstream files:

- `README.md`;
- `agents/demo_workflow.py`;
- `agents/ui_mate_agent.py`;
- `resources/example_demonstration/trajectory_captioned.json`;
- `examples/run_agent.py`.

### What the upstream implementation proves

UI-Mate separates general computer use from demonstration-guided computer use. Its README describes a demonstration as guidance rather than a script and states that the live screenshot remains authoritative.

`agents/demo_workflow.py` is a small workflow-state layer. It parses each demonstration into:

```text
WorkflowPlan
  -> Subtask
       title / intent_summary
       goal / sub_instruction
       completion_flag / subtask_complete_flag
       key_steps
```

For each step it renders:

```text
<workflow_progress>
<current_subtask>
<current_subtask_action_list>
```

The workflow pointer advances when the model reports `subtask_complete`. Recorded coordinates are not replayed by `DemoWorkflow`.

`agents/ui_mate_agent.py` layers `DemoWorkflow` over the normal GUI-agent loop. The dedicated DemoCUA checkpoint was trained to use this guidance; that learned checkpoint behavior is not required in our architecture because ordinary ChatGPT remains the workflow interpreter/planner.

The supplied `trajectory_captioned.json` is a rich raw/annotated trajectory, not the compact runtime plan. It includes observation, planner, executor, validation and grounding layers. The example demonstrates why annotations must not be trusted blindly: an early step says a click intended to open Terminal actually opened Files, while stored `step_correctness.is_correct` remains `true`.

The bundled `examples/run_agent.py` is an inference/inspection runner: it passes `--demo` into `UIMateAgent`, predicts actions against screenshots/recorded trajectories, compares/plots predicted coordinates and maintains history. It is not a complete production desktop recorder/executor.

The public repository snapshot contains inference/runtime code, examples and prepared resources. It does **not** expose a complete production recorder + raw-recording-to-`trajectory_captioned.json` compiler pipeline as a reusable public library. We therefore need our own recorder/compiler boundary.

## What we adopt

1. **Separate raw trajectory from compiled skill.**
2. **Store goals, completion criteria and useful milestones rather than replay coordinates.**
3. **Keep current state authoritative over remembered procedure.**
4. **Present only current subtask plus compact progress, not an ever-growing raw trace.**
5. **Use explicit subtask completion semantics.**
6. **Keep workflow runtime small, inspectable and non-agentic.**
7. **Treat prior successful runs as procedural evidence that can reduce exploration.**

## What we do not adopt

- no UI-Mate 27B/9B model as a second local planner;
- no mandatory dedicated CUA model for workflow interpretation;
- no model-issued raw `pyautogui` action stream as our primary safety boundary;
- no coordinate replay from demonstrations;
- no planner/model `subtask_complete` report as sufficient authorization to advance state;
- no automatic promotion of a skill after one lucky success;
- no hidden generic workflow engine inside `semantic-projection`;
- no automatic skill selection that can authorize consequential actions without ChatGPT understanding the selected procedure.

## Architectural split

```text
ordinary ChatGPT
  planner / task understanding / adaptation
        |
        | bounded procedure guidance when available
        v
procedural-memory substrate (local, non-agentic)
  raw trajectory recorder
  demo compiler
  skill store + versions
  retrieval/ranking evidence
  workflow progress state
  completion verifier
        |
        v
accepted capability layer
  current five semantic tools today
  existing focused backends/adapters
  later Windows desktop surface
```

The procedural-memory substrate must not decide the user's goal. Retrieval may rank candidate skills; selection remains non-authorizing guidance to ChatGPT.

## Raw trajectory contract

The first recorder should capture successful **Chat/tool-driven** trajectories from capabilities we already own. A raw event may contain:

- task/session identifier;
- timestamp/order;
- public semantic operation and bounded arguments after secret/path redaction;
- downstream capability class where useful;
- before/after observable state fingerprints;
- semantic vs visual execution source;
- result classification: acted / abstained / error;
- deterministic verification evidence;
- artifact references needed for debugging with an explicit retention policy.

Do **not** persist private chain-of-thought. Store only user-visible/structured intent summaries, actions, observations, results and explicit completion evidence.

Raw screenshots and sensitive text are not automatically permanent skill content. Retention/redaction must be designed before user demonstrations are stored long term.

## Compiled skill contract

A compiled skill should contain no replay coordinates and should be versioned. Proposed shape:

```text
skill_id
version
purpose
applicability / preconditions
required_capability_classes
provenance = human_demo | chat_success | imported_reference
subtasks[]
  goal
  completion_criteria[]
  prior_milestones[]
  recovery_notes[]
verification_policy
safety/consequence metadata
observed evidence
  success_count
  abstain_count
  failure_count
  last_verified
compatibility metadata
```

`prior_milestones` are hints from previous successful execution, not mandatory steps.

## Trust lifecycle

```text
CANDIDATE -> VERIFIED -> PROMOTED
     |          |          |
     +-------> STALE / DISABLED
```

A single successful trajectory may create a candidate. It must not silently become a trusted reusable skill. Promotion requires an explicit acceptance rule including successful re-application and completion verification.

Use measured operational evidence rather than invented model-confidence values as a substitute for outcomes.

## Completion semantics

ChatGPT may propose that a subtask is complete, but the local workflow pointer advances only after the applicable completion verifier returns a supported result.

```text
ChatGPT proposes completion
  -> deterministic/native verifier where possible
       PASS -> advance
       FAIL -> remain on current subtask
       UNKNOWN -> observe again / ABSTAIN / request user input as appropriate
```

For browser work, verification may use URL/state/accessibility evidence. For file work, it may use existence, path scope, type/hash/size or content predicates. Future desktop criteria should prefer native observable state where available and use vision only as bounded evidence.

## Current-state priority

```text
current observed state
  > completion criteria / current subtask goal
  > prior successful milestones
  > raw historical action sequence
```

A remembered procedure must be abandoned or adapted when it conflicts with current state.

## Stage 26 implementation order

### 26.0 — Upstream analysis and authoritative contract/context sync — DONE

Completed in PR #78, documentation milestone:

`04dccfd30eb06a82899e2771f6d53ab4c8387128`.

Result:

- official upstream pinned and technically reviewed;
- adopt/reject boundary documented;
- stale cross-chat source-of-truth files synchronized after Stage 25.2;
- procedural memory separated from planner/authorization;
- Windows desktop surface and later public-contract decision made explicit.

### 26.1 — Procedural data foundation — NEXT

Implement raw trajectory schema, redaction/retention/deletion policy, compiled skill schema, versioned local skill store and deterministic parser/validator. No public Chat tool-name changes.

### 26.2 — Demo Compiler + verifier + self-demo dogfood

Compile successful existing semantic/browser trajectories into candidate skills, then prove that the stored skill is coordinate-free, current-state-first and fail-closed. Start with Chat-executed/self-demo trajectories because the current platform can observe those actions exactly.

Acceptance must include a related-but-changed case, not only replay of the identical task. Changed data/layout must not cause stale remembered actions to override the live interface.

### 26.3 — Windows desktop surface — EXPLICIT PLANNED STAGE

**Do not lose this stage.**

Design a scoped Windows desktop capability layer using the best deterministic/native observation available first, with screen capture and bounded visual grounding only where needed. Keyboard/mouse actuation must remain reviewed and fail closed.

The specific local programs/capabilities to benchmark are **not preselected in the roadmap**. Choose them later from actual user tasks and evidence.

True human “show me once” recording of arbitrary desktop interaction belongs here or after this surface exists; the current browser semantic bridge primarily observes actions initiated through its own controlled session.

### 26.4 — Human demonstration capture + transferable skill acceptance

Record a real user demonstration through the desktop surface, compile it into a coordinate-free candidate, verify completion criteria, and re-apply it to a related changed task/state.

### 26.5 — Public contract decision

Only after the Windows desktop surface exists, make an explicit ADR deciding whether ordinary Chat needs any new public tool names or whether the same philosophy can be preserved with a few coarse truthful semantic capabilities.

Until that decision:

- accepted public tool names remain exactly five;
- do not hide workflow CRUD/execution behind misleading existing tool semantics;
- do not add a generic opaque `workflow_execute`/`tool_invoke` equivalent by default;
- Stage 26 foundations may remain internal/tested infrastructure until there is a truthful Chat-facing boundary.

## Acceptance gates for procedural memory

Before calling procedural memory product-accepted, prove at minimum:

1. compiled skills contain no actionable replay coordinates;
2. current state overrides prior milestones;
3. one success does not auto-promote trust;
4. secrets/private reasoning are not persisted into skills;
5. malformed/stale/incompatible skills fail closed;
6. subtask advancement requires verifier evidence, not only model assertion;
7. candidate retrieval cannot authorize an action by itself;
8. a same/near-same task can use the skill without increasing false actions;
9. a variant task with changed content/layout demonstrates adaptation rather than blind replay;
10. an incompatible demonstration does not force execution;
11. skill versioning and disable/stale behavior are deterministic;
12. no second planner/model runtime is introduced into the product path.

## Public-surface invariant for now

Current accepted public tools remain:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

This is the current contract, not a promise that the product can never evolve. Any future change requires its own architecture decision, exact schema review and ordinary-Chat acceptance. The explicit decision point is after the Windows desktop surface is available.

## Repository-state continuation rule

The stage milestones above are stable historical acceptance references. They are **not** a substitute for resolving live `main` before new work. Documentation merges can move `main` without changing the accepted runtime/code baseline.

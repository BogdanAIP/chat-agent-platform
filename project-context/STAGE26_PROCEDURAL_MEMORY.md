# Stage 26 — Procedural Memory / Demo2Workflow

Status: **ACTIVE / CORE UPSTREAM QUALIFICATION ACCEPTED / PRODUCT INTEGRATION NOT YET COMPLETE**

Stage 26.0 (UI-Mate analysis + authoritative contract/context synchronization) is **DONE** through PR #78.

Stage 26.1A (OpenAdapt core qualification) has a target PASS on qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`.

The next active gate is **Stage 26.1B — real bounded Windows Capture qualification**.

This document is the authoritative design contract after merged Stage 25.2. It does not declare a working end-user teach-by-demonstration feature.

## Goal

Let ordinary ChatGPT reuse previously successful procedures without adding a second planner or turning local execution into blind macro replay.

```text
current user task
  -> ordinary ChatGPT remains the only planner/intelligence
  -> relevant prior procedure may be supplied as bounded guidance
  -> current observed state remains authoritative
  -> deterministic/semantic capabilities are preferred
  -> bounded perception is used only where needed
  -> completion/effects are verified
  -> act / continue / HALT / ABSTAIN
```

A stored procedure is advice and evidence, not an autonomous agent and not authorization to perform an action.

## Upstream references

### Tencent/UI-Mate — workflow-guidance reference

Technical analysis was performed against public `Tencent/UI-Mate` commit:

`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`.

UI-Mate is useful primarily for the separation between:

```text
rich demonstration trajectory
        ↓
compact current-subtask guidance
        ↓
live state remains authoritative
```

We do **not** adopt UI-Mate as a second GUI planner or require its 9B/27B checkpoints.

### OpenAdapt Flow/Capture — procedural-engine candidate

Broader research found a much closer implementation match than the original Stage 26 design assumed.

Pinned and target-tested:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

License: MIT for both pinned projects.

Exact qualification details: `project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md`.

Real target evidence:

```text
Python 3.12.10
exact Flow/Capture source commit verification = PASS
PHASE_B_PASS=True
PHASE_C_TUTORIAL_PASS=True
PROBE_ERROR=<null>
ERROR=<null>
STAGE26_1A_PREFLIGHT_RESULT=PASSED
TEST_EXIT_CODE=0
Chrome processes before/after = 15/15
```

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json`

The tested Flow tutorial is model-free; upstream's lifecycle contract requires production `VERIFIED` outcome, effect evidence, digest-bound receipt and `model_calls=0`.

## What changed after broader upstream research

The pre-qualification Stage 26 plan said the project would implement its own:

- raw recorder;
- Demo Compiler;
- compiled-skill IR;
- versioned skill store;
- learning/repair lifecycle.

That is no longer the default plan.

OpenAdapt already provides substantial implementations of those boundaries. The project should now **reuse and adapt qualified upstream mechanisms first**, writing project-owned replacements only where a concrete integration/security/product requirement cannot be met.

## Current component decisions

### Flow compiler + `Workflow` / `ProgramGraph` — ADOPT

Use the pinned Flow compiler/IR as the upstream procedural-program substrate behind project boundaries.

Relevant properties already present upstream:

- `Workflow` / `ProgramGraph` state-machine IR;
- semantic/structural locators as first-class evidence;
- retained visual/OCR/geometry evidence as fallback;
- typed actions, parameters, predicates, guards, loops, branches and subflows;
- current-state re-observation during replay;
- stale/ambiguous structural refusal;
- postconditions and stronger effect verification;
- model-free deterministic paths.

Do not build a competing project IR/compiler before an actual blocker is demonstrated.

### `SkillLibrary` + learn/teach lifecycle — ADAPT

Reuse upstream version/provenance/regression infrastructure, but apply project trust policy at the boundary.

Upstream already provides:

```text
candidate
active
superseded
rolled_back
```

plus parent-version provenance, source trace ids, held-out/regression/canary gates and HALT -> teach -> learn -> promote/refuse flows.

Project adaptation is required because upstream `SkillLibrary.create_skill()` makes the bootstrap version immediately `active`. Chat Agent Platform keeps the stricter rule:

```text
new demonstration / first compiled procedure
        ↓
project CANDIDATE
        ↓
verification / variant reuse / policy gate
        ↓
trusted reusable status
```

A thin policy adapter is preferred over reimplementing the library.

### OpenAdapt Capture — CONTINUE QUALIFICATION

Do not build a new recorder first.

Upstream design already supports:

- mouse/keyboard/screen capture;
- Windows UIA evidence at action time where available;
- window-scoped capture;
- conversion into Flow's compile-ready recording format;
- local-only operation.

But real target Phase D still has to prove those claims in our environment before adoption.

### Windows backend/agent — ADAPT / SECURITY A/B REQUIRED

The pinned server is safer than the early research impression suggested:

- legacy `/execute_windows` arbitrary Python route is **disabled by default**;
- default production-facing routes are bounded typed operations;
- `/input/guarded` binds input to live frame/context/focus checks;
- `/uia/find` and `/uia/act` can refuse stale/ambiguous targets;
- delivery receipts distinguish action delivery from outcome verification.

Even so, the agent is a separate interactive-session authority boundary. Compare:

```text
A. OpenAdapt typed WindowsBackend + hardened local interactive-session agent
B. OpenAdapt IR/runtime + narrower native/project-owned actuator
```

No product decision until this A/B covers authority, authentication, process/session ownership, stale/focus/frame binding and blast radius.

### Local LFM2.5-VL F16 — ADAPT through OpenAdapt Grounder seam

The pinned OpenAdapt `Grounder` contract is narrow:

```text
current PNG + intent + optional OCR label
  -> GrounderMatch proposal OR None
```

A grounder proposal is not authorization; upstream identity/risk gates remain authoritative. This is compatible with the already accepted local LFM2.5-VL-450M F16 runtime.

The F16 adapter must remain:

- local;
- on-demand;
- unloadable;
- proposal-only;
- behind freshness/identity/risk/effect checks;
- invisible as a new public Chat vision tool.

### OpenAdapt Desktop — REFERENCE / ADAPT LATER

OpenAdapt Desktop overlaps later Stage 27 work with a Tauri cockpit, frozen Python sidecar and installer packaging lane.

Its pinned build currently embeds a different Flow version from the qualified Flow runtime, so it is not the execution baseline. Before Stage 27 builds equivalent distribution infrastructure from scratch, evaluate which Desktop packaging/lifecycle patterns can be reused safely.

## Architectural split after qualification

```text
ordinary ChatGPT
  planner / task understanding / procedure applicability / adaptation
        |
        | bounded procedure context or invocation of an accepted deterministic routine
        v
qualified procedural substrate
  OpenAdapt compiler + Workflow/ProgramGraph
  adapted SkillLibrary/trust policy
  accepted capture source
  accepted verifier/effect contracts
        |
        v
accepted capability layer
  current browser/files semantic capabilities
  future accepted Windows desktop surface
  local F16 only as bounded perception proposal
```

The procedural substrate must not decide the user's goal. Retrieval may rank candidate skills; selection remains non-authorizing guidance to ChatGPT.

## Procedural-memory data principles

### Raw traces

Raw traces may contain:

- task/session identifiers;
- ordered user-visible/structured actions;
- before/after observable state;
- semantic/structural evidence;
- screenshots or capture artifacts;
- result/effect evidence;
- abstain/error classifications.

Do **not** persist private chain-of-thought.

Raw capture is sensitive by default. A desktop recording may contain everything visible or typed. Long-lived retention/sync is forbidden until project policy covers deletion, encryption and redaction.

### Compiled procedures

Do not require procedures to be literally coordinate-free if the qualified upstream IR retains pixels as **fallback evidence**. The product invariant is stronger and more precise:

> A stored procedure must never rely on blind replay of historical absolute coordinates as its authority or primary identity mechanism.

Structural/native/semantic evidence comes first where available. Pixel/template/geometry evidence may remain inside a compiled bundle as bounded fallback evidence subject to live-state re-resolution, freshness, risk and verification gates.

### Trust lifecycle

Project policy remains candidate-first even when upstream primitives expose an `active` bootstrap state.

Use measured operational evidence rather than invented model-confidence values as a substitute for outcomes.

### Completion semantics

ChatGPT may propose that a subtask is complete, but workflow progress or task success must be supported by applicable verifier/effect evidence.

```text
ChatGPT proposes completion
  -> deterministic/native verifier or system-of-record effect where possible
       PASS -> advance
       FAIL -> remain / recover
       UNKNOWN -> observe again / HALT / ABSTAIN / user input
```

## Current-state priority

```text
current observed state
  > verifier/effect criteria / current goal
  > prior successful procedure evidence
  > raw historical action sequence
```

A remembered procedure must be abandoned or adapted when it conflicts with current state.

## Stage 26 implementation order

### 26.0 — UI-Mate analysis + authoritative contract/context sync — DONE

PR #78 established the high-level procedural-memory architecture and synchronized cross-chat source-of-truth documents.

### 26.1A — OpenAdapt core qualification — ACCEPTED ON TARGET

Target-tested qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`.

Result: Flow compiler/IR is an adoption candidate, lifecycle is an adaptation candidate, and writing project-owned recorder/compiler/store first is no longer justified.

### 26.1B — Real bounded Windows Capture qualification — NEXT

Use a harmless bounded fixture first.

Acceptance:

1. recording starts/stops in the interactive user session;
2. one selected window is scoped correctly;
3. click, typing, key and scroll evidence are captured;
4. UIA evidence is retained when exposed;
5. capture converts to Flow recording input;
6. compile/replay succeeds or explicitly refuses;
7. false actions = 0;
8. unrelated-window actions = 0;
9. raw artifacts remain in the explicit local qualification directory;
10. cleanup succeeds and normal user applications remain untouched.

### 26.1C — Windows executor A/B + F16 adapter

After capture/compiler acceptance:

- compare the typed OpenAdapt Windows agent with a narrower actuator boundary;
- prove legacy arbitrary exec cannot be used in the proposed product configuration;
- prototype local F16 through the Grounder seam;
- rerun stale/ambiguous/freshness/false-action acceptance.

### 26.2 — ChatGPT procedural integration + variant-task dogfood

Integrate accepted upstream mechanisms behind the existing ChatGPT-only planner boundary.

Acceptance must prove:

- ChatGPT owns applicability/task reasoning;
- current state overrides history;
- procedure retrieval cannot authorize actions;
- bootstrap procedures follow project candidate policy;
- verifier/effect evidence controls completion;
- a related changed task is handled without blind replay;
- an incompatible procedure HALTs/ABSTAINS rather than forcing execution.

### 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

**Do not lose this stage.**

Productize the winning Windows observation/actuation/verification combination:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

Specific local programs/capabilities are **not preselected in the roadmap**. Choose them later from actual user tasks and evidence.

### 26.4 — Human demonstration capture + transferable skill acceptance

After the desktop surface is accepted, record a real user demonstration, compile it through the qualified substrate, apply project trust policy, verify completion/effects and re-apply it to a related changed task/state.

### 26.5 — Public contract decision

Only after Windows desktop surface exists, make an explicit ADR deciding whether ordinary Chat needs any new public tool names or whether the same small-semantic-surface philosophy can continue with a few coarse truthful capabilities.

Until that decision:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

remain the accepted public tools.

Do not hide workflow CRUD/execution behind misleading existing tool semantics and do not add a generic opaque `workflow_execute`/`tool_invoke` equivalent by default.

## Acceptance gates before procedural memory is product-accepted

1. no blind historical coordinate replay as authority;
2. current state overrides prior procedure history;
3. one success/one demonstration does not silently become product-trusted;
4. secrets/private reasoning are not persisted into reusable skill metadata;
5. raw capture retention/redaction/encryption policy is explicit;
6. malformed/stale/incompatible procedure fails closed;
7. completion requires verifier/effect evidence, not only model assertion;
8. retrieval cannot authorize an action by itself;
9. same/near-same tasks can reuse a procedure without increasing false actions;
10. variant tasks demonstrate adaptation/re-resolution rather than blind replay;
11. incompatible demonstrations do not force execution;
12. versioning, rollback/quarantine/stale/disable behavior is deterministic;
13. no second planner/model runtime is introduced into the product path;
14. Windows desktop authority boundary is explicitly accepted;
15. legacy generic code execution is disabled/unreachable in the product configuration.

## Repository-state continuation rule

Milestone SHAs in documentation are stable historical acceptance references. They are not a substitute for resolving live `main` before new work.

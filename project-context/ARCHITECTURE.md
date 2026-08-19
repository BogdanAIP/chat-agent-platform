# Architecture

## Repository-state rule

Resolve live `main` before new work. Stable acceptance SHAs are historical evidence, not a substitute for resolving the current integration line.

This documentation branch is stacked on exact physically accepted PR #85 head `66390aca1dadf57c4f11568ec311ad6fcdbd7596`; C/D/E are not yet in `main` until the stacked PR chain is explicitly landed.

## Product boundary

`chat-agent-platform` is the local execution/perception/procedural layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = general intelligence / task interpretation / strategy / adaptation

local platform
  = scoped capabilities
  + deterministic/native observation
  + bounded specialist perception
  + guarded execution
  + verification
  + non-agentic procedural memory
  + optional specialist reasoning proposals later
```

Never add a second universal planner, autonomous workflow brain, generic local agent, or unbounded hidden execution channel.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused task-active backends/adapters
```

Current accepted public tool names remain:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal diagnostic/adaptive/aggregation infrastructure.

## Semantic projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map a truthful semantic request to one reviewed capability action or a small bounded deterministic sequence. It must not:

- decide user goals;
- run hidden plans;
- become procedural memory;
- become a generic model/tool gateway;
- expose a disguised `tool_invoke`;
- hide desktop/workflow consequence classes behind misleading web semantics merely to preserve a five-tool count.

The public contract is reconsidered only after the native Windows desktop surface exists.

---

# Capability and procedural trust

Capability authority and procedural trust are separate.

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure lifecycle:

```text
new/demo
 -> CANDIDATE
 -> replay/regression/variant verification
 -> trusted reusable
 -> stale / quarantined / disabled / rollback
```

A trusted procedure still cannot authorize every historical action. Current state and capability authorization remain authoritative.

Priority:

```text
current observed state
  > current goal / verifier criteria
  > trusted procedural evidence
  > raw historical action sequence
```

---

# Browser grounding — accepted Stage 25.2

Deterministic semantic structure is preferred whenever reliable evidence exists.

```text
web_interact(click)
  -> fresh accessibility snapshot
       -> exact enabled promoted semantic target
            -> semantic action; VLM stopped
       -> disabled/non-button/unresolved semantic ambiguity
            -> ABSTAIN; VLM stopped
       -> zero exact candidates on the reviewed visual path
            -> same-session screenshot
            -> local F16 proposal
            -> deterministic target/freshness authorization
            -> one coordinate action OR ABSTAIN
```

`targetText` remains the authorization anchor. Planner free-form text cannot redirect the visual target.

## Local vision boundary

Accepted target-laptop specialist:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
F16 mmproj
CPU 8 threads
ctx 2048
```

The model is perception only. It never plans, authorizes or declares completion by itself.

---

# Procedural substrate — accepted upstream direction

Pinned target-tested upstreams:

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
SkillLibrary/learn/teach internals
Windows typed backend/agent mechanics
```

The repository owns the policy/integration boundary rather than duplicating a generic recorder/compiler/skill engine without a measured gap.

Project policy remains candidate-first even where upstream bootstraps a first skill as active.

## Compiled procedure evidence rule

A compiled procedure may retain structural/native evidence and bounded geometry/pixel/template evidence. The product invariant is not “no coordinates exist”; it is:

> blind historical absolute-coordinate replay is never authority or primary identity.

Preferred resolution:

```text
live native/semantic/UIA evidence
 -> deterministic re-resolution
 -> bounded OCR/template/geometry/vision fallback where permitted
 -> identity/risk/freshness checks
 -> action
 -> observed effect verification
 -> ABSTAIN on unresolved state
```

---

# Windows execution boundary — physically accepted Stage 26.1C

Exact accepted PR #83 head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Selected direction: reuse the pinned OpenAdapt typed `WindowsBackend` + hardened interactive-session agent behind project-owned construction/configuration. Do not write a replacement actuator unless later evidence shows a blocker that cannot be closed within this boundary.

Accepted invariants:

```text
127.0.0.1 only
ephemeral authenticated agent
legacy arbitrary exec absent/disabled
typed bounded input only
stale frame refusal
stale context refusal
focus-bound keyboard
UIA unique target
fingerprint-bound structural action
bounded pointer/scroll
layout-independent Unicode text delivery
zero unrelated-window actions
zero false actions
```

Generic `/execute_windows` authority is not part of the product contract.

---

# Windows UI resolution — physically accepted Stage 26.1E

Stage 26.1D measured a ~184 second warm action cycle. Exact pinned upstream inspection showed desktop-wide `_find_candidates()` repeatedly traversing from `GetRootControl()`, including re-resolution before structural actuation.

Stage 26.1E replaces that qualification path with:

```text
expected process id
  -> Win32 EnumWindows (bounded)
  -> GetWindowThreadProcessId
  -> discard non-target process HWNDs before UIA conversion
  -> uiautomation.ControlFromHandle on same-process HWNDs only
  -> exact normalized WindowControl name
  -> native FindAll(TreeScope.Descendants, condition) inside bound window only
  -> pinned upstream candidate generation/fingerprint
  -> independent fresh re-resolution before act
```

Exact accepted PR #85 head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Physical result:

```text
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0

action p50=3323.570 ms
action p95=3720.061 ms
p50 speedup=55.244x
p95 speedup=49.883x
```

### Accuracy statement

This is 97/97 evidence for the controlled role+name fixture path, not proof of global Windows accuracy. `AutomationId`, custom controls, multiple real applications and vision fallback require dedicated evidence.

---

# Production Windows Runtime — next architecture target

Accepted qualification seams must now become a maintained capability layer rather than remain under `scripts/stage26-*`.

Conceptual boundary:

```text
runtime/windows/
  session/
    interactive-user-session
    application/process identity
  observation/
    Win32 window identity
    window-scoped UIA
    screenshot
  actuation/
    UIA
    guarded keyboard
    guarded pointer
    guarded scroll
  safety/
    stale frame
    stale context
    focus
    fingerprint
    application/window identity
  verification/
    effect/postcondition foundation
  lifecycle/
    start/stop/health/logging/recovery
```

The exact repository layout may differ; the separation of concerns is the important invariant.

## Verifier foundation is part of the runtime

Do not defer all verification until procedural-memory work.

Base capability contract:

```text
before = observe()
authorized = authorize(before, requested_action)
delivery = act(authorized)
after = observe()
verification = verify(before, after, expected_effect)
```

`delivery != success`.

Verifier result should fail closed:

```text
PASS
FAIL
UNKNOWN
```

`UNKNOWN` does not silently advance a workflow.

---

# Desktop Observation / DesktopState

Observation order:

```text
Win32 identity
 -> UIA/native structure
 -> screenshot
 -> bounded local VLM fallback
```

A canonical `DesktopState` should explicitly carry identity, freshness and provenance instead of becoming an untyped bag of UI data.

Expected fields/concepts:

```text
session_id
application_identity
process_id
window_handle
window_instance/generation
window_title
window_bounds
coordinate_space
focused_control
controls[]
visible_text
observed_capabilities[]
screenshot_digest
frame_digest
observed_at
observation_source
control fingerprint/bounds/enabled/visible/focused
provenance
```

`observed_capabilities` mean “evidence says this UI capability exists”; they do not mean authorization has been granted.

---

# Desktop Grounder boundary

The accepted browser visual CLI is CSS/Playwright viewport-specific. Native Windows has a different coordinate space and needs a separate adapter.

Grounder seam:

```text
locate(
  window_png,
  target_text,
  window_bounds,
  optional_uia_evidence
) -> GrounderProposal | None
```

Proposal evidence should bind to:

```text
point/region
coordinate_space
frame_digest
window identity
target evidence
confidence
```

The Grounder never outputs authority such as “click”, “continue”, “run workflow” or “task complete”.

Authorization after proposal must prove same window, same/current frame, permitted target/consequence class and fresh state before any coordinate action.

---

# Windows semantic/UIA -> vision routing

The desktop product should mirror the browser principle without pretending the implementation details are identical:

```text
native/UIA exact evidence
 -> deterministic structural action

no permitted structural target
 -> exact current-window screenshot
 -> local Grounder proposal
 -> deterministic same-window/frame/target authorization
 -> coordinate action OR ABSTAIN
```

Semantic ambiguity is not automatically permission to use vision. Routing classes must be explicitly promoted by evidence.

Before real application dogfood, test at least duplicate labels, disabled/hidden controls, wrong window/process, overlays, focus changes, stale/recreated window, `AutomationId`, role+name, custom/weak controls, UIA-missing visual fallback and visual ambiguity/ABSTAIN.

---

# Real application gate before procedural integration

The first production-level desktop E2E must use one real medium-complexity user application with a safe disposable artifact, deterministic postcondition and rollback.

The architecture does not permanently preselect VS Code, OriginPro, Reaper or any other application; those are candidates selected from real task/evidence.

Acceptance requires:

```text
false actions=0
unrelated-window actions=0
current-state verification=PASS
completion verification=PASS
recoverable mismatch=ABSTAIN
```

This gate validates the desktop capability itself before adding procedural memory to the product path.

---

# Verified Procedure Runtime — after real desktop E2E

```text
ordinary ChatGPT
 -> decide whether a known procedure is relevant
 -> load ProgramGraph
 -> observe current state
 -> resolve next abstract transition
 -> authorize capability action
 -> execute
 -> observe effect
 -> verify
 -> advance / recover / ABSTAIN
```

Retrieval/procedure selection is non-authorizing.

## Advanced verifier library

The runtime verifier foundation later expands to procedure-specific postconditions:

```text
UI state
file system
window state
application state
browser state
artifact existence
structured output
```

## Human demonstration transfer

```text
human demonstration
 -> Capture
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified replay
 -> changed-state/task replay
```

One demonstration is evidence, not permanent trust.

---

# Optional specialized reasoning — not a release prerequisite

Only after real verified procedure-state data exists and measurements show a need may the platform evaluate a `SpecializedReasoningBackend`.

It receives structured goal/state/ProgramGraph/transitions and returns only:

```text
proposal
confidence
proposed | abstain
```

Compare deterministic baseline with small transformer/TRM/STARM/FPRM/future recursive approaches if useful.

Primary safety metric is false-action proposal rate, not raw accuracy alone.

This specialist never authorizes or actuates.

---

# Multi-Chat / Codex orchestration — separate upper layer

Multi-Chat control is not part of Windows runtime or executor safety core.

```text
Multi-Chat Controller
 -> ChatGPT research/planning/review
 -> Codex code tasks where useful
 -> Chat Agent Platform as local capability layer
```

It may manage chat state/task/result collection, but must not become a hidden local planner inside the execution core. It is not a Stage 27/28 prerequisite.

---

# Public contract decision

After the Windows desktop surface exists, make a separate ADR and ordinary-Chat acceptance decision:

- preserve the current five tools if they remain truthful; or
- add a small number of coarse truthful desktop/procedure capabilities.

Never add an opaque generic workflow dispatcher or overload `web_interact` with native Windows semantics.

---

# Security/privacy boundaries

- tunnel reachability remains outbound from the user machine;
- normal semantic transport remains direct stdio;
- tunnel secrets remain outside repository content and use appropriate Windows protection;
- child backends do not inherit credentials without need;
- filesystem roots account for Windows junction/link escape;
- browser DNS/rebinding/redirect/private-network isolation remains explicit residual work;
- local inference is bounded, on-demand and non-authorizing;
- raw desktop demonstrations are sensitive local data and not safe-to-sync by default;
- private chain-of-thought is never procedural-memory data;
- generic Windows code execution remains disabled/unreachable;
- stale, ambiguous or incompatible state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager

The public manager/tray owns lifecycle/configuration/diagnostics only. It does not plan tasks or become procedure memory.

---

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, project trust/policy wrappers, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, autonomous workflow brain, generic workflow engine, general model-serving platform, duplicate OpenAdapt implementation or new Windows actuator while accepted upstream mechanisms cover those needs.

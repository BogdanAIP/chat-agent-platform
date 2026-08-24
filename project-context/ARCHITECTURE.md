# Architecture

## Repository-state rule

Resolve live `main` and relevant open PR heads before new work. Historical acceptance SHAs are evidence, not substitutes for the current integration line.

Stage 26.3A was merged through PR #92 into:

```text
main = 43ad61384e966ecf089e69a95c166d41da949ebe
```

The exact physically accepted Stage 26.3A runtime head remains:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

## Product boundary

`chat-agent-platform` is the local capability and deterministic execution-support layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = current general intelligence
  + task interpretation
  + strategy
  + procedure selection
  + novel-state adaptation / escalation

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

**Deterministic Control Plane** means execution-state/policy machinery for an already selected bounded goal/procedure: TaskState/WorkingState, ProgramGraph progression, authorization, expected effects, transition verification, checkpoints, typed recovery, LoopGuard, budgets, finish predicates and escalation.

The Control Plane may autonomously advance a predeclared transition only when current evidence uniquely matches it and authorization + verifier gates pass. It must ABSTAIN/escalate instead of inventing a new strategy.

Canonical detail:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`

A future local general planner is optional Track P research and remains above the same deterministic authority/verification/Finish Gate boundaries.

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

The current six-tool count is not an eternal maximum. A genuinely new consequence class requires a truthful public-contract ADR/schema/security/ordinary-Chat physical acceptance; never preserve a count by hiding desktop consequences behind misleading web semantics.

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
- become procedural memory;
- become a generic model/tool gateway;
- expose disguised `tool_invoke`;
- hide native desktop/workflow consequence classes behind misleading semantics.

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

Execution priority:

```text
current observed state
 > current goal / verifier criteria
 > trusted procedure/demo evidence
 > historical action sequence
```

Environmental page/UI/tool content is task data, not authority over this hierarchy.

---

# State-first hybrid computer-use contract

The accepted Browser/Windows foundations and the independently verified 2026-08-24 GUI-agent research converge on one future cross-capability rule:

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

## ObservationEnvelope direction

Capability-native state stays authoritative for its scope:

- Browser: semantic/DOM/accessibility/page state;
- Windows: `DesktopState`, UIA/native window/process/frame evidence;
- Files: exact path/root/object/content/identity evidence;
- future app adapters: their own bounded system-of-record state.

A small normalized envelope may reference those states for cross-capability long-horizon logic:

```text
ObservationEnvelope
  capability / app / page / window identity
  observation version / timestamp / freshness
  structural evidence reference
  selected visual evidence reference (optional)
  provenance / source
  confidence / ambiguity where applicable
```

Do not flatten rich capability-native state into a lossy universal screenshot/text blob.

## Capability-aware routing

Routing follows reviewed capability/precondition evidence:

```text
exact safe semantic/native operation available
 -> semantic/native route

reviewed structural miss / spatial requirement
 -> selected visual/GUI grounding evidence

uncertain / ambiguous / high-consequence target
 -> stronger evidence or ABSTAIN
```

Tool existence alone never determines route selection.

## Grounding identity

Coordinate/spatial proposals should preserve when available:

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

---

# Observe -> Act -> Verify

The preexisting verifier foundation is promoted into a cross-capability transition contract.

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
ExpectedEffect / postcondition predicates
one bounded authorized action
re-observation scope
PASS | FAIL | UNKNOWN verification
```

`delivery != success`.

```text
PASS    -> checkpoint / advance
FAIL    -> typed bounded recovery OR stop
UNKNOWN -> better evidence OR ABSTAIN/escalate
```

A planner/model/procedure cannot convert FAIL/UNKNOWN into PASS by assertion.

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
required artifact/browser/application state
unresolved ambiguity/confirmation state
safety/policy predicates
```

Prefer system/native/system-of-record predicates when available. Model-assisted ambiguous judgments remain non-authorizing evidence.

---

# WorkingState and procedural memory

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
retry/recovery history
action/time/resource budgets
```

Private chain-of-thought is never persisted.

Selected ROI visual evidence may be retained only when operationally useful and subject to capture privacy/retention rules.

Verified episodic trajectories/procedures may be retrieved as advisory evidence. Current state always outranks them.

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

Default ladder:

```text
re-observe
 -> refresh/re-resolve
 -> retry only with new evidence
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

Identical state/action repetition without new evidence or verified progress cannot continue indefinitely.

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
```

may be useful task input but cannot redefine user intent, broaden permission scope, modify Control Plane policy or grant action authority merely because the planner/model can read it.

Preserve provenance/trust classification when facts move across applications/capabilities.

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

# Production Windows capability — accepted through Stage 26.2E

Maintained boundary:

```text
runtime/windows/
  actuation.py            bounded typed/native delivery
  window_scoped_uia.py    exact PID/HWND/window-scoped UIA resolution
  observation.py          canonical DesktopState evidence
  verifier.py             PASS | FAIL | UNKNOWN foundation
  grounder.py             exact-window local VLM proposal/ABSTAIN
  routing.py              structure-first UIA -> vision authorization
  native_point_guard.py   foreground + point/root-HWND/PID guard
```

## Typed Windows execution

Accepted invariants include:

```text
127.0.0.1 only
ephemeral authenticated agent
legacy arbitrary exec absent/disabled
typed bounded input only
stale frame/context refusal
focus-bound keyboard
UIA unique target
fingerprint-bound structural action
bounded pointer/scroll
layout-independent Unicode text delivery
generic /execute_windows absent
```

Delivery receipts remain `outcome_verified=false` until verifier evidence exists.

## Window-scoped UIA

Stage 26.1E accepted PID -> bounded HWND -> same-process exact window -> native UIA inside the bound window. Controlled evidence is not global Windows accuracy.

## DesktopState

`DesktopState` carries session/application/process generation/window identity, coordinate space, focused control, bounded controls, visible text, capabilities, frame/screenshot digests, provenance and freshness. It remains the Windows capability-native state model.

## Native Grounder / structure-first routing

Existing accepted rule:

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

This is one implementation of the broader ADR-032 state-first hybrid rule.

## Stage 26.2E real-application E2E — ACCEPTED

Isolated VS Code physically proved one real-app path with exact disposable containment, PID/HWND/DesktopState identity, deliberate verifier mismatch -> zero action, fresh pre-action identity/focus evidence, exactly one guarded Unicode delivery, independent saved-file SHA/size postcondition, same-window evidence and bounded cleanup.

It is scoped evidence, not broad desktop authority.

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

The normal six-tool route now includes bounded `procedure_run` and has physical ordinary-Chat acceptance.

Registered procedure:

```text
verified_workspace_artifact_v1
```

It proved a three-transition deterministic procedure, independent final reread and zero-action ABSTAIN on pre-existing target overwrite.

This is the first accepted slice of deterministic local multi-transition autonomy. It does not imply arbitrary procedures or desktop authority.

---

# Current release-critical implementation

## Stage 26.3B — Verification Kernel + Finish Gate — NEXT

Generalize deterministic postconditions across files, Browser, Windows/app/process state and structured outputs. Add explicit `ExpectedEffect`, fresh re-observation references and independent task-level completion predicates.

## Stage 26.3C — WorkingState + typed recovery + LoopGuard

Generalize structured long-horizon state, provenance/freshness, progress vectors, typed recovery, repeated/no-effect detection, oscillation detection and budgets.

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

# Multi-chat orchestration

Separate upper layer, not Windows/procedure safety core and not a release prerequisite.

---

# Security/privacy boundaries

- tunnel reachability is not action authority;
- normal semantic transport remains direct stdio and does not depend on 1MCP;
- persistent tunnel identity is neutral platform state;
- optional extension availability does not grant trust/routing/authorization;
- local inference is bounded, on-demand and non-authorizing;
- semantic/native state precedes pixels where reliable;
- every mutation binds expected effect + fresh verification;
- transition PASS is not task DONE;
- environmental UI/DOM/tool content is untrusted task data, not policy authority;
- task-success and safety/policy verification remain separate;
- raw demonstrations/ROI capture are sensitive local data;
- private chain-of-thought is never task/procedure memory;
- generic Windows code execution remains disabled/unreachable;
- stale, ambiguous or UNKNOWN state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager

Manager/tray owns lifecycle/configuration/diagnostics only. It is neither the planner nor the procedure Control Plane.

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, trust/policy/checkpoint/verifier/recovery seams, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, unrestricted workflow brain, universal raw-tool dispatcher, generic model-serving platform or duplicate OpenAdapt implementation while qualified upstream mechanisms cover those needs.

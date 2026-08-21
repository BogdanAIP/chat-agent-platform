# Architecture

## Repository-state rule

Resolve live `main` and relevant open PR heads before new work. Historical acceptance SHAs are evidence, not substitutes for the current integration line.

At the start of Stage 26.2E, Stage 26.2D had been merged as PR #90 and `main` was `42d4130d59e23e2c2b1771ac428467efe27a4b98`.

## Product boundary

`chat-agent-platform` is the local execution, perception, verification and procedural-support layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = general intelligence / task interpretation / strategy / adaptation

local platform
  = scoped capabilities
  + deterministic/native observation
  + bounded specialist perception
  + deterministic authorization
  + guarded execution
  + verification
  + non-agentic procedural memory
  + optional specialist reasoning proposals later
```

Never add a second universal planner, autonomous workflow brain, generic local agent or unbounded hidden execution channel.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused task-active backends/adapters
```

Current accepted public tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal diagnostic/adaptive/aggregation infrastructure.

## Semantic projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic request to one reviewed capability action or a small bounded deterministic sequence. It must not:

- decide user goals;
- run hidden plans;
- become procedural memory;
- become a generic model/tool gateway;
- expose a disguised `tool_invoke`;
- hide native desktop/workflow consequence classes behind misleading web semantics.

The public contract is reconsidered only through a dedicated ADR after real desktop capability evidence.

---

# Capability authority and procedural trust

Capability authority and procedure trust are different state machines.

```text
capability:
AVAILABLE -> ACTIVE -> AUTHORIZED

procedure:
new/demo
 -> CANDIDATE
 -> replay/regression/variant verification
 -> trusted reusable
 -> stale / quarantined / disabled / rollback
```

A trusted procedure still does not authorize historical actions. Priority remains:

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
      -> reviewed zero-exact visual path
           -> same-session screenshot
           -> local F16 proposal
           -> deterministic target/freshness authorization
           -> one coordinate action OR ABSTAIN
```

`targetText` remains an authorization anchor. Planner free-form text cannot silently redirect the visual target.

Accepted target-laptop specialist:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
F16 mmproj
CPU 8 threads
ctx 2048
```

The model perceives/proposes only. It never plans, authorizes or declares task completion.

---

# Procedural substrate — qualified upstream direction

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
SkillLibrary/learn/teach mechanics
Windows typed backend/agent mechanics
```

The repository owns the project policy/integration boundary instead of duplicating a generic recorder/compiler/skill engine. First demonstration remains CANDIDATE, never automatic permanent trust.

Blind historical absolute-coordinate replay is never authority or primary identity. Preferred procedure resolution later remains:

```text
live native/semantic/UIA evidence
 -> deterministic re-resolution
 -> bounded visual/template/geometry fallback where permitted
 -> identity/risk/freshness checks
 -> action
 -> observed effect verification
 -> ABSTAIN on unresolved state
```

---

# Production Windows capability — accepted through Stage 26.2D

Maintained production boundary:

```text
runtime/windows/
  actuation.py            bounded typed/native delivery
  window_scoped_uia.py    exact PID/HWND/window-scoped UIA resolution
  observation.py          canonical DesktopState evidence
  verifier.py             PASS | FAIL | UNKNOWN postcondition baseline
  grounder.py             exact-window local VLM proposal/ABSTAIN
  routing.py              structure-first UIA -> vision authorization
  native_point_guard.py   foreground + point/root-HWND/PID native guard
```

## Typed Windows execution

Stage 26.1C physically accepted the hardened typed Windows executor; Stage 26.2A promoted the maintained runtime.

Core invariants:

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
generic /execute_windows absent
```

Delivery receipts keep `outcome_verified=false`.

## Window-scoped UIA

Stage 26.1E accepted:

```text
expected process id
 -> Win32 EnumWindows
 -> discard non-target PID HWNDs before UIA conversion
 -> ControlFromHandle only for same-process HWNDs
 -> exact normalized top-level WindowControl name
 -> native FindAll(TreeScope.Descendants, condition) inside bound window only
 -> bounded candidate/fingerprint generation
 -> independent fresh re-resolution before structural actuation
```

Physical controlled fixture evidence:

```text
97 scoped resolutions
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
p50=3323.570 ms
p95=3720.061 ms
```

This is not global Windows accuracy.

## DesktopState observation — Stage 26.2B

Canonical state explicitly carries:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
window_instance
window_title/window_bounds
screen physical coordinate space
focused control
bounded controls[]
visible text
observed capabilities
screenshot digest
frame digest
observed_at
observation source/provenance
freshness evidence
```

Screenshot bytes are not stored in DesktopState. Observation fingerprints are evidence, not action fingerprints or authority.

## Verifier foundation

Capability lifecycle:

```text
before = observe()
authorized = authorize(before, requested_action)
delivery = act(authorized)
after = observe()
verification = verify(before, after, explicit_expected_effect)
```

`delivery != success`.

Verifier results:

```text
PASS
FAIL
UNKNOWN
```

FAIL/UNKNOWN never silently advance a workflow.

## Native desktop Grounder — Stage 26.2C

The native Windows visual adapter is separate from browser CSS/viewport coordinates.

```text
exact current-window PNG
 + target text
 + DesktopState/window identity
 + bounded optional UIA evidence
 -> Grounder proposal OR ABSTAIN
```

Proposal binds to window/process/frame/screenshot/coordinate evidence. It never outputs action authority.

The physically observed controlled fixture read `1. Benchmark start` as `Benchmark start`. Accepted label policy is:

```text
exact label first
 -> inventory-absent only
      -> remove one leading ordinal N. / N)
      -> exactly one already-observed inventory label => continue
      -> zero/multiple => ABSTAIN
```

No broad fuzzy matching.

## Structure-first Windows visual routing — Stage 26.2D

Exact accepted architecture:

```text
current DesktopState/UIA
 -> exact safe structural target
      -> fresh structural re-resolution
      -> native UIA delivery

 -> explicitly promoted structural miss only
      -> current exact-window screenshot
      -> Stage 26.2C Grounder proposal
      -> deterministic grounder evidence gate
      -> request/role/UIA/process/window/frame/coordinate binding
      -> fresh exact-window re-observation
      -> unchanged screenshot/frame/structure
      -> native foreground + WindowFromPoint/root HWND/PID guard
      -> accepted backend guarded frame gate
      -> one physical click OR ABSTAIN
```

Known same-role UIA under a visual proposal point constrains authorization: if present it must be uniquely actionable. Weak/missing same-role UIA can leave the bounded visual path possible; it does not itself grant authority.

Action authorization is stricter than proposal acceptance: Stage 26.2D requires unique inventory/refinement evidence and positive coarse/refined consistency IoU before a visual proposal can reach execution.

Stage 26.2D physical acceptance (`1c74713edcd6321d5583a39234929169e68b5ac1`) proved one real guarded visual-fallback click with fresh identical screenshots, native wrong-window refusal, no-promotion/role-conflict refusal and one coordinate delivery. This remains controlled WinForms evidence.

---

# Current gate — Stage 26.2E real application E2E

Before procedural integration, the production Windows capability must complete one real medium-complexity application task with a disposable artifact, deterministic postcondition and rollback.

The current qualification candidate is isolated VS Code, selected because it supports a real application boundary while keeping user data outside the test.

```text
specifically prefixed TEMP root
 -> isolated VS Code --user-data-dir / --extensions-dir
 -> unique empty disposable .txt
 -> exact unique Code.exe top-level window
 -> PID/HWND/DesktopState binding
 -> focused editor + native point guard
 -> deliberate verifier mismatch => ABSTAIN, zero action
 -> exactly one guarded Unicode text delivery
 -> independent autosaved file size/SHA-256 verification
 -> same current window identity
 -> workspace contains only expected artifact
 -> close exact qualification window
 -> remove isolated TEMP root
 -> rollback PASS
```

No user project/profile/settings are part of the task. Recursive cleanup is permitted only after both Python and PowerShell independently prove the application root is a specifically prefixed child of the OS TEMP directory.

Read `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`.

A successful VS Code run proves one real application E2E only, not universal Windows accuracy.

---

# Verified Procedure Runtime — after Stage 26.2E

Do not create a second local general planner.

```text
ordinary ChatGPT
 -> decide whether a known procedure is relevant
 -> load ProgramGraph
 -> observe current state
 -> resolve one applicable abstract transition
 -> deterministic authorization
 -> bounded execution
 -> observe effect
 -> verify
 -> advance / recover / ABSTAIN
```

Retrieval/procedure selection is non-authorizing.

## Candidate-first trust

```text
human demo/new procedure
 -> Capture
 -> compile ProgramGraph
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantined/disabled as evidence degrades
```

## Advanced verifier library

Expand postconditions for UI state, filesystem, window/app state, browser state, artifact existence and structured outputs.

## Human demonstration transfer

```text
human demonstration
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified replay
 -> changed-state/task replay
```

One demonstration is evidence, not blind macro authority.

---

# Optional specialized reasoning

Only after real verified procedure-state data exists and measurements show need may the platform evaluate a `SpecializedReasoningBackend`. It receives structured state/goal/procedure evidence and returns proposal/confidence/abstain only. It never authorizes or actuates.

# Multi-chat orchestration

Separate upper layer, not part of Windows runtime/procedure safety core. Under the current operating constraint it must not use Codex or Work resources. It is not a release prerequisite.

---

# Security/privacy boundaries

- tunnel reachability remains outbound from the user machine;
- normal semantic transport remains direct stdio;
- tunnel secrets stay outside repository content;
- child backends receive credentials only when needed;
- filesystem roots account for Windows junction/link escape;
- browser DNS/rebinding/redirect/private-network isolation remains residual work;
- local inference is bounded, on-demand and non-authorizing;
- raw desktop demonstrations are sensitive local data and not safe-to-sync by default;
- private chain-of-thought is never procedural-memory data;
- generic Windows code execution remains disabled/unreachable;
- stale, ambiguous or incompatible state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager

Public manager/tray owns lifecycle/configuration/diagnostics only. It does not plan user tasks or become procedure memory.

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, project trust/policy wrappers, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, autonomous workflow brain, generic workflow engine, general model-serving platform, duplicate OpenAdapt implementation or replacement Windows actuator while accepted upstream mechanisms cover those needs.
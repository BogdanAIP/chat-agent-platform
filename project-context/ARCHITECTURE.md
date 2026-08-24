# Architecture

## Repository-state rule

Resolve live `main` and relevant open PR heads before new work. Historical acceptance SHAs are evidence, not substitutes for the current integration line.

At the start of Stage 26.2E, Stage 26.2D had been merged as PR #90 and `main` was:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

## Product boundary

`chat-agent-platform` is the local capability and deterministic execution-support layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = current general intelligence
  + task interpretation
  + strategy
  + procedure selection
  + adaptation / escalation

local platform
  = scoped capabilities
  + deterministic/native observation
  + bounded specialist perception
  + deterministic execution Control Plane
  + authorization
  + guarded execution
  + verification
  + checkpoints / bounded recovery
  + procedural memory
```

### General planner vs Control Plane

The repository intentionally distinguishes two roles:

**General planner** means open-ended semantic strategy: interpreting the user's goal, choosing materially different approaches, adapting to novel state and inventing a new strategy. Ordinary ChatGPT is the only **current** general planner.

**Deterministic Control Plane** means execution state/policy machinery for an already-selected bounded goal/procedure: `TaskState`, `ProgramGraph` progression, authorization, checkpoints, verifier/postconditions, retry/recovery ceilings and resource budgets.

The Control Plane may autonomously advance an already-defined transition when current evidence uniquely matches it and all authorization/postcondition gates pass. It must ABSTAIN/escalate to ChatGPT instead of inventing a new transition when the live state is novel, stale, ambiguous, incompatible or requires new strategy.

Canonical detail: `project-context/CONTROL_PLANE.md`.

A future local general planner is a separate optional Track P; it is not part of the current release-critical architecture and even if later accepted remains above the same deterministic Control Plane authority boundary.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> canonical six-tool semantic projection
  -> focused task-active capabilities / deterministic Control Plane
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

There is no normal runtime/profile/tray choice between five and six tools. The historical five-capability file/browser projection remains only as a private implementation/regression layer behind the canonical six-tool launcher.

### Persistent tunnel anchor

The accepted `tunnel_*` id is platform state, not 1MCP state.

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

is the neutral source of truth for the persistent tunnel anchor. An existing `local-1mcp.yaml` may be read only as a bounded migration fallback to recover one already accepted tunnel id. The normal semantic route must not require that legacy profile after migration.

### Optional Extension Manager

1MCP is retained as replaceable **optional internal Extension Manager infrastructure**, not as the normal semantic critical path.

Target extension topology:

```text
ordinary ChatGPT
        |
        v
canonical project-owned semantic surface
        |
        +----> project-owned capabilities / deterministic Control Plane
        |
        `----> internal Extension Manager
                    |
                   1MCP
                    |
              third-party MCP backends
```

1MCP may provide discovery, aggregation, enable/disable, lazy lifecycle, health and restart for extension backends. It does not own baseline reachability, the persistent tunnel anchor, Chat-facing authorization or the raw public tool contract.

Normal six-tool bootstrap/start/smoke/health must work without 1MCP or an `npx` 1MCP preflight. Failure of an optional extension must be isolated unless the current task explicitly depends on that extension.

Raw third-party MCP catalogs are never promoted automatically to ordinary ChatGPT. A supported extension remains behind the smallest truthful project-owned typed facade and the same consequence/authorization boundary.

## Semantic projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic request to one reviewed capability action or a small bounded deterministic sequence. It is **not** the local Control Plane.

It must not:

- decide user goals;
- run hidden open-ended plans;
- become procedural memory;
- become a generic model/tool gateway;
- expose a disguised `tool_invoke`;
- hide native desktop/workflow consequence classes behind misleading web semantics.

A separate public-contract ADR decides when a genuinely new consequence class needs a new public name. The current six-tool count is not an eternal maximum.

---

# Authority, trust and state

Capability authority and procedure trust are separate state machines:

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

A trusted procedure is not blanket action authority.

Execution priority:

```text
current observed state
 > current goal / verifier criteria
 > trusted procedure evidence
 > historical action sequence
```

The future Control Plane must preserve this priority at every transition.

---

# Browser grounding — accepted Stage 25.2

```text
web_interact(click)
 -> fresh accessibility snapshot
      -> exact enabled promoted semantic target
           -> semantic action; VLM stopped
      -> disabled/non-button/unresolved ambiguity
           -> ABSTAIN; VLM stopped
      -> reviewed bounded visual path
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

The model perceives/proposes only. It never grants authority or task completion.

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

The repository owns focused integration/policy/checkpoint seams rather than duplicating a generic recorder/compiler/agent framework.

A stored procedure may retain native/semantic/UIA and bounded visual/template/geometry evidence, but blind historical absolute-coordinate replay is never authority or primary identity.

Preferred future procedure execution:

```text
ChatGPT selects applicable procedure
 -> Control Plane loads exact version + TaskState
 -> live state observation
 -> exactly one permitted transition
 -> current capability authorization
 -> action
 -> observed effect verification
 -> checkpoint / advance
 -> repeat while known
 -> ABSTAIN/escalate on novel or incompatible state
```

This is stronger than treating a procedure as mere passive advice, but it is still not a second planner.

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

Delivery receipts keep `outcome_verified=false`.

## Window-scoped UIA

Stage 26.1E accepted PID -> bounded Win32 HWND -> same-process exact window -> native UIA FindAll inside the bound window only. Controlled evidence: 97 scoped resolutions, zero Desktop fallback/binding failures/ambiguities, p50 3323.570 ms / p95 3720.061 ms. This is not global Windows accuracy.

## DesktopState — Stage 26.2B

Canonical state carries session/application/process generation/window identity, physical coordinate space, focused control, bounded controls, visible text, observed capabilities, frame/screenshot digests, provenance and freshness evidence. Observation fingerprints are evidence, not executor authority.

## Verifier foundation

```text
before = observe()
authorized = authorize(before, requested_action)
delivery = act(authorized)
after = observe()
verification = verify(before, after, expected_effect)
```

`delivery != success`.

```text
PASS
FAIL
UNKNOWN
```

FAIL/UNKNOWN never silently advance a procedure.

## Native Grounder — Stage 26.2C

Exact-window proposal/ABSTAIN only. The controlled physical `1. Benchmark start` -> `Benchmark start` mismatch is handled by one narrowly bounded ordinal-prefix alias after inventory-absent; no general fuzzy matching.

## Structure-first Windows routing — Stage 26.2D

```text
current DesktopState/UIA
 -> exact safe structural target
      -> fresh structural re-resolution
      -> native UIA delivery

 -> explicitly promoted structural miss only
      -> current exact-window screenshot
      -> Grounder proposal
      -> deterministic proposal/evidence gate
      -> request/role/UIA/process/window/frame/coordinate binding
      -> fresh exact-window re-observation
      -> native foreground + WindowFromPoint/root HWND/PID guard
      -> guarded backend frame gate
      -> one bounded action OR ABSTAIN
```

Exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This proves one controlled WinForms path, not general desktop accuracy.

---

# Current gate — Stage 26.2E real application E2E

The current qualification application is isolated VS Code, selected as one real medium-complexity app with a strong disposable boundary.

```text
specifically prefixed TEMP root
 -> isolated VS Code user-data/extensions
 -> unique empty disposable .txt
 -> exact unique Code.exe PID/HWND/DesktopState
 -> focused editor precondition
 -> deliberate verifier mismatch => FAIL -> ABSTAIN, zero action
 -> fresh pre-action DesktopState
 -> same window + same focused-editor observation fingerprint
 -> native foreground/hit-test guard
 -> exactly one guarded Unicode delivery
 -> independent autosaved file size/SHA-256 verification
 -> current same-window identity
 -> workspace contains only expected artifact
 -> WM_CLOSE
 -> natural CLI exit
 -> remove isolated TEMP root
 -> rollback PASS
```

Forced CLI terminate/kill is cleanup-only and makes acceptance fail.

Read `STAGE26_2E_REAL_APPLICATION_E2E.md`.

---

# Stage 26.3 — Verified Procedure Runtime / Control Plane integration

After 26.2E, build the deterministic execution Control Plane around accepted components rather than another agent brain.

Core responsibilities:

```text
TaskState
ProgramGraph state/version
procedure trust state
current evidence references/digests
capability scope
transition authorization
checkpoints
postconditions/verifier
bounded retries/recovery branches
resource/action/time budgets
escalation reason
```

A known procedure may progress through multiple verified transitions without a ChatGPT round trip after every action. A new strategy is never invented locally; unknown/incompatible state escalates.

## Candidate-first trust

```text
new/demo
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantined/disabled/rollback
```

## Advanced verifier library

Expand postconditions across UI, files, applications/windows, browser state, artifacts and structured outputs.

## Human demonstration transfer — Stage 26.4

```text
human demonstration
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified replay
 -> changed-state/task replay
```

---

# Optional specialist reasoning

A future `SpecializedReasoningBackend` may receive structured goal/state/procedure evidence and return proposal/confidence/ABSTAIN only. It remains non-authorizing and is not a general planner.

# Future local planner — Track P

A local general planner is retained for future offline/autonomy research after real verified procedure-state data and measured need exist.

Progression is shadow/proposal-only -> bounded subtask planning -> optional general local mode. It remains behind the same deterministic Control Plane authorization/verifier boundary and never silently replaces ChatGPT as default.

See `ROADMAP.md` and `CONTROL_PLANE.md`.

# Multi-chat orchestration

Separate upper layer, not part of Windows/procedure safety core and not a release prerequisite. Under the current constraint do not use Codex/Work unless explicitly re-enabled.

---

# Security/privacy boundaries

- tunnel reachability remains outbound from the user machine;
- normal semantic transport remains direct stdio and does not depend on 1MCP;
- persistent tunnel identity is stored in neutral platform state;
- tunnel secrets stay outside repository/procedure content;
- optional Extension Manager backends do not gain implicit trust or public exposure;
- local inference is bounded, on-demand and non-authorizing;
- planner/model/procedure/extension output never bypasses deterministic authorization;
- raw desktop demonstrations are sensitive local data;
- private chain-of-thought is never procedural/task memory;
- generic Windows code execution remains disabled/unreachable;
- stale, ambiguous or incompatible state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager

Manager/tray owns lifecycle/configuration/diagnostics only. It is neither the general planner nor the procedure Control Plane.

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, project trust/policy/checkpoint wrappers, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, unrestricted autonomous workflow brain, generic model-serving platform or duplicate OpenAdapt implementation while qualified upstream mechanisms cover those needs.

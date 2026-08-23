# Architecture

## Repository-state rule

Resolve live `main` and relevant open PR heads before new work. Historical acceptance SHAs are evidence, not substitutes for the current integration line. Exact accepted heads/result locations belong in `EVIDENCE_INDEX.md`; this document defines durable architectural boundaries.

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

**General planner** means open-ended semantic strategy: interpreting the user's goal, choosing materially different approaches, adapting to novel state and inventing a new strategy. Ordinary ChatGPT is the only **current** general planner.

**Deterministic Control Plane** means execution state/policy machinery for an already-selected bounded goal/procedure: `TaskState`, `ProgramGraph` progression, authorization, checkpoints, verifier/postconditions, retry/recovery ceilings and resource budgets.

The Control Plane may autonomously advance an already-defined transition when current evidence uniquely matches it and every authority/postcondition gate passes. It must ABSTAIN/escalate to ChatGPT instead of inventing a new transition when live state is novel, stale, ambiguous, incompatible or requires new strategy.

Canonical detail: `CONTROL_PLANE.md`.

A future local general planner is a separate optional Track P. It is not part of the current release-critical architecture and, if ever accepted, remains above the same deterministic authority/verifier boundary.

---

# Ordinary Chat -> local transport

Accepted normal path:

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused local capabilities
```

Current accepted normal public tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal diagnostic/adaptive/aggregation infrastructure, not the normal public semantic critical path.

## Transport reliability is a separate authority boundary

Transport supervision owns availability/lifecycle of platform-owned transport processes. It is not the procedure Control Plane and not a planner.

```text
Transport Supervisor
  desired transport state
  exact lifecycle ownership
  layered health observation
  bounded recovery/backoff
  status/receipts
        |
        +-> tunnel-client
        +-> semantic launcher / projection
```

Health dimensions must remain distinct:

```text
local process/MCP readiness
 != remote/control-plane readiness
 != actual current ChatGPT connector route
```

A recovered local runtime is not by itself a completed recovery transaction. Recovery receipt/snapshot publication and continued supervisor heartbeat are independent evidence.

Normal transport recovery keeps the persistent tunnel resource; it must not silently perform remote tunnel create/update/delete or require long-lived admin authority.

---

# Semantic projection boundary

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic request to one reviewed capability action or a small bounded deterministic sequence. It is **not** the local procedure Control Plane.

It must not:

- decide user goals;
- run hidden open-ended plans;
- become procedural memory;
- become a generic model/tool gateway;
- expose a disguised `tool_invoke`;
- hide native desktop/workflow consequence classes behind misleading web semantics.

A procedure/multi-transition capability belongs on a truthful dedicated surface during qualification rather than being smuggled into `workspace_write` or `web_interact`.

The normal five-tool profile remains unchanged until a separate public-contract ADR and physical ordinary-Chat acceptance permit promotion.

---

# Authority, trust and current state

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

Historical action order, remembered coordinates or prior success never outrank live evidence.

---

# Deterministic execution Control Plane

Core responsibilities:

```text
TaskState
exact procedure / ProgramGraph version
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

Preferred execution:

```text
ChatGPT selects applicable known procedure + parameters
 -> Control Plane loads exact version + TaskState
 -> observe live state
 -> exactly one permitted known transition
 -> authorize current capability consequence
 -> act
 -> re-observe
 -> verify expected effect
 -> durable checkpoint / advance
 -> repeat while state remains known
 -> complete OR ABSTAIN/escalate
```

## Checkpoint/resume rule

A checkpoint is evidence for a known program state, not permission to infer an arbitrary interrupted action.

Resume is allowed only when exact retained TaskState/procedure/version/parameters and current state are compatible with a declared resumable checkpoint. An ambiguous mid-transition crash fails closed unless a separately designed write-ahead transaction receipt can prove the pending consequence and ownership.

## Ownership/rollback rule

Content equality alone does not prove ownership. Destructive rollback must require evidence strong enough to prove that the current object is still the object created/owned by the run. For file procedures this means digest plus filesystem-object identity where available; changed/ambiguous identity is left untouched and escalated.

---

# Verifier foundation

```text
before = observe()
authorized = authorize(before, requested_action)
delivery = act(authorized)
after = observe()
verification = verify(before, after, expected_effect)
```

`delivery != success`.

Verifier result classes:

```text
PASS
FAIL
UNKNOWN
```

FAIL/UNKNOWN never silently advance a procedure.

The verifier is independent from planner/model self-report: a model saying “done” is not completion evidence.

---

# Browser capability and local vision

Browser interaction remains structure-first:

```text
fresh accessibility state
 -> exact safe semantic target
      -> semantic action

 -> only an explicitly admitted structural miss
      -> same-session screenshot
      -> local bounded VLM proposal
      -> deterministic target/freshness authorization
      -> one coordinate action OR ABSTAIN
```

Unresolved semantic ambiguity, disabled/non-actionable exact targets and generic semantic action errors do not automatically escalate to vision.

Accepted specialist baseline remains local LFM2.5-VL through the project-owned bounded provider/runtime seam. The model perceives/proposes only; it never grants authority or task completion.

---

# Production Windows capability

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

## Typed execution invariants

```text
127.0.0.1-only local agent where applicable
ephemeral authentication
legacy arbitrary exec absent/disabled
typed bounded input only
stale frame/context refusal
focus-bound keyboard
unique/fingerprint-bound structural action
bounded pointer/scroll
layout-independent Unicode text delivery
generic code-execution route absent
```

Delivery receipts keep completion separate from action delivery.

## Window-scoped observation/authorization

Bind exact process/window identity before traversing native UIA; do not rely on desktop-wide tree walks as the normal path.

`DesktopState` is evidence, not authority. It carries session/application/process generation/window identity, physical coordinate space, focused control, bounded controls, visible text, frame/screenshot digests, provenance and freshness evidence.

A real keyboard target may legitimately be hidden/zero-size (for example an editor's focused accessibility textbox). Focused semantic identity and top-level native window geometry are separate channels. Do not fabricate visible control geometry from focus identity.

## Native visual fallback

```text
current exact-window DesktopState/UIA
 -> safe structural target
      -> fresh structural re-resolution
      -> native UIA delivery

 -> explicitly promoted structural miss only
      -> exact-window screenshot
      -> bounded Grounder proposal
      -> request/role/process/window/frame/coordinate evidence binding
      -> fresh exact-window re-observation
      -> native foreground/root-HWND/PID guard
      -> one bounded guarded action OR ABSTAIN
```

VLM proposal is never authorization.

---

# Procedural substrate

Pinned/qualified OpenAdapt Flow/Capture components are reused/adapted rather than duplicating a generic recorder/compiler/agent framework.

Reuse/adapt responsibilities include:

```text
Flow compiler + Workflow/ProgramGraph
Capture
SkillLibrary/learn/teach lifecycle mechanics
Windows typed backend/agent mechanics where project safety gates accept them
```

The repository owns the stricter integration seams: capability authority, current-state binding, candidate-first trust, checkpoints, verifier/postconditions, bounded rollback/recovery and privacy policy.

A stored procedure may retain native/semantic/UIA and bounded visual/template/geometry evidence, but blind historical absolute-coordinate replay is never primary identity or authority.

## Human demonstration transfer

```text
human demonstration
 -> structured trajectory
 -> compile coordinate-independent procedure evidence
 -> project CANDIDATE
 -> verified replay/regression/variants
 -> trusted reusable only after evidence
```

Raw desktop demonstrations are sensitive local data and require explicit retention/redaction/encryption policy before broad product use.

---

# Qualification-only procedure surface

Stage 26.3 may expose a separate typed `procedure_run` capability only in a qualification profile while the accepted normal profile remains five tools.

Required properties:

- fixed registered procedure id/schema, no generic dispatcher;
- caller cannot select arbitrary path, command, Python executable, backend or raw tool;
- workspace/state/admission are configuration authority, not Chat arguments;
- procedure child receives least-privilege environment and no unrelated transport/OpenAI credentials;
- direct MCP acceptance includes independent postcondition observation;
- ordinary-Chat promotion requires explicit ADR + physical E2E.

---

# Specialist reasoning and future planner

A future `SpecializedReasoningBackend` may receive structured goal/state/procedure evidence and return proposal/confidence/ABSTAIN only. It remains non-authorizing.

Future optional local general planner Track P progresses only after real verified procedure-state data and measured need:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planning
 -> P2 optional general local mode
```

It remains behind deterministic capability authorization/verifier boundaries and never silently replaces ordinary ChatGPT default.

---

# Multi-chat orchestration

Multi-chat/Codex orchestration is a separate upper layer, not part of Windows/procedure safety core and not a release prerequisite. Under the current project constraint, do not use Codex/Work unless explicitly re-enabled by the user.

---

# Security/privacy boundaries

- tunnel reachability remains outbound from the user machine;
- normal semantic transport remains direct stdio;
- tunnel secrets stay outside repository/procedure content and must not leak into unrelated capability children;
- local inference is bounded, on-demand and non-authorizing;
- planner/model/procedure output never bypasses deterministic authorization;
- current state outranks remembered history;
- raw desktop demonstrations are sensitive local data;
- private chain-of-thought is never procedural/task memory;
- generic Windows code execution remains disabled/unreachable;
- stale, ambiguous or incompatible state fails closed;
- artifact/model/Python/OpenAdapt reproducibility must become release-grade before stable distribution.

## Windows manager / supervisor

Manager/tray and Transport Supervisor own lifecycle/configuration/availability only. They are neither the general planner nor the procedure Control Plane.

Desired user/platform state and exact runtime ownership are separate concepts. A future product supervisor should persist explicit desired state independently from current owner identity; ownership must still be revalidated under serialized lifecycle authority before mutation.

# Ownership rule

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, project trust/policy/checkpoint wrappers, focused missing-boundary adapters, tests and authoritative context.

It does not own a generic AI gateway, unrestricted autonomous workflow brain, generic model-serving platform or duplicate upstream recorder/compiler implementation while qualified upstream mechanisms cover those needs.

# Stage 26 — Verified Procedural Execution / Demo2Workflow

## Status

**AUTHORITATIVE PROCEDURAL DESIGN; implementation resumes at Stage 26.3 after Stage 26.2E real-app acceptance.**

Older revisions of this document described 26.1B as next and treated 26.3 as the future Windows desktop surface. That chronology is historical and superseded.

Current sequence:

```text
26.1A/B OpenAdapt core + Capture qualification — accepted
26.1C-E Windows executor/UIA qualification — accepted
26.2A-D production Windows observation/grounding/routing — accepted/merged
26.2E real application E2E — active
26.3 Verified Procedure Runtime / deterministic Control Plane — next after 26.2E
26.4 Human Demo -> transferable verified candidate skill
```

## Goal

Let ordinary ChatGPT use previously successful procedures without either extreme:

- ChatGPT micromanaging every deterministic low-level action; or
- a second current local general planner freely deciding what to do.

Target split:

```text
ordinary ChatGPT
  general task understanding / strategy / procedure applicability / adaptation
       |
       | selected goal / procedure / parameters
       v
local deterministic execution Control Plane
  TaskState
  ProgramGraph current node
  capability policy / authorization
  checkpoints
  verifier/postconditions
  bounded retry/recovery
  budgets / escalation
       |
       v
accepted Files / Browser / Windows capabilities
       |
       v
observe -> authorize -> act -> verify -> checkpoint
       |
       +-> next known transition
       +-> ABSTAIN/escalate to ChatGPT on novel state
```

A procedure is not mere passive advice, but it is also not authority. Once ChatGPT selects an applicable procedure, the Control Plane may progress through predeclared transitions only when current state, action scope and postcondition all validate.

Canonical Control Plane contract: `CONTROL_PLANE.md`.

## Qualified upstream substrate

Pinned and target-tested:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Use/adapt:

- Flow compiler + `Workflow` / `ProgramGraph`;
- Capture;
- SkillLibrary version/provenance/regression/learn/teach mechanics;
- accepted Windows backend mechanics where still applicable.

Do not build a competing generic recorder/compiler/skill framework unless an actual blocker is demonstrated.

## UI-Mate relationship

Tencent/UI-Mate remains a useful demonstration-guided workflow/state reference. The project adopts the idea that rich trajectories can become compact reusable state/procedure evidence, not its full local GUI-planner architecture.

The current default general planner remains ordinary ChatGPT.

## Procedure trust

Project trust stays stricter than any upstream bootstrap shortcut:

```text
new demonstration / compiled procedure
 -> project CANDIDATE
 -> same/near-state replay evidence
 -> regression/variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled / rollback
```

One demonstration never becomes permanent product trust automatically.

Procedure trust and action authorization are separate.

## Current-state priority

```text
current observed state
 > verifier/postcondition criteria + current goal
 > trusted procedure evidence
 > historical low-level action sequence
```

A remembered procedure must be adapted by ChatGPT or abandoned when current state no longer matches a permitted deterministic branch.

## Compiled procedure evidence

Compiled procedures may retain:

- semantic/native/UIA locators;
- structural predicates;
- bounded visual/OCR/template/geometry evidence;
- abstract actions/transitions;
- expected postconditions;
- recovery branches;
- provenance/version metadata.

They must not use blind historical absolute-coordinate replay as authority or primary identity.

## Deterministic procedure progression

After ChatGPT selects a procedure:

```text
load exact procedure version
 -> create/resume TaskState
 -> observe live state
 -> match exactly one permitted transition
 -> check procedure/capability trust/scope
 -> authorize current action
 -> execute bounded capability
 -> observe result
 -> verify explicit effect
 -> persist checkpoint
 -> advance node
```

This loop may repeat locally while every state remains known/permitted.

### Mandatory escalation conditions

Stop local progression and return a structured escalation/ABSTAIN reason when:

- no transition matches current state;
- incompatible multiple transitions match;
- current evidence is stale/ambiguous/UNKNOWN;
- capability scope/consequence is not authorized;
- expected effect FAILs and no predeclared safe recovery branch applies;
- recovery/retry/action/time/resource budget is exhausted;
- procedure assumptions are materially invalid;
- continuing requires a new semantic strategy or user-goal interpretation.

The Control Plane does not improvise a new workflow to avoid escalation.

## Checkpoints and recovery

Longer procedures require explicit state rather than hidden conversational memory.

Checkpoint should record at least:

```text
task_id
selected procedure + version
current ProgramGraph node
verified completed transitions
current observation/evidence references
authorized capability scope
pending verifier criteria
last delivery receipt
last verification result
retry/recovery counters
rollback metadata
escalation reason
```

Recovery is permitted only through known bounded recovery branches or a fresh ChatGPT decision.

## Completion semantics

Neither ChatGPT, a local model, a stored procedure nor a future planner may assert completion as authority.

```text
before
 -> authorized action
 -> delivery
 -> after
 -> verifier
      PASS -> checkpoint/advance/complete
      FAIL -> bounded recovery or stop
      UNKNOWN -> observe/ABSTAIN/escalate
```

Prefer deterministic/native/system-of-record evidence where available.

## Procedural data/privacy

Raw trajectories may include actions, current state, structural evidence, screenshots, result/effect evidence and error/abstain classifications.

Never persist private chain-of-thought.

Raw desktop capture is sensitive local data. Long-term arbitrary capture requires explicit storage ownership, retention/expiry, redaction, secret filtering, deletion, encryption and export/sync policy.

## Specialist perception

Local LFM2.5-VL F16 remains proposal-only. It can help ground a current transition target when deterministic structure is insufficient, but cannot select procedure, authorize action or declare completion.

## Stage 26.3 implementation target

### 26.3A — candidate-first trust adapter + core TaskState/progression

Implement the smallest integration around qualified OpenAdapt structures:

- exact procedure version loading;
- project CANDIDATE/trust wrapper;
- structured TaskState;
- current node + permitted transition resolution;
- current-state precedence;
- deterministic escalation reasons;
- no new general planner.

### 26.3B — advanced verifier/postcondition library

Expand beyond current top-level-field verifier:

- file existence/hash/content;
- application/window/process state;
- UI state/selected/focused/enabled values;
- browser state;
- artifact creation/export;
- structured output;
- rollback/cleanup evidence.

### Checkpoint/recovery/budget requirement

Whether implemented in a separate 26.3C PR or folded into A/B, Stage 26.3 is incomplete without:

- persistent checkpoints;
- retry ceilings;
- bounded known recovery branches;
- action/time/resource budgets;
- deterministic escalation.

## Stage 26.4 — Human Demo -> transferable skill

After 26.3:

```text
human demonstration
 -> Capture
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verifier-controlled replay
 -> changed-state/task replay
```

Acceptance is not blind macro reproduction. It must prove live re-resolution and safe behavior when the new state differs.

## Public contract relationship

Procedure/control-plane machinery must not be hidden inside `semantic-projection` or misleadingly exposed as `web_interact`.

The current five public tools remain until a dedicated ADR adds truthful desktop/procedure capabilities and passes ordinary-Chat acceptance.

## Future local planner — Track P

A local general planner remains a deliberate future direction, not a forbidden concept.

It is deferred until verified procedure-state data and measured need exist. First research mode is shadow/proposal-only; later bounded subtask planning may be evaluated; optional general local mode requires parity/safety/resource evidence.

Even a future planner remains above the deterministic Control Plane and cannot self-authorize actions or bypass verifier gates.

Read `ROADMAP.md` and `CONTROL_PLANE.md`.

## Acceptance gates before verified procedures are product-accepted

1. no blind historical coordinate replay as authority;
2. current state overrides remembered procedure;
3. one success/demo does not silently become product-trusted;
4. private reasoning/secrets are excluded from reusable state;
5. raw capture privacy policy is explicit before arbitrary long-term storage;
6. malformed/stale/incompatible procedure fails closed;
7. completion requires verifier/effect evidence;
8. retrieval/selection cannot authorize an action;
9. deterministic local progression only follows predeclared transitions;
10. unknown/novel strategy escalates to ChatGPT;
11. recovery/retry is bounded;
12. checkpoint/provenance/versioning/rollback are deterministic;
13. generic Windows code execution remains disabled/unreachable;
14. no current second general planner is introduced;
15. future planner research remains proposal-only until explicitly accepted.

# External Execution Reuse Strategy — OpenAdapt and UFO

Status: **AUTHORITATIVE INTEGRATION DIRECTION**.

This document records how `chat-agent-platform` may reuse OpenAdapt and Microsoft UFO/UFO² mechanics without replacing project-owned authority, WorkingState, verification, recovery or completion boundaries.

`ARCHITECTURE_REUSE_BASELINE.md` is the canonical prior-lineage comparison point for fresh Stage Research. This document supplies detailed rationale; it does not make an upstream component automatically valid for every new consumer.

## Executive decision

The project should:

- keep ordinary ChatGPT as the only current general planner;
- keep the deterministic project Control Plane as owner of capability authority, WorkingState, recovery/reconciliation budgets, verification semantics and independent task completion;
- reuse OpenAdapt primarily for procedure compiler/IR/replay/checkpoint/effect-evidence/capture mechanics **where fresh Stage Research proves fit**;
- reuse UFO/UFO² selectively for focused Windows/Office UIA/Win32/WinCOM/application mechanics;
- never treat upstream completion/effect verdicts as unconditional project `PASS`/`DONE`;
- never import UFO HostAgent/AppAgent/Galaxy as a second current AgentOS/planner hierarchy;
- keep the accepted public semantic surface unchanged unless a later consequence-class decision explicitly widens it.

Target boundary:

```text
ordinary ChatGPT
       |
       v
project deterministic Control Plane
  authority / WorkingState / recovery / budgets
       |
       +--> project Files / Browser / Windows capabilities
       |
       +--> selected OpenAdapt procedure mechanics
       |
       +--> selected UFO-derived app/Windows mechanics
       |
       v
normalized current evidence
       |
       v
PROJECT Verification Kernel
       |
       v
PROJECT independent Finish Gate
```

External engines may execute or observe inside admitted scope. They do not own final project authority or completion semantics.

## Project-owned boundary

These remain project-owned:

```text
user intent / selected task scope
AVAILABLE -> ACTIVE -> AUTHORIZED lifecycle
ExpectedEffect binding
freshness / subject / stream / identity checks
capability-spanning WorkingState
logical operation / retry / reconciliation state
LoopGuard / budgets / StagnationReport
policy and safety gate
Verification Kernel PASS | FAIL | UNKNOWN
independent Finish Gate DONE | NOT_DONE | UNKNOWN
public Chat-facing semantic contract
```

The invariant is:

```text
external component proposes / executes / observes
project Control Plane decides authority
project Verification Kernel decides transition status
project Finish Gate decides task completion
```

## OpenAdapt role

### Qualified sources

Exact qualified versions/pins belong to `config/stage26-openadapt-lock.json` and supply-chain owner files. Do not duplicate transient pins into the architecture reuse baseline.

Current selected OpenAdapt role families are:

```text
demonstration capture / compile
Workflow / ProgramGraph IR
deterministic healthy-path replay
procedure-local checkpoint / resume
teach / correction / candidate lifecycle mechanics
effect contracts / effect-verifier evidence
certification / effect coverage
procedure-local execution reporting
```

These mechanics are attractive because rebuilding generic recorder/compiler/replayer/checkpoint/certification machinery would duplicate mature upstream work.

### Effect evidence is not project authority

An OpenAdapt verifier result is provenance-bearing **evidence**.

Conceptually:

```text
OpenAdapt verifier result
 -> narrow project evidence adapter
 -> subject/effect identity + provenance + freshness
 -> project ObservationSnapshot / ExpectedEffect
 -> project Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

Therefore a positive upstream verdict may still produce project `FAIL` or `UNKNOWN` when subject identity, stream/freshness, effect-contract identity, required evidence or provenance does not satisfy project policy.

Never use:

```text
upstream CONFIRMED == project PASS
```

as an unconditional mapping.

### Procedure-local resume is below WorkingState

OpenAdapt checkpoint/resume may be useful for one compiled procedure, but it does not own capability-spanning project state.

Relationship:

```text
project WorkingState
  -> selected procedure id/version/node
  -> optional external procedure checkpoint reference
  -> current capability/evidence/authorization/reconciliation state
```

OpenAdapt state must not replace project WorkingState or independent recovery authority.

### Capture privacy boundary

Production demonstration capture requires explicit local scope, retention/deletion policy, redaction/masking where appropriate, sensitive-data handling and no mandatory cloud dependency.

OpenAdapt Cloud is not a baseline product dependency.

## Microsoft UFO / UFO² role

Reuse expensive Windows/application mechanics selectively:

```text
UIA
Win32
WinCOM
application-specific introspection
Excel / Word / PowerPoint / Outlook patterns
hybrid GUI + native/API mechanics
control-detection patterns
isolated/non-disruptive desktop ideas where applicable
```

These belong behind focused project-owned adapters with explicit operation/identity/observation/ExpectedEffect/verification boundaries.

Do **not** adopt as current authority:

```text
UFO HostAgent planner hierarchy
UFO AppAgent planner hierarchy
UFO task-completion authority
UFO model-routing/configuration as product authority
UFO³ Galaxy / Constellation orchestration
raw UFO MCP catalogs exposed directly to ordinary ChatGPT
```

Preferred shape:

```text
ChatGPT planner
 -> project Control Plane
 -> one focused Office/Windows adapter
 -> current project evidence
 -> project Verification Kernel / Finish Gate
```

UFO³ Galaxy remains deferred until multi-device orchestration is an observed bottleneck and then requires fresh architecture research.

## Current Stage 26 mapping

Historical #114/#115 Windows verification work is complete; it is not an active integration constraint anymore.

### Stage 26.3B — accepted/closed

Shared Verification Kernel + Finish Gate is accepted for recorded representative file/Browser/Windows scope. Do not reopen that stage merely to adopt OpenAdapt/UFO.

### Stage 26.3C — project-owned state/recovery foundation accepted

PR #124 accepted the L1 WorkingState/reconciliation/budget/LoopGuard foundation without production procedure wiring.

The current production integration must preserve the project-owned state/authority boundary while comparing any procedure-local custom mechanics with the previously selected OpenAdapt roles.

At this snapshot draft #126 has re-entered strengthened Stage Research and currently returns `NARROW` for a process-restart workspace-artifact integration. Its comparison includes procedure-local checkpoint/resume as a prior selected OpenAdapt role; the draft must explain precisely what upstream semantics do or do not cover before retaining custom prepared-intent/reconciliation mechanics.

Draft implementation is not acceptance.

### Pre-26.4 bounded OpenAdapt spike

After the current 26.3C production recovery shape is accepted, run a bounded integration spike only after a fresh Architecture Lineage comparison:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> upstream effect evidence
 -> project evidence adapter
 -> project Verification Kernel
 -> project Finish Gate
```

Acceptance requires:

- no new raw public workflow/tool catalog;
- no generic Windows/shell/Python authority;
- deterministic healthy replay where upstream supports it;
- project authorization and evidence binding remain authoritative after resume;
- upstream verdict preserved as provenance, never substituted for project verification;
- capture/privacy remains bounded/local;
- exact selected upstream version is compatibility-tested.

If the exact role does not fit, keep the component qualified but outside production rather than forcing architecture around it.

### Stage 26.4 — primary procedure/capture reuse target

If revalidated, prefer upstream mechanics for demonstration -> candidate procedure, compile/IR, replay, checkpoint/resume, correction and certification/effect coverage.

Project trust remains:

```text
one demo/success -> at most CANDIDATE
 -> replay/regression/variant evidence
 -> project verifier/Finish Gate evidence
 -> promoted reusable skill
```

### Stage 26.5 — selective Office reuse

Adopt one application adapter at a time. Each must define:

```text
allowed operations
application/document identity
observation schema
ExpectedEffect schema
freshness rules
authority requirements
recovery/rollback limits
strongest available independent effect evidence
L1/L2/L3 acceptance
```

## Version / supply-chain rule

Keep external reuse behind small project adapters. Record exact version/commit/license/runtime constraints in lock/supply owners rather than duplicating pins across architecture prose.

Upgrade only after a measured bug/security/capability reason:

```text
need
 -> review upstream diff
 -> update pin
 -> compatibility tests
 -> relevant physical/L3 gate when behavior/authority changes
```

The current OpenAdapt lock already reflects the accepted six-tool semantic contract. Older prose claiming that the lock still refers to five tools is superseded and must not be revived.

## Why reuse remains valuable

The project does not need to differentiate itself by rebuilding browser automation, Windows controls, capture or generic workflow IR.

The intended product value is the composition:

```text
small truthful Chat-facing boundary
 + explicit scoped authority
 + current-state identity/freshness
 + project-owned WorkingState/reconciliation/LoopGuard
 + independent Verification Kernel
 + independent Finish Gate
 + source/effect acceptance discipline
 + planner-independent deterministic Control Plane
```

Reuse is preferred when it lets engineering effort concentrate on those boundaries rather than commodity mechanics.

## Non-goals

This strategy does not:

- make OpenAdapt/UFO production-approved merely by documentation;
- replace fresh Stage Research for a material new consumer;
- add public desktop/office/shell/Python/generic-dispatch tools;
- accept OpenAdapt Cloud as baseline dependency;
- accept UFO HostAgent/AppAgent/Galaxy as current planner/authority;
- declare broad Windows/Office reliability proven;
- replace required exact-head CI, representative L3 or physical evidence.

# External Execution Reuse Strategy — OpenAdapt and UFO

Status: **AUTHORITATIVE INTEGRATION DIRECTION**.

This document records how `chat-agent-platform` may reuse OpenAdapt and Microsoft UFO/UFO² mechanics without replacing project-owned authority, WorkingState, verification, recovery or completion boundaries.

`ARCHITECTURE_REUSE_BASELINE.md` is the canonical prior-lineage comparison point for fresh Stage Research. This document supplies detailed rationale; it does not own active PR state, release order or acceptance evidence.

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

Exact qualified versions/pins belong to `config/stage26-openadapt-lock.json` and supply-chain owner files. Do not duplicate transient pins into architecture prose or the reuse baseline.

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

A positive upstream verdict may still produce project `FAIL` or `UNKNOWN` when subject identity, stream/freshness, effect-contract identity, required evidence or provenance does not satisfy project policy.

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

When a release-critical consumer proposes custom procedure-local persistence/recovery mechanics, Stage Research must explicitly compare those mechanics with the prior selected OpenAdapt role and explain whether the decision is `KEEP`, `REUSE_MORE`, `REFINE`, `REPLACE`, `DEFER` or `REJECT`.

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

## Stage interaction

Stage/release ordering belongs to `ROADMAP.md`; active work belongs to `CURRENT_STATE.md`. This strategy only constrains how external mechanics may be reused when a stage needs them.

Durable stage interaction rules are:

- accepted project Verification Kernel / Finish Gate semantics remain authoritative regardless of external executor/verifier choice;
- accepted project WorkingState/reconciliation/LoopGuard semantics remain project-owned and capability-spanning;
- a new consumer must revalidate the exact upstream role rather than assuming an old qualification automatically transfers;
- fresh Stage Research must compare custom mechanics against previously selected external roles before duplicating them;
- upstream procedure/session state may be referenced from project state but must not replace project-wide authority/state ownership.

## Bounded OpenAdapt spike direction

When the roadmap reaches the bounded OpenAdapt integration spike, use a fresh Architecture Lineage comparison and test an explicit composition such as:

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

## Candidate-skill / Office reuse direction

For demonstration-to-skill work, prefer revalidated mature upstream mechanics for capture, compile/IR, replay, checkpoint/resume, correction and certification/effect coverage rather than rebuilding them locally.

Project trust remains:

```text
one demo/success -> at most CANDIDATE
 -> replay/regression/variant evidence
 -> project verifier/Finish Gate evidence
 -> promoted reusable skill
```

For Office breadth, adopt one focused application adapter at a time. Each must define:

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

The current OpenAdapt lock reflects the accepted six-tool semantic contract. Older prose claiming that the lock still refers to five tools is superseded and must not be revived.

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
- own active PR/design snapshots or release order;
- add public desktop/office/shell/Python/generic-dispatch tools;
- accept OpenAdapt Cloud as baseline dependency;
- accept UFO HostAgent/AppAgent/Galaxy as current planner/authority;
- declare broad Windows/Office reliability proven;
- replace required exact-head CI, representative L3 or physical evidence.

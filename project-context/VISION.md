# Vision

Let ordinary ChatGPT use the user's own Windows computer as a modular professional capability surface without requiring a custom cloud backend or a competing current general AI planner.

The product stays ChatGPT-first while becoming substantially more autonomous in execution:

```text
ordinary ChatGPT
  = current general reasoning
  + task planning / strategy
  + procedure selection
  + adaptation to novel state

local companion
  = scoped capabilities
  + deterministic/native observation
  + bounded specialist perception
  + deterministic execution Control Plane
  + procedural memory
  + authorization / verification
  + checkpoints / bounded recovery / budgets
```

The key distinction is **general planning vs deterministic execution control**.

The local Control Plane should be able to continue an already-selected known procedure through multiple independently authorized and verified state transitions without asking ChatGPT after every low-level action. When the live state is novel, ambiguous, stale, incompatible or requires new strategy, it stops and escalates to ChatGPT.

This gives long-horizon autonomy without immediately duplicating ChatGPT with a second general agent brain.

Canonical contract: `CONTROL_PLANE.md`.

## Replaceable local foundation

The bridge should remain boring and replaceable where possible:

- official Secure MCP Tunnel;
- small truthful Chat-facing semantic contract;
- replaceable focused backends;
- task-driven component/model activation;
- qualified upstream procedural components;
- project-owned deterministic state/policy/verification seams only where product safety/integration requires them.

Capability growth should not mean plugin/tool explosion or permanent process growth. Concrete local programs are selected from actual user tasks/evidence rather than precommitted as a fixed application list.

## User-teachable direction

The long-term product should allow successful work or a human demonstration to become a versioned candidate procedure that can later execute safely against current state.

```text
successful work / human demo
 -> structured trajectory
 -> ProgramGraph / candidate procedure
 -> replay/regression/variant evidence
 -> trusted reusable procedure
 -> future ChatGPT task
 -> ChatGPT selects applicable goal/procedure
 -> local Control Plane progresses known transitions
 -> current state authorization + verification at every step
 -> ABSTAIN/escalate on novelty
```

Remembered procedure is not blanket authority and not blind macro replay. Current observed state remains authoritative. Completion is verified.

## Windows desktop direction

The Windows desktop foundation is no longer merely future work: bounded production runtime, DesktopState, native visual Grounder and structure-first UIA -> vision routing are accepted through Stage 26.2D.

Stage 26.2E is the first real-application E2E. After it, Stage 26.3 integrates deterministic procedure/control-plane execution over accepted capabilities.

Native/deterministic evidence stays preferred; screen/vision is bounded fallback; keyboard/mouse actuation remains guarded and fail-closed.

## Future local planner direction

A local general planner is not prohibited forever. It is explicitly retained as optional future **Track P — Local Planner / Offline Autonomy** after verified procedure-state data and measured need exist.

Possible reasons include offline operation, planning round-trip latency, parallel/multi-machine work or deployment/privacy constraints.

It should mature through:

```text
shadow/proposal-only
 -> bounded subtask planner
 -> optional local general-planner mode
```

Even then, planner output never bypasses the deterministic Control Plane's capability policy, authorization and verifier.

The default product can therefore remain ChatGPT-manager-first while preserving a credible path to stronger local/offline autonomy later.

## Public capability direction

Current five public semantic tools remain the accepted contract until a dedicated ADR proves truthful desktop/procedure capabilities are needed. Do not hide native consequences inside web semantics or generic dispatch.

## Product-ready direction

A stable product requires:

- real-app desktop evidence;
- verified deterministic procedure runtime;
- candidate-first human-demo transfer;
- normal installation/update/repair/rollback/restart recovery;
- clean-user E2E;
- release-grade dependency/model/procedure artifact reproducibility;
- explicit privacy/security boundaries for task state, procedural memory and desktop capture;
- optional future planner research kept separate from release-critical safety evidence.

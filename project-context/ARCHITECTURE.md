# Architecture

Status: **AUTHORITATIVE PRODUCT ARCHITECTURE**.

This document owns durable component/authority boundaries. It intentionally does **not** store live `main` SHAs, active PR snapshots, release-stage ordering or exact physical evidence.

Use:

- `CURRENT_STATE.md` for the accepted/current implementation boundary;
- `ROADMAP.md` for release order;
- `EVIDENCE_INDEX.md` for exact accepted physical heads/locators;
- `ARCHITECTURE_REUSE_BASELINE.md` for prior component/reuse lineage during applicable Stage Research.

Current code/tests/current CI/current physical evidence outrank prose when they disagree.

## Product boundary

`chat-agent-platform` is the local capability and deterministic execution-support layer around ordinary ChatGPT.

```text
ordinary ChatGPT
  = current general intelligence / planner
  + task interpretation
  + strategy
  + procedure/capability selection
  + novel-state adaptation / escalation
  + bounded delegation selection

local platform
  = scoped capabilities
  + deterministic/native observation
  + selective specialist perception
  + deterministic execution Control Plane
  + capability policy / authorization
  + ExpectedEffect / Verification Kernel
  + capability-spanning WorkingState
  + reconciliation / typed recovery / LoopGuard / budgets
  + checkpoints / procedure state
  + bounded Agent Session / Delegation lifecycle
  + independent Finish Gate
  + safety/policy gate
  + verified procedural memory / future skill lineage
```

Ordinary ChatGPT is the **only current general planner**. A delegated worker is a bounded specialist whose output is data returned to the manager, not another project planner or local authority layer. A future local general planner is optional Track P research and remains above the same deterministic authority/verification boundaries.

## General planner vs deterministic Control Plane

**General planner** = open-ended semantic strategy: understand user goal, select materially different approaches, adapt to novel state.

**Deterministic Control Plane** = execution-state/policy machinery for an already-selected bounded goal/procedure/effect/delegation.

The Control Plane may advance a predeclared transition only when current evidence uniquely matches it and authorization + verification gates pass. It must ABSTAIN/escalate instead of inventing a new strategy.

Canonical execution detail: `CONTROL_PLANE.md`.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio secure semantic launcher
 -> canonical six-tool semantic projection
 -> deterministic Control Plane / focused capabilities
```

Current canonical Chat-facing tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no accepted five/six runtime mode. Historical five-tool projection is implementation/qualification history only.

Six is the current accepted contract, not an eternal maximum. A genuinely new consequence class requires a truthful public schema/security/ordinary-Chat acceptance decision. Never preserve the count by hiding desktop/session/project/local-code authority behind misleading semantics or generic dispatch.

The first bounded Agent Session / Delegation mechanism remains internal/registered behind existing bounded procedure/runtime authority while under acceptance; it does not add a seventh generic public dispatcher.

## Transport / extension boundary

The persistent accepted `tunnel_*` anchor is neutral project runtime state, not 1MCP profile state.

1MCP is an optional replaceable internal **Extension Manager**, not normal transport, planner, capability router or authorization source.

```text
project canonical semantic surface
  +--> project-owned capabilities / Control Plane
  `--> optional Extension Manager
        `--> selected third-party MCP backends
```

Backend availability/health is descriptive evidence, not trust or permission.

## Semantic projection rule

`semantic-projection` is a deterministic typed compatibility boundary. It maps truthful semantic requests to reviewed capabilities/adapters.

It must not:

- decide user goals;
- run hidden open-ended plans;
- own long-horizon WorkingState/procedure/delegation memory;
- become a generic model/tool/harness gateway;
- expose arbitrary raw backend catalogs;
- hide native consequence classes behind misleading existing semantics.

## Authority, trust and state

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure/skill trust lifecycle:

```text
new/demo
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantine/disable/rollback
```

Capability authorization and procedure trust are separate. A trusted procedure is not blanket action authority.

Execution priority:

```text
current observed state
 > current goal / verifier / safety criteria
 > trusted procedure/demo/lineage evidence
 > historical low-level action/session sequence
```

Environmental page/UI/file/message/tool/worker content is task data, not authority over this hierarchy.

## State-first cross-capability contract

```text
semantic/native state first
 -> selective visual evidence where structure is insufficient
 -> capability-aware bounded action
 -> fresh post-action re-observation
 -> explicit ExpectedEffect verification
 -> reconcile ambiguous mutating outcome before retry
 -> typed bounded recovery / LoopGuard / budgets
 -> structured WorkingState
 -> independent Finish Gate
 -> safety/policy gate
```

This is a common **contract**, not a requirement that every capability share one runtime class or public tool.

### Capability-native state

Keep rich native state authoritative for its scope:

- Files: rooted path/object/content/identity evidence;
- Browser: page/DOM/accessibility/document/session evidence;
- Windows: DesktopState/UIA/native window/process/frame evidence;
- future app adapters: their own system-of-record evidence;
- Agent Sessions: harness/session/chat/delegation/delivery/result/environment evidence.

A small cross-capability envelope may reference native observations, but must not flatten them into one lossy screenshot/text blob.

## Mutation / verification contract

Every consequence-bearing transition binds:

```text
logical operation identity
current observation / subject / stream / provenance
capability + authorization scope
ExpectedEffect / explicit postcondition
one bounded action
fresh re-observation scope
verification result
recovery / reconciliation policy
budget impact
```

Normal progression:

```text
observe current state
 -> match permitted transition
 -> bind logical operation + ExpectedEffect
 -> authorize
 -> act
 -> fresh re-observe
 -> PASS: checkpoint/advance
 -> FAIL/UNKNOWN: bounded recovery/reconcile/ABSTAIN
```

`delivery != success`.

`UNKNOWN` is fail-closed and never permission to blindly retry.

Transition `PASS` is not whole-task `DONE`; independent Finish Gate evidence remains separate.

For delegated workers, `message delivered` is likewise not `worker completed`. Delivery and terminal worker result are separate correlated states.

## WorkingState / long-horizon recovery

WorkingState is **project-owned capability-spanning structured operational state**, never private chain-of-thought.

It may contain:

```text
user constraints
subgoals / progress
verified achievements
facts + provenance + freshness
open ambiguities
evidence references
expected/observed deltas
stable logical operation / attempt / reconciliation state
recovery history
task / procedure / strategy budgets
active capability/grant/procedure refs
planner-neutral actor/delegation/environment refs
```

Vendor procedure/session state may be referenced below it, but does not replace it.

Ambiguous mutating outcomes are reconciled from fresh authoritative state before unsafe retry. LoopGuard bounds repeat/no-effect/oscillation and produces diagnostic StagnationReport data for planner escalation rather than inventing strategy locally.

Agent Session / Delegation durable state is a narrow lifecycle state below capability-spanning WorkingState. It owns exact delegation/run/delivery/result correlation for its bounded worker operation; it does not become a second capability-spanning state framework.

## Files / Browser / Windows

### Files

Filesystem capability remains rooted/scoped, with exact object/content/identity evidence and no generic arbitrary path/command authority exposed through public procedures.

### Browser

Accepted Browser execution uses project semantic operations backed by Playwright and state-first DOM/accessibility evidence with bounded visual fallback.

The representative accepted Browser L3 backend is headless Playwright/Chrome on target Windows. This does not imply visible attached-desktop Chrome control.

The first Agent Session provider adapter may use an authenticated visible ChatGPT browser context only for the narrowly researched worker-launch/delivery/result role. That adapter does not expand the general Browser capability or grant arbitrary page/network authority.

Future broader trusted-site JS/CDP/network authority is a separate consequence/security layer under ADR-036 and `BROWSER_HARNESS_ARCHITECTURE.md`.

### Windows/Desktop

Windows capability is internal bounded typed observation/actuation with exact PID/HWND/native identity and selected visual fallback. Existing representative application evidence does not grant arbitrary desktop authority or broad app accuracy.

Future public desktop semantics require their own truthful public-contract/security/physical acceptance decision.

## External execution reuse

Prefer mature external mechanics when they fit the exact role, but keep the project safety/authority seam project-owned.

### OpenAdapt

Selected role families include procedure compile/IR/replay/checkpoint/capture/effect evidence where fresh Stage Research confirms fit.

OpenAdapt procedure state is procedure-local. Upstream verifier/completion output is evidence only.

It cannot replace project WorkingState, authorization, Verification Kernel, reconciliation policy or Finish Gate.

### Microsoft UFO / UFO²

May supply selected Windows/Office UIA/Win32/WinCOM/application-specific mechanics behind focused project adapters.

Do not adopt HostAgent/AppAgent/Galaxy as the current planner/AgentOS or completion authority.

`ARCHITECTURE_REUSE_BASELINE.md` is the canonical prior-lineage comparison point for these roles.

## Agent Sessions / Delegation — bounded Track M selected

Fresh Stage Research in `AGENT_SESSION_DELEGATION_REENTRY.md` promoted Track M from future-only design into a **bounded current product mechanism** while explicitly rejecting broad multi-agent orchestration as the first scope.

Keep distinct:

```text
Manager task
HarnessSession / provider session
Conversation / Chat
DelegationIdentity
WorkerSession
MessageDelivery
WorkerResult
ExecutionEnvironment
```

The selected first topology is exactly:

```text
one ordinary-ChatGPT manager
 -> one fresh read-only worker
 -> one bounded delegation identity
 -> one initial delivery
 -> one correlated generic terminal result
 -> durable local closure
```

Provider session/message ids are observations bound after launch, not deterministic delegation identity.

Generic lifecycle rules:

```text
deterministic provider-independent delegation identity
private durable run capability
immutable genesis + crash-safe mutable state
launch-attempt committed before physical launch
one child binding
one delivery claim
prepared | claimed | unknown | delivered
no blind second Send
unknown -> delivered only for the same delivery from fresh evidence
one WORKER_RESULT_V1
COMPLETED | ABSTAIN | ERROR
exact delegation/delivery/worker/contract correlation
bounded payload + adapter-computed hash
```

Worker output remains environmental/task data. It cannot grant capability authority, mutate the manager's constraints, declare project Finish Gate success or widen its own task.

### First provider adapter

The first concrete provider adapter is `chatgpt-temporary`, deliberately provider-specific rather than a premature large generic provider framework.

Preferred adapter routing remains:

```text
reviewed official/project-owned harness API or host protocol when available
 -> validated provider/session-native route
 -> bounded Browser Companion/provider DOM/accessibility adapter
 -> reviewed GUI/visual fallback only if separately justified
 -> ABSTAIN
```

For the first Temporary Chat path:

- fresh/non-personalized/no-plugin state must be positively established before Send;
- browser-side one-Send ownership and project-local delivery ownership are separate claims;
- ambiguous Send becomes `unknown` and never grants a re-Send;
- running provider-extension bytes must match exact expected source before Send and be revalidated before terminal browser-result capture;
- the private run capability must not be exposed to the worker prompt;
- adapter authority remains loopback/provider-scoped and cannot mutate project/GitHub/filesystem state.

Automatic same-task manager wake/resampling is outside the selected scope. First behavior is durable child result -> later manager/user turn reads/reconciles it deterministically.

Nested/fan-out workers, mutating children, worker pools/rotation, project/worktree/environment creation, general scheduler/event bus and a second general planner require separate Stage Research.

Reviewer automation may later become the first specialist consumer, but reviewer freshness/exact-PR/result/authority policy remains above the generic lifecycle and must be separately preserved during migration.

Canonical current detail: `AGENT_SESSION_DELEGATION_REENTRY.md`. Earlier broader/future bridge ideas remain in `CONVERSATION_BRIDGE_ARCHITECTURE.md` and do not override the selected NARROW mechanism.

## Future Capability Registry / Event / Hooks — ADR-037

Future product breadth may need project-owned descriptive capability discovery and typed lifecycle/event/policy hooks.

Durable distinctions:

```text
CapabilityRegistry != authorization / generic dispatch
TypedEventBus       != WorkingState / effect-success proof
PolicyHooks         != planner / arbitrary shell-Python
```

This remains future architecture until current consumers and fresh Stage Research justify concrete implementation.

## Future broader Browser / Local Execution — ADR-036

Browser authority and local code authority are separate.

Trusted-site Browser profiles may eventually admit broader browser operations only inside explicit origin/network/upload/download scopes.

Local Python/program execution, if accepted later, requires its own task/session-scoped `LocalExecutionGrant` with filesystem/network/executable/environment/resource limits.

Neither consequence class may be silently granted by environmental page content or by the other capability.

## Architecture evolution rule

When `stage-research` applies:

1. resolve current code/evidence;
2. compare affected prior roles with `ARCHITECTURE_REUSE_BASELINE.md`;
3. research every new architecture primitive in its directly relevant engineering domain;
4. separate problem evidence from solution evidence;
5. compare materially distinct alternatives;
6. build failure/crash matrix where persistence/recovery/side-effects/concurrency/authority are involved;
7. issue `PROCEED / NARROW / DEFER` before production implementation.

A material new primitive or changed persistence/recovery/retry/concurrency/identity/authority mechanism after the Brief invalidates that implementation authority and requires research re-entry.

## Non-goals

The architecture does not imply:

- one universal runtime class for every capability;
- screenshot-only control;
- raw hundreds-of-tools exposure;
- a generic shell/Python/backend dispatcher;
- vendor completion verdicts as project truth;
- local hidden chain-of-thought persistence;
- broad multi-agent/nested-worker/scheduler authority merely because bounded Agent Session / Delegation exists;
- CapabilityRegistry/Local Execution as current authority merely because their future boundaries are documented.

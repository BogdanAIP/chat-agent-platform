# Agent Session / Delegation Re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-01**

Accepted BASE at research start: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skills at that BASE:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## 1. Stage goal

Promote the already-proposed Track M Agent Session / Delegation boundary from future architecture into the next bounded CAP product mechanism, without turning CAP into a specialized code-review product.

The first production slice is deliberately narrow:

```text
ordinary ChatGPT manager
 -> create ONE fresh read-only worker chat
 -> bind one bounded task/delegation identity
 -> deliver exactly one initial task message
 -> prove the intended worker/context received that task
 -> observe a structured terminal worker result
 -> bind that result to the exact delegation
 -> persist/reconcile the result under project-owned state
 -> expose it to the manager on a later turn
```

The first worker adapter may target a **non-personalized ChatGPT Temporary Chat** because physical experiments already demonstrated fresh-chat launch/Send/result capture on the user's actual Plus/browser path. The core object/state model must remain provider-neutral so later adapters can target another harness without changing delegation identity or project authority.

This stage is a general agent capability. Code review may later consume it, but reviewer methodology, repository-context construction, code graphs, reviewer benchmarks and reviewer learning are not owned by this stage.

## 2. Current project baseline

Accepted CAP already has:

- exactly six public Chat-facing tools;
- ordinary ChatGPT as the only current general planner;
- deterministic Control Plane authority;
- `WorkingState`, stable mutating-operation identity, bounded budgets and LoopGuard;
- accepted process-crash checkpoint/reconciliation mechanics for the first consequence-bearing procedure;
- Verification Kernel and independent Finish Gate;
- a future Track M architecture that already distinguishes session, conversation, delegation, message delivery and execution-environment identities;
- accepted reviewer-specific local state/procedure wiring from PRs #141/#142;
- experiment-only fresh-chat/browser evidence from PR #145.

The accepted Track M document already states the critical identity rule:

```text
Session identity != Task identity != Message delivery identity
```

and already models `DelegationRecord`, `DeliveryReceipt`, worker ownership, shallow topology, bounded budgets and operation-scoped reconciliation. Therefore this re-entry should **promote/refine existing Track M**, not invent a second session framework.

## 3. Exact stage question

The question is no longer:

> How should CAP implement an automatic reviewer?

It is:

> What is the smallest production Agent Session / Delegation mechanism that lets the current ChatGPT manager safely hand one read-only bounded task to one genuinely fresh child worker and receive a correlated result, while preserving existing project authority and leaving worker-specific intelligence outside the generic runtime?

### Product outcome

After this stage, CAP can use a fresh worker for tasks such as:

- independent semantic review;
- external research;
- security/audit second opinion;
- bounded evaluation;
- other read-only specialist work.

### Explicitly out of scope

- reviewer-specific repository snapshot/context engines;
- code graphs or reviewer retrieval;
- MimiSeek or any other reviewer product internals;
- worker writes to GitHub, filesystem or user applications;
- worker inheritance of manager capabilities;
- arbitrary plugin/tool delegation;
- nested/recursive delegation;
- worker pools or broad fan-out;
- generic scheduler/event bus;
- same-task autonomous manager wake/resampling;
- project/worktree/environment creation;
- long-lived autonomous background workers;
- public expansion beyond the accepted six-tool surface;
- a second general planner inside the local Control Plane.

## 4. Problem evidence

### 4.1 CAP nearly coupled generic worker mechanics to one specialist

The accepted automatic-review work contains useful generic mechanics — fresh context launch, private correlation, durable dispatch state, one-Send ownership and result reconciliation — but current owner documents place them under a reviewer-specific release item and reviewer-specific state names.

Continuing that direction would make a general agent capability evolve inside one specialist workflow, despite Track M already being the intended product boundary for multi-chat/session delegation.

### 4.2 The reviewer experiments proved worker feasibility, not only review feasibility

CAP PR #145 physically demonstrated on the target Windows/Plus/browser path that automation can:

- open a fresh non-personalized Temporary Chat;
- inject a run-bound task;
- perform one automatic Send;
- wait for a structured result;
- capture that result locally.

PASS, STALE and known-finding controls established that the child context can do meaningful independent reasoning. For this stage, the reusable evidence is the **fresh child lifecycle and transport feasibility**. Reviewer-specific quality/context conclusions are outside scope.

### 4.3 Existing Track M already anticipates the correct generic objects

`CONVERSATION_BRIDGE_ARCHITECTURE.md` already separates:

- `HarnessSession`;
- `ConversationSnapshot`;
- `DelegationRecord`;
- `DeliveryReceipt`;
- `ExecutionEnvironment`.

It already states that delivery does not prove worker start/completion, session identity cannot correlate several delegations, worker lifecycle authority must not be inherited, and `UNKNOWN` outcomes require reconciliation before retry.

The missing step is not another architecture family. It is selecting and implementing the first narrow Track M slice.

## 5. Architecture lineage comparison

### General planning / novel strategy

Prior owner: ordinary ChatGPT.

Decision: **KEEP**.

The manager remains the only current general planner. A worker is a bounded child reasoner for an explicit delegated task, not a second local planning layer.

### Agent session / long-lived host lifecycle and orchestration

Prior source: `openai/codex` as `REFERENCE_REVALIDATE_PER_STAGE`, with CAP-owned authority retained.

Decision: **KEEP** the reference-only relationship and **REFINE** the CAP implementation target to one-shot read-only child delegation first.

Codex remains implementation evidence, not a runtime dependency.

### Multi-chat / provider conversation extraction and browser adaptation

Prior source: CtxPort-derived ideas + project Browser Companion / `GenericChatAdapter` direction.

Decision: **REFINE**.

The Browser Companion becomes the first provider adapter beneath Agent Sessions. Provider DOM/UI details must not define generic delegation identity/state.

### Capability-spanning operational state

Prior owner: project `WorkingState`.

Decision: **KEEP**.

Delegation/result references integrate with project operational state rather than creating a competing reasoning/state framework.

### Transition verification and task completion authority

Prior owner: project Verification Kernel + Finish Gate.

Decision: **KEEP**.

A worker result is evidence/data. It cannot self-authorize a CAP consequence or self-declare the manager's entire task complete.

### Automatic-review concurrent ownership / immutable genesis / mutable result state

Prior source: accepted Stage 26.3C file-lock/checkpoint primitives adapted by #141.

Decision: **REUSE_MORE** at the mechanism level, but not by treating reviewer-specific identity as the new generic schema.

The new delegation operation should reuse the accepted lock, exclusive-create and crash-safe checkpoint patterns rather than create another persistence framework. Reviewer-specific parsers/fields remain specialist logic.

### Automatic-review deep-link/composer mechanics

Prior source: experiment PR #138/#145.

Decision: **REUSE_MORE** as the first ChatGPT Browser Companion adapter mechanics.

The generic core must not know ChatGPT DOM selectors or Temporary Chat URL details.

### Automatic-review browser Send ownership

Prior source: MV3 service worker + IndexedDB unique-key claim proposal/experiment.

Decision: **REFINE** into generic `delivery_id` ownership for the Browser Companion adapter.

Exactly-once logical dispatch is generic; the storage implementation is adapter-local and must be tested against browser restart/multi-tab races.

### Automatic-review reviewer authority qualification

Prior role: prove GitHub mutation actions unavailable.

Decision: **DEFER** as reviewer/consumer-specific policy outside the generic session core.

The generic first worker profile is stronger and simpler: **read-only worker**. Any later specialist-specific authority qualification is an adapter/consumer policy layered on top.

### Automatic-review local result submit/reconcile

Prior source: fixed reviewer submit/reconcile procedures.

Decision: **REFINE**.

The useful generic mechanic is durable correlated worker-result closure. `REVIEW_RESULT_V1` parsing remains specialist code; generic core should accept a bounded `WORKER_RESULT_V1` envelope plus task-specific opaque result payload/hash.

### Code-review evaluation harness

Decision: **DEFER** outside this stage.

Reviewer quality is not Agent Session lifecycle quality.

## 6. Architecture primitives and adjacent engineering domains

### Stable delegation identity

Domain: distributed workflow/task identity and idempotency.

Guarantee: one logical delegated task has one stable identity independent of session/chat/message IDs.

### Parent/child ownership

Domain: process supervision, structured concurrency and agent graph lifecycle.

Guarantee: CAP can prove which manager-created child belongs to which parent/delegation and can refuse unrelated/stale results.

### Durable dispatch marker

Domain: crash recovery / write-ahead intent.

Guarantee: restart cannot blindly launch/send a duplicate after an ambiguous attempt.

### Delivery claim

Domain: concurrent single-writer/idempotent delivery.

Guarantee: duplicate tabs/adapters cannot both Send the same logical task.

### Result correlation and closure

Domain: message correlation, workflow completion and state machines.

Guarantee: a late result from the same worker cannot be accepted for the wrong delegation, and only one terminal result closes the operation.

### Capability profile

Domain: least privilege / capability security.

Guarantee: the first child is read-only and cannot inherit manager mutation authority merely because the manager can perform broader actions.

### Provider adapter boundary

Domain: ports-and-adapters / anti-corruption layer.

Guarantee: ChatGPT UI mechanics can change without changing generic session/delegation identity and state contracts.

## 7. Source-code evidence

### 7.1 `openai/codex`

Exact ref: `6127478086e611323e3bff40c943588606c1c571`

Research date: 2026-09-01.

Material paths inspected:

- `codex-rs/core/src/tools/handlers/multi_agents.rs`
- `codex-rs/core/src/tools/handlers/multi_agents/spawn.rs`
- `codex-rs/core/src/tools/handlers/multi_agents/wait.rs`
- `codex-rs/core/src/agent/control.rs`
- current session-lifecycle implementation and recent public issue history.

Classification: `OPEN_IMPLEMENTED` for spawn/wait/parent-child runtime mechanics; persistence/restoration has known incomplete/failure edges.

Lesson: `REFERENCE_ONLY` / `ADAPT_MECHANIC`.

Code-level findings relevant here:

- `spawn_agent` creates a child with explicit parent thread/turn/root-turn metadata and a bounded spawn-depth check;
- child configuration is derived from the live turn and then selectively overridden, rather than being an unstructured prompt-only clone;
- `AgentControl` is scoped to one root session tree and shared with descendants, preserving a parent-owned registry boundary;
- `wait_agent` subscribes to status changes and distinguishes final states from timeout/no-result;
- current public issue #34220 reports a restart bug where a previously completed descendant may reload with `PendingInit`, causing a later wait to miss the completed result;
- issue #38144 reports active-writer/session-resume ownership friction after fork;
- issue #38805 reports stale/orphaned subagent accumulation on Windows.

Mapping to CAP:

- parent/child identity and shallow spawn limits are useful mechanics;
- live status alone is not sufficient durable truth across restart;
- CAP must not copy Codex's authority/tool model or treat thread completion as project task completion.

### 7.2 `OpenHands/OpenHands`

Exact ref: `b4428e1f8529fe726039437c8e54a7e7319986eb`

Research date: 2026-09-01.

Material paths inspected:

- `src/api/launch-child-conversation-client-tool.ts`
- `src/services/child-conversation-launch.ts`
- `src/constants/child-conversation.ts`
- child-launch tests/indexed paths on the same ref.

Classification: `OPEN_IMPLEMENTED` for client-driven child conversation launch; some durability/ownership semantics are browser/frontend-scoped.

Lesson: `REFERENCE_ONLY` / selective `ADAPT_MECHANIC`.

Code-level findings relevant here:

- the child receives a self-contained task and cannot see the parent's conversation history;
- local children can use worktree isolation or a shared workspace; cloud children use isolated sandboxes;
- the tool is explicitly non-idempotent and the frontend keeps a per-parent launch ledger;
- the ledger claims before network work to suppress replay, but corrupt/unavailable browser storage intentionally fails open and accepts duplicate-launch risk;
- worktree creation can fall back to shared mode, explicitly warning that parent and child may then conflict;
- creation acknowledgement and actual conversation availability are separate for cloud launch and require bounded polling.

Mapping to CAP:

- self-contained child task, explicit parent link and isolation choice are useful patterns;
- fail-open duplicate launch on storage failure is unacceptable for CAP's consequence model;
- automatic fallback from isolated worktree to shared workspace would also be too permissive for a future mutating CAP worker; the first CAP worker avoids this by being read-only and not owning project/environment creation.

### 7.3 Temporal durable-workflow domain

Current official Temporal documentation was reviewed as mechanism evidence for durable workflow concepts.

Classification: mature external workflow-engine approach; no dependency selected.

Lesson: `REFERENCE_ONLY`.

Temporal demonstrates the alternative of putting child-workflow identity, crash recovery and durable continuation under a dedicated workflow service. That is much stronger than CAP needs for the first child-chat delegation and would introduce another persistent runtime/service boundary. It remains a useful comparison for future long-lived/scheduled/same-task continuation, not the minimum current design.

## 8. Current ChatGPT adapter evidence

Current OpenAI Temporary Chat documentation (2026-08-27+ behavior) states:

- Temporary Chats start non-personalized by default;
- non-personalized Temporary Chats do not use memory, custom instructions or plugins;
- personalization is fixed when the Temporary Chat starts;
- unsaved Temporary Chats stay out of history and do not create memories;
- files uploaded in Temporary Chat are not saved to the account/Library.

This makes non-personalized Temporary Chat a credible first **read-only child adapter** on personal Plus because it starts without the development chat's plugin/action surface.

This is product behavior, not a generic CAP invariant. The adapter must positively qualify the intended mode; failure to prove it yields `ABSTAIN/UNKNOWN`, not optimistic dispatch.

## 9. Alternatives comparison

### Approach A — continue reviewer-specialized automation as the release-critical architecture

Owner: reviewer-specific local state + Temporary Chat harness.

Strengths:

- much of the state machine already exists;
- directly reduces current manual review friction.

Weaknesses:

- couples generic child-chat lifecycle to one specialist;
- encourages reviewer context/retrieval logic to grow inside CAP;
- creates naming/state/schema migration later when other workers arrive.

Decision: **REJECT as the generic product architecture**. Retain accepted reviewer code until a generic replacement is proven; do not delete it in this stage.

### Approach B — bounded project-owned Agent Session / Delegation core + provider adapter

Owner: CAP Control Plane / WorkingState; ChatGPT Browser Companion is first adapter.

Strengths:

- matches existing Track M architecture;
- reuses accepted persistence/reconciliation primitives;
- keeps six public tools;
- works with current Plus/browser constraints;
- can later support other worker types/adapters;
- does not require a scheduler or external service.

Weaknesses:

- browser UI is still an operationally fragile adapter;
- child-chat creation/Send/result capture need physical evidence and fail-closed reconciliation;
- parent does not automatically receive a new model turn when the child finishes.

Decision: **SELECTED / NARROW**.

### Approach C — embed/reuse a full external agent runtime such as Codex or OpenHands as CAP's worker host

Owner: external agent runtime.

Strengths:

- mature session/subagent lifecycle;
- built-in status, parent-child structures and environment features.

Weaknesses:

- imports a broader planner/tool/authority model;
- conflicts with the project's current ordinary-ChatGPT/Plus path and bounded semantic surface;
- risks duplicating/replacing project WorkingState/Control Plane/verification semantics;
- Codex quota/product constraints and OpenHands runtime requirements are not the intended CAP user path.

Decision: **REJECT as first production dependency**, keep as source-code references.

### Approach D — adopt a dedicated durable workflow/scheduler engine now

Owner: Temporal-like workflow service / generic event-scheduler substrate.

Strengths:

- mature crash recovery, timers, child workflows and durable continuation.

Weaknesses:

- introduces another runtime/service/persistence owner;
- solves same-task wake/scheduling problems that this first stage explicitly excludes;
- significantly increases install/operations complexity before a demonstrated need.

Decision: **DEFER** to future long-lived/scheduled continuation research.

## 10. Selected minimum architecture

### 10.1 Generic objects

Introduce the minimum runtime form of existing Track M concepts:

```text
AgentSessionRef
  adapter_id
  session_id
  conversation_id? 
  ownership
  observation_ref

DelegationRecord
  delegation_id
  parent_task_id / manager_ref
  worker_session_ref?
  task_hash
  status
  delivery_id
  result_contract_id
  result_hash?
  evidence_refs[]

DeliveryRecord
  delivery_id
  delegation_id
  status = prepared | claimed | delivered | unknown
  adapter evidence
```

Do not add the full future Track M object catalog until a real consumer requires each field.

### 10.2 Worker profile

First admitted profile:

```text
fresh_readonly_worker_v1
```

Properties:

- fresh child context;
- no inherited CAP/Local Bridge/GitHub mutation authority;
- no nested worker creation;
- no project/environment mutation;
- one initial task message;
- bounded result size/time;
- structured terminal result.

### 10.3 First provider adapter

`chatgpt_temporary` Browser Companion adapter:

- opens a non-personalized Temporary Chat;
- positively verifies the expected Temporary mode before Send;
- binds a run/delegation marker not guessable from unrelated chats;
- uses adapter-local durable single-delivery claim;
- captures only a result matching delegation/result contract;
- exposes normalized session/result evidence to generic core;
- does not export browser credentials/cookies/tokens.

### 10.4 Result contract

Generic envelope:

```text
WORKER_RESULT_V1

delegation_id=<exact>
worker_kind=<bounded identifier>
status=PASS|FINDINGS|ABSTAIN|ERROR
result_sha256=<...>
...
CAP_WORKER_COMPLETE=<run-bound marker>
```

Task-specific payload remains opaque to the generic lifecycle validator except for size/hash/schema-id and caller-provided specialist validation.

### 10.5 Parent continuation

Out of scope for this stage:

```text
child completes -> automatically obtain another manager model turn
```

Instead:

```text
child completes
 -> durable result closes delegation
 -> next manager/user turn can reconcile/read it deterministically
```

Automatic same-task resampling remains separate future Stage Research.

## 11. Failure / crash matrix

| Boundary | Durable state before failure | Possible physical state | Required evidence / rule | Retry |
|---|---|---|---|---|
| Before delegation genesis | none | no child/no Send | nothing committed | new operation allowed |
| Genesis written, before launch intent | prepared | no child | exact state proves no launch attempt | launch may proceed |
| Launch-attempt marker written, browser launch not observed | launch_attempted | child absent or unknown | reconcile adapter/browser identity; absence must be proven | no blind relaunch while unknown |
| Child created, launch acknowledgement lost | launch_attempted | child exists | find exact run-bound child identity | reuse existing child; do not create second |
| Child exists, before delivery claim | child_bound | no task message | exact child + no claim | claim may proceed |
| Delivery claim committed, before Send | claimed | message absent | adapter-specific evidence distinguishes not-applied vs unknown | retry only if absence proven under same delivery id |
| Send physically applied, acknowledgement lost | claimed/unknown | message exists | fresh child conversation observation must bind exact delivery marker/hash | mark delivered; never Send again |
| Duplicate tab/process sees same delegation | any | two contenders | only one committed adapter claim may Send | loser must observe only |
| Worker completes, result capture not persisted | delivered | terminal result visible | fresh result observation + exact delegation marker | persist once; no new Send |
| Result persisted, browser crashes | terminal | result durable | load/revalidate exact identity/hash/schema | return existing result |
| Mutable state corrupt/missing while genesis exists | genesis only/inconsistent | physical child/result may exist | fail closed; do not manufacture new delegation id | manual/research recovery only |
| Stale/unrelated worker result appears | active | another chat/result | delegation/session/result marker mismatch | reject |
| Worker never settles within budget | delivered | generating/blocked/unknown | bounded timeout + final observation | terminal ABSTAIN/ERROR; no auto-spawn retry |
| Temporary mode cannot be proven | prepared | browser page ambiguous | no Send | ABSTAIN |
| Browser storage for Send claim unavailable/corrupt | prepared/child_bound | ownership cannot be proven | fail closed | no Send |

No release-critical cell permits a second physical Send merely because an acknowledgement or result was missed.

## 12. Failure lessons and shields

### Codex restart/status lesson

Failure: completed subagent status can be lost/reinitialized after restart.

Shield: CAP terminal result authority must be durable project-owned state, not reconstructed solely from live worker status.

### Codex writer/orphan lesson

Failure: session ownership/lifecycle can leave active writers or orphan descendants.

Shield: initial CAP topology is one manager -> one child; child creation is run-bound; no recursive spawning; no destructive cleanup claim until ownership proof is accepted.

### OpenHands duplicate-launch lesson

Failure: replay ledger can fail open when browser storage is corrupt/unavailable.

Shield: CAP Browser Companion must fail closed if it cannot prove the delivery/launch claim state.

### OpenHands worktree fallback lesson

Failure: isolation creation can silently degrade into shared workspace with conflict risk.

Shield: first CAP child is read-only and environment creation is out of scope. A later mutating worker must not silently downgrade isolation.

### Browser/UI drift

Failure: provider DOM/state may change.

Shield: generic core trusts only normalized adapter evidence; adapter qualification can fail `UNKNOWN/ABSTAIN` without weakening task authority.

## 13. Acceptance ladder

### L1 — generic state/identity

Tests must prove:

- stable delegation identity;
- exact parent/delegation/result correlation;
- immutable genesis + crash-safe checkpoint using accepted primitives;
- duplicate delivery contenders cannot both win;
- stale/foreign result rejected;
- bounded payload/result limits;
- fail-closed corrupt/missing state.

### L2 — adapter integration

Test Browser Companion with fixtures for:

- fresh Temporary qualification;
- one child only;
- one Send only;
- duplicate-tab race;
- restart before/after Send;
- wrong chat/wrong marker result rejection;
- timeout/ABSTAIN;
- no plugin/credential export.

### L3 — target Windows / ordinary Plus

Use a **non-reviewer read-only worker task** first so the test proves generic delegation rather than code-review semantics.

Required evidence:

```text
manager operation identity
 -> exactly one fresh child
 -> expected non-personalized Temporary mode
 -> exactly one bound task delivery
 -> structured result with exact delegation correlation
 -> durable local result
 -> no unintended session/message creation
 -> source/runtime provenance for installed adapter bytes
```

Then, as a separate consumer proof, a reviewer or researcher may use the same generic delegation path without changing the core lifecycle.

## 14. What would falsify this design

Return to Stage Research if any of these occur:

- reliable child launch requires a general scheduler/event bus;
- result capture cannot be made run/delegation-bound without broad browser authority;
- browser duplicate/restart behavior cannot fail closed without an entirely new persistence primitive;
- one-shot child isolation cannot be positively qualified on the target product;
- another real worker consumer requires fundamentally different generic identity/state than this design;
- implementation introduces automatic manager wake, nested delegation, mutating workers or environment creation;
- a proposed change would replace project WorkingState/Verification/Finish Gate authority.

## 15. Architecture decision

**NARROW**.

Production implementation may proceed only for:

```text
one manager
 -> one fresh read-only worker
 -> one bounded delegation
 -> one initial delivery
 -> one correlated structured terminal result
 -> durable local closure
```

Must have now:

- provider-neutral delegation identity/state;
- project-owned parent/child/result correlation;
- accepted lock/exclusive-create/checkpoint mechanics reused rather than a new persistence framework;
- adapter-local fail-closed one-delivery ownership;
- non-personalized Temporary Chat qualification for the first adapter;
- no inherited mutation authority;
- bounded budgets and result size;
- no blind relaunch/re-Send after ambiguity;
- exact installed-source provenance for physical acceptance.

Explicitly deferred:

- reviewer-specific context/retrieval/quality machinery;
- nested/multiple workers;
- mutating workers;
- automatic same-task manager wake/resampling;
- generic event bus/scheduler;
- project/worktree/environment lifecycle;
- cross-provider matrix beyond the first adapter;
- worker deletion/destructive cleanup;
- external agent-runtime dependency.

The accepted six-tool surface remains unchanged. The first internal/user-visible route should use bounded `procedure_run` registration rather than a new generic public dispatcher.

Before merge of an implementation that adopts this decision, update `CURRENT_STATE.md`, `ROADMAP.md`, `PROJECT_RISKS.md` and `ARCHITECTURE_REUSE_BASELINE.md` so they no longer state that reviewer-specific automation is the release-critical product prerequisite or that Track M remains purely parallel/future.
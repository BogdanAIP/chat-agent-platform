# Agent Session / Delegation Re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-01**

Accepted BASE at research start: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable accepted skills:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## 1. Decision summary

CAP should stop treating automatic code review as the product-level release-critical architecture and instead promote the already-proposed Track M **Agent Session / Delegation** boundary into a bounded general worker mechanism.

Selected first production scope:

```text
one ordinary-ChatGPT manager
 -> one genuinely fresh read-only worker
 -> one bounded delegation identity
 -> one initial delivery
 -> one correlated structured terminal result
 -> durable local closure
```

The first physical provider adapter may use a non-personalized ChatGPT Temporary Chat because CAP already has target-Windows/Plus physical evidence for fresh-chat launch, one Send and structured result capture. The **generic core is provider-neutral** and must not encode ChatGPT DOM details or reviewer semantics.

Code review may later consume this capability. Reviewer methodology, repository snapshots, code graphs, review-specific retrieval, reviewer benchmarks and reviewer learning are not owned by this stage.

Decision: **NARROW**.

## 2. Why Stage Research re-entry is required

Accepted `CURRENT_STATE.md` still places bounded automatic independent review on the immediate release path while Track M remains future/parallel. That is now too narrow a product boundary: the reusable mechanics discovered during reviewer automation are general child-worker lifecycle mechanics.

This change affects release-critical:

- task/child identity;
- persistence and recovery;
- concurrent launch/delivery ownership;
- capability isolation;
- browser/provider authority;
- result correlation and completion evidence.

Therefore accepted Stage Research v1.2 requires direct solution-domain evidence, materially distinct alternatives and an explicit failure/crash matrix before production implementation.

## 3. Existing project baseline and reuse boundary

CAP already owns the mechanisms that must remain authoritative:

- exactly six public Chat-facing tools;
- ordinary ChatGPT as the only current general planner;
- deterministic Control Plane authority;
- WorkingState and stable mutating-operation identity;
- bounded budgets and LoopGuard;
- accepted OS-backed single-writer locking, immutable genesis and crash-safe checkpoint patterns;
- Verification Kernel and independent Finish Gate;
- browser observation/action verification;
- a provisional Track M architecture separating session, conversation, delegation, delivery and execution-environment identities.

`project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md` already states the key invariant:

```text
Session identity != Task identity != Message delivery identity
```

and already models `HarnessSession`, `ConversationSnapshot`, `DelegationRecord`, `DeliveryReceipt` and `ExecutionEnvironment`.

This stage therefore **promotes/refines existing Track M**. It does not create a second session framework.

## 4. Exact stage question

> What is the smallest production Agent Session / Delegation mechanism that lets the current ChatGPT manager hand one read-only bounded task to one genuinely fresh child worker and receive a correlated result, while preserving CAP-owned authority and leaving worker-specific intelligence outside the generic runtime?

Useful first consumers may include:

- independent reviewer;
- researcher;
- security/audit second opinion;
- evaluator;
- other bounded read-only specialists.

## 5. Must have now

The first accepted slice must provide:

- deterministic delegation identity independent of provider session/message identity;
- private run capability not exposed to the ordinary manager;
- immutable exclusive-created genesis;
- crash-safe mutable checkpoint using accepted project primitives;
- parent/delegation/worker/result-contract correlation;
- durable launch-attempt state before physical launch authority;
- one-delivery ownership before physical Send;
- explicit `unknown` delivery state after ambiguous Send outcome;
- no second Send while delivery is `claimed`, `unknown` or `delivered`;
- reconciliation path from `unknown` to `delivered` only when fresh evidence proves the original Send applied;
- one terminal result bound to delegation and delivery identity;
- bounded result size/hash;
- first child profile is read-only and cannot inherit manager mutation authority;
- fail-closed corrupt/missing/residue/foreign state;
- provider adapter details below the generic state boundary;
- exact installed-source provenance for physical acceptance;
- accepted six-tool public surface unchanged.

## 6. Explicitly deferred

This stage does **not** add:

- reviewer-specific repository context/retrieval or quality logic;
- worker writes to GitHub, filesystem or user applications;
- inherited manager capabilities;
- arbitrary plugin/tool delegation;
- nested/recursive delegation;
- worker pools or broad fan-out;
- generic scheduler/event bus;
- same-task automatic manager wake/resampling;
- project/worktree/environment creation;
- long-lived background workers;
- destructive child cleanup;
- cross-provider matrix beyond the first adapter;
- external agent-runtime dependency;
- a second local general planner.

## 7. Architecture lineage decisions

Each existing affected role receives one canonical lineage decision.

### General planning / novel strategy — `KEEP`

Owner remains ordinary ChatGPT. The child is a bounded reasoner for one delegated task, not a second local planning layer.

### Track M Agent Session / Delegation — `REFINE`

Promote the accepted future boundary into the first one-manager/one-read-only-child runtime slice. Do not implement the entire future Track M catalog at once.

### Agent host reference — `KEEP`

`openai/codex` remains `REFERENCE_REVALIDATE_PER_STAGE`. CAP may adapt mechanics but does not depend on Codex runtime or inherit its authority/tool model.

### Browser/provider adaptation — `REFINE`

Existing Browser Companion / generic chat-adapter direction becomes the first provider adapter beneath Agent Sessions. DOM/UI details must not define generic delegation identity.

### WorkingState / project operational state — `KEEP`

Delegation/result references integrate with project-owned operational state rather than creating a competing reasoning/state authority.

### Verification Kernel + Finish Gate — `KEEP`

A worker result is evidence/data. It never self-authorizes a CAP consequence and never by itself means the manager's whole task is complete.

### Accepted lock/exclusive-create/checkpoint mechanics — `REUSE_MORE`

Reuse the Stage 26.3C mechanism family for delegation persistence rather than introduce a new persistence framework.

### Reviewer-specific local state — `REFINE`

The reusable lifecycle lessons become generic delegation mechanics. Reviewer-specific identities/parsers/results remain specialist logic and are not the generic schema.

### Deep-link / autosend experiments — `REUSE_MORE`

PRs #138/#145 are experiment evidence for the first ChatGPT adapter only. They are not generic runtime authority.

### Reviewer authority qualification — `DEFER`

Specialist-specific requirements such as GitHub mutation-action unreachability remain consumer policy. The generic first profile is simply read-only.

### Reviewer benchmark/evaluation plane — `DEFER`

Reviewer semantic quality is separate from Agent Session lifecycle reliability.

## 8. Engineering primitives and adjacent domains

### Delegation identity

Domain: distributed workflow identity / idempotency.

Guarantee: one logical child task has one stable identity independent of chat/session/message ids.

### Parent/child ownership

Domain: process supervision / structured concurrency / agent graphs.

Guarantee: CAP can prove which child belongs to which manager/delegation and reject unrelated/stale results.

### Durable launch-attempt marker

Domain: write-ahead intent / crash recovery.

Guarantee: restart cannot blindly create a second child after an ambiguous launch.

### Delivery claim

Domain: single-writer/idempotent message delivery.

Guarantee: two tabs/processes cannot both obtain authority to Send the same logical task.

### Delivery reconciliation

Domain: exactly-once-effect approximation under ambiguous transport.

Guarantee: `unknown` blocks re-Send; fresh observation may establish that the original delivery applied and transition the same delivery to `delivered`.

### Result correlation

Domain: request/reply correlation / workflow closure.

Guarantee: a result from the wrong worker/delegation/delivery/contract cannot close the operation.

### Capability profile

Domain: least privilege.

Guarantee: the first child cannot inherit manager mutation authority merely because the manager has broader capabilities.

### Provider adapter

Domain: ports-and-adapters / anti-corruption layer.

Guarantee: ChatGPT UI mechanics can change without changing generic delegation identity/state semantics.

## 9. Direct source-code research

### 9.1 `openai/codex`

Exact researched ref: `6127478086e611323e3bff40c943588606c1c571`

Research date: 2026-09-01.

Material paths inspected:

- `codex-rs/core/src/tools/handlers/multi_agents.rs`
- `codex-rs/core/src/tools/handlers/multi_agents/spawn.rs`
- `codex-rs/core/src/tools/handlers/multi_agents/wait.rs`
- `codex-rs/core/src/agent/control.rs`
- current public multi-agent/session issue history.

Classification: `OPEN_IMPLEMENTED` for spawn/wait/parent-child mechanics; persistence/restoration still has observable failure edges.

Relevant code-level findings:

- child creation records explicit parent/root/depth metadata;
- spawn depth is bounded;
- `AgentControl` is scoped to one root session tree and shared with descendants;
- wait subscribes to status changes and distinguishes terminal states from timeout;
- issue #34220 reports a completed descendant reloading as `PendingInit` after restart, causing a later wait to miss completion;
- issue #38144 reports active-writer/session-resume ownership friction after fork;
- issue #38805 reports stale/orphaned subagent accumulation on Windows.

CAP lesson: adapt parent/child identity and shallow topology; never make live child status the sole durable terminal truth.

### 9.2 `OpenHands/OpenHands`

Exact researched ref: `b4428e1f8529fe726039437c8e54a7e7319986eb`

Research date: 2026-09-01.

Material paths inspected:

- `src/api/launch-child-conversation-client-tool.ts`
- `src/services/child-conversation-launch.ts`
- related child-launch constants/tests.

Classification: `OPEN_IMPLEMENTED` for client-driven child-conversation launch; some launch ownership is browser-scoped.

Relevant code-level findings:

- child receives a self-contained task and does not see parent conversation history;
- local children may use worktree isolation or shared workspace; cloud children use isolated sandboxes;
- launch is explicitly non-idempotent and guarded by a per-parent browser launch ledger;
- the ledger claims before network work, but corrupt/unavailable browser storage fails open and accepts duplicate-launch risk;
- failed worktree creation may fall back to shared workspace;
- cloud creation acknowledgement and actual conversation availability are separate and require bounded polling.

CAP lesson: keep self-contained child task + explicit parent link, but fail closed when claim storage is unavailable and never silently downgrade future mutating-worker isolation.

### 9.3 Temporal durable-workflow domain

Current official Temporal documentation was reviewed as a materially different architecture family for durable child workflows, timers and continuation.

Classification: mature external workflow-engine approach.

Decision: `REFERENCE_ONLY / DEFER`.

A dedicated workflow service would solve substantially more than the first child-chat delegation but would introduce another persistent runtime/service owner. Reconsider only for future scheduled/long-lived/same-task continuation.

## 10. ChatGPT first-adapter evidence

Current OpenAI Temporary Chat behavior researched on 2026-09-01 includes:

- non-personalized Temporary Chat starts without memory, custom instructions or plugins;
- personalization is fixed at chat start;
- unsaved Temporary Chats are not ordinary history/new-memory state;
- files uploaded directly in Temporary Chat are not stored in Library.

CAP PR #145 also physically demonstrated on the target Windows/Plus/browser path that automation can create a fresh Temporary Chat, deliver one run-bound task, perform one Send and capture a structured response.

Reusable conclusion: **fresh child transport is feasible enough for an adapter experiment**.

Non-conclusion: Temporary Chat is not a generic CAP invariant and is not yet accepted production adapter authority.

## 11. Alternatives

### A — Continue reviewer-specialized automation as the general architecture

Strengths: existing state/procedure work; immediately reduces manual review friction.

Weaknesses: couples generic child lifecycle to one specialist and invites reviewer context/retrieval logic into CAP.

Decision: **REJECT as generic architecture**. Do not delete accepted reviewer state until a generic consumer migration is separately proven safe.

### B — CAP-owned bounded Agent Session core + provider adapter

Strengths:

- matches existing Track M;
- reuses project persistence/reconciliation mechanisms;
- keeps six public tools;
- works with current ordinary ChatGPT/Plus path;
- supports later specialist types without changing core identity.

Weaknesses:

- browser adapter remains operationally fragile;
- child launch/Send/result capture need physical fail-closed evidence;
- no automatic manager model turn when the child finishes.

Decision: **SELECTED / NARROW**.

### C — Embed Codex/OpenHands as CAP worker runtime

Strengths: mature session/subagent structures.

Weaknesses: imports broader planner/tool/authority model, duplicates CAP state/verification boundaries and does not match the intended ordinary-ChatGPT/Plus runtime.

Decision: **REJECT as first dependency; keep as source references**.

### D — Add Temporal-like workflow/scheduler service now

Strengths: strong durability, child workflows, timers and continuation.

Weaknesses: new runtime/service/persistence owner and solves out-of-scope automatic wake/scheduling before demonstrated need.

Decision: **DEFER**.

## 12. Minimum generic state model

The first implementation may use a reduced runtime form of Track M:

```text
DelegationIdentity
  parent_task_id
  subgoal_id
  worker_kind
  worker_profile = fresh_readonly_worker_v1
  task_sha256
  result_contract_id

DelegationGenesis
  delegation_id
  private run_id
  delivery_id
  exact identity

DelegationState
  launch_state = prepared | launch-attempted | child-bound
  worker_session_ref?
  delivery_state = prepared | claimed | unknown | delivered
  delivery_evidence_ref?
  result_state = open | recorded
  terminal result status/payload/hash?
```

Provider session ids are observations bound after launch, not part of deterministic delegation identity.

## 13. Generic terminal result contract

The lifecycle layer must not encode reviewer statuses such as `PASS` or `FINDINGS`.

Generic envelope semantics:

```text
WORKER_RESULT_V1

delegation_id=<exact>
delivery_id=<exact>
worker_kind=<bounded specialist id>
result_contract_id=<bounded schema id>
status=COMPLETED|ABSTAIN|ERROR
payload=<task-specific bounded text>
payload_sha256=<exact>
```

The task-specific payload is opaque to the generic lifecycle except for its declared contract id, size and hash. A review consumer may validate `REVIEW_RESULT_V1`; a researcher may validate a different payload contract.

## 14. Parent continuation boundary

Out of scope:

```text
child completes -> automatically obtain a new manager model turn
```

First behavior:

```text
child completes
 -> durable delegation result is recorded
 -> a later manager/user turn reconciles and reads it deterministically
```

General same-task wake/resampling requires separate Stage Research.

## 15. Failure / crash matrix

| Boundary | Durable state | Possible physical state | Required rule | Retry authority |
|---|---|---|---|---|
| Before genesis | none | no child | nothing committed | new operation allowed |
| Genesis/state prepared | prepared | no child | exact state proves no launch attempt | initial launch may proceed |
| Launch-attempt committed, browser outcome missing | launch-attempted | child absent or exists | reconcile exact adapter evidence | no blind relaunch |
| Child exists, acknowledgement lost | launch-attempted | exact child exists | bind exact run-bound child | reuse child only |
| Child bound, before delivery claim | child-bound/prepared | no task message | exact child + no claim | claim may proceed |
| Delivery claim committed | claimed | message absent/present/unknown | observe exact delivery marker/hash | no second claim/Send |
| Send outcome ambiguous | unknown | message may exist | fresh observation may prove original Send applied | no re-Send; may reconcile same delivery to delivered |
| Delivered | delivered | task visible/worker running | exact delivery evidence | never Send again |
| Worker result visible, not persisted | delivered/open | terminal response exists | exact delegation/delivery/contract marker | persist once |
| Result persisted | recorded | browser may crash | reload + revalidate state/hash | return existing result |
| Genesis exists, mutable state missing | inconsistent | unknown | fail closed | no identity replacement |
| Canonical state plus temp residue | ambiguous | prior write uncertain | fail closed on every load/transition | no mutation until investigated |
| Foreign/stale result | active | another child/result | identity mismatch | reject |
| Worker timeout | delivered/open | blocked/generating | bounded final observation | ABSTAIN/ERROR; no auto-spawn retry |
| Temporary mode unproven | prepared | page ambiguous | no Send | ABSTAIN |
| Browser claim storage corrupt/unavailable | child-bound/prepared | ownership unproven | fail closed | no Send |

No release-critical cell authorizes a second physical Send merely because acknowledgement/result capture was missed.

## 16. Known external failure lessons and CAP shields

### Codex restart/status loss

Shield: terminal worker result authority is project-owned durable state, never live status alone.

### Codex writer/orphan lifecycle friction

Shield: first topology is exactly one manager -> one child; no recursive spawning or destructive cleanup claim.

### OpenHands fail-open launch ledger

Shield: adapter delivery/launch claim storage failure yields no Send/launch authority.

### OpenHands shared-workspace fallback

Shield: first worker is read-only; future mutating workers require separate isolation research and may not silently downgrade.

### Provider UI drift

Shield: generic core consumes normalized adapter evidence. Adapter qualification may return `UNKNOWN/ABSTAIN`; provider DOM text never becomes project authority by itself.

## 17. Acceptance ladder

### L1 — generic state/identity

Must prove:

- deterministic provider-independent delegation id;
- private run capability;
- immutable genesis + crash-safe checkpoint;
- one-shot launch-attempt transition;
- stable child binding;
- one delivery claim under contention;
- `unknown` blocks blind re-claim/re-Send;
- fresh evidence can reconcile the same unknown delivery to delivered;
- stale/foreign result rejection;
- one terminal result + idempotent same-result replay;
- bounded payload/result;
- corrupt/missing/temp-residue state fails closed;
- failed checkpoint replace preserves prior valid canonical state.

### L2 — first provider adapter

Must prove with deterministic fixtures:

- fresh Temporary qualification;
- one child only;
- one Send only;
- duplicate-tab/process race;
- restart before/after Send;
- exact child/session/result correlation;
- wrong chat/marker result rejection;
- timeout/ABSTAIN;
- no plugin/credential export;
- adapter cannot mutate project/GitHub/filesystem.

### L3 — target Windows / ordinary Plus

First physical task must be a **non-reviewer read-only worker task**, so success proves generic delegation rather than code-review semantics.

Required evidence:

```text
manager delegation identity
 -> exactly one fresh child
 -> expected non-personalized Temporary mode
 -> exactly one bound task delivery
 -> structured generic result with exact correlation
 -> durable local closure
 -> no unintended child/message creation
 -> installed-source provenance for adapter/runtime bytes
```

A reviewer/researcher consumer may then reuse the same core without changing generic lifecycle semantics.

## 18. What falsifies this NARROW decision

Return to Stage Research if:

- reliable child launch requires a general scheduler/event bus;
- result capture cannot be bound to delegation without broad browser authority;
- duplicate/restart behavior cannot fail closed using accepted persistence + adapter-local claim mechanics;
- fresh/read-only child qualification cannot be positively established;
- a second real worker consumer requires fundamentally different generic identity/state;
- implementation needs nested/fan-out workers, mutation, environment creation or automatic parent wake;
- proposed work would replace project WorkingState/Verification/Finish Gate authority;
- accepted six-tool public surface would have to expand.

## 19. Final architecture decision

**NARROW — implementation may proceed only for:**

```text
one manager
 -> one fresh read-only worker
 -> one bounded delegation
 -> one initial delivery
 -> one correlated generic terminal result
 -> durable local closure
```

The first internal/user-visible route should remain behind bounded `procedure_run` registration rather than add a seventh tool or a generic arbitrary dispatcher.

Before any merge that adopts this direction, canonical project owners must be updated so they no longer claim reviewer-specific automation is the product-level release-critical prerequisite or that Track M remains purely future/parallel. At minimum inspect/update:

- `CURRENT_STATE.md`
- `ROADMAP.md`
- `PROJECT_RISKS.md`
- `ARCHITECTURE_REUSE_BASELINE.md`
- `CONVERSATION_BRIDGE_ARCHITECTURE.md` if its provisional status changes.

Mandatory fresh ordinary-ChatGPT exact-head semantic review remains required before merge.
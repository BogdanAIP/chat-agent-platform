# Codex Agent Host Source Review

Status: **PINNED SOURCE-CODE RESEARCH EVIDENCE — REFERENCE ONLY**

Research date: **2026-08-28**

Upstream repository: `openai/codex`

Exact inspected upstream ref:

`8bcac28f93f78b70d1159d97dbf11254bfb56a49`

This document establishes the source-level evidence behind the `ARCHITECTURE_REUSE_BASELINE.md` row for future Agent Session / long-lived Agent Host / Persistent / orchestration research.

It is **not** runtime implementation authority, a dependency lock, or a decision to embed Codex. Every future stage must revalidate the exact role against a current pinned upstream ref and at least one materially independent implementation when credible.

## Research question

Does the public Codex repository contain concrete implementation mechanisms useful as a reference for:

- long-lived thread/session lifecycle and resume;
- planner-independent contextual/world state;
- multi-agent parent/child ownership and restoration;
- asynchronous user communication during an ongoing turn;
- Persistent mode state integration;
- automatic sleep/wake continuation after the agent decides to wait?

The relevant Chat Agent Platform boundary is deliberately narrower than “copy Codex”: learn from its agent-harness lifecycle while retaining project-owned consequence authority, `WorkingState`, Verification Kernel, Finish Gate, grants and physical Browser/Windows verification.

## Source-code evidence

### 1. App Server thread lifecycle and resume

Classification: `OPEN_IMPLEMENTED`

Lesson: `REFERENCE_ONLY`

Inspected paths:

- `codex-rs/app-server/src/request_processors/thread_processor.rs`
- `codex-rs/app-server-protocol/src/protocol/v2/thread.rs`
- `codex-rs/app-server/src/message_processor.rs`
- `codex-rs/app-server/tests/suite/v2/thread_resume.rs`

Execution/state path followed:

```text
App Server request
  -> thread processor
  -> start/read/resume/fork request handling
  -> persisted thread metadata/history
  -> ThreadManager / CodexThread runtime
  -> later turn can continue on the resumed thread
```

Concrete code findings:

- the thread processor imports and uses persisted resume settings and thread-store persistence;
- resume logic compares requested overrides with the active/persisted configuration instead of treating resume as a fresh unrelated process;
- app-server integration tests create persisted rollout/history, start one App Server instance, resume and extend the thread, shut it down, start another instance, resume the same thread again and continue with another turn;
- the public protocol has explicit V2 thread request/response types rather than representing lifecycle only as generic tool calls.

What this proves for our research:

- a durable Agent Host can model `Thread` identity separately from one UI/client process;
- resume is an explicit lifecycle operation with persisted metadata/history and configuration semantics;
- a host protocol can expose lifecycle separately from capability/tool authority.

What this does **not** prove:

- Codex thread persistence is a substitute for project `WorkingState` consequence/reconciliation history;
- Codex completion semantics satisfy our Finish Gate;
- Codex resume proves arbitrary physical side effects are safe to retry.

### 2. Persistent mode as WorldState/context state

Classification: `OPEN_IMPLEMENTED`

Lesson: `REFERENCE_ONLY`

Inspected paths/symbols:

- `codex-rs/core/src/context/world_state/persistent_mode.rs`
  - `PersistentModeState`
  - `PersistentModeSnapshot`
  - `WorldStateSection for PersistentModeState`
- `codex-rs/core/src/context/world_state/persistent_mode_tests.rs`

Execution/state path followed:

```text
reasoning effort/config
  -> PersistentModeState::new(...)
  -> developer-context fragment
  -> WorldState snapshot/hash
  -> render_diff(previous,...)
  -> unchanged / replacement / removal of persistent instructions
```

Concrete code findings:

- Persistent instructions are enabled only when `ReasoningEffort::Persistent` is selected;
- the section is represented in WorldState with its own snapshot/hash rather than injected blindly every turn;
- a change replaces old instructions, and disabling Persistent emits an explicit removal notice;
- tests cover unchanged, replacement and retirement transitions, including reconstruction when the prior snapshot is absent but retained context exists.

What this proves for our research:

- Persistent behavior has a concrete versioned/context-state mechanism in the public runtime;
- current operating state can be kept separately from the raw historical conversation and reintroduced/retired deliberately.

What this does **not** prove:

- `PersistentModeState` is a scheduler;
- the public code shown here can autonomously wake a sleeping unfinished task and sample the planner again after a deadline or external condition.

### 3. Multi-agent persisted metadata and parent ownership on resume

Classification: `OPEN_IMPLEMENTED`

Lesson: `REFERENCE_ONLY`

Inspected path/symbols:

- `codex-rs/core/src/agent/control/spawn.rs`
  - `restore_v2_agent_metadata`
  - `validate_loaded_v2_child`
  - `ensure_v2_agent_loaded`

Execution/state path followed:

```text
root thread / AgentControl
  -> agent_graph_store open spawn descendants
  -> restore child metadata
  -> resume/load requested child
  -> reconstruct resume config/history
  -> validate recorded parent identity + live parent + MultiAgent V2 + shared AgentControl state
  -> permit or reject loaded child
```

Concrete code findings:

- restart restoration reads open descendant relationships from `agent_graph_store` and restores child metadata without pretending all runtimes are already live;
- a loaded V2 child is accepted only when it is running, remains V2, records the expected parent thread, and belongs to the same `AgentControl` state;
- parent-driven resume verifies the parent is the registered live thread and checks recorded parent IDs from stored/resumed state for inconsistencies;
- role application deliberately restores runtime approval policy, approvals reviewer, cwd and permission-profile snapshot rather than allowing a role change to silently replace those runtime authority settings.

What this proves for our research:

- parent/child ownership is a first-class lifecycle invariant worth comparing with future manager/worker identity and leases;
- persisted agent graph metadata and live runtime ownership are treated as different facts;
- resume can fail closed on inconsistent parent ownership.

What this does **not** prove:

- Codex's worker authority model should be copied;
- its filesystem/tool sharing is acceptable for Chat Agent Platform;
- parent ownership alone proves effect safety or task completion.

### 4. Asynchronous user messaging during ongoing work

Classification: `OPEN_IMPLEMENTED`

Lesson: `REFERENCE_ONLY`

Inspected paths/symbols:

- `codex-rs/core/src/tools/handlers/send_user_message_async.rs`
  - `SendUserMessageAsyncHandler`
- `codex-rs/core/tests/suite/send_user_message_async.rs`
  - `persistent_async_message_guidance_follows_tool_availability`
  - `send_user_message_async_emits_item_and_does_not_end_the_turn`

Execution/state path followed:

```text
model tool call
  -> SendUserMessageAsyncHandler
  -> validate message
  -> emit async AgentMessage item started/completed
  -> return {accepted:true}
  -> current turn continues
  -> later user reply is independent asynchronous input
```

Concrete code findings:

- the tool description explicitly states it returns immediately without ending the turn or waiting for a reply;
- the handler emits an `AgentMessageDelivery::Async` item and returns successful tool output;
- integration tests verify the async item and then observe another model response/turn completion, proving the tool call itself did not terminate ongoing work;
- Persistent-mode guidance mentions the async tool only when it is actually available to the relevant root session.

What this proves for our research:

- proactive communication can be modeled independently from stopping the current turn;
- user-message delivery can be an event/lifecycle concern rather than a planner-completion boundary.

What this does **not** prove:

- asynchronous messaging is equivalent to autonomous task wake/resume;
- a user message can safely grant consequence authority without the project's own grant/policy checks.

### 5. Automatic Persistent sleep/wake scheduler

Classification: `NOT_FOUND_AFTER_TARGETED_SEARCH`, with the broader product boundary therefore `OPEN_PARTIAL` / `CLOSED_OR_UNKNOWN` for this specific lifecycle.

Lesson: `UNRESOLVED`

Targeted searches performed against the public repository snapshot/current index included combinations of:

- `next_check`
- `persistent wake sleep scheduler`
- `wake thread persistent scheduler sleep`

No implementation path was located that established the full lifecycle:

```text
unfinished task
  -> agent decides to sleep until time/condition
  -> durable wake registration
  -> process/UI may disappear
  -> wake fires once with duplicate/cancellation handling
  -> same task/thread is reacquired safely
  -> planner/model is sampled again
  -> work continues
```

Important interpretation:

- this is **not proof that such a mechanism does not exist anywhere in Codex**;
- the public repository definitely contains Persistent mode context/state and asynchronous messaging mechanisms;
- this review did not locate a complete public wake scheduler/continuation path that would justify selecting a scheduler architecture for Chat Agent Platform;
- the missing lifecycle may be not yet merged, implemented under different terminology, delegated to closed product infrastructure, or otherwise outside the inspected paths.

Therefore future Persistent Continuation work must research scheduler/wake semantics as its own architecture problem rather than inferring them from `PersistentModeState` or `send_user_message_async`.

## Tests and failure-oriented evidence inspected

Evidence inspected in the pinned tree includes:

- Persistent WorldState tests covering replacement/removal and missing-snapshot reconstruction;
- async-message integration tests covering tool availability and non-termination of the current turn;
- App Server `thread_resume` integration coverage exercising persisted history across separate App Server instances;
- runtime fail-closed checks in multi-agent V2 resume for live parent registration, parent identity, agent version and shared control ownership.

This review did not attempt to prove every Codex lifecycle guarantee or audit the entire repository. A future stage must inspect the exact mechanisms it proposes to reuse or reject and must search upstream issues/PR history for the failure classes relevant to that stage.

## Important architecture differences

The code evidence supports Codex as a reference for the **life of an agent**, not as authority for the **consequences of an action**.

Keep these Chat Agent Platform boundaries independent:

- deterministic Control Plane consequence authorization;
- project-owned `WorkingState` and effect/reconciliation history;
- `ObservationRef` / fresh evidence / `ExpectedEffect` transition verification;
- Verification Kernel `PASS | FAIL | UNKNOWN`;
- independent Finish Gate;
- capability grants and actor/environment/evidence binding;
- bounded public semantic tool surface;
- physical Browser/Windows post-action verification.

A Codex thread/session/agent graph may be a strong reference for future host/session identity, but it is not a universal replacement for `Task`, `WorkingState`, effect identity or task completion authority.

## Baseline decision

For the architectural role **Agent session / long-lived host lifecycle and orchestration**:

- source: `openai/codex` pinned here at `8bcac28f93f78b70d1159d97dbf11254bfb56a49`;
- lesson classification: `REFERENCE_ONLY`;
- baseline posture: `REFERENCE_REVALIDATE_PER_STAGE`;
- selected dependency: **none**;
- future research requirement: compare Codex code with at least one independent mature open agent/harness implementation when a credible materially distinct implementation exists;
- Persistent wake/scheduler mechanism: **unresolved**, not selected from Codex by this review.

This is sufficient to establish Codex as a prior source-code reference in the reuse baseline without granting it runtime or authority ownership.

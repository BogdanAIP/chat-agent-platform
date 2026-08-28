---
name: source-code-research
description: Code-level evidence gate for Stage Research and architecture/reuse decisions when relevant public implementations exist. Use for agent runtimes/harnesses, session lifecycle, orchestration, persistence/recovery/concurrency/identity/security/authority mechanisms, or external-component comparisons. README-only/product-description review does not count as implementation evidence when source code is available.
compatibility: Designed for Chat Agent Platform research with repository and current web/GitHub access.
metadata:
  version: "1.0"
  project: "chat-agent-platform"
---

# Source-Code Research

Use this skill together with `stage-research` whenever a release-critical architecture question has credible public implementations whose code can materially test the proposed mechanism or reuse decision.

The goal is not repository tourism. The goal is to understand **what executable mechanisms actually exist, how they fail, and which boundaries remain closed or unproven** before this project adopts, duplicates, rejects, or replaces them.

## Trigger

Activate when research touches one or more of:

- agent runtime / harness / host architecture;
- long-lived sessions, threads, resume/fork or continuation;
- persistent/proactive execution;
- multi-agent delegation, ownership or worker lifecycle;
- context compaction / durable world state / reinjection;
- hooks, event streams, tool lifecycle or approvals;
- persistence, recovery, retry/reconciliation, concurrency, identity/correlation or authority mechanisms that have relevant public implementations;
- an external component or reference implementation being evaluated for `KEEP`, `REUSE_MORE`, `REFINE`, `REPLACE`, `DEFER` or `REJECT` lineage.

Do not force agent-repository study onto an unrelated low-level mechanism when the strongest evidence lives in another engineering domain. Filesystem durability should still be researched from filesystem/database/OS sources; distributed coordination from distributed-systems sources; and so on. Source-code study complements domain evidence rather than replacing it.

## Hard rules

When relevant source code is public, **README, product documentation, architecture diagrams, blog posts and model-generated summaries are not sufficient implementation evidence by themselves**.

For every source-code claim that materially affects the architecture decision:

1. bind the repository to an exact commit SHA or immutable tag;
2. identify the concrete files/modules/symbols that implement the mechanism;
3. trace the relevant execution/state path rather than inferring behavior from names;
4. inspect tests for the claimed invariant or lifecycle when available;
5. inspect issue/review/history evidence for known failure modes when consequence-relevant;
6. distinguish what is implemented in the public repository from what is only documented, inferred, experimental, disabled, or apparently closed;
7. record what was **not found** when absence matters to the decision.

Never describe a mutable `main` snapshot as timeless product architecture. Record the inspected exact ref and research date.

## 1. Build a mechanism-relevant reference cohort

Choose repositories because they implement the architectural role being studied, not because they are popular.

For Agent Host / session lifecycle / Persistent / delegation / multi-agent / context/hook/tool-orchestration research:

- `openai/codex` is a mandatory comparison reference while its public repository remains relevant to the role;
- inspect at least **one independent mature open agent/harness implementation** when a credible materially distinct implementation exists;
- prefer a second independent implementation when the approaches differ enough to improve the architecture comparison.

Examples of currently relevant public repositories include `OpenHands/OpenHands`, `aaif-goose/goose`, and `cline/cline`; these are **research candidates, not selected dependencies or frozen mandatory vendors**. Revalidate repository identity, activity and fit at research time.

If only one credible public implementation exists for the exact role, state that explicitly rather than padding the cohort with irrelevant repositories.

## 2. Pin source provenance before drawing conclusions

For every inspected repository record:

```text
repository
exact commit SHA / immutable tag
research date
relevant paths/modules/symbols
why this repository is in the cohort
```

If search results point at an older indexed commit, refetch the relevant file at the intended exact ref before treating it as current evidence.

Do not mix files from different commits into one supposed implementation snapshot without saying so.

## 3. Trace executable mechanisms

For each mechanism under comparison, follow enough code to answer the real runtime question. Depending on the subsystem, inspect:

- public/internal entry point;
- state/data types and identity model;
- state owner and lifecycle boundaries;
- persistence/checkpoint/write ordering;
- locks, queues, leases, cancellation or concurrency controls;
- tool/action delivery path;
- approval/permission propagation;
- retry/recovery/reconciliation/resume path;
- event emission and consumer ordering;
- context reconstruction/compaction/reinjection;
- cleanup/termination behavior;
- tests covering the claimed behavior.

A filename or type name is not proof. Follow the call/state path far enough to establish the mechanism and its boundary.

## 4. Study negative space and closed boundaries

An important research result may be that a mechanism is **not present in the open code**.

Use one of these classifications:

- `OPEN_IMPLEMENTED` — executable implementation and supporting path were located;
- `OPEN_PARTIAL` — some mechanism/state is public, but a required lifecycle piece is missing or external;
- `DOCUMENTED_ONLY` — public docs/prompts/contracts describe it, but implementation was not located;
- `CLOSED_OR_UNKNOWN` — evidence indicates the required behavior may live in private infrastructure, or the public repository is insufficient to tell;
- `NOT_FOUND_AFTER_TARGETED_SEARCH` — targeted code/search paths did not locate it; this is not proof of global nonexistence.

For absence claims, record the searched terms/areas and use cautious wording. Do not turn "I did not find it" into "it does not exist".

## 5. Inspect tests and failure history

For each candidate mechanism, look beyond the happy path.

Prefer evidence from:

- unit/state-machine/integration tests around the exact mechanism;
- crash/restart/concurrency/ownership tests;
- regression tests added with fixes;
- issue tracker and PR discussions describing real failures;
- commits that changed the mechanism because earlier semantics were insufficient.

Record whether the observed protection is:

- enforced by types/state machine;
- enforced by runtime checks;
- enforced only by convention/prompt;
- tested directly;
- not tested or not visible.

## 6. Separate architecture inspiration from reusable code

For every useful external mechanism classify the lesson:

- `REFERENCE_ONLY` — architecture/code lesson; do not import the component;
- `ADAPT_MECHANIC` — a bounded implementation pattern may be adapted behind project authority;
- `REUSE_COMPONENT` — reuse the upstream component through a narrow adapter;
- `REJECT_MECHANIC` — implementation conflicts with project invariants or failure model;
- `UNRESOLVED` — evidence is insufficient.

A strong reference implementation is not automatically a dependency.

In particular, do not infer that this project should inherit another agent's planner authority, broad tool surface, shared-filesystem authority, completion semantics, or trust model merely because its lifecycle implementation is mature.

## 7. Map code evidence to Chat Agent Platform

For each important source-code finding answer:

1. Which exact role/failure in this repository does it illuminate?
2. Is the external mechanism above, below, or parallel to our Control Plane authority?
3. Which invariant can be reused as an idea without copying the external trust model?
4. Does it duplicate a role already assigned in `ARCHITECTURE_REUSE_BASELINE.md`?
5. What project-owned boundary must remain independent?
6. What test/failure shield would prove our adaptation rather than merely resemble the reference code?

Prefer mechanism-level comparisons such as:

```text
external agent graph ownership
  -> parent/child/session identity invariant
  -> our WorkerLease / manager-worker ownership question
```

not superficial comparisons such as:

```text
external project uses Rust
  -> therefore we should use Rust
```

## 8. Required Stage Research Brief block

When this skill applies, the Stage Research Brief must contain a distinct section:

### Source-code evidence

For each inspected codebase include:

- repository + exact ref;
- concrete files/modules/symbols inspected;
- execution/state path followed;
- mechanism proven by code;
- tests/failure history inspected;
- open/partial/documented/closed/not-found classification for material claims;
- lesson classification: `REFERENCE_ONLY`, `ADAPT_MECHANIC`, `REUSE_COMPONENT`, `REJECT_MECHANIC`, or `UNRESOLVED`;
- direct mapping to this repository's role/invariant;
- important differences that make blind copying unsafe.

A Stage Research Brief that relies on a public implementation but contains only README/docs-level evidence is incomplete.

## 9. Codex-specific comparison boundary

`openai/codex` is especially relevant as a **reference implementation** for future Agent Host / Agent Sessions / Persistent / orchestration research because its public code exposes concrete lifecycle mechanisms such as thread/session state, world-state/context handling, multi-agent ownership, hooks/events and async interaction.

Treat those as mechanisms to inspect, not as automatic project authority or a selected runtime dependency.

Do not delegate these Chat Agent Platform boundaries merely because Codex implements adjacent lifecycle machinery:

- deterministic Control Plane authority;
- project `WorkingState` and consequence/reconciliation history;
- Verification Kernel and independent Finish Gate;
- capability grants / actor-environment-evidence binding;
- bounded public semantic tool surface;
- project-specific physical Browser/Windows verification guarantees.

Persistent/proactive behavior is particularly sensitive to open/closed boundaries: if the public repository exposes prompt/state integration but no complete wake/scheduler lifecycle, classify that honestly as partial/unknown and research the missing scheduler/continuation mechanism separately before implementation.

## 10. Completion check

Before treating source-code research as complete, verify:

- exact refs are recorded;
- at least one real implementation path was traced for every material reused/rejected mechanism;
- tests or explicit lack of tests are recorded;
- failure/history evidence was checked where consequence-relevant;
- open vs closed/unknown boundaries are explicit;
- code evidence is separated from docs/marketing claims;
- the reference cohort is mechanism-relevant and not popularity-driven;
- the Stage Research Brief contains the `Source-code evidence` block;
- conclusions are mapped to our own invariants and do not silently import another agent's authority model.

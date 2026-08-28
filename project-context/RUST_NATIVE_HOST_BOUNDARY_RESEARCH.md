# Rust Native Host Boundary — Stage Research Brief

Status: **STAGE RESEARCH BRIEF — DEFER PRODUCTION ADOPTION**

Research date: 2026-08-28

Project snapshot: `BogdanAIP/chat-agent-platform@bc13c7de3d559f5cf42dbee6f14ad5b2cc8681cc`

<!-- RUST_BOUNDARY_DECISION_V1
stage_decision=DEFER
production_rust=BLOCKED
future_native_boundary=RESEARCH_ONLY
future_native_language=UNRESOLVED
critical_path_change=NO
-->

## Decision contract

The structured `RUST_BOUNDARY_DECISION_V1` block above is the **sole implementation-decision representation in this Brief**. All prose below is explanatory evidence and constraints subordinate to that block.

Production Rust work is blocked. This Brief does not authorize implementation, a dependency/toolchain change, a public-tool change, or a Stage 26.3C architecture change.

Do **not** migrate the deterministic Control Plane, `WorkingState`, Verification Kernel, Finish Gate, public semantic projection, skills/configuration or Stage 26.3C artifact-recovery logic merely because major agent runtimes use Rust.

The research identifies a credible **future native-host boundary**, but **does not select its implementation language**. A future implementation requires fresh Stage Research against then-current requirements and must compare Rust against an equivalent language-neutral/current-runtime implementation of the same boundary.

Conceptual future boundary:

```text
ordinary ChatGPT / current planner
        |
project semantic surface + Control Plane authority
        |
        | typed private IPC / capability request
        v
future optional native host (language unresolved)
        |
        +-- process / process-tree ownership
        +-- PTY / terminal lifecycle
        +-- Windows Job Objects / native process handles
        +-- sandbox bootstrap / native OS containment
        +-- cancellation / shutdown / child reaping
        +-- narrow OS-specific adapters where qualified
```

Any future host remains **below project authority**. It may execute an already-authorized operation and return evidence/receipts. It must not become a planner, grant/refresh its own authority, decide `PASS`, decide task `DONE`, own `WorkingState`, or widen the six-tool Chat-facing surface.

---

## Research question and scope

Question:

> Should Chat Agent Platform adopt Rust now, and if a native systems boundary becomes useful later, is Rust actually the best implementation language for that exact boundary?

This is not a language-preference or benchmark exercise. The relevant problem is where low-level ownership, crash, process-tree, sandbox and native-handle semantics become materially harder to express, verify or distribute safely in the current Python/Node/PowerShell implementation.

In scope:

- process/process-tree ownership;
- PTY/terminal lifecycle;
- Windows Job Object/native process-handle semantics;
- sandbox bootstrap and OS containment;
- private IPC between project authority and a native executor;
- future Track M / long-lived Agent Host implications;
- Rust versus a language-neutral/current-runtime implementation of the **same narrow native boundary**;
- whether current Control Plane/durable state should move to Rust.

Out of scope:

- changing the six public semantic tools;
- replacing ordinary ChatGPT as current planner;
- rewriting active Stage 26.3C;
- choosing a database/WAL/storage engine;
- same-task wake/scheduler design;
- selecting a durable native idempotency/attempt ledger;
- replacing OpenAdapt/UFO/Playwright roles;
- a general language benchmark.

---

## Current repository truth

### Release order

At the inspected project head, Stage 26.3C production integration/restart reconciliation is the immediate critical path. Track M Agent Session / Delegation remains future/parallel and non-release-critical. A native-host implementation must therefore not be inserted into 26.3C merely because its mechanism or implementation language is attractive.

### Current semantic/process boundary

`runtime/semantic-projection/bin/semantic-projection-launcher.mjs` is Node/JavaScript and owns:

- exact six-tool inventory preflight;
- runtime-output directory ownership;
- child `spawn(...)`;
- stdio forwarding;
- signal forwarding;
- child exit/error propagation.

It is small and understandable, but it is child-process-object oriented rather than a dedicated OS process-tree containment subsystem. This is **not** evidence of a current accepted defect; it identifies the seam where stronger native lifecycle requirements would land if a future consumer proves the need.

### Current consequence/recovery boundary

`runtime/control_plane/verified_workspace_artifact.py` is Python and already owns policy-heavy, consequence-aware mechanics including:

- filesystem observations/evidence;
- file-object identity checks;
- ExpectedEffect verification;
- checkpoint serialization;
- explicit `fsync` + replace ordering;
- rollback ownership checks;
- procedure state/recovery validation.

No evidence found in this research shows Python execution speed or language-level memory management is the current limiting factor for those semantics. Rust would not by itself solve ambiguous external effects, stale observations, incorrect authorization/operation identity, reconciliation mistakes, power-loss durability or task-completion correctness.

---

## Architecture lineage comparison

| Affected role | Prior lineage | Fresh result | Decision |
|---|---|---|---|
| Capability authorization / consequence policy | project deterministic Control Plane | native execution mechanisms do not justify delegating authority | `KEEP` |
| Capability-spanning operational state | project `WorkingState` | no inspected evidence requires a language migration | `KEEP` |
| Transition verification / completion | project Verification Kernel + Finish Gate | a native host can return evidence, never project `PASS`/`DONE` | `KEEP` |
| Agent session / long-lived host reference | Codex reference-only | strong process/native mechanisms; different trust/authority boundary | `KEEP` reference-only |
| Windows/native execution mechanics | selective project-owned adapters | a focused native boundary is credible; language not selected | `DEFER` / `UNRESOLVED` |
| Node semantic projection | project-owned six-tool projection | Cline demonstrates that a native shell can coexist with a TS sidecar | `KEEP` |
| Stage 26.3C artifact recovery | Python project-owned implementation + researched failure model | systems language does not remove consequence ambiguity/reconciliation | `KEEP` |

No baseline role is replaced by this Brief, so `ARCHITECTURE_REUSE_BASELINE.md` is not changed.

---

## Problem Evidence

### P1 — no demonstrated current Rust-requiring bottleneck

The current problem is restart-safe consequence handling, not CPU throughput, memory pressure or a proven native-memory defect. Rewriting accepted policy/state logic would add migration risk without addressing the actual failure model.

### P2 — a credible future native-lifecycle seam exists

Future Agent Host / worker / PTY / sandbox work may require:

- terminating the whole owned descendant tree when its owner dies;
- native process-handle identity rather than reusable PID assumptions;
- containment before a child can create descendants;
- explicit nested Windows Job Object behavior;
- cross-platform cancellation/shutdown contracts;
- a small reviewed wrapper around unsafe/native APIs.

These requirements are visible in mature open agent code today.

### P3 — the boundary can stay narrow, but the language is not proven

Cline demonstrates that a native desktop/process shell can remain separate from a TypeScript agent sidecar. Codex and Goose demonstrate that Rust can implement strong native lifecycle mechanics. Microsoft/Linux documentation shows the underlying OS mechanisms are not Rust-specific.

Therefore the evidence supports **the boundary**, not a current Rust selection.

### P4 — lost acknowledgement exposes a separate idempotency/concurrency research problem

If process creation may have happened but acknowledgement is lost, a retry can create a duplicate physical effect unless the system can prove otherwise. The current evidence set proves process-lifecycle mechanisms, not the consistency semantics of an atomic request-claim or durable deduplication store.

Therefore this Brief records only the **observable safety invariant** required of any future implementation. It intentionally does **not** select how that invariant is enforced.

---

## Solution Evidence

### Engineering-domain evidence

Source-code study does not replace OS evidence.

Primary sources:

- Microsoft `CreateJobObjectW`: <https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjectw>
- Microsoft `AssignProcessToJobObject`: <https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject>
- Microsoft process handles/identifiers: <https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers>
- Linux man-pages `PR_SET_PDEATHSIG`: <https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html>

Mechanism conclusions:

- `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` terminates associated processes when the final Job Object handle closes;
- Job assignment is handle-based and can fail under nested-job/security constraints;
- assigning an already-running process is not equivalent to creating it contained; designs needing a no-escape guarantee must close that pre-assignment race;
- a native process handle remains bound to the process object while owned, while a numeric PID should not be treated as permanent ownership identity;
- Linux `PR_SET_PDEATHSIG` provides a parent-death signal primitive but is platform-specific.

These sources support the **mechanism**, not a claim that Rust is uniquely capable of it.

### Source-code evidence

#### OpenAI Codex

Repository/ref: `openai/codex@4ee04c0aa5833ac39b1763f6ea44c7bc777c83dd`

Classification: `OPEN_IMPLEMENTED`

Inspected:

- `codex-rs/core/src/spawn.rs`
- `codex-rs/utils/pty/src/win/job.rs`

Code path:

- `spawn_child_async(...)` builds a `tokio::process::Command`, scrubs non-inheritable environment, applies sandbox/network state, configures stdio and uses `kill_on_drop(true)`;
- Linux pre-exec installs a parent-death signal path;
- Windows `JobObject` uses `CreateJobObjectW`, `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, owned process handles, suspended spawn, assignment-before-resume and whole-job termination.

Tests/failure evidence:

A targeted search at this exact ref for direct `JobObject` / `spawn_contained` / `kill_on_drop` lifecycle tests did **not** locate a dedicated direct test outside the implementation file. Classification remains `OPEN_IMPLEMENTED`, not “independently proven reliable”. A future project spike must own its fault tests.

Lesson: `ADAPT_MECHANIC` / `REFERENCE_ONLY`.

Project mapping: strong evidence that Rust is a credible implementation candidate for a narrow native boundary; no evidence to move Control Plane/WorkingState/verification authority into Rust.

#### Goose

Repository/ref: `aaif-goose/goose@a9060fd2eff2ef32c207bb39e9f0e229b8a2fb87`

Classification: `OPEN_IMPLEMENTED`

Inspected:

- `crates/goose/src/subprocess.rs`
- `crates/goose/tests/subprocess_cleanup.rs`

Code/test path:

- Unix subprocesses are placed in their own process group;
- Linux uses `PR_SET_PDEATHSIG(SIGTERM)` and rechecks parent identity during setup;
- long-lived MCP subprocess spawn is separated from an arbitrary Tokio worker thread;
- tests require a child to disappear after parent death, require a long-lived child to survive only the spawning thread ending, then require it to die when the actual owner process is killed.

Lesson: `ADAPT_MECHANIC` / `REFERENCE_ONLY`.

Project mapping: process ownership should be a separately specified/tested contract, not “we called kill”.

#### Cline

Repository/ref: `cline/cline@1fbcfab05dccad23c12ef75ce45f99d711a82fb7`

Classification: `OPEN_IMPLEMENTED` for the **boundary shape**; operational lifecycle reliability remains only partially evidenced.

Inspected:

- `apps/examples/desktop-app/src-tauri/src/main.rs`
- `apps/examples/desktop-app/sidecar/server.ts`
- commit history around desktop sidecar shutdown, including `036fc75b1f89ca0af9fee84162064758183b0bc0` and `f5224abdf527fe6679a3c8bf1ba35d84222eccbe`

Code path:

Rust/Tauri owns `DesktopBackendState`, explicit lock ordering, child ownership/shutdown, platform-specific termination, Windows `CREATE_NO_WINDOW`, update serialization and native desktop lifecycle. TypeScript/Bun owns HTTP/WebSocket transport, origin checks, approval-token gating and command routing.

Failure/history evidence:

- `f5224ab...` recorded an earlier design that waited past the sidecar's graceful-shutdown budget before escalating to kill so restart would not interrupt persistence;
- `036fc75...` later records a real macOS failure: a malformed shutdown URL meant the sidecar never received shutdown, and polling the child on the main thread caused a 5–7 second beach-ball; the fix changed Unix quit behavior to signal `SIGTERM` and return while the sidecar performs bounded graceful shutdown;
- current code at the inspected ref contains the corresponding nonblocking Unix shutdown and separate immediate Windows kill/wait path;
- targeted searches did not locate a dedicated direct unit/integration test for `DesktopBackendState.stop()` process termination itself.

Lesson: `REFERENCE_ONLY` for the **separation shape** plus useful failure-history evidence. It is not treated as proof that the exact shutdown implementation is generally reliable.

Project mapping: Cline demonstrates that native/process ownership can be separated from a TS agent runtime. It does not decide which language our future native boundary should use.

#### OpenHands

Repository/ref: `OpenHands/OpenHands@226a6d2e68ebd5c86e4f275a0f33ca25f1ee0878`

Classification: `OPEN_PARTIAL` for the ACP process boundary examined here.

Inspected:

- `src/utils/acp-command.ts`
- `__tests__/utils/acp-command.test.ts`

The TypeScript layer converts a human-entered ACP command into argv and documents that a separate agent-server passes it to Python `subprocess.create_subprocess_exec` without a shell. Tests cover quoting, shell-metacharacter literal handling, URL/query-string regression, empty argv elements and no environment/subshell expansion.

The actual agent-server subprocess implementation was not located in this repository during targeted search, so this Brief does **not** claim to have proven its complete lifecycle implementation.

Lesson: `REFERENCE_ONLY`.

Project mapping: useful negative evidence against “major agent = Rust core everywhere”; semantic normalization can remain in a higher-level language behind a separate execution boundary.

---

## Approaches compared

### A — keep current Python/Node/PowerShell with no new native-host boundary

Pros:

- zero migration/toolchain risk;
- preserves current acceptance evidence;
- fastest 26.3C path;
- high iteration speed.

Cons:

- native lifecycle semantics may scatter if PTY/Job Object/process-tree requirements later expand.

Disposition: **KEEP current production**.

### B — narrow language-neutral/current-runtime native boundary

Shape:

```text
existing Python/Node project authority
 -> private typed boundary or focused native binding
 -> OS process / PTY / Job Object / sandbox mechanism
```

Possible implementations at future spike time include focused bindings from an existing runtime or a minimal helper written in another systems language. This Brief selects none of them.

Pros:

- may reuse existing runtime/toolchain and reduce migration surface;
- can expose the same small process/handle contract without changing Control Plane semantics;
- proves whether a separate compiled Rust component is actually necessary.

Cons:

- FFI/native bindings can still be unsafe and platform-specific;
- handle lifetime and process-tree ownership may be less ergonomic than RAII-heavy Rust code;
- a helper in another language may still create packaging/signing/version-skew costs.

Disposition: **DEFER; credible same-boundary alternative. Must be compared directly with Rust on re-entry.**

### C — narrow Rust native host below project authority

Shape:

```text
Python/Node project authority
 -> versioned typed private IPC
 -> small Rust native host
 -> process / PTY / Job Object / sandbox / native handles
```

Pros:

- isolates native/unsafe details;
- RAII/ownership model maps naturally to process/handle lifetime;
- strong real-world precedent in Codex/Goose;
- independently fault-testable.

Cons:

- adds binary/toolchain/signing matrix, IPC/version skew and another crash domain;
- no current benchmark/failure comparison proves it superior to Approach B for this project's exact boundary.

Disposition: **DEFER; credible candidate, not selected. Future native-host language remains `UNRESOLVED`.**

### D — migrate Control Plane / WorkingState / broad agent runtime to Rust

Pros: one systems language; some low-level invariants could benefit from stronger types/ownership.

Cons: no current problem evidence, large regression/migration surface, invalidates accepted semantics/evidence, delays critical path, and Rust does not solve semantic reconciliation automatically.

Disposition: **REJECT for the current architecture horizon**.

### E — move only durable checkpoint/state storage to Rust

Pros: possible future typed native storage owner.

Cons: persistence correctness is about journal/fsync/transaction/external-effect protocol, not Rust itself; adds IPC/FFI around sensitive state and would reopen 26.3C.

Disposition: **DEFER as separate persistence research**.

### Comparison conclusion

The current evidence chooses only this much:

```text
current release-critical stack        KEEP
future narrow native-host seam        CREDIBLE / RESEARCH-ONLY
future native-host implementation     UNRESOLVED: Rust vs language-neutral/current-runtime boundary
broad Rust control/state migration    REJECT current horizon
```

A future spike must compare Approach B and Approach C against the **same** process-tree/PTY/Job Object requirements and the same packaging, crash, security and physical-qualification tests before selecting a language.

---

## Duplicate delivery / lost acknowledgement safety invariant

Process launch is a consequence-bearing side effect. A future native boundary must not treat request transport as exactly-once delivery.

Project `WorkingState` remains authoritative for `logical_operation_id`, `AttemptIntent`/`AttemptRecord`, unresolved outcome and reconciliation authority. A future request may carry `logical_operation_id + attempt_id` for correlation, but this Brief does not choose a host-side claim, deduplication database, lock, transaction, durable ledger, queue or other consistency primitive.

Required observable behavior:

- **maximum physical effects before reconciliation: at most one spawn for one authorized attempt;**
- duplicate or concurrent delivery must never increase that maximum;
- if spawn may have happened but acknowledgement is lost, project `WorkingState` records the attempt as `OUTCOME_UNKNOWN` / unresolved and blocks another physical attempt;
- another physical attempt under the same logical operation is permitted only after fresh reconciliation proves the prior attempt `CONFIRMED_NOT_APPLIED` and normal LoopGuard/budget/authority checks pass;
- `CONFIRMED_APPLIED` advances without a re-spawn; `STILL_UNKNOWN` remains blocked;
- if a candidate implementation cannot establish the at-most-one-spawn invariant across its declared concurrency/crash scope, that implementation does not qualify for the consequence-bearing path.

**Implementation mechanism is intentionally unspecified.** The consistency boundary, crash behavior, retained state, contention model, alternatives and failure history of any mechanism proposed to enforce duplicate/concurrent-delivery safety require fresh Stage Research before that primitive can enter production architecture.

---

## Failure / Crash Matrix for any future native-host spike

| Failure | Required behavior |
|---|---|
| binary/helper missing or wrong version | capability unavailable; no fallback mutation |
| IPC/binding contract mismatch | reject before delivery |
| Control Plane disconnect before delivery | no execution without current authorization |
| duplicate/concurrent delivery before spawn | **at most one spawn** within the declared scope; enforcement mechanism requires separate research |
| host/helper crashes before spawn | `NOT_APPLIED` only if freshly established; otherwise reconcile |
| spawn occurs but acknowledgement is lost | attempt becomes unresolved; no blind retry or second physical attempt before reconciliation |
| host/helper restarts while prior attempt unresolved | project WorkingState remains authoritative; no redelivery before reconciliation |
| owner dies | owned descendant tree terminates unless reviewed semantics explicitly preserve it |
| child spawns before containment | prevent with suspended/atomic containment where required; otherwise fail closed |
| Windows nested-job/assignment failure | explicit containment failure; no silent uncontained consequence fallback |
| PID reused | use owned native handle/identity where ownership depends on identity |
| cancel races with completion | one terminal lifecycle outcome; distinguish cancelled/completed/unknown |
| sandbox bootstrap fails | no unsandboxed fallback when sandbox is required |
| stdio/PTY task dies | bounded cleanup; no leaked tree |
| stale/expired grant | reject before native delivery; executor cannot renew its own authority |
| executor says success, postcondition false | project Kernel can return `FAIL`; delivery success is evidence only |
| external effect happened but ack lost | project reconciliation handles `OUTCOME_UNKNOWN`; no blind retry |
| native/helper binary differs from qualified source | source-provenance gate rejects release-critical claim |
| OS/machine power loss | outside process-lifetime guarantee unless separately researched |
| IPC peer/request mismatch | reject actor/environment/capability/effect mismatch |
| package/update failure | keep known-good runtime or capability unavailable; never weaken policy |

---

## Future authority boundary

A future request should resemble:

```text
ExecuteNativeOperation {
  protocol_version
  logical_operation_id
  attempt_id
  capability_id
  actor/environment binding
  scoped executable/argv/cwd/env policy
  containment requirements
  timeout/cancellation policy
  authorization/grant reference
  evidence_correlation_id
}
```

not `run_anything(command)`.

The executor returns lifecycle/delivery evidence with the same logical/attempt correlation, native identity, containment state, started/exited/cancelled/unknown status, exit/signal metadata and evidence refs. Project observation + Verification Kernel still decides whether the intended effect occurred.

---

## What stays where by default

### Keep Python

- `WorkingState` and reconciliation domain rules;
- LoopGuard/budgets;
- Verification Kernel/Finish Gate policy;
- policy-heavy capability code where native APIs are not the bottleneck;
- research/qualification tooling.

### Keep Node/TypeScript

- MCP/semantic projection and six-tool Chat-facing contract;
- Playwright/browser integration;
- higher-level UI/adapters not requiring native ownership guarantees.

### Keep declarative

- skills;
- schemas/configuration;
- architecture/acceptance policy;
- procedure definitions where a selected external IR/runtime owns the role.

---

## Re-entry triggers

Re-run fresh Stage Research before production Rust work **or any new native-host implementation** if one or more becomes true:

1. repeated accepted evidence of leaked child/grandchild processes or incorrect process ownership;
2. a release-critical capability requires Job Object/native-handle semantics that current code cannot provide cleanly/testably;
3. Track M needs a long-lived local Agent Host with strong child/process/PTY lifecycle guarantees;
4. 26.5/native computer-use needs a shared sandbox/PTY/native layer across capabilities;
5. process-lifecycle logic is duplicated across enough Node/Python/PowerShell capabilities that one owner measurably reduces risk;
6. distribution/signing/update needs favor one small native helper/host;
7. benchmark/failure evidence shows the current language/runtime itself — not architecture semantics — causes a material reliability/security/performance problem.

Re-entry must re-pin then-current references. The refs in this 2026-08-28 Brief are evidence for this decision, **not timeless architecture**.

Any proposed duplicate/concurrent-delivery primitive is itself a material concurrency/recovery mechanism and must receive its own solution-domain evidence, alternatives and failure/crash analysis during re-entry rather than inheriting authority from this Brief.

---

## Verification plan for a future bounded spike

If future re-entry authorizes a prototype, compare language-neutral/current-runtime and Rust implementations against the same contract and require at minimum:

- no public Chat-facing tool change;
- strict versioned private protocol/binding contract;
- exact executed native/helper source provenance;
- Windows Job Object root + grandchild cleanup test;
- Windows nested-job/assignment-failure fail-closed test;
- Linux owner-death/process-group test comparable to Goose;
- duplicate/concurrent delivery fault test proving the **at-most-one-spawn** invariant for the candidate's declared scope;
- spawn/lost-ack fault test proving zero new physical attempt before fresh reconciliation;
- restart with unresolved attempt proving zero redelivery before fresh reconciliation;
- separate research evidence for whatever consistency primitive is proposed to enforce those invariants;
- crash before spawn, after spawn/before ack and after exit/before ack;
- cancellation/completion race tests;
- stale/expired grant rejection before delivery;
- proof executor `success` cannot directly create project Verification `PASS` or Finish `DONE`;
- unsupported platform => capability unavailable, not broad fallback;
- target-Windows packaging/update/provenance qualification;
- measurement of binary/toolchain/packaging complexity and failure surface for each candidate;
- physical ordinary-Chat qualification only if the host enters a release-critical consequence path.

---

## Final conclusion

Rust is **not currently justified as a migration target for Chat Agent Platform's control/state architecture**, and this research does not justify selecting Rust even for a future narrow native-host implementation.

The code plus OS-mechanism evidence supports a more careful conclusion:

> If future work requires stronger process-tree, PTY, sandbox or native-handle guarantees, introduce one small project-owned native execution boundary *below* existing semantic/Control Plane authority. At that future re-entry, compare Rust against an equivalent language-neutral/current-runtime implementation of the same boundary before selecting the language. Research any duplicate/concurrent-delivery consistency primitive separately rather than smuggling one in as part of the language choice.

For the current roadmap the structured decision remains `DEFER`. Stage 26.3C continues on its already-researched Python/project-owned recovery path.

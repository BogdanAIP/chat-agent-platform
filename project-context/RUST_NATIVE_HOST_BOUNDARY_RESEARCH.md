# Rust Native Host Boundary — Stage Research Brief

Status: **STAGE RESEARCH BRIEF — DEFER PRODUCTION ADOPTION**

Research date: 2026-08-28

Project snapshot: `BogdanAIP/chat-agent-platform@bc13c7de3d559f5cf42dbee6f14ad5b2cc8681cc`

## Decision

**Top-level Stage Research decision: `DEFER`.**

Do **not** introduce Rust into the current release-critical production path and do not migrate the deterministic Control Plane, `WorkingState`, Verification Kernel, Finish Gate, public semantic projection, skills/configuration or Stage 26.3C artifact-recovery logic merely because major agent runtimes use Rust.

The research does identify one credible future boundary worth re-opening when there is a concrete consumer or failure signal:

```text
ordinary ChatGPT / current planner
        |
project semantic surface + Control Plane authority
        |
        | typed private IPC / capability request
        v
future optional Rust native host
        |
        +-- process / process-tree ownership
        +-- PTY / terminal lifecycle
        +-- Windows Job Objects / native process handles
        +-- sandbox bootstrap / native OS containment
        +-- native cancellation / shutdown / child reaping
        +-- narrow OS-specific adapters where qualified
```

The native host, if ever introduced, would be **below project authority**. It may execute an already-authorized operation and return evidence/receipts; it must not become a planner, grant authority to itself, decide `PASS`, decide task `DONE`, own `WorkingState`, or silently widen the six-tool Chat-facing surface.

Production implementation remains blocked until a future Stage Research re-entry is triggered by an observed requirement and revalidates the then-current code, failure model, alternatives and upstream references.

---

## Research question

Should Chat Agent Platform adopt Rust now, and if Rust becomes useful later, what is the smallest justified architectural boundary?

This is intentionally **not** a language-preference or benchmark question. The relevant question is where low-level ownership, crash, process-tree, sandbox and native-handle semantics become materially harder to express, verify or distribute safely in the current Python/Node/PowerShell implementation.

---

## Scope

In scope:

- process and process-tree ownership;
- PTY/terminal lifecycle;
- Windows Job Object/native process-handle semantics;
- sandbox bootstrap and OS containment;
- local private IPC boundary between project authority and a native executor;
- implications for future Track M / long-lived Agent Host work;
- whether current Control Plane/durable state should move to Rust.

Out of scope:

- changing the current six public semantic tools;
- replacing ordinary ChatGPT as the current general planner;
- rewriting Stage 26.3C while its current recovery work is active;
- choosing a new database/WAL/storage engine;
- same-task wake/scheduler design;
- replacing OpenAdapt/UFO/Playwright lineage decisions;
- a general language benchmark.

---

## Current repository truth

### Release order

At the inspected project head, Stage 26.3C production integration/restart reconciliation is the immediate critical path. Track M Agent Session / Delegation remains future/parallel and is explicitly non-release-critical. Therefore a new native-host implementation must not be inserted into 26.3C simply because the mechanism is attractive.

### Current semantic/process boundary

`runtime/semantic-projection/bin/semantic-projection-launcher.mjs` is Node/JavaScript and currently owns important launcher mechanics:

- exact six-tool inventory preflight;
- runtime-output directory ownership;
- child `spawn(...)`;
- stdio forwarding;
- signal forwarding;
- child exit/error propagation.

The current implementation is small and understandable, but it is process-id/child-object oriented rather than a dedicated OS process-tree containment subsystem. This observation is **not** evidence of a current accepted defect; it identifies the seam where stronger native lifecycle requirements would land if future consumers need them.

### Current consequence/recovery boundary

`runtime/control_plane/verified_workspace_artifact.py` is Python and already owns policy-heavy, consequence-aware mechanics including:

- filesystem observations and evidence;
- file-object identity checks;
- ExpectedEffect verification;
- checkpoint serialization;
- explicit `fsync` + replace ordering;
- rollback ownership checks;
- procedure state/recovery validation.

No evidence found in this research shows that Python execution speed or language-level memory management is currently the limiting factor for these semantics. Moving this code to Rust now would therefore be a migration without a demonstrated problem.

---

## Architecture lineage comparison

| Affected role | Prior lineage | Fresh code research | Decision |
|---|---|---|---|
| Capability authorization / consequence policy | project deterministic Control Plane | external Rust agents show native execution mechanisms, not a reason to delegate project authority | `KEEP` |
| Capability-spanning operational state | project `WorkingState` | no inspected source demonstrates a requirement to move project policy/state semantics into Rust | `KEEP` |
| Transition verification / task completion | project Verification Kernel + independent Finish Gate | native host can at most return execution evidence; external runtime success must not become project `PASS`/`DONE` | `KEEP` |
| Agent session / long-lived host reference | Codex is reference-only | current Codex code strongly supports Rust for child/sandbox/native lifecycle mechanics, while its trust/authority model remains different | `KEEP` as reference-only |
| Windows / native execution mechanics | selective project-owned adapters using mature external mechanics | Codex and Cline show a focused Rust layer is credible for Job Objects/native process lifetime | `DEFER` future bounded Rust-host candidate |
| Current Node semantic projection | project-owned six-tool projection | Cline demonstrates that a Rust desktop/native shell can coexist with a TypeScript sidecar instead of replacing it | `KEEP`; possible future private native executor below it |
| Stage 26.3C artifact recovery | current Python project-owned implementation + researched failure model | Rust does not remove ambiguous external-effect/reconciliation requirements | `KEEP`; no language migration in 26.3C |

No current baseline role is replaced by this Brief. Therefore `ARCHITECTURE_REUSE_BASELINE.md` does not need a new selected-component row yet.

---

## Problem Evidence

### P1 — there is no demonstrated current Rust-requiring bottleneck

The current critical-path work is restart-safe consequence handling, not CPU throughput, memory pressure or unsafe native code. The Python artifact procedure already expresses the important safety rules explicitly. Rust would not by itself solve:

- ambiguous external effects;
- stale observations;
- incorrect operation identity;
- incorrect authorization;
- bad reconciliation logic;
- power-loss durability;
- task completion correctness.

These remain architecture/protocol/evidence problems regardless of language.

### P2 — a real future native-lifecycle seam exists

The current Node launcher spawns and signals a child process. Future Agent Host / persistent worker / PTY / sandbox work may require stronger guarantees such as:

- kill the entire descendant tree if owner dies;
- bind identity to a native process handle rather than a reusable PID;
- atomically contain a child before it can spawn descendants;
- handle nested Windows Job Object constraints;
- make cancellation/shutdown semantics explicit across platforms;
- safely wrap unsafe Windows APIs behind a small reviewed surface.

Those requirements are visible in mature Rust agent implementations today.

### P3 — the language boundary can remain narrow

Cline provides a concrete counterexample to a full rewrite: its Tauri/Rust desktop shell owns native process/update lifecycle while a TypeScript/Bun sidecar owns the agent-facing HTTP/WebSocket/command runtime. That is much closer to the boundary this project would need than migrating all control/state logic to Rust.

---

## Solution Evidence

### Source-code evidence

#### 1. OpenAI Codex

Repository/ref:

`openai/codex@4ee04c0aa5833ac39b1763f6ea44c7bc777c83dd`

Classification: `OPEN_IMPLEMENTED`

Relevant code inspected:

- `codex-rs/core/src/spawn.rs`
- `codex-rs/utils/pty/src/win/job.rs`

Mechanism proven by code:

`spawn_child_async(...)` constructs a `tokio::process::Command`, scrubs non-inheritable environment, applies sandbox/network state, configures stdio and uses `kill_on_drop(true)`. On Linux it installs a parent-death signal path before exec so spawned shell children are terminated if the Codex parent dies.

The Windows `JobObject` implementation goes substantially further:

- `CreateJobObjectW`;
- `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`;
- process-handle capture before numeric PID reuse can confuse ownership;
- suspended spawn before Job assignment;
- `AssignProcessToJobObject` before resume;
- explicit handling when nested Job assignment is unavailable;
- whole-job termination;
- RAII ownership of Windows handles.

Lesson: `ADAPT_MECHANIC` / `REFERENCE_ONLY`.

Mapping to this project:

This is strong evidence for a future narrow process/native host if our requirements reach process-tree containment, PTY/sandbox or native-handle identity. It is **not** evidence to move Control Plane/WorkingState/verification authority into Rust.

Important difference:

Codex is a different agent harness with a broader local execution model. Its native process mechanisms can be studied without importing its authority model or tool surface.

#### 2. Goose

Repository/ref:

`aaif-goose/goose@a9060fd2eff2ef32c207bb39e9f0e229b8a2fb87`

Classification: `OPEN_IMPLEMENTED`

Relevant code/tests inspected:

- `crates/goose/src/subprocess.rs`
- `crates/goose/tests/subprocess_cleanup.rs`

Mechanism proven by code:

Goose centralizes subprocess configuration in Rust. On Unix it creates a separate process group; on Linux it installs `PR_SET_PDEATHSIG(SIGTERM)` and verifies the parent did not already change during setup. For long-lived MCP subprocesses it uses a dedicated spawning thread so lifecycle is bound to the process rather than an arbitrary Tokio worker thread.

The tests directly exercise lifecycle behavior:

- a child must disappear after its owning parent process exits;
- a long-lived child must survive the *spawning thread* ending;
- after the actual owning helper process is killed, the child must terminate.

Lesson: `ADAPT_MECHANIC` / `REFERENCE_ONLY`.

Mapping to this project:

This is evidence that process ownership is worth specifying and testing independently from task/control semantics. A future native host should have equivalent fault tests instead of relying on “we called kill”.

#### 3. Cline

Repository/ref:

`cline/cline@1fbcfab05dccad23c12ef75ce45f99d711a82fb7`

Classification: `OPEN_IMPLEMENTED` for the inspected desktop example boundary.

Relevant code inspected:

- `apps/examples/desktop-app/src-tauri/src/main.rs`
- `apps/examples/desktop-app/sidecar/server.ts`

Mechanism proven by code:

The Rust/Tauri side owns desktop-native state and the backend child process. The inspected code has:

- `DesktopBackendState` with explicit lock-order comment;
- child-process ownership and shutdown;
- platform-specific termination behavior;
- Windows `CREATE_NO_WINDOW` handling;
- update-cycle serialization and Windows-specific staged installation behavior;
- native app/tray/update lifecycle.

The agent sidecar remains TypeScript/Bun and owns HTTP/WebSocket transport, request origin checks, approval-token gating and command routing.

Lesson: `ADAPT_MECHANIC`.

Mapping to this project:

This is the strongest direct precedent for the preferred *shape* of a future Rust adoption:

```text
existing project semantic/control layers
 -> private typed boundary
 -> Rust native/process shell
```

rather than:

```text
rewrite semantic/control/state architecture in Rust
```

#### 4. OpenHands

Repository/ref:

`OpenHands/OpenHands@226a6d2e68ebd5c86e4f275a0f33ca25f1ee0878`

Classification: `OPEN_PARTIAL` for the specific ACP process boundary examined here.

Relevant code/tests inspected:

- `src/utils/acp-command.ts`
- `__tests__/utils/acp-command.test.ts`

Mechanism supported by the inspected public code:

The TypeScript UI parses a human-entered ACP command into an argv array and explicitly documents that the separate agent-server passes the array to Python `subprocess.create_subprocess_exec` without a shell. The tests cover quoting, literal shell metacharacters, URL/query-string corruption regressions, empty argv elements and no environment/subshell expansion.

The actual agent-server subprocess implementation was not located in this repository during this targeted search, so this Brief does **not** claim to have proven its complete lifecycle implementation.

Lesson: `REFERENCE_ONLY`.

Mapping to this project:

OpenHands is useful negative evidence against “major agent = Rust core everywhere”. It also reinforces a narrower principle: command/semantic normalization can stay in a higher-level language while process execution is separated behind another boundary.

---

## Approaches compared

### Approach A — keep the current Python/Node/PowerShell stack and harden only where failures appear

Shape:

```text
Python Control Plane + WorkingState
Node semantic projection / launcher
PowerShell/native commands where already bounded
```

Advantages:

- zero migration risk now;
- preserves accepted tests and physical evidence;
- fastest path through current 26.3C;
- easiest inspection/change velocity for policy-heavy logic;
- no new compiler/toolchain/distribution artifact.

Disadvantages:

- increasingly awkward if future requirements need PTY/native handles/Job Objects/process-tree containment across OSes;
- process-lifecycle semantics can become scattered across Node/Python/PowerShell;
- native API wrappers may become harder to reason about and qualify as the surface grows.

Disposition: **KEEP for current production**.

### Approach B — narrow Rust native host below project authority

Shape:

```text
Python/Node project authority
 -> versioned typed private IPC
 -> small Rust native host
 -> process / PTY / Job Object / sandbox / native handles
```

Advantages:

- isolates unsafe/native details into a small reviewed component;
- strong RAII ownership for process/handle lifetime;
- maps closely to mechanisms seen in Codex/Goose and boundary shape seen in Cline;
- can be tested independently with crash/process-tree fault tests;
- does not require rewriting policy/state/verification logic.

Disadvantages:

- adds a compiled binary, Rust toolchain and cross-platform packaging/signing matrix;
- creates an IPC/version-skew boundary;
- adds another crash/restart domain;
- may be needless complexity unless a real consumer needs it.

Disposition: **preferred future candidate, but production `DEFER` now**.

### Approach C — migrate the Control Plane / WorkingState / agent runtime substantially to Rust

Advantages:

- one systems language for more runtime internals;
- type/ownership model could help some low-level invariants;
- resembles broad Rust-centric agent runtimes such as Codex/Goose.

Disadvantages:

- no current problem evidence justifies the migration;
- rewrites accepted policy and verification semantics with high regression risk;
- confuses “native lifecycle needs Rust-like mechanisms” with “all agent logic should be Rust”;
- would invalidate a large body of current tests/acceptance evidence and delay the release-critical path;
- Rust does not solve the core semantic ambiguity/reconciliation problem automatically.

Disposition: **REJECT for the current architecture horizon**. Reconsider only if a future measured problem is specifically caused by the current language/runtime boundary rather than by design semantics.

### Approach D — move only durable state/checkpoint storage to Rust

Advantages:

- could eventually provide a typed native persistence library;
- could centralize state-file/DB serialization and locking.

Disadvantages:

- persistence correctness depends on storage protocol, fsync/journal/transaction ordering and external-effect reconciliation, not on Rust alone;
- introduces FFI/IPC around the most semantically sensitive state;
- current Stage 26.3C has already researched a narrower failure model and must not be replaced mid-stream without re-entry.

Disposition: **DEFER as a separate persistence research question**. Do not bundle it with native-host adoption.

---

## Failure / Crash Matrix for any future Rust native-host spike

| Failure point | Required behavior |
|---|---|
| native host binary missing / wrong version | capability unavailable; no fallback mutation |
| IPC protocol/version mismatch | fail handshake closed before delivery |
| Control Plane disconnect before native delivery | no execution without a valid current request/grant |
| host crashes before child spawn | report/not-observe `NOT_APPLIED`; bounded retry only after fresh authority/evidence |
| host crashes after spawn before acknowledgement | process/job ownership must make effect state observable; never blind-redeliver |
| owner process dies | owned child tree terminates unless a reviewed operation explicitly permits survival |
| child spawns grandchild before containment | prevent with suspended/atomic containment where platform supports it; otherwise fail closed for guarantees that require containment |
| Windows Job assignment rejected/nested-job conflict | explicit unsupported/failed containment result; no silent uncontained consequence-bearing fallback |
| PID reused | use owned native handle/process identity where ownership claims depend on identity |
| cancellation races with completion | one terminal lifecycle outcome; evidence must distinguish completed vs cancelled vs unknown |
| sandbox bootstrap fails | do not run unsandboxed when sandbox is a required precondition |
| stdio/PTY reader dies | bounded cleanup; no leaked process tree |
| host receives stale/expired grant | reject before execution; host cannot extend/refresh its own authority |
| host returns `success` but postcondition is false | project Verification Kernel may return `FAIL`; host success is delivery evidence only |
| host cannot report outcome after external effect | project reconciliation path handles `OUTCOME_UNKNOWN`; Rust does not authorize blind retry |
| host/update binary differs from qualified source | source-provenance gate rejects release-critical claim |
| OS/machine power loss | outside any process-lifetime guarantee unless separately researched; Rust alone provides no transactional power-loss guarantee |
| private IPC compromised/misrouted | request identity + actor/environment/capability/effect binding required; reject mismatched peer/request |
| packaging/signing/updater failure | preserve previous working runtime or mark capability unavailable; never weaken authority to recover availability |

---

## Authority boundary if the research is re-opened

A future native host request should be conceptually closer to:

```text
ExecuteNativeOperation {
  protocol_version
  operation_id
  capability_id
  actor/environment binding
  scoped executable/argv/cwd/env policy
  containment requirements
  timeout/cancellation policy
  authorization/grant reference
  evidence correlation id
}
```

than to a generic:

```text
run_anything(command)
```

The host returns delivery/lifecycle evidence, not project truth:

```text
NativeExecutionReceipt {
  operation_id
  native_process_identity
  containment status
  started / exited / cancelled / unknown
  exit/signal metadata
  stdout/stderr evidence refs
  native errors
}
```

Project observation + Verification Kernel still decides whether the intended effect occurred.

---

## What stays Python / Node / declarative by default

### Keep Python

- `WorkingState` domain model and consequence/reconciliation rules;
- LoopGuard/budgets;
- Verification Kernel/Finish Gate policy;
- effect/observation policy-heavy capability code where native APIs are not the bottleneck;
- research/qualification tooling that benefits from fast iteration.

Reason: no current evidence shows a systems-language requirement, while migration would endanger already-accepted semantics.

### Keep Node/TypeScript

- MCP/semantic projection and protocol integration where the ecosystem/API surface is naturally JS/TS;
- current six-tool Chat-facing contract;
- browser integration where Playwright/Node remains the mature selected mechanism;
- higher-level UI/adapter code not requiring native ownership guarantees.

Cline specifically demonstrates that a Rust native shell does not require the agent sidecar to stop being TypeScript.

### Keep declarative/docs/skills

- skills;
- schemas/configuration;
- architecture/acceptance policy;
- procedure definitions where an external selected IR/runtime already owns the role.

Do not move declarative policy into compiled code merely to increase the Rust share of the repository.

---

## Re-entry triggers

Re-run fresh Stage Research before production Rust work if one or more of these becomes true:

1. repeated accepted evidence of leaked child/grandchild processes or incorrect process ownership;
2. a release-critical capability requires Windows Job Object/native-handle semantics that the current stack cannot provide cleanly and testably;
3. Track M needs a long-lived local Agent Host with strong child/process/PTY lifecycle guarantees;
4. 26.5/native computer-use work requires a reviewed sandbox/PTY/native execution layer across multiple capabilities;
5. current Node/Python/PowerShell lifecycle code becomes duplicated across enough capabilities that one native owner measurably reduces risk;
6. distribution/signing/update requirements favor one small native host over several script/runtime-specific process supervisors;
7. a benchmark or failure study demonstrates that the current language/runtime itself — not architecture semantics — is causing a material reliability/security/performance problem.

A re-entry must re-pin current Codex/Goose/Cline/OpenHands or other mechanism-relevant repositories; these 2026-08-28 refs are evidence for this Brief, not timeless architecture.

---

## Verification plan for a future bounded spike

If re-entry authorizes a prototype, require at minimum:

- no public Chat-facing tool change;
- versioned private protocol with strict unknown-field/version behavior;
- source-provenance binding to the exact native binary executed;
- Windows: owned Job Object test proving root + grandchild cleanup;
- Windows: nested-job/assignment-failure test proving fail-closed behavior when containment is required;
- Linux: owner-death/process-group test comparable to Goose parent-death tests;
- crash immediately before spawn, after spawn/before ack, after child exit/before ack;
- cancellation-vs-completion race tests;
- stale/expired grant rejection before native delivery;
- test proving native `success` cannot directly create project Verification `PASS` or Finish `DONE`;
- unsupported-platform behavior returns capability unavailable rather than broad fallback;
- packaging/update/source-provenance qualification on target Windows;
- physical ordinary-Chat qualification only if/when the native host enters a release-critical consequence path.

---

## Final conclusion

Rust is **not currently justified as a migration target for Chat Agent Platform's control/state architecture**.

The code study does support a much narrower architectural hypothesis:

> If future work requires stronger OS process-tree, PTY, sandbox or native-handle guarantees, introduce one small project-owned Rust native host *below* the existing semantic/Control Plane authority, rather than rewriting the planner, WorkingState, Verification Kernel or semantic projection.

For the current roadmap this remains **`DEFER`**. Stage 26.3C continues on its already-researched Python/project-owned recovery path. The Rust boundary should be reopened only when a concrete native-lifecycle consumer or failure signal appears.
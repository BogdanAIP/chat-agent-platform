# Rust Native Host Boundary — Stage Research Brief

Status: **STAGE RESEARCH BRIEF — DEFER PRODUCTION ADOPTION**

Research date: 2026-08-28

Project snapshot: `BogdanAIP/chat-agent-platform@bc13c7de3d559f5cf42dbee6f14ad5b2cc8681cc`

## Decision

**Top-level Stage Research decision: `DEFER`.**

Do **not** introduce Rust into the current release-critical production path and do not migrate the deterministic Control Plane, `WorkingState`, Verification Kernel, Finish Gate, public semantic projection, skills/configuration or Stage 26.3C artifact-recovery logic merely because major agent runtimes use Rust.

The only credible future Rust boundary identified by this research is a **small optional native host below project authority**:

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
        +-- cancellation / shutdown / child reaping
        +-- narrow OS-specific adapters where qualified
```

The host may execute an already-authorized operation and return evidence/receipts. It must not become a planner, grant authority to itself, decide `PASS`, decide task `DONE`, own `WorkingState`, or widen the six-tool Chat-facing surface.

Production implementation remains blocked until a future Stage Research re-entry is triggered by an observed requirement and revalidates current code, failure model, alternatives and upstream references.

---

## Research question and scope

Question:

> Should Chat Agent Platform adopt Rust now, and if Rust becomes useful later, what is the smallest justified architectural boundary?

This is not a language-preference or benchmark exercise. The question is where low-level ownership, crash, process-tree, sandbox and native-handle semantics become materially harder to express, verify or distribute safely in the current Python/Node/PowerShell implementation.

In scope:

- process/process-tree ownership;
- PTY/terminal lifecycle;
- Windows Job Object/native process-handle semantics;
- sandbox bootstrap and OS containment;
- private IPC between project authority and a native executor;
- future Track M / long-lived Agent Host implications;
- whether current Control Plane/durable state should move to Rust.

Out of scope:

- changing the six public semantic tools;
- replacing ordinary ChatGPT as current planner;
- rewriting active Stage 26.3C;
- choosing a database/WAL/storage engine;
- same-task wake/scheduler design;
- replacing OpenAdapt/UFO/Playwright roles;
- a general language benchmark.

---

## Current repository truth

### Release order

At the inspected project head, Stage 26.3C production integration/restart reconciliation is the immediate critical path. Track M Agent Session / Delegation remains future/parallel and non-release-critical. A Rust/native-host implementation must therefore not be inserted into 26.3C merely because the mechanism is attractive.

### Current semantic/process boundary

`runtime/semantic-projection/bin/semantic-projection-launcher.mjs` is Node/JavaScript and owns:

- exact six-tool inventory preflight;
- runtime-output directory ownership;
- child `spawn(...)`;
- stdio forwarding;
- signal forwarding;
- child exit/error propagation.

It is small and understandable, but it is child-process-object oriented rather than a dedicated OS process-tree containment subsystem. This is **not** evidence of a current accepted defect; it identifies the seam where stronger native lifecycle requirements would land.

### Current consequence/recovery boundary

`runtime/control_plane/verified_workspace_artifact.py` is Python and already owns policy-heavy, consequence-aware mechanics including:

- filesystem observations/evidence;
- file-object identity checks;
- ExpectedEffect verification;
- checkpoint serialization;
- explicit `fsync` + replace ordering;
- rollback ownership checks;
- procedure state/recovery validation.

No evidence found in this research shows Python speed or memory management is the current limiting factor for those semantics. Rust would not by itself solve ambiguous external effects, stale observations, incorrect authorization/operation identity, reconciliation mistakes, power-loss durability or task-completion correctness.

---

## Architecture lineage comparison

| Affected role | Prior lineage | Fresh result | Decision |
|---|---|---|---|
| Capability authorization / consequence policy | project deterministic Control Plane | native execution mechanisms do not justify delegating authority | `KEEP` |
| Capability-spanning operational state | project `WorkingState` | no inspected evidence requires a language migration | `KEEP` |
| Transition verification / completion | project Verification Kernel + Finish Gate | native host can return evidence, never project `PASS`/`DONE` | `KEEP` |
| Agent session / long-lived host reference | Codex reference-only | strong process/native mechanisms; different trust/authority boundary | `KEEP` reference-only |
| Windows/native execution mechanics | selective project-owned adapters | focused Rust layer is credible for Job Objects/native lifetime | `DEFER` future candidate |
| Node semantic projection | project-owned six-tool projection | Cline proves Rust shell can coexist with TS sidecar | `KEEP` |
| Stage 26.3C artifact recovery | Python project-owned implementation + researched failure model | Rust does not remove consequence ambiguity/reconciliation | `KEEP` |

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

### P3 — the boundary can stay narrow

Cline is direct evidence that Rust need not own the agent logic: its Tauri/Rust desktop shell owns native/process lifecycle while its TypeScript/Bun sidecar owns the agent-facing HTTP/WebSocket/command runtime.

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

These sources support the **mechanism**, not a claim that Rust is uniquely capable of it. If this project later needs these semantics, they should live behind an explicit native lifetime/containment boundary regardless of implementation language.

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

A targeted search at this exact ref for direct `JobObject` / `spawn_contained` / `kill_on_drop` lifecycle tests did **not** locate a dedicated direct test outside the implementation file. Classification remains `OPEN_IMPLEMENTED`, not “independently proven reliable”. This negative space is one reason the future project verification plan requires its own process-tree fault tests rather than inheriting confidence from Codex.

Lesson: `ADAPT_MECHANIC` / `REFERENCE_ONLY`.

Project mapping: strong evidence for a future narrow process/native host; no evidence to move Control Plane/WorkingState/verification authority into Rust.

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

Classification: `OPEN_IMPLEMENTED` for the inspected desktop example.

Inspected:

- `apps/examples/desktop-app/src-tauri/src/main.rs`
- `apps/examples/desktop-app/sidecar/server.ts`

Code path:

Rust/Tauri owns `DesktopBackendState`, explicit lock ordering, child ownership/shutdown, platform-specific termination, Windows `CREATE_NO_WINDOW`, update serialization and native desktop lifecycle. TypeScript/Bun still owns HTTP/WebSocket transport, origin checks, approval-token gating and command routing.

Lesson: `ADAPT_MECHANIC`.

Project mapping: this is the strongest precedent for the preferred future shape:

```text
existing project semantic/control layers
 -> private typed boundary
 -> Rust native/process shell
```

not a broad rewrite.

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

### A — keep current Python/Node/PowerShell and harden only observed problems

Pros: zero migration, preserves acceptance evidence, fastest current 26.3C path, high iteration speed, no compiled distribution artifact.

Cons: native lifecycle semantics may scatter if PTY/Job Object/process-tree requirements expand.

Disposition: **KEEP current production**.

### B — narrow Rust native host below project authority

```text
Python/Node project authority
 -> versioned typed private IPC
 -> small Rust native host
 -> process / PTY / Job Object / sandbox / native handles
```

Pros: isolates native/unsafe details, strong handle/process ownership, independently fault-testable, maps to Codex/Goose mechanisms and Cline boundary shape.

Cons: adds binary/toolchain/signing matrix, IPC/version skew and another crash domain; may be needless until a consumer exists.

Disposition: **preferred future candidate; production `DEFER` now**.

### C — migrate Control Plane / WorkingState / broad agent runtime to Rust

Pros: one systems language; some low-level invariants could benefit from stronger types/ownership.

Cons: no current problem evidence, large regression/migration surface, invalidates accepted semantics/evidence, delays critical path, and Rust does not solve semantic reconciliation automatically.

Disposition: **REJECT for the current architecture horizon**.

### D — move only durable checkpoint/state storage to Rust

Pros: possible future typed native storage owner.

Cons: persistence correctness is about journal/fsync/transaction/external-effect protocol, not Rust itself; adds IPC/FFI around sensitive state and would reopen 26.3C.

Disposition: **DEFER as separate persistence research**.

---

## Failure / Crash Matrix for any future native-host spike

| Failure | Required behavior |
|---|---|
| binary missing/wrong version | capability unavailable; no fallback mutation |
| IPC version mismatch | reject before delivery |
| Control Plane disconnect before delivery | no execution without current authorization |
| host crashes before spawn | `NOT_APPLIED` only if freshly established; otherwise reconcile |
| host crashes after spawn before ack | process/job state must be observable; never blind-redeliver |
| owner dies | owned descendant tree terminates unless reviewed semantics explicitly preserve it |
| child spawns before containment | prevent with suspended/atomic containment where required; otherwise fail closed |
| Windows nested-job/assignment failure | explicit containment failure; no silent uncontained consequence fallback |
| PID reused | use owned native handle/identity where ownership depends on identity |
| cancel races with completion | one terminal lifecycle outcome; distinguish cancelled/completed/unknown |
| sandbox bootstrap fails | no unsandboxed fallback when sandbox is required |
| stdio/PTY task dies | bounded cleanup; no leaked tree |
| stale/expired grant | reject before native delivery; host cannot renew its own authority |
| host says success, postcondition false | project Kernel can return `FAIL`; delivery success is evidence only |
| external effect happened but ack lost | project reconciliation handles `OUTCOME_UNKNOWN`; no blind retry |
| native binary differs from qualified source | source-provenance gate rejects release-critical claim |
| OS/machine power loss | outside process-lifetime guarantee unless separately researched |
| IPC peer/request mismatch | reject actor/environment/capability/effect mismatch |
| package/update failure | keep known-good runtime or capability unavailable; never weaken policy |

---

## Future authority boundary

A future request should resemble:

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
  evidence_correlation_id
}
```

not `run_anything(command)`.

The host returns lifecycle/delivery evidence such as native identity, containment state, started/exited/cancelled/unknown status, exit/signal metadata and evidence refs. Project observation + Verification Kernel still decides whether the intended effect occurred.

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

Cline demonstrates that a Rust native shell does not require the agent sidecar to stop being TypeScript.

### Keep declarative

- skills;
- schemas/configuration;
- architecture/acceptance policy;
- procedure definitions where a selected external IR/runtime owns the role.

---

## Re-entry triggers

Re-run fresh Stage Research before production Rust work if one or more becomes true:

1. repeated accepted evidence of leaked child/grandchild processes or incorrect process ownership;
2. a release-critical capability requires Job Object/native-handle semantics that current code cannot provide cleanly/testably;
3. Track M needs a long-lived local Agent Host with strong child/process/PTY lifecycle guarantees;
4. 26.5/native computer-use needs a shared sandbox/PTY/native layer across capabilities;
5. process-lifecycle logic is duplicated across enough Node/Python/PowerShell capabilities that one owner measurably reduces risk;
6. distribution/signing/update needs favor one small native host;
7. benchmark/failure evidence shows the current language/runtime itself — not architecture semantics — causes a material reliability/security/performance problem.

Re-entry must re-pin then-current references. The refs in this 2026-08-28 Brief are evidence for this decision, **not timeless architecture**.

---

## Verification plan for a future bounded spike

If future re-entry authorizes a prototype, require at minimum:

- no public Chat-facing tool change;
- strict versioned private protocol;
- exact native-binary source provenance;
- Windows Job Object root + grandchild cleanup test;
- Windows nested-job/assignment-failure fail-closed test;
- Linux owner-death/process-group test comparable to Goose;
- crash before spawn, after spawn/before ack and after exit/before ack;
- cancellation/completion race tests;
- stale/expired grant rejection before delivery;
- proof native `success` cannot directly create project Verification `PASS` or Finish `DONE`;
- unsupported platform => capability unavailable, not broad fallback;
- target-Windows packaging/update/provenance qualification;
- physical ordinary-Chat qualification only if the host enters a release-critical consequence path.

---

## Final conclusion

Rust is **not currently justified as a migration target for Chat Agent Platform's control/state architecture**.

The code plus OS-mechanism research supports a narrower hypothesis:

> If future work requires stronger process-tree, PTY, sandbox or native-handle guarantees, introduce one small project-owned Rust native host *below* existing semantic/Control Plane authority instead of rewriting the planner, WorkingState, Verification Kernel or semantic projection.

For the current roadmap this remains **`DEFER`**. Stage 26.3C continues on its already-researched Python/project-owned recovery path. Reopen the Rust boundary only for a concrete native-lifecycle consumer or accepted failure signal.
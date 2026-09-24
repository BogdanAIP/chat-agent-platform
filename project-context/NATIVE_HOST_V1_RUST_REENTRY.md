# Native Host v1 — Rust re-entry on frozen CAP Core

Research date: 2026-09-24

Repository base: BogdanAIP/chat-agent-platform@ca6923924952a2f457dc12e3604c97034a8fae23

Applicable repository skills:

- .agents/skills/stage-research/SKILL.md v1.2
- .agents/skills/source-code-research/SKILL.md v1.0

Prior research input: draft PR #170, created from the earlier Core head
c9fce847c0712ac913d6cb49787f892c11514fbb. This document refreshes that research against
the final aggregate Core freeze head instead of treating #170 as implementation authority.

## Stage goal

Add the smallest native systems executor needed below CAP Core for one already-authorized,
bounded Windows process operation.

The first production slice must provide:

~~~
one short-lived host process
 -> bounded private framed stdio
 -> one BeginOperation
 -> Windows non-interactive child
 -> suspended create
 -> Job Object assignment
 -> resume only after containment
 -> bounded stdout/stderr evidence
 -> root/tree lifecycle observation
 -> whole-tree cancellation
 -> owner-loss cleanup
 -> terminal receipt
~~~

The host must not become a second planner, policy engine, WorkingState owner, scheduler,
daemon, generic shell tool or task-completion authority.

## Current project baseline

CAP Core v1 is frozen pending physical qualification at
ca6923924952a2f457dc12e3604c97034a8fae23.

The post-#169 Core changes strengthen rather than invalidate the Native Host boundary:

- #172 extracts explicit semantic provider seams, making the executor replaceability boundary
  clearer;
- #173 binds each Windows Case Desk physical transition to an exact Core grant/attempt before
  delivery;
- #174 adds forward-only legacy workspace grant handoff without rewriting historical attempts;
- #175 quarantines later Browser mutations after unverified delivery and removes hidden
  workspace rollback mutations.

Therefore a native host may consume only an operation already admitted by the capability
adapter/Core path. authorization_ref and native_operation_ref are correlation evidence only;
the host cannot issue, refresh, widen or reinterpret authority.

No public Chat tool is added. The six-tool semantic surface remains unchanged.

## Architecture lineage comparison

| Role | Prior owner/source | Current evidence | Decision |
|---|---|---|---|
| General planning | ordinary ChatGPT | Native process ownership does not require a second planner | KEEP |
| Capability authorization | CAP Core | #166-#175 now enforce exact grants across consequence-bearing paths | KEEP |
| WorkingState / reconciliation | CAP Core | Core already owns ambiguous outcome and permission for a later attempt | KEEP |
| Verification / Finish Gate | project Kernel / Finish Gate | native receipt is evidence, not project PASS/DONE | KEEP |
| Native systems execution | no accepted production owner; historical Rust-first branch is reference only | Job/process-tree ownership remains a distinct low-level role | REFINE into the selected narrow Native Host row |
| External implementation reference | openai/codex; aaif-goose/goose | current source still exposes relevant lifecycle mechanics but not CAP authority | KEEP as REFERENCE_ONLY / ADAPT_MECHANIC |

No role required by the selected first slice remains DEFER.

## Architecture primitives and adjacent engineering domains

| Primitive | Engineering domain | Required guarantee | Boundary |
|---|---|---|---|
| one short-lived host per operation | OS process supervision | one native owner/crash domain for one attempt | no daemon/session service |
| u32 length-framed UTF-8 JSON over anonymous stdio | local IPC/protocol framing | bounded unambiguous message boundaries | transport ACK is not effect success |
| one-active-operation state machine | concurrency control | a second Begin cannot create another target | memory-only, no durable host ledger |
| Windows Job Object + KILL_ON_JOB_CLOSE | Windows process containment | owned descendants terminate with host/job owner loss | not a sandbox |
| CREATE_SUSPENDED then assign then resume | process creation ordering | target cannot run before containment | assignment failure is fail-closed |
| native Job/process handles | OS object identity | lifecycle ownership is not PID-only | PID remains receipt data |
| explicit inherited-handle allowlist | capability/handle hygiene | child receives only intended handles | protocol/job handles never leak by default |
| bounded stdout/stderr | backpressure/resource accounting | output is complete within budget or operation fails explicitly | no silent lossy queue |
| exact toolchain/binary provenance | software supply chain | qualification binds reviewed bytes | no floating stable evidence |

Adjacent PTY/ConPTY and sandbox policy are explicitly outside this slice.

## Problem evidence

The project needs a replaceable native executor that can own process trees below deterministic
Core authority. Higher-level process wrappers do not by themselves prove whole-tree owner
death, exact native handle identity, inheritance hygiene or assignment-before-run ordering.

Recent public Windows failure reports in openai/codex continue to show orphan descendants and
root-only cancellation races when particular execution paths are outside effective Job/tree
containment, including issues #21994, #35726 and #45172. These reports are failure evidence,
not proof that CAP should copy Codex architecture.

Microsoft documents Job Objects as the Windows unit for managing process groups and confirms
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE terminates associated processes when the final job handle
closes. Microsoft also documents PROC_THREAD_ATTRIBUTE_HANDLE_LIST for restricting the handles
inherited by a child process.

Rust 1.98.1 remains the current stable release on 2026-09-24 and fixes a vtable
miscompilation in 1.98.0. Release qualification must therefore pin an exact patch toolchain,
not mutable stable.

## Solution evidence

The selected mechanism matches the exact required guarantee:

1. create/configure the Job before target execution;
2. create the target suspended;
3. assign the target to the Job while still non-runnable;
4. if assignment fails, terminate the suspended child and report failure;
5. resume only after successful assignment;
6. retain the Job handle until the owned tree is complete or explicitly cancelled;
7. owner/protocol loss closes/terminates the Job rather than leaving descendants unmanaged.

This ordering removes the pre-assignment execution window. A private one-operation stdio host
avoids daemon endpoint authentication, reconnect/multiplexing and host-side durable state.
Core remains the sole durable owner of UNKNOWN/reconciliation, so a lost terminal receipt
cannot authorize blind replay.

## Best current approaches

### A. Higher-level process wrapper only

Use std::process/tokio::process and kill the root Child.

Strengths: simple and portable.

Failure: root-process ownership does not prove descendant-tree cleanup or exact Windows Job
containment. Rejected for this first Windows lifecycle guarantee.

### B. Persistent native daemon/service

Use named pipe/HTTP/RPC plus a long-lived Rust service owning many operations.

Strengths: amortized startup and future multiplexing.

Failure: adds endpoint ACL/auth, reconnect/version skew, multi-client concurrency, durable
service lifecycle and pressure for host-side scheduling/state. Rejected for v1.

### C. Short-lived one-operation Rust host over anonymous framed stdio

Strengths: one owner, one attempt, no discoverable endpoint, small provenance surface, natural
Job/native-handle lifecycle, no durable host state.

Selected: NARROW.

## Failure lessons

- Assignment after a child is already running leaves a race window; use suspended creation.
- A compatibility fallback that resumes an uncontained child weakens the guarantee; CAP must
  fail closed instead.
- PID-only ownership is vulnerable to reuse and does not retain object authority; keep native
  handles.
- Broad inheritable handles can leak protocol/job/file capabilities; use an explicit allowlist.
- Root exit is not tree completion; retain the Job and account for active descendants.
- A lost host receipt after resume is ambiguous; Core records/reconciles UNKNOWN and does not
  blindly retry.
- Silent output dropping corrupts execution evidence; budget overflow must be explicit failure.
- Job containment and detached daemon behavior conflict; detached/background service semantics
  are outside v1.

## Failure / crash matrix

| Boundary | Possible physical state | Required behavior | Retry authority |
|---|---|---|---|
| before valid Begin | no target | reject/exit with no spawn | caller may create a fresh authorized attempt |
| Begin accepted, before Job creation | no target | fail with no spawn | fresh attempt allowed by Core |
| Job created, before target creation | no target | close Job and fail | fresh attempt allowed by Core |
| target created suspended, before assignment | target exists but has not run | terminate suspended target; never resume | fresh attempt allowed only after Core records no applied effect |
| assignment failed | target suspended/uncontained | terminate; fail closed; no fallback resume | no effect should have run |
| assigned, before resume | target contained/suspended | host crash closes Job and kills it | no runnable effect expected |
| resume succeeded, before process_spawned receipt | effect may have begun | host/job cleanup; parent treats outcome as ambiguous | no blind replay; Core reconciliation required |
| running/output | effect may be partial | enforce runtime/output budgets; cancel whole Job on fatal protocol/output failure | Core decides after fresh evidence |
| root exited, descendants active | descendants still part of owned effect | keep Job until tree completion/cancel | no new attempt while unresolved |
| cancellation race | effect may be partial | TerminateJobObject/close semantics; terminal receipt best effort | lost receipt => UNKNOWN |
| parent protocol EOF / host owner loss | effect may be partial | terminate active Job/tree and exit | Core reconciliation required |
| host restart | no durable host state | never auto-replay previous operation | only Core may authorize a new attempt |
| terminal receipt emitted but parent dies before durable Core record | effect may be complete | host exits normally; Core observes unknown durable outcome | fresh observation/reconciliation before later effect |

No release-critical matrix cell depends on host-side replay or a durable host ledger.

## Source-code evidence

### openai/codex

Exact ref inspected:
53446f90a56692dede3c8f413e8d486a6adb77b5 (2026-09-24).

Paths inspected:

- codex-rs/core/src/spawn.rs
- codex-rs/utils/pty/src/win/job.rs
- codex-rs/utils/pty/src/win/mod.rs
- codex-rs/utils/pty/src/win/conpty.rs
- codex-rs/utils/pty/src/win/psuedocon_tests.rs

Classification: OPEN_IMPLEMENTED for the inspected Windows Job/process-tree and ConPTY lifecycle
paths.

The current JobObject implementation exposes KILL_ON_JOB_CLOSE, a no-breakaway constructor,
suspended preparation and spawn_contained assignment-before-resume. It also contains a separate
assign_and_resume_process compatibility path that may resume after assignment failure; CAP
explicitly rejects that fallback for consequence-bearing Native Host v1.

Current tests directly exercise output closure, surviving descendants after root exit and
termination behavior in the ConPTY path.

Lesson: ADAPT_MECHANIC / REFERENCE_ONLY. Do not import Codex planner/session/tool authority.

### aaif-goose/goose

Exact ref inspected:
80c1197583cc9dc909b7e010c78b4ad58c81e8ce (2026-09-24).

Paths inspected:

- crates/goose/src/subprocess.rs
- crates/goose/tests/subprocess_cleanup.rs

Classification: OPEN_IMPLEMENTED for the inspected Linux parent-death path.

Goose sets PR_SET_PDEATHSIG with a parent identity recheck and tests both true parent-process
death and the distinct case where the spawning thread exits but the owner process remains.

Lesson: ADAPT_MECHANIC / REFERENCE_ONLY. The transferable lesson is to test real owner death,
not merely explicit Child::kill.

Important difference: this is Linux evidence; it does not replace Windows Job Object evidence.

## Fit to CAP architecture

Native Host sits strictly below capability-specific adapters:

~~~
ordinary ChatGPT
 -> semantic capability
 -> CAP Core authorization / WorkingState / verification
 -> capability-specific adapter
 -> Native Host v1
 -> Windows
~~~

The host consumes an already-authorized bounded operation. Its receipt cannot become grant,
Verification Kernel PASS or Finish Gate DONE.

The #172 provider seams make this separation cleaner. The #173 exact Windows grant path means
the host never needs to interpret policy. #174 and #175 add no requirement for a host-side
rollback, grant store, browser state or recovery ledger.

## Architecture decision

Decision: **NARROW**

Implement now:

- Rust 1.98.1 pinned exactly for this stage;
- one Windows-first binary;
- one-operation lifetime;
- private u32-be length-framed UTF-8 JSON protocol;
- strict bounded message/field validation;
- one BeginOperation plus optional matching CancelOperation;
- Job Object with KILL_ON_JOB_CLOSE and no breakaway fallback;
- suspended create -> assign -> resume;
- native process/job handle ownership;
- exact inherited-handle allowlist;
- bounded stdout/stderr event stream;
- runtime/output budget enforcement;
- owner EOF cleanup;
- deterministic terminal result classification;
- no public semantic-tool changes.

Explicitly defer:

- ConPTY/interactive input/resize;
- graceful Ctrl-C policy;
- AppContainer/restricted-token sandboxing;
- persistent daemon/service;
- cross-platform parity;
- host-side durable state/queue;
- generic local execution or public shell capability.

Explicitly reject for v1:

- reviving chat/rust-relay-server as the Control Plane;
- TCP/HTTP/named-pipe daemon;
- uncontained resume fallback;
- host-issued or host-refreshed grants;
- blind retry after lost acknowledgement.

## Protocol bounds carried forward

First-slice hard ceilings:

- protocol frame: 262,144 encoded bytes;
- identifier fields: 128 ASCII characters;
- argv count: 256;
- one argv item: 8,192 UTF-8 bytes;
- env entries: 256;
- env name: 128 characters;
- one env value: 8,192 UTF-8 bytes;
- total serialized env values: 65,536 UTF-8 bytes;
- raw output chunk: 32,768 bytes;
- max output budget: 8,388,608 raw bytes combined;
- runtime budget: 1..3,600,000 ms.

The adapter may authorize less. The host cannot widen these ceilings.

## Verification plan

L1 / deterministic:

- frame boundary/size/UTF-8/message validation;
- second Begin rejected before spawn;
- mismatched Cancel rejected;
- command/argv/env/runtime/output bounds;
- event_seq monotonicity;
- protocol stdout contains no diagnostic text.

L2 / Windows hosted:

- create suspended -> assign -> resume ordering;
- assignment failure causes zero runnable target behavior;
- descendant remains owned after root exit;
- hard cancel removes the whole tree;
- parent EOF kills an active tree;
- output budget overflow terminates explicitly;
- timeout terminates explicitly;
- exact inherited-handle allowlist;
- repeated fault injection around every crash-matrix boundary.

Assurance:

- exact Rust 1.98.1 toolchain;
- committed Cargo.lock once dependencies exist;
- hosted CI/security on exact PR head;
- fresh ordinary-ChatGPT independent semantic review on exact BASE..HEAD.

Physical:

- target-Windows owner-death/process-tree qualification on the exact reviewed Native Host head
  before acceptance/merge of the release-critical implementation.

## Complexity budget

New:

- one Rust crate/binary;
- one private protocol module;
- one Windows lifecycle module;
- focused tests and one CI job family;
- this Stage Research owner document.

Not added:

- service manager;
- daemon discovery/auth;
- database/WAL;
- scheduler/event bus;
- plugin registry;
- second policy engine;
- public tool;
- PTY subsystem;
- sandbox framework.

The design remains intentionally smaller than the historical Rust-first CAP architecture while
adding the one low-level role the frozen Core does not own.

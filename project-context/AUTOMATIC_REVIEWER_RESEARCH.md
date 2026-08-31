# Automatic Independent Reviewer — Stage Research Brief

Status: **STAGE RESEARCH — NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)**

Research date: 2026-08-31

`NARROW` limits implementation scope; it does **not** reduce the research depth required by accepted `stage-research` v1.2 or `source-code-research` v1.0. Production implementation remains blocked until this research PR passes exact-head CI, mandatory fresh ordinary-Chat review and merge. Only after acceptance does the decision become implementation authority.

Research baseline:

```text
main = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
Stage 26.3C process-crash/restart scope = accepted / closed
PR #138 = experiment-only launch evidence
public Chat-facing surface = six canonical semantic tools
mandatory primary semantic reviewer = fresh ordinary ChatGPT
```

## Stage goal

Remove routine user launch/paste/result-copy work from the already-required independent review gate without weakening exact-head review, falsification, reviewer independence, result integrity, or the project-owned consequence boundaries.

Bounded target lifecycle:

```text
review-ready exact PR identity
 -> registered launch_independent_review_v1 behind procedure_run
 -> crash-safe exact-operation record + private review_run_id
 -> one bounded browser launch
 -> one atomic browser-side Send claim
 -> fresh ordinary-Chat reviewer
 -> REVIEW_RESULT_V1
 -> one top-level PR result-evidence comment
 -> development-side full-comment-set + live-ref validation
 -> manual fallback on ambiguous/failed automatic execution
```

Non-goals remain explicit: no recurring/general scheduler, no arbitrary GitHub watcher, no `WAITING -> wake -> planner continuation`, no automatic wake/resampling of the unfinished development conversation, no worker rotation or multi-agent runtime, no seventh public tool/shell, no arbitrary URL/prompt/command launcher, no Native Messaging result bus, no automatic retry after ambiguous external effect, no reviewer merge/approval authority, no Harbor production authority, and no general browser database/storage dispatcher or general browser database runtime.

## Current project baseline

### Existing public/procedure authority

The accepted public Chat-facing surface remains exactly six canonical tools. `procedure_run` already admits only registered bounded procedures through the semantic projection and Control Plane. The automatic reviewer therefore adds only a future fixed `launch_independent_review_v1` procedure behind this existing boundary; it does not create a seventh tool or a generic launcher.

### Accepted Stage 26.3C cooperating-runner lock

Accepted BASE `runtime/control_plane/_verified_workspace_artifact_support.py` contains `_TaskLock` and `_acquire_task_lock`, using an OS-backed nonblocking exclusive lock: `msvcrt.locking(..., LK_NBLCK, ...)` on Windows and `flock(..., LOCK_EX | LOCK_NB)` on POSIX. Process death releases live lock ownership.

Required automatic-review reuse:

```text
canonical review identity
 -> derive review_operation_key / bounded lock id
 -> acquire existing project OS-backed exclusive lock
 -> no unlocked fallback
 -> only holder may load/create/transition durable operation state
 -> hold through durable dispatch-attempted transition and one launch decision
 -> release after bounded launcher returns
```

### Accepted Stage 26.3C crash-atomic checkpoint persistence

The OS lock is **not** the persistence primitive. The same accepted BASE implementation contains `_write_checkpoint`, `_load_checkpoint` and `_validate_resume_state`. Its checkpoint pattern is:

```text
same-directory sibling temp
 -> serialize complete versioned JSON candidate
 -> write
 -> flush
 -> os.fsync
 -> os.replace(temp, canonical)
 -> strict canonical load + semantic validation
```

`tests/test_stage26_3c_workspace_hard_crash.py` exercises process death around physical effects and committed transition state. `tests/test_stage26_3c_checkpoint_progress_validation.py` and `tests/test_stage26_3c_checkpoint_identity_validation.py` prove that inconsistent retained state is rejected before consequence-bearing continuation.

The automatic reviewer therefore **REUSE_MORE** of two separate accepted mechanisms: the OS lock for cooperating-writer ownership and the checkpoint write/load/validation pattern for process-crash durable state. No machine/power-loss transactional guarantee is added.

### PR #138 launch evidence

PR #138 physically demonstrated a narrow run-bound ChatGPT deep-link/autosend path and one bounded Send. Its page/session state did not prove durable operation ownership, crash-safe local state, cross-tab Send serialization, structured result handoff or general scheduler authority. It is therefore a launch/UI mechanic source only.

## Architecture lineage comparison

| Role | Prior / candidate | Decision | Reason |
|---|---|---|---|
| primary semantic reviewer | fresh ordinary ChatGPT | **KEEP** | mandatory accepted reviewer remains unchanged |
| review protocol | project `code-review` skill | **KEEP / REFINE** | exact refs/falsification remain; proposed v1.1 adds only bounded result publication |
| bounded launch consequence | registered `procedure_run` | **REUSE_MORE / NARROW** | no seventh public tool or arbitrary launcher |
| local concurrent operation ownership | Stage 26.3C OS-backed lock | **REUSE_MORE** | closes cooperating first-creator/writer race |
| durable local operation record | Stage 26.3C atomic checkpoint pattern | **REUSE_MORE** | closes process-crash write/load ambiguity without a new persistence framework |
| deep-link/composer mechanics | PR #138 | **REFINE** | retain proved UI mechanics, replace page-local ownership |
| Browser-side cross-tab Send ownership | MV3 extension service worker + extension-origin IndexedDB | **SELECT / NARROW** | transactional unique-key claim closes same-run tab race |
| result handoff | GitHub top-level PR Conversation comment | **REFINE / SELECT** | existing durable review channel; evidence is independently revalidated |
| development continuation | current user-driven development chat | **KEEP MANUAL / DEFER automatic wake** | avoids hidden same-task-continuation runtime |
| evaluation harness | Harbor | **REUSE_MORE / EVALUATION ONLY** | avoids building benchmark runner; no production authority |
| optional second reviewer | Codex Review | **KEEP OPTIONAL** | additional signal only |
| generic scheduler/event bus/multi-worker runtime | future concepts | **REJECT for this slice** | unnecessary authority expansion |

## Architecture primitives and adjacent domains

The selected design deliberately separates four release-critical primitives:

1. **Live local ownership** — process-held OS lock. Domain: local concurrency control. It prevents cooperating concurrent writers but does not make durable writes atomic.
2. **Durable local state** — complete checkpoint replacement + strict load validation. Domain: filesystem crash consistency/checkpointing. It protects process-restart state but does not own browser tabs.
3. **Browser Send ownership** — one MV3 extension service worker + IndexedDB unique-key transaction. Domain: browser transaction/concurrency control. It prevents same-run multi-tab Send duplication.
4. **Remote review evidence** — GitHub result comment + exact identity/author/edit/digest/full-set validation. Domain: mutable remote evidence / TOCTOU integrity. It transports evidence but never self-authorizes merge.

Adjacent domains explicitly researched: filesystem replacement semantics, SQLite transactional state, append-only journal/WAL recovery, MV3 service-worker lifecycle, IndexedDB transaction serialization, Web Locks, browser KV persistence, Native Messaging/local callback transport, idempotency/correlation, mutable GitHub evidence and ambiguous external effects.

## Problem evidence

The accepted manual process works but requires repeated human handoff:

```text
development chat freezes exact refs
 -> user opens fresh ordinary ChatGPT
 -> user pastes REVIEW_REQUEST_V1
 -> reviewer independently reconstructs evidence
 -> user copies REVIEW_RESULT_V1 back
 -> development chat validates result + live identity
```

The project has already observed or independently reviewed the concrete hazards relevant to automation:

- material head changes make earlier reviews stale;
- Stage 26.3C established that concurrent cooperating ownership needs an explicit OS lock;
- a fresh review of #140 rejected `chrome.storage.local` check/set as a non-atomic cross-tab claim;
- a later fresh review correctly separated OS serialization from crash-atomic operation-record persistence;
- result comments are mutable/duplicable evidence and therefore need a final complete-set rescan;
- OpenHands independently documents replayed child-launch ActionEvents as a duplicate/billable side-effect hazard.

These are release-relevant failure modes, not speculative optimization targets.

## Solution evidence

### Local operation record

The selected local state mechanism reuses the accepted Stage 26.3C checkpoint pattern under the accepted OS lock.

The durable record contains at minimum:

```text
schema_version
review_operation_key
repository
pr_number
base_sha
head_sha
review_skill
review_skill_version
review_run_id
dispatch_state = prepared | dispatch-attempted
created_at
dispatch_attempted_at | null
```

Required ordering:

```text
derive exact operation identity
 -> acquire OS-backed exclusive operation lock
 -> reconcile retained canonical/temp state
 -> strict load OR proven first creation
 -> generate review_run_id exactly once only for first creation
 -> atomically persist canonical prepared record
 -> atomically persist canonical dispatch-attempted record
 -> only after successful replacement invoke one OS/browser launch consequence
 -> release operation lock after bounded launcher returns
```

The exact checkpoint replacement is sibling-temp -> complete JSON -> `flush` -> `os.fsync` -> `os.replace`. The accepted destination is never an in-place partially updated record.

Fail-closed load/recovery rules:

- existing canonical record with invalid JSON, unsupported schema, wrong exact review identity, inconsistent operation key or invalid/missing stable nonce -> reject and **never recreate/reset it automatically**;
- canonical absent and a matching sibling temp residue exists -> `operation_persistence_ambiguous`; fail closed/manual recovery rather than treating it as first creation;
- canonical valid and sibling temp residue exists -> canonical is authoritative; temp is never consumed as state;
- write, flush, `os.fsync` or `os.replace` failure -> **no external browser launch**;
- canonical disappearance after a previously known/created operation -> `operation_persistence_ambiguous`, zero automatic launch and no replacement nonce;
- canonical destination mutation/disappearance while the operation lock is held -> fail closed;
- a new first record may be created only when canonical state and ambiguous retained operation artifacts are both absent.

`dispatch-attempted` must be successfully replaced into canonical state **before** invoking the OS/browser launch consequence. A crash before that replace leaves the prior valid `prepared` canonical state and no external launch has yet been invoked by ordering. A crash after successful replace leaves valid `dispatch-attempted`, which forbids an automatic relaunch.

### Browser-side cross-tab Send ownership

A content script never self-authorizes Send. The selected owner is one **MV3 extension service worker** and one **extension-origin IndexedDB** object store `review_send_claims`.

```text
validated ChatGPT root/new-chat route
 -> content script sends claim-review-send-v1(review_run_id)
 -> service worker validates sender/origin/message
 -> open pre-initialized exact-version IndexedDB
 -> one readwrite transaction
 -> add primary-key record review_run_id
 -> wait for transaction completion
 -> only the caller whose add transaction committed receives claim_status=granted
 -> winning content script revalidates route/composer/button
 -> one Send click
```

Never treat `chrome.storage.local` `get()` / `set()` as an atomic Send-claim primitive; **it is not Send ownership**.

The claim path **must not lazily create or upgrade the database schema**. Missing marker/store, missing object store, unexpected version, `onupgradeneeded`, transaction abort/error, service-worker failure, malformed response or ambiguous response all fail closed with **no automatic Send**.

If **two tabs request the same run claim concurrently**, overlapping IndexedDB readwrite transactions serialize; **exactly one `add(review_run_id)` can commit** and **only that caller gets grant**. The budget is **0 extra Sends**.

If the **service worker / claim transaction fails or aborts before commit**, no grant exists. If the **claim commits but response is lost or winning tab dies before click**, the **durable claim remains** and blocks a second automatic grant; use **manual fallback**. The content script **does not automatically retry an ambiguous claim response**.

### Result handoff

The automatic reviewer gets one narrow write exception: one top-level PR Conversation comment carrying its own `REVIEW_RESULT_V1 + review_run_id`. It may not edit branch/files, approve/request changes, label, merge, close/reopen or change settings.

Initial consumption queries the complete top-level PR comment collection and requires exact nonce, configured result principal, unedited body, exact repository/PR/BASE/HEAD/policy/context identity and valid structured result.

Final gate queries the **complete collection again**, requires `matching-comment count == 1`, same accepted id/author/body digest/metadata, and then **re-fetches that sole exact comment**. A **late duplicate**, edit, deletion or author mismatch invalidates automatic result evidence.

## Best current approaches

The strongest current fit is a composition of narrow primitives rather than an imported general framework:

- local single writer: accepted Stage 26.3C OS lock;
- durable operation record: accepted Stage 26.3C sibling-temp/flush/fsync/replace + strict load-validation pattern;
- browser Send claim: MV3 service worker + IndexedDB unique `add(review_run_id)` transaction;
- result transport: GitHub PR Conversation comment + full-set integrity rescan;
- semantic reviewer: fresh ordinary ChatGPT under project `code-review` policy;
- evaluation: Harbor only after the first honest production-like E2E.

This preserves the existing six-tool/Control Plane boundary and introduces no generic scheduler, callback bus or local database framework.

## Failure lessons

- **Lock != crash-atomic persistence.** Serializing writers cannot make an in-place JSON transition recoverable.
- **Durable KV != atomic claim.** `chrome.storage.local` persistence does not provide transactional compare-and-claim semantics.
- **Service-worker memory != durable ownership.** MV3 workers may terminate; globals cannot own the Send claim.
- **Committed effect + lost response is ambiguity.** A committed browser claim, clicked Send or created comment is never blindly repeated because its acknowledgement was lost.
- **Checkpoint replacement is scoped.** sibling temp + flush/fsync + replace is reused only for the accepted process-crash/restart model, not promoted to power-loss durability.
- **OpenHands availability-first behavior is wrong for this gate.** Its inspected launch ledger may proceed when local claim state is corrupt/unavailable; CAP must fail closed instead.
- **Mutable remote evidence must be revalidated.** A once-valid result comment can later be edited, deleted or duplicated.
- **General persistence frameworks create obligations.** SQLite WAL/journal lifecycle or a custom append-only log would add schema/recovery/compaction state beyond the current one-record need.

## Alternatives comparison

### Local durable operation state

| Alternative | State/crash model | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|
| accepted Stage 26.3C lock + atomic file checkpoint | one versioned file; sibling-temp/flush/fsync/replace; process-restart scope | already project-qualified and minimal | no multi-record transactions; no power-loss claim | **SELECT / REUSE_MORE** |
| **SQLite transaction** / optional WAL | DB transaction/journal recovery | mature ACID, UNIQUE operation key possible | new DB/schema/migrations/journal/WAL/checkpoint owner | **REJECT for v1; reconsider if state becomes relational/multi-record** |
| **append-only journal/WAL** | replay from immutable events | rich audit/replay history | framing, checksums, torn-tail detection, replay, compaction, schema evolution | **REJECT for v1** |
| **raw/in-place JSON write** | overwrite live record | simplest code | torn/partial durable state possible on process death | **REJECT** |

### Browser Send ownership

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| service worker + IndexedDB transaction | durable same-origin transactional unique claim | bounded schema/transaction lifecycle needed | **SELECT / NARROW** |
| **Web Locks** + durable ledger | good live origin-scoped exclusion | lock is ephemeral and still needs a second durable store | **REJECT for v1** |
| **service-worker in-memory Set** + `chrome.storage.local` | easy | worker lifetime ephemeral; KV check/set non-atomic | **REJECT** |
| **Native Messaging** / local dispatcher | could centralize browser ownership | privileged host/transport/deployment authority expansion | **REJECT for this slice** |

### Result handoff

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| GitHub PR comment + nonce/full rescan | existing durable review channel | mutable evidence requires strict revalidation | **SELECT / REFINE** |
| **local callback/result server** | direct transport | new ingress/auth/state owner | **REJECT for v1** |
| **user copy/paste** | already accepted manual route | human friction remains | **KEEP as fallback** |

Three materially distinct approaches are therefore compared for each new persistence/transport role; no fewer-than-three exception is used.

## Source-code evidence

### Chat Agent Platform accepted Stage 26.3C

```text
repository = BogdanAIP/chat-agent-platform
exact ref = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
research date = 2026-08-31
classification = OPEN_IMPLEMENTED (project accepted implementation)
lesson = ADAPT_MECHANIC / REUSE_MORE within project lineage
```

Inspected symbols/files:

- `runtime/control_plane/_verified_workspace_artifact_support.py`: `_TaskLock`, `_acquire_task_lock`, `_write_checkpoint`, `_load_checkpoint`, `_validate_resume_state`;
- `tests/test_stage26_3c_workspace_hard_crash.py`;
- `tests/test_stage26_3c_checkpoint_progress_validation.py`;
- `tests/test_stage26_3c_checkpoint_identity_validation.py`.

Execution path followed: stable task identity -> OS lock -> strict checkpoint load/validation -> sibling-temp full write -> flush/fsync -> `os.replace` -> consequence/reconciliation from canonical state. The hard-crash tests verify process-death recovery without duplicate consequence; validation tests reject inconsistent retained progress/identity before physical continuation.

Mapping: reuse the lock and atomic checkpoint mechanic for the review operation record, but do not import file-artifact-specific WorkingState/effect authority into reviewer launch.

### Harbor

```text
repository = harbor-framework/harbor
exact ref = 389bd4f8ce796ef4a97de4b62675021e262c8e76
research date = 2026-08-31
classification = OPEN_IMPLEMENTED for custom-agent / SingleStepTrial evaluation lifecycle
production fresh-Chat launch = NOT_FOUND_AFTER_TARGETED_SEARCH
lesson = REUSE_COMPONENT for evaluation only
```

Inspected:

- `src/harbor/agents/base.py`: `BaseAgent.run`, capabilities, session/context identity;
- `src/harbor/trial/single_step.py`: `_run`, `_run_agent`, `_recover_outputs`, verifier/error paths;
- `tests/unit/test_single_step_trial.py`: artifact collection idempotence, recovery collection, success/error output cleanup.

Execution path: task/trial -> one agent run -> output sync/artifact collection -> verifier -> result. This proves Harbor can host a thin CAP evaluation adapter while remaining outside production launch/authorization. The exact CAP fresh ordinary-Chat/GitHub result lifecycle was **NOT_FOUND_AFTER_TARGETED_SEARCH**, which is not a claim of global nonexistence.

Blind reuse is unsafe because Harbor owns an evaluation trial/environment, while CAP must preserve its own exact-ref, fresh-context and repository authority contract.

### openai/codex

```text
repository = openai/codex
exact ref = 94cbbddafc1776d5e377bca1b05932c697e82238
research date = 2026-08-31
thread/session lifecycle classification = OPEN_IMPLEMENTED
exact fresh ordinary-Chat reviewer wake path = NOT_FOUND_AFTER_TARGETED_SEARCH / OPEN_PARTIAL for adjacent lifecycle
lesson = REFERENCE_ONLY
```

Inspected:

- `codex-rs/core/src/thread_manager.rs`: `ThreadManager`, `StartThreadOptions`, thread store, reserved IDs, start/resume/fork paths;
- `codex-rs/core/src/thread_manager_tests.rs`: reserved ID rules, distinct root/child/fork identities and resume preserving stored thread ID.

Execution path: allocate/reserve thread identity -> start/store -> child/fork or resume from persisted rollout -> resume retains original identity. Tests explicitly ensure resume does not allocate a replacement identity.

Mapping: stable lifecycle identity is a useful reference. A complete public mechanism matching `fresh ordinary ChatGPT -> CAP GitHub evidence -> bounded result comment` was **NOT_FOUND_AFTER_TARGETED_SEARCH**, so Codex remains `REFERENCE_ONLY` and optional review evidence.

### OpenHands

```text
repository = OpenHands/OpenHands
exact ref = 1098d73df42351a31b2940557efb9fe8750365c4
research date = 2026-08-31
classification = OPEN_IMPLEMENTED
claim-before-effect lesson = ADAPT_MECHANIC
corrupt/unavailable-ledger fail-open lesson = REJECT_MECHANIC
```

Inspected:

- `src/services/child-conversation-launch.ts`: `claimToolCall`, local/cloud child launch and bounded readiness polling;
- `__tests__/services/child-conversation-launch.test.ts`: `ignores a replayed tool call`, no unnecessary retry, worktree fallback/error cases.

Execution path: validate action -> `claimToolCall(parentConversationId, toolCallId)` before network launch -> create child -> report result. Code comments explicitly identify socket reconnect / REST-WebSocket replay as a duplicate/billable-launch hazard, and the `ignores a replayed tool call` test calls the same tool-call id twice and asserts one creation.

Negative evidence: when its localStorage ledger is corrupt/unavailable, the inspected code can proceed and explicitly accepts replay risk. CAP adopts claim-before-effect as `ADAPT_MECHANIC` but classifies that availability-first behavior as `REJECT_MECHANIC`; mandatory review launch must fail closed.

## Failure/Crash Matrix

| Boundary / failure | Authoritative state / rule | Max unauthorized additional effect |
|---|---|---:|
| malformed/exact identity missing | reject before any state or launch | 0 |
| two concurrent same-operation callers before record exists | exactly one acquires OS lock; loser does no record/nonce/launch work | 0 extra launches |
| process dies while holding lock before record creation | OS releases lock; next caller must re-evaluate retained state | 0 |
| crash during first temp write | canonical absent + matching temp residue => `operation_persistence_ambiguous` | 0 launches |
| create/write/flush/fsync/replace fails | no canonical transition completion | 0 launches |
| canonical corrupt/unsupported/mismatched | never recreate/reset; manual recovery | 0 launches |
| canonical disappearance after known creation | `operation_persistence_ambiguous`, no replacement nonce | 0 launches |
| valid canonical + temp residue | canonical only is authoritative; temp never consumed as state | 0 duplicate launches |
| crash after durable record/nonce creation but before dispatch-attempted | valid `prepared`; same nonce may advance after locked validation | <=1 total launch |
| crash/persistence failure while replacing dispatch-attempted checkpoint | launch is impossible until replacement call succeeds | <=1 total launch |
| dispatch-attempted durable then crash before/during browser open | marker forbids automatic relaunch | 0 extra launches |
| existing `/c/...` route | refuse Send | 0 Sends |
| claim schema/marker/store missing or unexpected version | fail closed; no claim-time creation/upgrade | 0 Sends |
| service worker / claim transaction fails or aborts before commit | no grant | 0 Sends |
| two tabs request the same run claim concurrently | overlapping IndexedDB readwrite transactions serialize; exactly one `add(review_run_id)` can commit; only that caller gets grant | **0 extra Sends** |
| claim commits but response is lost or winning tab dies before click | durable claim remains; manual fallback; no re-grant | 0 extra Sends |
| Send click/transport becomes ambiguous | no automatic redelivery | 0 extra Sends |
| reviewer timeout/no result | manual fresh-review fallback | 0 relaunches |
| result-comment creation ambiguous | reviewer does not retry | 0 extra comment attempts |
| malformed/wrong-author/edited/stale result | reject | 0 merge authority |
| valid result then late duplicate/edit/delete | final complete-set rescan/re-fetch rejects | 0 merge authority |
| live BASE/HEAD moves | old result stale; new exact-head review required | 0 stale merge authority |
| Harbor unavailable | production reviewer unaffected | 0 production effects |

No release-critical cell is left `unknown` within the declared process-crash/restart scope. Machine/power-loss durability and hostile non-cooperating state-directory mutation remain outside the claimed guarantee.

## Fit to this architecture

The selected composition preserves current authority layers instead of importing a new agent runtime:

```text
fresh ordinary ChatGPT reviewer       -> semantic judgment / findings
project code-review policy            -> exact review protocol + falsification
procedure_run                          -> bounded launch consequence
Stage 26.3C OS lock                   -> local live single-writer ownership
Stage 26.3C checkpoint pattern        -> local crash-safe operation state
MV3 service worker + IndexedDB        -> browser Send ownership only
GitHub PR comment                     -> mutable result transport evidence
development lifecycle                 -> result disposition + final live-ref/merge gate
Harbor                                -> evaluation only, not production
```

The local lock and checkpoint are project-owned reusable primitives already accepted for the same process-crash scope. IndexedDB is introduced only because browser tabs/service-worker execution form a different concurrency domain. GitHub comment transport reuses an existing remote surface and gains no acceptance authority by itself.

This architecture does **not** add a second planner, general scheduler/event bus, general browser database runtime, local callback service or broad native-host ingress.

## Reviewer evaluation method

Reviewer quality and automation reliability remain separate planes.

### Plane A — reviewer semantic quality

Measure benchmark-native precision/recall/F1/decision accuracy, false approve/reject behavior, revision resolution and signal/noise as applicable.

### Plane B — lifecycle reliability

Measure fresh-context success, exact-head binding, stale rejection, duplicate suppression, timeout/failure disposition, malformed/wrong-author/edited-result rejection, human interventions, wall time and cost where measurable.

**Do not collapse these planes into one score.**

First evaluation ladder after the honest production E2E:

```text
Harbor evaluation adapter -> ReviewBench baseline
 -> bounded SWE-Review-Bench subset
 -> CR-Bench / CR-Evaluator signal-to-noise control
 -> CAP Review Regression Set
```

Harbor is selected as evaluation infrastructure only, not production authority. Use a development set for iteration, fixed regression subsets for routine comparison and a holdout set / official evaluation for periodic validation. The first benchmark run is a **baseline, not a release exam**; do not invent an arbitrary quality target before measuring the manual/current control. Semantic quality must not materially regress merely because lifecycle friction improves.

## Acceptance checks

Before a later production implementation can be accepted, tests/qualification must prove:

1. fixed `launch_independent_review_v1` schema only; arbitrary URL/prompt/command rejected;
2. deterministic operation key + one durable high-entropy nonce;
3. OS lock acquired before any operation-record load/create/nonce generation and no unlocked fallback;
4. operation writes use sibling-temp + `flush` + `os.fsync` + `os.replace`;
5. strict schema/exact-identity/state validation on load;
6. invalid canonical state never silently resets/recreates;
7. canonical-absent + temp residue fails closed; valid canonical + temp residue never consumes temp as authority;
8. `dispatch-attempted` replacement succeeds before browser launch; persistence failure produces no launch;
9. hard-crash tests cover before/during/after checkpoint replacement and after dispatch marker;
10. MV3 service worker is sole Send-claim owner and claim-time DB upgrade/recreation is forbidden;
11. deterministic concurrency test proves one IndexedDB committed grant;
12. **two real same-run tabs released concurrently prove exactly one service-worker IndexedDB claim grant and exactly one Send click**;
13. committed-claim/lost-response and tab-death cases do not re-grant;
14. stale/malformed/wrong-author/edited/duplicate result comments reject;
15. final gate rescans all top-level comments and re-fetches the sole accepted result;
16. reviewer automatic authority is exactly one result comment and no other GitHub mutation;
17. six-tool public surface remains unchanged except registered procedure behind `procedure_run`;
18. no generic scheduler/event bus, general browser database/storage dispatcher, Native Messaging result bus or automatic developer wake is reachable;
19. mandatory fresh ordinary-Chat review + exact-head CI remain required;
20. target-Windows ordinary-Chat physical E2E proves zero routine launch/paste/result-copy intervention and all selected negative cases fail closed.

## Architecture decision

**NARROW — proposed by this Brief; effective only after this PR is accepted and merged.**

If accepted, implementation authority is limited to:

```text
exact frozen review identity
 -> registered bounded procedure_run launcher
 -> accepted Stage 26.3C OS-backed single-writer lock
 -> accepted Stage 26.3C crash-atomic checkpoint pattern + private review_run_id
 -> durable dispatch-attempted before one browser launch
 -> fresh-root ChatGPT deep-link/autosend
 -> MV3 service-worker IndexedDB unique-key Send claim
 -> exactly one automatic Send attempt
 -> fresh ordinary-Chat reviewer
 -> exactly one bounded PR result comment
 -> complete-comment-set + live exact-ref validation
 -> manual fallback after ambiguity
```

After the first real E2E, the thin Harbor/ReviewBench/SWE-Review-Bench/CR-Bench evaluation seam may be added without granting benchmark infrastructure production authority.

Any requirement for a recurring/general scheduler, automatic developer wake, new public tool, arbitrary launcher, new local persistence/lease framework, general browser database runtime, Native Messaging/local result bus, blind retry after ambiguity, broader reviewer mutation authority, machine/power-loss transactional guarantee, worker rotation or multi-agent runtime invalidates this decision and requires Stage Research re-entry.
# Automatic Independent Reviewer — Stage Research Brief

Status: **STAGE RESEARCH — NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)**

This Brief governs the first production slice of automatic independent semantic review after accepted Stage 26.3C. `NARROW` limits implementation scope; it does **not** reduce the research depth required by accepted `stage-research` v1.2 or `source-code-research` v1.0.

Research baseline:

```text
main = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
Stage 26.3C declared process-crash/restart scope = accepted / closed
PR #138 = experiment-only launch evidence
public Chat-facing surface = six canonical semantic tools
mandatory primary semantic reviewer = fresh ordinary ChatGPT
```

Production implementation remains blocked until this research PR passes exact-head CI, mandatory fresh ordinary-Chat review and merge. Only after acceptance does the final `NARROW` decision become implementation authority.

## Goal

Remove routine user launch/paste/result-copy work from the already-required independent review gate without weakening exact-head review, falsification, reviewer independence, result integrity, or the project-owned consequence boundaries.

Selected bounded lifecycle:

```text
review-ready exact PR identity
 -> registered launch_independent_review_v1 behind procedure_run
 -> one durable exact-operation record + private review_run_id
 -> one bounded browser launch
 -> one atomic browser-side Send claim
 -> fresh ordinary-Chat reviewer
 -> REVIEW_RESULT_V1
 -> one bounded top-level PR result comment
 -> development-side full-comment-set + live-ref validation
 -> manual fallback on ambiguous/failed automatic execution
```

## Non-goals

This Brief does **not** authorize:

- a recurring/general scheduler or arbitrary GitHub event watcher;
- general `WAITING -> wake -> planner continuation` semantics;
- automatic wake/resampling of the unfinished development conversation;
- worker rotation, multi-agent runtime or a second planner;
- arbitrary prompt/URL/command/backend launch;
- a seventh public tool, shell or general local execution capability;
- Native Messaging or a general local callback/result bus;
- automatic retry after ambiguous launch, claim, Send or result-comment creation;
- reviewer branch/file/approval/label/merge/settings mutation beyond the one result-evidence comment envelope;
- Harbor as production runtime authority;
- a general browser database/storage dispatcher;
- tuning the reviewer directly against the complete public benchmark corpus;
- benchmark score as security, acceptance or merge authority;
- a standalone reviewer product in this slice.

## Problem evidence

The accepted manual process works but has repeatable human friction:

```text
development chat freezes exact refs
 -> user opens a fresh ordinary ChatGPT conversation
 -> user pastes REVIEW_REQUEST_V1
 -> reviewer independently reconstructs evidence
 -> user copies REVIEW_RESULT_V1 back
 -> development chat validates result and live identity
```

PR #138 physically proved a narrower one-shot route:

```text
Windows launch
 -> run-id-bound ChatGPT deep link
 -> small content script validates URL/composer
 -> one bounded Send
```

That experiment did **not** prove durable operation ownership, crash-safe dispatch state, cross-tab Send serialization, structured result handoff, stale-result rejection or production reviewer authority.

Two fresh reviews of this research exposed distinct failure classes that must be incorporated before implementation authority can open:

1. a browser `chrome.storage.local` check/set is persistence, not an atomic cross-tab claim;
2. an OS process lock is concurrency ownership, not crash-atomic durable-record persistence.

Those lessons are now explicit design inputs rather than deferred implementation details.

## Solution evidence

The selected design is supported by four different evidence classes.

### Project evidence

Accepted Stage 26.3C already contains the two local primitives needed here:

- OS-backed nonblocking cooperating-runner serialization (`_TaskLock`);
- crash-oriented checkpoint persistence (`_write_checkpoint`, `_load_checkpoint`, `_checkpoint_matches_program`) using sibling temporary state, `flush`, `os.fsync`, `os.replace`, strict load/identity validation and fail-closed retained-state handling.

Reusing both avoids inventing a second local lock or persistence framework.

### Browser-platform evidence

Chrome MV3 provides a single extension service-worker coordination point and allows IndexedDB from extension service workers. IndexedDB `readwrite` transactions are atomic and overlapping write transactions on the same object-store scope serialize. A unique-key `add(review_run_id)` therefore provides the missing cross-tab claim property that asynchronous `chrome.storage.local` `get()`/`set()` does not.

Primary platform sources:

- https://developer.chrome.com/docs/extensions/develop/concepts/service-workers
- https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/basics
- https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies
- https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Basic_Terminology
- https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API/Using_IndexedDB
- https://www.w3.org/TR/IndexedDB/

### Durable-file evidence

Python `os.replace` provides replacement semantics suitable for the already accepted same-filesystem sibling-temp checkpoint pattern. This Brief does not upgrade that pattern into a machine/power-loss transactional guarantee; it only reuses the accepted process-crash/restart scope.

Primary source:

- https://docs.python.org/3/library/os.html#os.replace

### External lifecycle/evaluation evidence

Pinned source-code reads of Harbor, Codex and OpenHands show mature approaches to bounded trial lifecycle, conversation/session lifecycle, duplicate child-launch ownership and failure handling. They are evidence/reference sources, not production authority.

## Current implementation evidence

### Existing six-tool / procedure boundary

`project-context/STAGE26_3A_PROCEDURE_RUN_SURFACE.md`, `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs` and `runtime/control_plane/cli.py` establish one typed public `procedure_run` boundary whose schemas admit only registered procedures. The automatic reviewer therefore uses one fixed `launch_independent_review_v1`; it does not add a seventh public tool or arbitrary launcher.

### Accepted Stage 26.3C cooperating-runner lock

`runtime/control_plane/_verified_workspace_artifact_support.py` uses an OS-backed nonblocking exclusive lock (`msvcrt.locking(...LK_NBLCK...)` on Windows / `flock(...LOCK_EX | LOCK_NB...)` on POSIX). Process death releases live ownership; durable state remains the restart evidence.

Required automatic-review reuse:

```text
canonical review identity
 -> derive review_operation_key / bounded lock id
 -> acquire existing project OS-backed exclusive lock
 -> no unlocked fallback
 -> only holder may read/create/transition durable operation state
 -> hold through durable dispatch-attempted transition and one launch decision
 -> release after bounded launcher returns
```

### Accepted Stage 26.3C crash-atomic checkpoint persistence

The OS lock is **not** the persistence primitive. The automatic-review durable operation record must separately reuse the accepted checkpoint-write/load role:

```text
same-directory sibling temp
 -> serialize complete versioned JSON candidate
 -> flush
 -> os.fsync
 -> os.replace(temp, canonical)
 -> strict canonical reload/validation
```

The durable operation record contains at minimum exact repository/PR/BASE/HEAD/skill identity, schema/version, stable `review_operation_key`, once-generated high-entropy `review_run_id`, and state such as `prepared` or irreversible `dispatch-attempted`.

Load/reconciliation rules are fail closed:

- existing canonical record with invalid JSON, wrong schema/version, wrong exact review identity, inconsistent operation key or invalid/missing stable nonce -> reject; **never recreate/reset it automatically**;
- canonical absent and a matching sibling temp residue exists -> state is ambiguous; fail closed/manual recovery rather than treating it as first creation;
- canonical valid and sibling temp residue exists -> canonical is authoritative; temp is never consumed as state and may be removed/quarantined only under the operation lock after exact canonical validation;
- write, flush, `os.fsync` or `os.replace` failure -> no external browser launch;
- `dispatch-attempted` must be successfully replaced into canonical state **before** invoking the OS/browser launch consequence;
- crash before that replace leaves the prior canonical `prepared` record authoritative, so after locked validation the still-unused first launch may occur;
- crash after successful replace leaves canonical `dispatch-attempted`, which forbids an automatic relaunch;
- canonical disappearance after a previously known/created operation is ambiguity, not permission to manufacture a new nonce.

This is the declared accepted-style process-crash/restart guarantee only. No machine/power-loss transactional durability claim is made.

### PR #138 deep-link/autosend experiment and browser-side claim refinement

The experiment uses page/session state. Production browser Send ownership moves out of independent content scripts.

A content script never self-authorizes Send from `sessionStorage` or `chrome.storage.local`. Never treat `chrome.storage.local` `get()` / `set()` as an atomic Send-claim primitive; it is not Send ownership.

Selected browser-side claim:

```text
validated ChatGPT root/new-chat route + exact composer payload
 -> content script sends claim-review-send-v1(review_run_id)
 -> MV3 extension service worker validates sender/origin/message
 -> open pre-initialized extension-origin IndexedDB
 -> one readwrite transaction on review_send_claims
 -> add primary-key record review_run_id (not put/overwrite)
 -> wait for transaction complete
 -> only the caller whose add transaction committed receives claim_status=granted
 -> winning content script revalidates route/composer/button
 -> one Send click
```

The service-worker claim path must not lazily create or upgrade the database schema. Missing marker/store, unexpected version, `onupgradeneeded` during claim, transaction abort/error, worker failure, malformed response or ambiguous response all fail closed with **no automatic Send**. A committed claim is not automatically deleted because a tab later fails.

If two tabs request the same run claim concurrently, overlapping IndexedDB readwrite transactions serialize; exactly one `add(review_run_id)` can commit; only that caller gets grant. The loser gets no Send authority.

If the service worker / claim transaction fails or aborts before commit, no grant exists. If the claim commits but response is lost or winning tab dies before click, the durable claim remains and blocks a second automatic grant; manual fallback is used. The content script does not automatically retry an ambiguous claim response.

The extension claim store is one bounded review-Send ownership store, **not a general project database or scheduler/event bus**.

## Architecture lineage comparison

| Role | Prior / candidate | Decision | Reason |
|---|---|---|---|
| general semantic reviewer | fresh ordinary ChatGPT | **KEEP** | mandatory accepted independent reviewer remains unchanged |
| review protocol | project `code-review` skill | **KEEP / REFINE automatic envelope only** | exact refs/falsification remain; HEAD v1.1 adds only bounded result publication |
| bounded launch consequence | registered `procedure_run` | **REUSE_MORE / NARROW** | no seventh tool or arbitrary launcher |
| local concurrent operation ownership | Stage 26.3C OS-backed lock | **REUSE_MORE** | closes cooperating first-creator race |
| durable local operation record | Stage 26.3C checkpoint write/load pattern | **REUSE_MORE** | closes process-crash write/load ambiguity without new persistence framework |
| deep-link/composer mechanics | PR #138 experiment | **REFINE** | retain proved narrow browser mechanics, replace page-local ownership |
| Browser-side cross-tab Send ownership | MV3 extension service worker + extension-origin IndexedDB one-store `readwrite` transaction | **SELECT / NARROW** | unique `add(review_run_id)` is a transactional claim |
| result handoff | GitHub top-level PR Conversation comment | **REFINE / SELECT** | durable existing review channel; full-set integrity checks retain acceptance authority locally |
| development continuation | user-driven current development chat | **KEEP MANUAL / DEFER automatic wake** | prevents hidden same-task continuation runtime |
| evaluation harness | Harbor | **REUSE_MORE / EVALUATION ONLY** | avoids building benchmark runner; no production authority |
| optional second reviewer | Codex Review | **KEEP OPTIONAL** | additional signal only |
| generic scheduler/event bus/multi-worker runtime | future architecture | **REJECT for this slice** | unnecessary authority expansion |

## Architecture primitives and adjacent domains

The design separates four primitives that must not be conflated:

1. **Live local ownership** — process-held OS lock; solves cooperating concurrent writers, not persistence.
2. **Durable local state** — complete checkpoint replacement + strict load validation; solves process-crash record integrity, not browser-tab ownership.
3. **Browser Send ownership** — IndexedDB transaction claim in one extension service worker; solves same-run cross-tab Send race, not local launch ownership.
4. **Review-result evidence** — GitHub comment plus exact identity, author, edit, digest and full-set uniqueness validation; transports evidence but does not self-authorize merge.

Adjacent domains considered:

- filesystem checkpointing / atomic replacement;
- SQLite transactional state;
- append-only WAL/journal recovery;
- MV3 service-worker lifecycle;
- IndexedDB transaction serialization;
- Web Locks API;
- browser local/session/extension KV persistence;
- Native Messaging / local callback transport;
- mutable remote evidence integrity;
- idempotency and ambiguity after externally visible consequences.

## Source-code evidence

### Project Stage 26.3C — accepted implementation

```text
repository = BogdanAIP/chat-agent-platform
ref = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
path = runtime/control_plane/_verified_workspace_artifact_support.py
symbols = _TaskLock, _write_checkpoint, _load_checkpoint, _checkpoint_matches_program
classification = PROJECT_ACCEPTED_CODE
lesson = REUSE_MORE
```

Execution path: acquire task lock -> load/validate checkpoint -> construct complete candidate -> sibling-temp write -> flush/fsync -> `os.replace` -> later reconciliation from canonical checkpoint. Failure behavior rejects malformed/mismatched retained state and releases OS ownership on process death. This is the direct source for both selected local primitives.

### Harbor — evaluation lifecycle

```text
repository = harbor-framework/harbor
ref = 389bd4f8ce796ef4a97de4b62675021e262c8e76
paths = src/harbor/agents/base.py; src/harbor/trial/single_step.py; src/harbor/models/agent/context.py
classification = OPEN_SOURCE
lesson = ADAPT / EVALUATION_ONLY
```

Execution path: bounded trial setup -> environment/agent setup -> agent run with timeout/error capture -> verifier/reward -> cleanup/result metadata. This supports a thin custom CAP-review evaluation adapter without making Harbor the production launch/control plane.

Tests/failure-history evidence: the inspected `single_step.py` itself contains timeout/error/cleanup paths. A targeted test dedicated to the exact future CAP-review adapter seam was **NOT_FOUND** in the inspected pinned tree; no such test is claimed.

### openai/codex — conversation/session lifecycle reference

```text
repository = openai/codex
ref = 94cbbddafc1776d5e377bca1b05932c697e82238
paths = codex-rs/app-server/src/request_processors/thread_processor.rs; codex-rs/app-server/tests/suite/v2/thread_resume.rs
classification = OPEN_SOURCE
lesson = REFERENCE_ONLY
```

Execution path: thread start/resume/fork -> session registration -> conversation lifecycle/status restoration. The pinned resume suite supplies concrete lifecycle test evidence for history/model/rollout resume behavior.

Failure/reuse lesson: useful lifecycle ownership patterns exist, but no complete public path matching `fresh ordinary ChatGPT -> this repository's GitHub evidence -> bounded result comment` was found in the targeted source review. It does not replace the selected CAP mechanism.

### OpenHands — child-conversation launch reference

```text
repository = OpenHands/OpenHands
ref = 1098d73df42351a31b2940557efb9fe8750365c4
path = src/services/child-conversation-launch.ts
classification = OPEN_SOURCE
lesson = REFERENCE_ONLY; AVAILABILITY_FIRST CLAIM BEHAVIOR REJECTED
```

Execution path: parent/source-key claim -> child spawn -> readiness/status polling -> mark/release on failure. It demonstrates that duplicate child launch/replay is a real lifecycle concern.

Failure lesson: the inspected claim-ledger error path can proceed when local claim state is unavailable/corrupt, preferring availability over duplicate prevention. That tradeoff is rejected for CAP's mandatory review gate; CAP must fail closed. A targeted test for this exact claim helper was **NOT_FOUND** in the inspected pinned tree, so no stronger test coverage is claimed.

## Best current approaches

For this bounded slice the best fit is a composition of already accepted/project-compatible primitives rather than one imported framework:

- local single writer: accepted Stage 26.3C OS lock;
- durable operation record: accepted Stage 26.3C checkpoint replacement/load-validation pattern;
- browser cross-tab Send claim: one MV3 service worker + IndexedDB unique-key transaction;
- result transport: GitHub top-level PR comment with final full-set uniqueness/integrity rescan;
- semantic reviewer: fresh ordinary ChatGPT under the accepted skill;
- evaluation: Harbor only after production E2E, as a separate harness.

This minimizes new authority while covering the actual concurrency and process-crash domains separately.

## Failure lessons

- **Lock != crash-atomic persistence.** A process lock serializes writers but does not make an in-place record update recoverable.
- **Durable KV != atomic claim.** `chrome.storage.local` persistence does not provide transactional compare-and-claim semantics.
- **Service-worker memory != durable ownership.** MV3 workers may stop; in-memory sets cannot own a release-critical claim.
- **Committed claim + lost response is ambiguity.** Prefer manual fallback over another automatic grant/Send.
- **Checkpoint replacement is scoped.** sibling temp + flush/fsync + replace is reused for the accepted process-crash model, not claimed as whole-machine transactional durability.
- **Mutable remote evidence must be revalidated.** One accepted comment snapshot is insufficient; the complete matching set must be rescanned before merge.
- **Availability-first duplicate behavior is wrong here.** OpenHands' inspected willingness to proceed when claim state is unavailable is explicitly rejected.
- **Ambiguous external effects are not retry permission.** Launch, Send and comment creation each fail closed after uncertain consequence delivery.

## Alternatives comparison

### Local durable operation record

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| Stage 26.3C lock + sibling-temp/flush/fsync/`os.replace` checkpoint | already accepted, bounded, identity-validation pattern exists | scoped to declared process-crash/local-filesystem assumptions | **SELECT / REUSE_MORE** |
| SQLite transaction / `BEGIN IMMEDIATE` (optionally WAL) | mature transactional state and concurrency | adds DB lifecycle/schema/recovery framework for one bounded record; duplicates accepted role | **REJECT for v1 / reconsider if state grows** |
| append-only journal/WAL | strong history/replay potential | adds sequence, replay, corruption, compaction and reconciliation semantics | **REJECT for v1** |
| raw/in-place JSON write | simple | torn/partial record possible at process death; no safe transition boundary | **REJECT** |

### Browser cross-tab Send ownership

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| MV3 service worker + IndexedDB `readwrite` unique `add` | durable browser-local transactional claim; one bounded store | requires schema/version + service-worker failure handling | **SELECT / NARROW** |
| Web Locks + separate durable ledger | provides live mutual exclusion | lock is ephemeral and still needs durable claim/recovery state; two mechanisms instead of one transaction | **REJECT for v1** |
| service-worker in-memory Set + `chrome.storage.local` ledger | simple implementation | worker lifetime is ephemeral; KV check/set is not atomic | **REJECT** |
| Native Messaging/local callback holding local owner through browser ack | can centralize ownership locally | introduces native host/local transport and broader lifecycle authority | **REJECT for this slice** |

### Result handoff

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| GitHub top-level PR comment + nonce/integrity/full-set rescan | existing durable review channel, user no longer copies result | mutable; requires strict revalidation | **SELECT / REFINE** |
| local callback/result server | direct result transport | new ingress/service/authorization surface | **REJECT for v1** |
| user copy/paste | already works and safest fallback | routine human intervention remains | **KEEP as fallback, not primary automatic path** |

At least three materially distinct choices were evaluated for each new persistence/transport role. No alternative is selected merely because it is newer or more general.

## Product / options / ecosystem comparison

Product-level launch options were also considered:

- PR #138 deep-link/autosend: useful narrow physical evidence, but requires production hardening selected above;
- Windows Task Scheduler: useful one-shot experiment, but immediate review launch needs no timer owner -> **DEFER**;
- ChatGPT Scheduled Tasks: product capability exists, but current evidence does not prove this exact fresh ordinary-Chat + GitHub-tool isolation contract and event-triggered variants may require Work -> **DEFER**;
- Codex Review: optional independent signal but cannot replace mandatory ordinary-Chat review -> **KEEP OPTIONAL**;
- Harbor: excellent evaluation harness, not production lifecycle authority -> **SELECT EVALUATION ONLY**.

## Selected production-v1 lifecycle

### 1. Freeze and call bounded launcher

Caller-visible procedure accepts only:

```text
procedure=launch_independent_review_v1
repository=<owner/repo>
pr_number=<number>
base_sha=<40-hex>
head_sha=<40-hex>
review_skill=code-review
review_skill_version=<version>
```

No arbitrary prompt, URL, command, backend or findings input is accepted.

### 2. Stable operation key, OS single writer and crash-safe durable record

Three identities are separate:

```text
review_operation_key = deterministic exact review identity key
review_operation_lock_id = deterministic bounded OS-lock identity
review_run_id = high-entropy nonce generated exactly once and retained in durable canonical record
```

Required ordering:

```text
derive exact identity/key
 -> acquire existing OS-backed exclusive operation lock
 -> reconcile canonical/temp retained state fail-closed
 -> strict load OR first creation through checkpoint replacement
 -> generate review_run_id only for proven first creation
 -> write canonical prepared state atomically
 -> write canonical dispatch-attempted state through sibling-temp + flush + os.fsync + os.replace
 -> only after successful replacement invoke one OS/browser launch
 -> release lock after bounded launcher returns
```

A concurrent caller that cannot acquire the lock performs no record/nonce/launch work. Existing invalid/corrupt/missing-after-known state never falls back to clean creation.

### 3. Atomic browser Send claim

A content script never self-authorizes Send. The MV3 service worker owns `review_send_claims`; a `readwrite` transaction performs `add(review_run_id)`. Only the caller whose transaction commits receives `claim_status=granted` and may revalidate the root route/composer/button and issue the one Send click.

### 4. Fresh ordinary-Chat boundary

Existing `/c/...` conversation routes are refused. The reviewer receives only immutable review identity + private `review_run_id`, not development reasoning or suspected findings.

### 5. Bounded reviewer result authority

HEAD `code-review` v1.1 proposes exactly one automatic exception: the reviewer may publish its own structured `REVIEW_RESULT_V1 + review_run_id` as one top-level PR Conversation comment. It may not edit branch/files, approve/request changes, label, merge, close/reopen, or change settings. Ambiguous comment creation is not automatically retried.

### 6. Result consumption and final merge gate

Initial consumption queries the **complete** top-level PR comment collection and requires exactly one matching private nonce, configured expected principal, unedited body, exact repository/PR/BASE/HEAD/policy/context identity and valid result fields. It records comment id/body digest/created/updated metadata.

Final automatic-result merge gate queries the complete collection again (all pages, not only the saved comment), requires matching-comment count == 1, same id/author/body digest/metadata and live exact PR identity, then re-fetches that sole exact comment. A late duplicate, edit, deletion, author mismatch or ref movement invalidates the result.

### 7. No hidden automatic developer continuation

Completion does not automatically wake/replan the unfinished development conversation. That remains a separate same-task-continuation Stage Research seam.

## Failure / crash matrix

| Boundary / failure | Required behavior | Unauthorized duplicate/effect budget |
|---|---|---:|
| malformed/missing exact launch identity | reject before launch | 0 launches |
| two concurrent local callers before record exists | exactly one OS-lock holder; loser does no record/nonce/launch work | 0 extra launches |
| process dies before canonical record creation | OS releases lock; no canonical/temp ambiguity required before first creation | 0 effects |
| process dies during first checkpoint temp write | canonical absent + temp residue is ambiguous -> fail closed/manual recovery | 0 launches |
| first-record write/fsync/replace fails | fail closed; do not browser-launch | 0 launches |
| canonical record corrupt/partial/schema-mismatched | reject; never recreate/reset | 0 launches |
| canonical disappears after operation was known/created | ambiguity -> manual recovery; no new nonce | 0 launches |
| valid canonical plus temp residue | canonical only is authority; temp never consumed as state | 0 duplicate launches |
| crash while writing dispatch-attempted temp before replace | old canonical `prepared` remains; after locked validation first launch may still occur | <= 1 total launch |
| dispatch-attempted fsync/replace failure | no browser launch | 0 launches |
| crash after successful dispatch-attempted replace, before/during browser open | canonical forbids automatic retry | 0 extra launches |
| existing `/c/...` route | content script refuses Send | 0 Sends |
| extension claim schema/initialization marker missing, corrupt or version-mismatched | service worker fails closed; no grant | 0 Sends |
| two tabs request same run claim concurrently | overlapping IndexedDB readwrite transactions serialize; exactly one `add(review_run_id)` can commit; only that caller gets grant | 0 extra Sends |
| service worker / claim transaction fails or aborts before commit | no grant; no automatic Send | 0 Sends |
| claim commits but response is lost or winning tab dies before click | durable claim remains; no automatic retry/second grant; manual fallback | 0 extra Sends |
| same run appears in multiple tabs | service-worker claim permits at most one automatic Send attempt | 0 extra Sends |
| browser/transport ambiguous after click | no automatic redelivery | 0 additional Sends |
| reviewer timeout/no result | operational timeout; manual fresh-review fallback | 0 relaunches |
| malformed/wrong-author/edited/stale result | reject | 0 merge authority |
| ambiguous result-comment creation | reviewer does not retry | 0 extra comment attempts |
| late second matching comment | final full-set rescan fails closed | 0 merge authority |
| accepted result changes/disappears | final rescan/re-fetch invalidates it | 0 merge authority |
| live PR head/base moves | old result becomes stale; fresh review required | 0 stale merge authority |
| Harbor unavailable | production reviewer unaffected | 0 production effects |

No release-critical cell intentionally receives blind automatic retry.

## Evaluation method

Semantic-review quality and automation reliability are separate planes.

### Plane A — reviewer semantic quality

Track at minimum Precision, Recall/Coverage, F1, Decision Accuracy, False Approve Rate, False Reject Rate and Resolve Rate after Revision.

### Plane B — lifecycle reliability

Track launch success, fresh-context proof, exact-head binding, stale rejection, duplicate suppression, timeout/failure disposition, malformed/wrong-author/edited-result rejection, human interventions, wall time and measured cost where applicable.

Do not collapse these planes into one score.

Evaluation ladder after the first production E2E:

1. Harbor adapter + ReviewBench baseline;
2. bounded SWE-Review-Bench subset;
3. CR-Bench / CR-Evaluator signal-to-noise comparison;
4. development/fixed-regression/holdout separation and CAP Review Regression Set.

The first run is a **baseline, not a release exam**. Do not invent an arbitrary threshold before measuring current/manual behavior under the pinned harness. `project-context/BENCHMARK_EVALUATION_STRATEGY.md` remains the cross-capability owner.

## Acceptance checks

Deterministic/hosted shields must prove at least:

1. fixed launch schema only; arbitrary URL/prompt/command rejected;
2. deterministic operation key + one high-entropy durable nonce;
3. OS lock acquired before any operation-record load/create/nonce generation;
4. no unlocked fallback for concurrent callers;
5. durable operation writes reuse sibling-temp + `flush` + `os.fsync` + `os.replace`;
6. strict schema/version/exact-identity/nonce validation on load;
7. corrupt/mismatched canonical state never recreates/reset automatically;
8. canonical-absent + temp residue fails closed; valid canonical + temp residue never consumes temp as authority;
9. dispatch-attempted replacement succeeds before browser launch; write/replace failure yields no launch;
10. crash-before-replace vs crash-after-replace recovery matches the matrix;
11. MV3 service worker is sole browser Send-claim owner;
12. preinitialized/version-bound IndexedDB schema; no lazy claim-path upgrade;
13. deterministic two-tab barrier: exactly one transaction commits/grant reaches Send;
14. committed-claim/lost-response and tab-death cases do not re-grant;
15. stale/malformed/wrong-author/edited/duplicate result comments reject;
16. final merge gate rescans all top-level comments and re-fetches the sole accepted comment;
17. reviewer automatic authority is exactly one result comment and nothing else;
18. existing six-tool public surface remains unchanged except registered procedure behind `procedure_run`;
19. no generic scheduler/event bus/general browser storage database/Native Messaging result bus is reachable;
20. manual fresh-review fallback and optional Codex remain valid.

Physical target-Windows qualification must prove on frozen source/install/runtime bytes:

```text
one automatic development-side launch request
 -> zero user launch/paste intervention
 -> genuinely new ordinary ChatGPT conversation receives exact request + private nonce
 -> independent GitHub reconstruction
 -> valid REVIEW_RESULT_V1
 -> exactly one expected-principal result comment
 -> zero user result-copy intervention
 -> development side consumes it from GitHub
 -> final complete-comment-set integrity gate
 -> two real same-run tabs released concurrently prove exactly one service-worker IndexedDB claim grant and exactly one Send click
 -> local crash/persistence, stale, duplicate, edited, wrong-author, timeout and claim-store negative cases fail closed
```

## Stage decision

**NARROW — proposed by this Brief; effective only after this PR is accepted and merged.**

If accepted, production implementation may begin only for:

```text
exact frozen review identity
 -> registered bounded procedure_run launcher
 -> Stage 26.3C OS-backed local single-writer lock
 -> Stage 26.3C-style crash-atomic durable operation record + private nonce
 -> durable dispatch-attempted before one browser launch
 -> fresh-root ChatGPT deep-link/autosend
 -> MV3 service-worker IndexedDB unique-key Send claim
 -> exactly one automatic Send attempt
 -> fresh ordinary-Chat reviewer under bounded result envelope
 -> exactly one structured PR result comment
 -> full-comment-set + live exact-ref validation
 -> manual fallback after ambiguity
```

After the first production E2E, evaluation work may add only the thin Harbor/ReviewBench/SWE-Review-Bench/CR-Bench seam described above.

Any material introduction of a recurring/general scheduler, automatic developer wake, new public tool, arbitrary launcher, new local persistence/lease framework, non-transactional browser claim, general browser database runtime, Native Messaging/local result bus, blind retry after ambiguity, broader reviewer mutation authority, benchmark-driven production authority, worker rotation or multi-agent runtime invalidates this implementation authority and requires Stage Research re-entry.
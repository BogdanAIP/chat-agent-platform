# Automatic Independent Reviewer — Stage Research Brief

Status: **STAGE RESEARCH — NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)**

Research date: 2026-08-31

`NARROW` limits implementation scope; it does **not** lower the research standard required by accepted `stage-research` v1.2 or `source-code-research` v1.0. Production implementation remains blocked until this research PR passes exact-head CI, mandatory fresh ordinary-Chat review and merge.

Research baseline:

```text
main = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
Stage 26.3C process-crash/restart scope = accepted / closed
PR #138 = experiment-only launch evidence
public Chat-facing surface = six canonical semantic tools
mandatory primary semantic reviewer = fresh ordinary ChatGPT
```

## Stage goal

Remove routine user launch/paste/result-copy work from the already-required independent review gate without weakening exact-head review, falsification, reviewer independence, result integrity, crash/retry safety or deterministic least-privilege authority.

Selected v1 lifecycle:

```text
review-ready exact PR identity
 -> launch_independent_review_v1 behind procedure_run
 -> immutable genesis + crash-safe mutable state
 -> private high-entropy review_run_id
 -> one bounded browser launch
 -> one atomic browser-side Send claim
 -> fresh ordinary-Chat reviewer in a qualified read-only GitHub authority environment
 -> REVIEW_RESULT_V1
 -> submit_independent_review_result_v1
 -> local crash-safe result state
 -> reconcile_independent_review_result_v1 in development chat
 -> exact-head/fresh-context/result validation
 -> merge gate or fail closed
```

There is **no GitHub write in reviewer automation v1**. The earlier top-level PR-comment publisher design is rejected for v1 because it adds a provider credential, a broader permission bucket and an ambiguous external POST that the local crash/reconciliation model cannot make disappear.

Non-goals: no recurring/general scheduler, no arbitrary GitHub watcher, no `WAITING -> wake -> planner continuation`, no automatic wake/resampling of the unfinished development conversation, no worker rotation or multi-agent runtime, no seventh public tool/shell, no arbitrary URL/prompt/command launcher, no Native Messaging result bus, no raw GitHub write credential/action in the reviewer, no generic GitHub proxy, no reviewer merge/approval authority, no Harbor production authority and no general browser database/storage runtime.

## Current project baseline

### Existing public/procedure authority

The accepted Chat-facing surface remains exactly six tools. `procedure_run` already admits only registered bounded procedures through the semantic projection and deterministic Control Plane. Reviewer automation therefore uses only fixed procedures behind that existing boundary.

Stage 24 already established least-privilege projection as a project pattern: expose only the typed actions needed by a profile while broader backend mechanics remain outside the planner's authority surface.

### Accepted Stage 26.3C cooperating-runner lock

Accepted BASE `runtime/control_plane/_verified_workspace_artifact_support.py` contains `_TaskLock` / `_acquire_task_lock`, using a process-held OS-backed nonblocking exclusive lock. Process death releases live lock ownership. Reviewer automation reuses that role for exact-operation single-writer ownership before any genesis/state read, nonce generation, result submission or manual-fallback closure.

### Accepted Stage 26.3C crash-oriented file primitives

The same accepted BASE implementation contains:

- `_exclusive_create_file`: exclusive create -> complete bytes -> `flush` -> `os.fsync`;
- `_write_checkpoint`: same-directory sibling temp -> complete JSON -> `flush` -> `os.fsync` -> `os.replace`;
- `_load_checkpoint` / `_validate_resume_state`: strict canonical/schema/identity validation.

Reviewer automation reuses these primitives but keeps their declared guarantee narrow: cooperating process crash/restart on the supported local filesystem, not storage rollback, hostile deletion or machine/power-loss transactional durability.

### PR #138 launch evidence

PR #138 physically demonstrated a run-bound ChatGPT deep-link/autosend path and one bounded Send. It did not prove durable operation ownership, browser cross-tab serialization, qualified reviewer tool authority or result handoff. It remains a launch/UI mechanic source only.

## Architecture lineage comparison

For every **existing BASE role**, exactly one canonical lineage decision is recorded. Scope qualifiers are separate and are not second decisions.

| Role | Prior source / owner | Canonical lineage decision | Scope qualifier / reason |
|---|---|---|---|
| primary semantic reviewer | fresh ordinary ChatGPT | **KEEP** | required reviewer remains unchanged |
| review protocol | project `code-review` skill | **REFINE** | keep exact refs/falsification; add bounded local automatic-result submission/reconciliation |
| bounded launch consequence | registered `procedure_run` | **REUSE_MORE** | reuse existing admission surface; no seventh tool |
| local concurrent operation ownership | Stage 26.3C OS-backed lock | **REUSE_MORE** | exact reviewer operation gets the same cooperating single-writer role |
| immutable creation evidence | Stage 26.3C `_exclusive_create_file` mechanic | **REUSE_MORE** | reuse for reviewer genesis; no new persistence framework |
| mutable durable local state | Stage 26.3C checkpoint mechanic | **REUSE_MORE** | reuse for launch/result/fallback state |
| deep-link/composer mechanic | PR #138 experiment | **REFINE** | retain proved UI mechanics; replace page-local ownership with durable claim state |
| development continuation | current user-driven development chat | **KEEP** | result copy/paste is removed; automatic wake remains out of scope |
| optional second reviewer | Codex Review | **KEEP** | optional evidence only |

New architecture roles introduced by this Stage Research are explicitly marked **NEW_ARCHITECTURE** rather than receiving a fake lineage decision:

- reviewer authority qualification/isolation;
- browser cross-tab Send claim via MV3 service worker + IndexedDB;
- local automatic-result submission/reconciliation state;
- Harbor-backed evaluation seam.

These new roles are covered by the Research Scope Expansion Gate below.

## Architecture primitives and adjacent domains

### Primitive A — process-held OS lock

Engineering domain: local inter-process concurrency / file locking.

Guarantee here: only one cooperating local caller may create/read/transition one review operation at a time.

Assumptions/boundary: cooperating processes use the lock; process death releases ownership. It is not durable state and does not defend against hostile non-cooperating writers.

### Primitive B — immutable exclusive-created genesis

Engineering domain: filesystem create-if-absent / identity persistence.

Guarantee here: distinguish true first creation from disappearance of mutable state while the genesis survives.

Assumptions/boundary: supported local filesystem; hostile deletion of both genesis and state, storage rollback and machine/power-loss loss are outside the guarantee.

### Primitive C — crash-safe mutable checkpoint replacement

Engineering domain: filesystem persistence / atomic replacement.

Guarantee here: a process restart observes either the old valid canonical state or the new valid canonical state, while failed/ambiguous temp residue fails closed.

Assumptions/boundary: same filesystem/directory; successful `os.replace`; process-crash scope. This does not claim universal power-loss durability.

### Primitive D — MV3 service-worker + IndexedDB unique-key claim

Engineering domain: browser extension lifecycle + transactional browser storage.

Guarantee here: across concurrent tabs for the same `review_run_id`, at most one committed claimant receives automatic Send authority.

Assumptions/boundary: pre-initialized expected IndexedDB schema/version; one extension origin; no lazy schema upgrade on the claim path; transaction success is required before grant.

### Primitive E — reviewer authority-qualified ChatGPT environment

Engineering domain: application capability control / least privilege.

Guarantee here: the fresh reviewer cannot invoke a GitHub mutation action, not merely that it chooses not to.

Accepted qualification states:

1. GitHub app is disconnected/disabled/unavailable in the reviewer account/workspace; or
2. a workspace Action Control that actually removes GitHub write actions from the reviewer role/app surface is enabled and fresh evidence proves only read actions are available.

Per-message non-selection, `@mention` omission, `Always ask`, `Any changes`, `Important actions`, or another confirmation policy is **not** accepted as authority removal.

If neither accepted qualification state can be proved on the target ordinary-Chat environment, `launch_independent_review_v1` must fail closed as `reviewer_authority_unqualified` before automatic Send. Manual fresh ordinary-Chat review remains the fallback.

### Primitive F — local result submission and reconciliation

Engineering domain: local idempotent state machine / reconciliation.

Guarantee here: automatic result delivery has no external side effect and cannot race a manual fallback into a late unresolved result after fallback closure.

The same OS lock serializes automatic result recording and manual-fallback closure. A final development-side reconciliation is mandatory before merge. A valid immutable genesis with missing mutable state never permits automatic relaunch or automatic result submission, but it is not allowed to make the exact PR head permanently uncloseable: the development-side reconciliation procedure may use the retained genesis identity and the same `review_run_id` to record one **manual-only terminal recovery** backed by a complete fresh manual review.

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

Confirmed hazards from this PR's review history:

- same-run concurrent launch/Send needs explicit serialization;
- live OS locking does not provide crash-atomic persistence;
- mutable state disappearance cannot be distinguished from first creation without retained creation evidence;
- a fsynced genesis followed by process death before the first mutable checkpoint must not create an unrecoverable merge block;
- prompt-only GitHub mutation prohibitions do not remove capability;
- per-message app non-selection proves non-use, not durable capability revocation;
- an ambiguous external comment POST can complete after a zero-result scan and race manual fallback;
- remote comments add edit/delete/duplicate integrity work that is unnecessary if the result can remain local;
- service-worker memory is not durable ownership because MV3 workers terminate;
- stale BASE/HEAD invalidates otherwise correct review evidence.

## Solution evidence

### Filesystem genesis/checkpoint evidence

Primary/strong solution-domain evidence:

- POSIX `open()` / `O_CREAT|O_EXCL`: the existence check and creation are atomic with respect to competing opens of the same name: https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html
- POSIX `fsync()`: waits for requested file synchronization or an error: https://pubs.opengroup.org/onlinepubs/009695399/functions/fsync.html
- Python `os.fsync`: on Unix invokes native `fsync`, on Windows `_commit`; Python explicitly requires `flush()` before `os.fsync()` for buffered files: https://docs.python.org/3/library/os.html#os.fsync
- Python `os.replace`: same-filesystem successful replacement is the cross-platform replace primitive; Python documents successful rename/replace as atomic where the platform contract provides it: https://docs.python.org/3/library/os.html#os.replace

Project mapping:

```text
operation lock
 -> clean all-absent check
 -> generate review_run_id once
 -> exclusive-create/fsync immutable genesis
 -> strict reload
 -> sibling-temp/flush/fsync/replace mutable state
 -> strict pair validation
```

The direct sources support create-if-absent, flushing/synchronization and replacement mechanics. They do **not** justify a stronger machine/power-loss or hostile-state rollback claim, so v1 does not make one.

### Browser claim evidence

Primary solution-domain evidence:

- W3C IndexedDB 3.0 transaction model: overlapping `readwrite` transactions do not run simultaneously against the same scope; the earlier transaction has exclusive access until it finishes: https://www.w3.org/TR/IndexedDB/#transaction-scheduling
- W3C IndexedDB `add()`: `add` uses a no-overwrite operation and fails with `ConstraintError` when the key already exists: https://www.w3.org/TR/IndexedDB/#dom-idbobjectstore-add
- W3C transaction abort semantics revert changes made by an aborted transaction: https://www.w3.org/TR/IndexedDB/#dom-idbtransaction-abort
- Chrome extension service-worker lifecycle: workers may terminate after inactivity or unexpectedly; globals are lost and important state must be persisted: https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle
- Chrome's termination testing guidance explicitly recommends testing termination and persisting state: https://developer.chrome.com/docs/extensions/how-to/test/test-serviceworker-termination-with-puppeteer

Project mapping:

```text
content script requests claim(review_run_id)
 -> MV3 service worker validates sender/origin/message
 -> exact pre-initialized DB/store/version
 -> one readwrite transaction
 -> objectStore.add(claim, review_run_id)
 -> wait for transaction completion
 -> committed winner receives grant
 -> duplicate key / abort / lost response receives no new automatic grant
```

This directly supports the selected cross-tab serialization claim. It does not justify keeping ownership in service-worker globals, and the design explicitly does not do that.

### Reviewer authority evidence

Primary product evidence:

- OpenAI `Apps in ChatGPT`: app permissions control when ChatGPT asks; they do not remove provider access, and to remove an app's access it must be disconnected or disabled by workspace control: https://help.openai.com/en/articles/11487775
- OpenAI admin controls: app access determines who can use an app; where supported, **Action control determines what the app can do** and can allow only read actions or a custom action set: https://help.openai.com/en/articles/11509118
- OpenAI developer-mode docs: app selection applies to the message where it is used and multiple apps may be invoked; selection is an invocation mechanism, not accepted here as a security proof that a separately available write app does not exist: https://help.openai.com/en/articles/12584461

Therefore the selected security invariant is not “GitHub was not selected.” It is **GitHub mutation actions are unavailable to the reviewer security context**. The target-Windows ordinary-Chat physical gate must prove that condition from fresh platform/app/action evidence before automatic review is accepted.

### Local result-state evidence

No provider-side write is needed. `submit_independent_review_result_v1` and `reconcile_independent_review_result_v1` reuse the already accepted local OS-lock + checkpoint mechanics.

Mutable state contains at minimum:

```text
dispatch_state = prepared | dispatch-attempted | automation-abandoned
result_state = open | automatic-result-recorded | manual-fallback-recorded
result_source = null | automatic | manual
result_body_sha256 = null | <sha256>
result_payload = null | <validated REVIEW_RESULT_V1 + findings>
result_recorded_at = null | <timestamp>
recovery_reason = null | state-missing-after-genesis
```

Automatic submit under the operation lock:

```text
require valid genesis/state + dispatch-attempted + result_state=open
 -> validate review_run_id + exact result identity/context/schema
 -> compute result_body_sha256
 -> atomically persist automatic-result-recorded + payload + digest
 -> return recorded receipt
```

If the transport response is lost after persistence, a repeated same-nonce/same-digest call may return `already_recorded` without another external effect. A different digest or a closed manual-fallback state is rejected.

Development reconciliation:

```text
reconcile_independent_review_result_v1(exact review identity, optional manual_result)
 -> acquire same operation lock
 -> load/strictly validate genesis
 -> if canonical state exists: strictly validate the genesis/state pair
 -> if automatic-result-recorded: return automatic result; never overwrite it
 -> if open and no manual_result: return pending
 -> if open and valid manual_result supplied: atomically persist manual-fallback-recorded
 -> if manual-fallback-recorded: return stored manual result
 -> if valid genesis exists but canonical state is missing:
      * launcher and automatic submit remain permanently disabled for this operation
      * without manual_result return manual_recovery_required
      * with a complete valid fresh manual_result bound to the same exact PR identity,
        atomically create canonical terminal state using the existing genesis review_run_id,
        dispatch_state=automation-abandoned,
        result_state=manual-fallback-recorded,
        result_source=manual,
        recovery_reason=state-missing-after-genesis
      * never generate a replacement nonce and never relaunch
```

A sibling temp residue is never promoted to authority. When genesis is valid and canonical state is missing, the manual-only recovery transition may leave such residue as forensic evidence; the newly committed terminal canonical state is authoritative because the transition is explicit, same-lock, manual-result-bound and permanently closes automatic launch/submission. This rule deliberately does not apply when a canonical file exists but is corrupt, schema-invalid, identity-mismatched or nonce-mismatched: those states remain fail closed for separate operator recovery rather than being silently overwritten.

This closes both relevant races. Automatic submit and normal manual-fallback closure contend on the same local lock, so whichever commits first defines the authoritative result state. If mutable state vanished or the process crashed after fsynced genesis but before the initial checkpoint, the retained genesis prevents a new automatic attempt while still permitting one explicit manual terminal closure with the same nonce. A later automatic submit cannot appear after either form of `manual-fallback-recorded`.

Before merge, development must perform a final reconciliation against the live exact PR identity. `open`, `manual_recovery_required`, corrupt, mismatched, stale or ambiguous state blocks merge.

## Best current approaches

Selected composition:

- Stage 26.3C OS lock — local cooperating single-writer ownership;
- immutable exclusive-created genesis — prior-creation evidence;
- Stage 26.3C atomic checkpoint — launch/result/fallback mutable state;
- manual-only terminal recovery — same-genesis/same-nonce closure after missing mutable state, with automation permanently abandoned;
- MV3 service worker + IndexedDB `readwrite`/`add(review_run_id)` — browser cross-tab Send ownership;
- qualified ordinary-Chat reviewer environment — no GitHub mutation action available;
- fixed local `submit_independent_review_result_v1` — automatic result record;
- fixed local `reconcile_independent_review_result_v1` — development consumption/manual fallback closure/final gate;
- fresh ordinary ChatGPT — semantic judgment;
- Harbor — evaluation only after first honest production-like E2E.

No local callback server, GitHub publisher, generic scheduler, generic GitHub proxy or second planner is introduced.

## Failure lessons

- **Prompt prohibition != least privilege.** If a mutation action is technically available, prose does not remove it.
- **Per-message app non-selection != capability revocation.** Automatic review qualifies only an environment where write actions are actually unavailable.
- **Approval policy != action removal.** Asking before writes is useful safety UX but is not the project security boundary.
- **Lock != durable state.** Process serialization and crash-safe persistence are separate roles.
- **Atomic replacement != prior-creation proof.** Immutable genesis remains separate from mutable state.
- **Fail-closed must not mean permanently uncloseable.** A retained valid genesis with missing mutable state abandons automation but may be closed only by an explicit same-lock fresh-manual-result terminal transition that preserves the original nonce.
- **Service-worker memory != durable browser ownership.** MV3 workers terminate and lose globals.
- **Durable KV != atomic claim.** `chrome.storage.local` check/set is not a transactional unique claim.
- **Ambiguous external POST creates a distributed reconciliation problem.** v1 removes the POST instead of adding timeouts/quarantine heuristics.
- **Local result state can close fallback races deterministically.** Automatic submit and manual closure share one operation lock/state machine.
- **Benchmark infrastructure is evidence, not authority.** Harbor never decides production acceptance.

## Alternatives comparison

### Result handoff / authority

| Approach | Core owner | Crash/ambiguity boundary | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|---|
| direct reviewer GitHub write app/token | Chat reviewer | provider mutation | simple | broad authority; prompt-only restriction | **REJECT** |
| backend GitHub App + allowlisted one-comment publisher | local publisher + provider | ambiguous external POST can complete late | durable PR-visible evidence | credential lifecycle, provider permission bucket, late POST reconciliation | **REJECT for v1** |
| local crash-safe result state + fixed submit/reconcile procedures | Control Plane | accepted local process-crash scope | no provider write; same-lock fallback closure | result is local rather than PR-visible | **SELECT** |
| local callback/result HTTP server | new ingress service | network/auth/receiver lifecycle | direct | new privileged service/result bus | **REJECT** |
| user copy/paste | user | manual | already works | routine friction | **KEEP as fallback** |

### Local durable operation state

| Approach | State owner | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|
| exclusive genesis + accepted atomic checkpoint | project files | reuses accepted mechanics, detects missing mutable state | two small files/pair validation | **SELECT** |
| SQLite transaction/WAL | database | mature transactional state | new schema/migrations/journal owner | **REJECT for v1** |
| append-only event journal | local log | rich replay history | framing/checksum/replay/compaction lifecycle | **REJECT for v1** |
| raw in-place JSON | one file | simple | torn/corrupt overwrite; no creation proof | **REJECT** |

### Browser Send claim

| Approach | Owner | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|
| MV3 service worker + IndexedDB unique-key `add` | extension origin | transactional same-run claim across tabs | small schema/version lifecycle | **SELECT** |
| Web Locks + durable ledger | browser lock + store | good live exclusion | ephemeral lock still requires separate durable claim | **REJECT for v1** |
| service-worker memory / `chrome.storage.local` check-set | worker/KV | easy | worker termination + non-atomic check/set | **REJECT** |
| Native Messaging local dispatcher | native host | centralized ownership | privileged host/transport expansion | **REJECT** |

### Reviewer authority isolation

| Approach | Authority owner | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|
| per-message GitHub non-selection / approval prompts | Chat UI policy | low friction | does not prove write action unavailable | **REJECT as security boundary** |
| reviewer workspace/role with GitHub Action Control limited to read actions | ChatGPT workspace policy | explicit action removal where supported | workspace/admin configuration and revalidation | **SELECT when available** |
| dedicated reviewer account/workspace with GitHub app disconnected/disabled | ChatGPT account/workspace | simple deterministic absence | separate qualified environment may be operationally inconvenient | **SELECT fallback qualification** |
| same broad development context | user account | no setup | broad GitHub write authority remains | **REJECT for automatic mode** |

## Source-code evidence

### Chat Agent Platform accepted Stage 26.3C

```text
repository = BogdanAIP/chat-agent-platform
exact ref = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
research date = 2026-08-31
classification = OPEN_IMPLEMENTED
lesson = REUSE_COMPONENT / ADAPT_MECHANIC
```

Inspected symbols/tests:

- `_TaskLock`, `_acquire_task_lock`, `_exclusive_create_file`, `_write_checkpoint`, `_load_checkpoint`, `_validate_resume_state`;
- `tests/test_stage26_3c_workspace_hard_crash.py`;
- `tests/test_stage26_3c_checkpoint_progress_validation.py`;
- `tests/test_stage26_3c_checkpoint_identity_validation.py`.

Reuse only the accepted local process-crash mechanics; do not import workspace-artifact effect authority into reviewer semantics.

### Harbor

```text
repository = harbor-framework/harbor
exact ref = 389bd4f8ce796ef4a97de4b62675021e262c8e76
research date = 2026-08-31
classification = OPEN_IMPLEMENTED
lesson = REUSE_COMPONENT for evaluation only
exact CAP production fresh-Chat launch = NOT_FOUND_AFTER_TARGETED_SEARCH
```

Inspected `src/harbor/agents/base.py`, `src/harbor/trial/single_step.py`, `src/harbor/models/agent/context.py`, and `tests/unit/test_single_step_trial.py`. Harbor owns evaluation trial execution/artifact/verifier lifecycle; it does not become production authority.

### openai/codex

```text
repository = openai/codex
exact ref = 94cbbddafc1776d5e377bca1b05932c697e82238
research date = 2026-08-31
classification = OPEN_IMPLEMENTED for adjacent thread/session lifecycle
exact CAP fresh ordinary-Chat reviewer wake = NOT_FOUND_AFTER_TARGETED_SEARCH
lesson = REFERENCE_ONLY
```

Inspected `codex-rs/core/src/thread_manager.rs` and `thread_manager_tests.rs`. Stable/resumed identity is a useful reference; Codex remains optional evidence, not the mandatory reviewer runtime.

### OpenHands

```text
repository = OpenHands/OpenHands
exact ref = 1098d73df42351a31b2940557efb9fe8750365c4
research date = 2026-08-31
classification = OPEN_IMPLEMENTED
claim-before-effect lesson = ADAPT_MECHANIC
availability-first corrupt-ledger behavior = REJECT_MECHANIC
```

Inspected `src/services/child-conversation-launch.ts` and `__tests__/services/child-conversation-launch.test.ts`, including `ignores a replayed tool call`. Claim-before-effect is useful; fail-open replay risk is not.

## Failure/Crash Matrix

| Boundary / failure | Authoritative durable state | Possible physical state | Required fresh evidence | Retry / reconciliation permission | Shield / test | Max unauthorized additional effect |
|---|---|---|---|---|---|---:|
| malformed exact launch identity | none | no operation | live PR + schema | no launch | fixed-schema negatives | 0 |
| concurrent first callers | OS lock | one holder / loser | lock result + directory state | loser no create/nonce | barrier test | 0 extra launches |
| crash before genesis create | none | no effect | all-absent scan under lock | clean first creation allowed | crash-before-genesis | 0 |
| crash during genesis create | invalid/partial genesis possible | no browser launch | strict genesis reload | existing invalid genesis blocks | create fault injection | 0 launches |
| crash after fsynced genesis before initial mutable checkpoint | valid genesis; canonical state missing; same original review_run_id retained | no launch if crash precedes first checkpoint; if state disappeared later, historical automation progress is unknown | strict genesis validation + canonical/temp scan + live exact PR identity | **automatic relaunch and automatic submit forbidden**; without manual result return `manual_recovery_required`; with complete fresh manual result, `reconcile_independent_review_result_v1` may atomically create same-nonce terminal `automation-abandoned` + `manual-fallback-recorded` state | genesis-only-crash manual-closure test | 0 automatic relaunches / 0 late accepted automatic results |
| valid genesis, missing mutable state after any later point | valid genesis proves prior creation; canonical absent | earlier automation may have progressed, but v1 has no GitHub write side effect | same evidence as genesis-only crash + complete fresh manual review before closure | same manual-only terminal recovery; never infer old physical progress, never create a new nonce, never relaunch, late automatic submit rejected | missing-state manual-recovery test | 0 automatic relaunches / 0 repository effects |
| state exists, genesis missing | untrusted state | history unknown | pair validation | fail closed | missing-genesis test | 0 launches |
| pair/nonce mismatch | untrusted pair | history unknown | strict pair validation | fail closed | mismatch tests | 0 launches |
| mutable temp write/replace failure with canonical present | old canonical + residue | effect bounded by canonical state | persistence result + reload | canonical remains authority; temp never consumed | replacement fault injection | 0 unauthorized effects |
| mutable temp residue with genesis valid and canonical missing | genesis only + non-authoritative residue | interrupted initial/later state write possible | genesis/temp scan + fresh manual review for closure | launcher/submit blocked; reconcile may create terminal manual-only canonical with same nonce and leave temp as forensic residue; temp is never parsed as authority | genesis-plus-temp manual-recovery test | 0 automatic relaunches |
| prepared durable, crash before dispatch-attempted | prepared | no browser launch by ordering | strict state reload | same nonce may transition once | crash-before-dispatch | <=1 total launch |
| dispatch-attempted durable, browser open ambiguous | dispatch-attempted | browser unopened/opened | state + browser diagnosis | no automatic relaunch | crash-after-dispatch | 0 extra launches |
| existing `/c/...` route | dispatch-attempted; no Send claim | wrong conversation | fresh route/composer state | refuse claim/Send | route-refusal physical test | 0 Sends |
| authority environment not qualified | no Send claim | GitHub write action may exist | fresh app/action/access evidence | abort automatic mode | negative authority gate | 0 GitHub mutations |
| service worker terminates before claim commit | no committed claim | no Send authority | IDB transaction state | no Send | termination test | 0 Sends |
| two tabs claim same run | one IDB key may commit | two composers | both transaction outcomes | one grant only | deterministic + two-real-tab test | 0 extra Sends |
| claim commits, response lost/tab dies | committed claim | zero or one click attempt | durable claim + tab state | no regrant; manual fallback | lost-response test | 0 extra Sends |
| automatic reviewer submit before local state commit | result_state=open | no result recorded | locked reload | same request may be retried/reconciled | submit fault injection | 0 repository effects |
| result state commit succeeds, submit response lost | automatic-result-recorded | result durable | locked reload + digest | same nonce/digest returns already_recorded; different result rejected | lost-response idempotence test | 0 repository effects |
| manual fallback and automatic submit race | one operation lock | either may arrive first | locked state | winner commits authoritative result; loser cannot overwrite | concurrent submit/fallback barrier | 0 late accepted results |
| manual fallback commits first | manual-fallback-recorded | late automatic submit may arrive | locked state | late submit rejected | late-submit test | 0 late results |
| automatic result commits first | automatic-result-recorded | manual result may exist separately | locked state | manual path cannot overwrite; automatic result must be dispositioned | precedence test | 0 overwritten findings |
| corrupt/stale/mismatched local result | invalid result state | result bytes exist | strict result + live PR identity validation | no merge | corruption/stale tests | 0 merge authority |
| live BASE/HEAD moves | result bound to old identity | PR now different | fresh PR identity | mark stale/new review required | stale-head test | 0 stale merge authority |
| hostile deletion/storage rollback/power loss | local proof may disappear | history may be lost | outside declared v1 guarantee | no guarantee claimed | scope assertion | no false guarantee |
| Harbor unavailable | production state unchanged | benchmark absent | harness status | retry evaluation only | isolation test | 0 production effects |

No release-critical cell is left `unknown` within the declared cooperating process-crash/restart and qualified-reviewer-environment scope.

## Fit to this architecture

```text
fresh ordinary ChatGPT reviewer       -> semantic judgment; GitHub write actions unavailable
project code-review policy            -> exact review protocol + falsification
procedure_run launch                   -> bounded launch consequence
Stage 26.3C OS lock                   -> local live single-writer ownership
exclusive-created genesis             -> prior-creation evidence
Stage 26.3C checkpoint pattern        -> launch/result/fallback durable local state
MV3 service worker + IndexedDB        -> browser Send ownership only
procedure_run submit                  -> automatic result recording only
procedure_run reconcile               -> development consumption/manual closure/manual-only recovery/final gate
public web/GitHub GET evidence        -> repository evidence without GitHub mutation
Harbor                                -> evaluation only
```

The selected v1 removes the entire automated GitHub mutation path rather than attempting to constrain a broad provider permission bucket with more local code.

## Reviewer evaluation method

Keep two planes separate.

### Plane A — semantic reviewer quality

Measure precision, coverage/recall, F1, decision accuracy, false approve/reject behavior, revision resolution and signal/noise as supported by each benchmark.

### Plane B — lifecycle reliability

Measure fresh-context success, authority qualification success/failure, exact-head binding, launch/Send duplicate suppression, result handoff, stale rejection, timeout/failure classes, human interventions, wall time and cost where measurable.

Do **not** collapse these planes into one score.

Evaluation ladder after the first honest production-like E2E:

```text
Harbor adapter -> ReviewBench baseline
 -> bounded SWE-Review-Bench subset
 -> CR-Bench / CR-Evaluator signal-to-noise control
 -> CAP Review Regression Set
```

Use a development subset for iteration, fixed regression subsets for routine comparison and a holdout/official evaluation for independent validation. The first run is a **baseline, not a release exam**.

## Acceptance checks

Before later production implementation can be accepted, tests/qualification must prove:

1. fixed `launch_independent_review_v1`, `submit_independent_review_result_v1` and `reconcile_independent_review_result_v1` schemas only;
2. arbitrary URL/prompt/command/GitHub mutation/result-bus inputs rejected;
3. deterministic operation key + immutable genesis + one durable high-entropy `review_run_id`;
4. `review_run_id` is not returned to the development caller before automatic result recording;
5. OS lock precedes genesis/state access and has no unlocked fallback;
6. genesis uses exclusive create + flush/fsync and is never automatically overwritten/deleted;
7. mutable writes use sibling-temp + flush/fsync + replace + strict reload;
8. genesis/state missing/mismatch/corruption/temp-residue cases never create a replacement nonce or permit automatic relaunch;
9. valid genesis + missing canonical state is recoverable only through `reconcile_independent_review_result_v1` with a complete fresh manual review, preserving the original `review_run_id` and atomically recording terminal `automation-abandoned` + `manual-fallback-recorded` state;
10. genesis-only crash and genesis-plus-temp crash tests prove the PR head remains manually closeable while automatic launch/submission stay closed;
11. `dispatch-attempted` is durable before browser launch;
12. hard-crash tests cover genesis creation and mutable transition replacement;
13. MV3 service worker is the sole Send-claim owner and claim-time DB create/upgrade is forbidden;
14. W3C-compatible readwrite unique-key claim semantics are exercised by deterministic concurrency tests;
15. two real same-run tabs released concurrently produce exactly one committed grant and one Send click;
16. committed-claim/lost-response/tab-death cases never re-grant automatically;
17. automatic reviewer qualification proves GitHub mutation actions are **unavailable**, not merely unselected or approval-gated;
18. accepted qualification is either disconnected/disabled GitHub app or workspace Action Control that exposes only read actions; otherwise automatic launch fails closed;
19. ordinary-Chat physical gate proves required Chat Local Bridge capability remains available in that qualified reviewer environment;
20. `submit_independent_review_result_v1` validates nonce/exact refs/policy/context/result schema and atomically records result locally;
21. same-nonce/same-digest duplicate submit is reconciliation only; different/stale/late-after-manual result is rejected;
22. `reconcile_independent_review_result_v1` under the same operation lock atomically resolves automatic-result vs manual-fallback races and the missing-state manual-only recovery transition;
23. `manual-fallback-recorded` permanently closes automatic submission for that operation;
24. final merge gate performs fresh live PR identity + local result reconciliation and rejects open/manual_recovery_required/corrupt/mismatched/stale state;
25. no GitHub write credential, GitHub publisher, generic GitHub/HTTP/GraphQL proxy or automatic PR comment exists in v1;
26. existing public semantic tool surface remains six tools;
27. no generic scheduler/event bus/general browser DB/Native Messaging result bus/automatic developer wake is reachable;
28. mandatory fresh ordinary-Chat review + exact-head hosted CI remain required;
29. target-Windows ordinary-Chat E2E proves zero routine user launch/paste/result-copy intervention **when the authority environment qualifies**;
30. if target environment cannot prove reviewer write-action unreachability, automatic mode fails closed and manual fresh review remains valid.

## Architecture decision

**NARROW — proposed by this Brief; effective only after this PR is accepted and merged.**

If accepted, implementation authority is limited to:

```text
exact frozen review identity
 -> registered launch_independent_review_v1
 -> Stage 26.3C OS-backed single-writer lock
 -> immutable exclusive-created genesis + private review_run_id
 -> Stage 26.3C crash-safe mutable checkpoint
 -> durable dispatch-attempted before one browser launch
 -> fresh-root ChatGPT deep-link/autosend
 -> qualified ordinary-Chat reviewer environment with GitHub mutation actions unavailable
 -> MV3 service-worker IndexedDB unique-key Send claim
 -> exactly one automatic Send authority grant
 -> fresh ordinary-Chat reviewer
 -> fixed submit_independent_review_result_v1 storing result locally
 -> fixed reconcile_independent_review_result_v1 for development consumption/manual fallback/manual-only missing-state recovery/final merge gate
 -> no automated GitHub write
```

The automatic path is **conditionally available**: if the target ChatGPT account/workspace cannot prove GitHub mutation actions unavailable while retaining the required review bridge/read evidence, the launcher must not send an automatic review request. That environment failure does not weaken the mandatory manual fresh-review path.

After the first honest E2E, the thin Harbor/ReviewBench/SWE-Review-Bench/CR-Bench evaluation seam may be added without granting benchmark infrastructure production authority.

Any requirement for recurring/general scheduling, automatic developer wake, new public tool, arbitrary launcher, reviewer-held GitHub write capability, automatic GitHub publisher/comment path, new general DB/lease framework, Native Messaging/local callback bus, blind retry after ambiguous external consequence, machine/power-loss transactional guarantee, worker rotation or multi-agent runtime invalidates this decision and requires Stage Research re-entry.
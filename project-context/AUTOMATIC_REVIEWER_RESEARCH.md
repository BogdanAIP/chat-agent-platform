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

Remove routine user launch/paste/result-copy work from the already-required independent review gate without weakening exact-head review, falsification, reviewer independence, result integrity, or deterministic least-privilege authority.

Bounded target lifecycle:

```text
review-ready exact PR identity
 -> registered launch_independent_review_v1 behind procedure_run
 -> immutable genesis record + crash-safe mutable operation checkpoint
 -> private single-use review_run_id
 -> one bounded browser launch
 -> one atomic browser-side Send claim
 -> fresh ordinary-Chat reviewer with no GitHub write credential/action
 -> REVIEW_RESULT_V1
 -> one submit_independent_review_result_v1 call
 -> project-owned allowlisted publisher creates at most one top-level PR result comment
 -> development-side full-comment-set + live-ref validation
 -> manual fallback on ambiguous/failed automatic execution
```

Non-goals remain explicit: no recurring/general scheduler, no arbitrary GitHub watcher, no `WAITING -> wake -> planner continuation`, no automatic wake/resampling of the unfinished development conversation, no worker rotation or multi-agent runtime, no seventh public tool/shell, no arbitrary URL/prompt/command launcher, no Native Messaging result bus, no automatic retry after ambiguous external effect, no raw GitHub write credential/action exposed to the reviewer, no generic GitHub proxy, no reviewer merge/approval authority, no Harbor production authority, and no general browser database/storage dispatcher or general browser database runtime.

## Current project baseline

### Existing public/procedure authority

The accepted public Chat-facing surface remains exactly six canonical semantic tools. `procedure_run` already admits only registered bounded procedures through the semantic projection and deterministic Control Plane. The automatic reviewer therefore adds only fixed registered procedures behind this existing boundary; it does not create a seventh tool or generic command/HTTP/GitHub dispatcher.

Stage 24 already established the project pattern of least-privilege capability projection: concrete profiles expose only admitted actions while broader backend mechanics remain behind the project boundary. The automatic reviewer reuses that principle rather than giving a model a broad external credential and relying on prose not to use it.

### Accepted Stage 26.3C cooperating-runner lock

Accepted BASE `runtime/control_plane/_verified_workspace_artifact_support.py` contains `_TaskLock` and `_acquire_task_lock`, using an OS-backed nonblocking exclusive lock: `msvcrt.locking(..., LK_NBLCK, ...)` on Windows and `flock(..., LOCK_EX | LOCK_NB)` on POSIX. Process death releases live lock ownership.

Required automatic-review reuse:

```text
canonical review identity
 -> derive review_operation_key / bounded lock id
 -> acquire existing project OS-backed exclusive lock
 -> no unlocked fallback
 -> only holder may inspect/create/transition operation state
 -> hold through durable dispatch-attempted transition and one launch decision
 -> release after bounded launcher returns
```

### Accepted Stage 26.3C crash-oriented file primitives

The OS lock is **not** the persistence primitive. The same accepted BASE implementation contains:

- `_write_checkpoint` / `_load_checkpoint` / `_validate_resume_state` for sibling-temp complete JSON -> `flush` -> `os.fsync` -> `os.replace` -> strict canonical load;
- `_exclusive_create_file` for exclusive create (`xb`) -> complete bytes -> `flush` -> `os.fsync`.

The automatic reviewer reuses both roles:

1. an immutable **genesis record** uses exclusive-create semantics and is never automatically overwritten or deleted in v1;
2. mutable operation state uses the accepted atomic checkpoint-replacement pattern.

`tests/test_stage26_3c_workspace_hard_crash.py`, `tests/test_stage26_3c_checkpoint_progress_validation.py` and `tests/test_stage26_3c_checkpoint_identity_validation.py` establish the accepted process-crash/restart and fail-closed validation style. No machine/power-loss transactional guarantee is added.

### PR #138 launch evidence

PR #138 physically demonstrated a narrow run-bound ChatGPT deep-link/autosend path and one bounded Send. Its page/session state did not prove durable operation ownership, crash-safe local state, cross-tab Send serialization, structured result handoff or general scheduler authority. It is therefore a launch/UI mechanic source only.

## Architecture lineage comparison

| Role | Prior / candidate | Decision | Reason |
|---|---|---|---|
| primary semantic reviewer | fresh ordinary ChatGPT | **KEEP** | mandatory accepted reviewer remains unchanged |
| review protocol | project `code-review` skill | **KEEP / REFINE** | exact refs/falsification remain; proposed v1.1 adds only bounded local result submission |
| bounded launch consequence | registered `procedure_run` | **REUSE_MORE / NARROW** | no seventh public tool or arbitrary launcher |
| local concurrent operation ownership | Stage 26.3C OS-backed lock | **REUSE_MORE** | closes cooperating first-creator/writer race |
| immutable prior-creation evidence | Stage 26.3C `_exclusive_create_file` style | **REUSE_MORE / REFINE** | persistent genesis marker distinguishes first creation from missing mutable state after a known operation |
| mutable durable local operation state | Stage 26.3C atomic checkpoint pattern | **REUSE_MORE** | closes process-crash write/load ambiguity without new DB/WAL framework |
| deep-link/composer mechanics | PR #138 | **REFINE** | retain proved UI mechanics, replace page-local ownership |
| browser-side cross-tab Send ownership | MV3 extension service worker + extension-origin IndexedDB | **SELECT / NARROW** | transactional unique-key claim closes same-run tab race |
| reviewer GitHub authority | no direct write credential/action; project-owned fixed publisher | **REFINE / LEAST_PRIVILEGE** | planner cannot exercise labels/branch/review/settings mutations because those actions are absent from its authority surface |
| result transport | fixed local submit procedure -> allowlisted GitHub App publisher -> one PR Conversation comment | **REFINE / SELECT** | keeps durable visible PR evidence without delegating raw GitHub authority to the reviewer |
| development continuation | current user-driven development chat | **KEEP MANUAL / DEFER automatic wake** | avoids hidden same-task-continuation runtime |
| evaluation harness | Harbor | **REUSE_MORE / EVALUATION ONLY** | avoids building benchmark runner; no production authority |
| optional second reviewer | Codex Review | **KEEP OPTIONAL** | additional signal only |
| generic scheduler/event bus/multi-worker/runtime/GitHub proxy | future concepts | **REJECT for this slice** | unnecessary authority expansion |

## Architecture primitives and adjacent domains

The selected design deliberately separates six release-critical primitives:

1. **Live local ownership** — process-held OS lock. Prevents cooperating concurrent writers but does not make durable writes atomic.
2. **Immutable operation genesis** — exclusive-created, fsynced identity/nonce record that proves an automatic operation was created. Detects mutable-state disappearance within the cooperating process-crash scope.
3. **Mutable durable operation state** — complete checkpoint replacement + strict load validation. Protects process-restart state transitions but does not prove first creation by itself.
4. **Browser Send ownership** — one MV3 extension service worker + IndexedDB unique-key transaction. Prevents same-run multi-tab Send duplication.
5. **Reviewer submission authority** — a private, single-use `review_run_id` accepted only by a fixed `submit_independent_review_result_v1` procedure. It is correlation plus a one-shot bearer submission capability until consumed; it grants no generic procedure/GitHub authority.
6. **GitHub publication/evidence** — a project-owned publisher holds the external credential and may invoke only the exact top-level-comment endpoint for the exact repository/PR. The resulting mutable comment is evidence and is independently rescanned before merge.

Adjacent domains explicitly researched: filesystem exclusive-create and replacement semantics, SQLite transactional state, append-only journal/WAL recovery, MV3 service-worker lifecycle, IndexedDB transaction serialization, Web Locks, browser KV persistence, capability projection, GitHub App installation tokens/permission buckets, allowlisted outbound clients, idempotency/correlation, mutable GitHub evidence and ambiguous external effects.

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

The project has already observed or independently reviewed concrete hazards relevant to automation:

- material head changes make earlier reviews stale;
- Stage 26.3C established that concurrent cooperating ownership needs an explicit OS lock;
- a fresh review of #140 rejected `chrome.storage.local` check/set as a non-atomic cross-tab claim;
- a later fresh review correctly separated OS serialization from crash-atomic mutable-state persistence;
- another review showed that mutable-state disappearance cannot be distinguished from first creation unless separate durable prior-creation evidence exists;
- giving a reviewer a GitHub credential/action with broader write permissions contradicts a claimed comment-only authority boundary even if the prompt says not to use the extra actions;
- result comments are mutable/duplicable evidence and therefore need a final complete-set rescan;
- OpenHands independently documents replayed child-launch ActionEvents as a duplicate/billable side-effect hazard.

These are release-relevant failure modes, not speculative optimization targets.

## Solution evidence

### Immutable genesis + mutable operation checkpoint

The deterministic `review_operation_key` owns two different durable files under the operation lock:

```text
<review_operation_key>.genesis.json   # immutable after first successful creation attempt
<review_operation_key>.state.json     # mutable canonical checkpoint
```

Genesis contains at minimum:

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
created_at
```

Mutable state contains the same exact identity + nonce and at minimum:

```text
dispatch_state = prepared | dispatch-attempted
submission_state = open | publication-attempted | published | publication-ambiguous
dispatch_attempted_at | null
result_body_sha256 | null
published_comment_id | null
```

First-creation ordering:

```text
derive exact operation identity
 -> acquire OS-backed exclusive operation lock
 -> inspect genesis + canonical + matching temp residues
 -> first creation permitted only when all are absent
 -> generate review_run_id exactly once
 -> _exclusive_create_file-style genesis create + write + flush + os.fsync
 -> strict reload/validate genesis
 -> atomically write canonical prepared state via sibling temp + flush + os.fsync + os.replace
 -> strict reload/validate genesis + canonical pair
```

A crash during genesis creation may leave no file or a partial/corrupt exclusive-created file. If no genesis was created, a clean first creation remains possible. If any genesis file exists but fails strict validation, future automatic execution fails closed; it is never overwritten/reset automatically. Genesis is never automatically deleted in v1.

Pair invariants after genesis exists:

- `genesis exists + canonical missing` -> `operation_state_missing_after_genesis`; **no new nonce and no automatic recreation**;
- `canonical exists + genesis missing` -> `operation_genesis_missing`; fail closed;
- genesis/canonical identity or `review_run_id` mismatch -> fail closed;
- canonical absent + matching mutable temp residue -> `operation_persistence_ambiguous`; fail closed/manual recovery;
- canonical valid + mutable temp residue -> canonical remains authority; temp is never consumed as state;
- invalid canonical JSON/schema/state -> never recreate/reset it automatically;
- write, flush, `os.fsync` or `os.replace` failure -> **no external browser launch**.

`dispatch-attempted` must be successfully replaced into canonical state **before** invoking the OS/browser launch consequence. A crash before that replace leaves valid `prepared`; a crash after successful replace leaves `dispatch-attempted`, which forbids automatic relaunch.

This detects disappearance of the mutable canonical record because the immutable genesis survives ordinary cooperating process crash/restart. Hostile/non-cooperating deletion of both genesis and canonical, deletion of the whole state root, machine/power-loss filesystem loss and storage rollback are explicitly outside this v1 guarantee and are not claimed as detectable.

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

The claim path **must not lazily create or upgrade the database schema**. Missing marker/store, unexpected version, `onupgradeneeded`, transaction abort/error, service-worker failure, malformed response or ambiguous response all fail closed with **no automatic Send**.

If **two tabs request the same run claim concurrently**, overlapping IndexedDB readwrite transactions serialize; **exactly one `add(review_run_id)` can commit** and **only that caller gets grant**. The budget is **0 extra Sends**.

If the **service worker / claim transaction fails or aborts before commit**, no grant exists. If the **claim commits but response is lost or winning tab dies before click**, the **durable claim remains** and blocks a second automatic grant; use **manual fallback**. The content script **does not automatically retry an ambiguous claim response**.

### Deterministic reviewer GitHub authority

The fresh reviewer must not receive a raw GitHub installation/user token and must not have a selected mutation-capable GitHub app/action in the automatic review context. For this public-repository v1, repository evidence is reconstructed through credentialless/public GitHub GET/web evidence or another physically proven read-only evidence path. ChatGPT app approval settings are not treated as a security boundary: OpenAI documents that permission settings primarily control when actions ask for approval and do not remove underlying app access.

Primary product evidence:

- https://help.openai.com/en/articles/11487775 — app permissions and action controls; personal permission settings do not grant/remove provider capability by themselves;
- https://docs.github.com/en/rest/issues/comments — public issue-comment reads can be unauthenticated for public resources; creating a comment requires write permission;
- https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app — GitHub App endpoint permissions;
- https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation — installation tokens can be scoped to repositories/permissions and expire after one hour.

GitHub's own permission bucket for creating a top-level PR Conversation comment (`POST /repos/{owner}/{repo}/issues/{issue_number}/comments`) requires Issues-write or Pull-requests-write, each broader than one exact comment. Therefore **token scope alone is insufficient** for the claimed one-comment authority.

Selected enforcement is two-layered:

```text
fresh reviewer
 -> no raw GitHub write credential/action
 -> one fixed submit_independent_review_result_v1 procedure call
 -> project Control Plane validates single-use run capability + exact result schema/state
 -> persist publication-attempted before external POST
 -> local publisher mints/loads short-lived dedicated GitHub App installation token
 -> allowlisted client permits only POST /repos/<exact owner>/<exact repo>/issues/<exact pr>/comments
 -> no generic HTTP method/path/GraphQL/GitHub SDK surface is exposed to the reviewer
 -> one comment attempt only
```

The GitHub App is installed only on the target repository and requests only the minimum permission bucket needed for comment creation. Its private key/installation token stays outside repository/workspace/chat-visible state. The local publisher additionally enforces exact owner/repo/pr/method/path/body constraints because GitHub's permission bucket is broader than the desired effect.

Negative authorization tests must prove the publisher rejects or has no code path for: file/branch mutation, review submission/approval/request-changes, labels/assignees/milestones, merge/close/reopen, settings, comment edit/delete, arbitrary issue creation, arbitrary repository choice, GraphQL mutation, arbitrary REST method/path, or a second publication attempt.

The automatic launch qualification must also prove the fresh reviewer context has no selected mutation-capable GitHub app/action. A permission prompt or instruction saying “do not mutate” is not accepted as deterministic enforcement.

### Single-use local result submission

`review_run_id` remains high-entropy and private until the one result submission has been consumed. The launcher stores it only in private operation state and injects it into the fresh review request; it **does not return review_run_id to the development caller**, does not place it in PR metadata before submission and does not use it as a general authorization token.

The reviewer calls only:

```text
procedure=submit_independent_review_result_v1
review_run_id=<same private value from REVIEW_REQUEST_V1>
result=<complete REVIEW_RESULT_V1 + findings>
```

The fixed procedure, under the operation lock:

1. resolves the operation by the high-entropy run id in private state;
2. requires valid genesis + canonical exact identity and `dispatch_state=dispatch-attempted`;
3. requires `submission_state=open` and exact structured result fields;
4. verifies result repository/PR/BASE/HEAD/policy/skill/context/run id match the operation;
5. computes and persists `result_body_sha256` and `submission_state=publication-attempted` **before** any GitHub POST;
6. consumes the run's automatic submission authority at that transition; later calls cannot regain it;
7. performs at most one allowlisted publisher POST.

If the local procedure call/POST outcome becomes ambiguous after `publication-attempted`, neither the reviewer nor another caller automatically retries the POST. The development side scans GitHub evidence. If exactly one valid expected-bot comment exists, it may reconcile that external result evidence; if none or multiple exist, automatic handoff fails closed and the manual fresh-review fallback remains available.

Once the result comment exists, `review_run_id` is public correlation data, but the local one-shot submission authority has already been consumed, so disclosure does not permit a second publication.

### Result evidence consumption

The expected comment author is the dedicated publisher GitHub App/bot identity, not the reviewer user's broad GitHub identity.

Initial consumption queries the **top-level PR comment collection** and requires exact nonce, expected publisher principal, unedited body, exact repository/PR/BASE/HEAD/policy/context identity and valid structured result. It records comment id/body digest/created/updated metadata.

Final gate queries the **complete collection again**, requires `matching-comment count == 1`, same accepted id/author/body digest/metadata, and then **re-fetches that sole exact comment**. A **late duplicate**, edit, deletion or **author mismatch** invalidates automatic result evidence.

The comment never self-authorizes `PASS` or merge. The development lifecycle remains the consumer/acceptance authority.

## Best current approaches

The strongest current fit is a composition of narrow primitives rather than an imported general framework:

- local single writer: accepted Stage 26.3C OS lock;
- durable prior-creation evidence: immutable exclusive-created genesis;
- mutable operation state: accepted Stage 26.3C sibling-temp/flush/fsync/replace + strict load-validation pattern;
- browser Send claim: MV3 service worker + IndexedDB unique `add(review_run_id)` transaction;
- reviewer result authority: private single-use run capability + fixed local submit procedure;
- GitHub mutation: dedicated repository-scoped GitHub App credential hidden behind an endpoint-allowlisted publisher;
- result transport: one top-level PR Conversation comment + full-set integrity rescan;
- semantic reviewer: fresh ordinary ChatGPT under project `code-review` policy;
- evaluation: Harbor only after the first honest production-like E2E.

This preserves the existing Control Plane/public-tool boundary and introduces no generic scheduler, callback bus, GitHub proxy or local database framework.

## Failure lessons

- **Prompt prohibition != deterministic least privilege.** A planner holding a broader write credential still has the forbidden authority even if instructed not to exercise it.
- **Provider permission bucket != exact action boundary.** GitHub comment creation requires a permission bucket broader than one comment, so an allowlisted local publisher is still required.
- **Lock != crash-atomic persistence.** Serializing writers cannot make an in-place JSON transition recoverable.
- **Atomic replace != prior-creation proof.** If the only mutable canonical state disappears, absence alone cannot distinguish first creation; immutable genesis is a separate invariant.
- **Durable KV != atomic claim.** `chrome.storage.local` persistence does not provide transactional compare-and-claim semantics.
- **Service-worker memory != durable ownership.** MV3 workers may terminate; globals cannot own the Send claim.
- **Committed effect + lost response is ambiguity.** A committed browser claim, clicked Send or created GitHub comment is never blindly repeated because acknowledgement was lost.
- **Checkpoint replacement is scoped.** sibling temp + flush/fsync + replace is reused only for the accepted process-crash/restart model, not promoted to power-loss durability.
- **OpenHands availability-first behavior is wrong for this gate.** Its inspected launch ledger may proceed when local claim state is corrupt/unavailable; CAP must fail closed instead.
- **Mutable remote evidence must be revalidated.** A once-valid result comment can later be edited, deleted or duplicated.
- **General persistence/credential frameworks create obligations.** SQLite/WAL, custom event logs, generic GitHub proxies and native callback buses add broader lifecycle/authority than this one bounded operation needs.

## Alternatives comparison

### Local durable operation state

| Alternative | State/crash model | Strength | Failure/maintenance cost | Decision |
|---|---|---|---|---|
| immutable exclusive-created genesis + accepted Stage 26.3C atomic checkpoint | genesis proves prior creation; mutable file uses sibling-temp/flush/fsync/replace | reuses accepted primitives and distinguishes missing mutable state | two small files and pair validation; no power-loss claim | **SELECT / REUSE_MORE** |
| **SQLite transaction** / optional WAL | DB transaction/journal recovery with UNIQUE operation key | mature ACID and relational uniqueness | new DB/schema/migrations/WAL/checkpoint owner | **REJECT for v1; reconsider if state becomes relational/multi-record** |
| **append-only journal/WAL** | replay from immutable events | rich audit/replay history | framing, checksums, torn-tail detection, replay, compaction, schema evolution | **REJECT for v1** |
| **raw/in-place JSON write** | overwrite live record | simplest code | torn/partial state and no prior-creation proof | **REJECT** |

### Browser Send ownership

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| service worker + IndexedDB transaction | durable same-origin transactional unique claim | bounded schema/transaction lifecycle needed | **SELECT / NARROW** |
| **Web Locks** + durable ledger | good live origin-scoped exclusion | lock is ephemeral and still needs a second durable store | **REJECT for v1** |
| **service-worker in-memory Set** + `chrome.storage.local` | easy | worker lifetime ephemeral; KV check/set non-atomic | **REJECT** |
| **Native Messaging** / local dispatcher | could centralize browser ownership | privileged host/transport/deployment authority expansion | **REJECT for this slice** |

### Reviewer result/GitHub authority

| Alternative | Strength | Failure/cost | Decision |
|---|---|---|---|
| reviewer directly uses connected GitHub write app/token | simple UI flow | permission bucket/actions broader than one comment; prompt-only restriction | **REJECT** |
| fixed local submit procedure + hidden dedicated GitHub App token + exact endpoint allowlist | deterministic planner authority, durable visible PR evidence | needs one project-owned publisher and bot setup | **SELECT / NARROW** |
| local-only result artifact, no GitHub comment | smallest external authority | development-side discovery/history less portable; adds local result-read contract | **DEFER as fallback design** |
| **local callback/result server** | direct transport | new ingress/auth/state owner | **REJECT for v1** |
| **user copy/paste** | already accepted manual route | human friction remains | **KEEP as fallback** |

Three materially distinct approaches are therefore compared for each new persistence/transport/authority role; no fewer-than-three exception is used.

## Source-code evidence

### Chat Agent Platform accepted Stage 26.3C

```text
repository = BogdanAIP/chat-agent-platform
exact ref = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
research date = 2026-08-31
classification = OPEN_IMPLEMENTED (project accepted implementation)
lesson = ADAPT_MECHANIC / REUSE_COMPONENT within project lineage
```

Inspected symbols/files:

- `runtime/control_plane/_verified_workspace_artifact_support.py`: `_TaskLock`, `_acquire_task_lock`, `_exclusive_create_file`, `_write_checkpoint`, `_load_checkpoint`, `_validate_resume_state`;
- `tests/test_stage26_3c_workspace_hard_crash.py`;
- `tests/test_stage26_3c_checkpoint_progress_validation.py`;
- `tests/test_stage26_3c_checkpoint_identity_validation.py`.

Execution path followed: stable task identity -> OS lock -> strict retained-state validation -> exclusive consequence/create mechanics or sibling-temp full checkpoint write -> flush/fsync -> `os.replace` -> reconciliation from canonical state. Mapping: reuse lock, exclusive-create genesis and atomic checkpoint mechanics, but not file-artifact-specific effect authority.

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

Execution path: task/trial -> one agent run -> output sync/artifact collection -> verifier -> result. The exact CAP fresh ordinary-Chat/result-publication lifecycle was **NOT_FOUND_AFTER_TARGETED_SEARCH**; Harbor remains evaluation-only.

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

Execution path: allocate/reserve thread identity -> start/store -> child/fork or resume from persisted rollout -> resume retains original identity. A complete public mechanism matching `fresh ordinary ChatGPT -> CAP evidence -> bounded result submission` was **NOT_FOUND_AFTER_TARGETED_SEARCH**, so Codex remains `REFERENCE_ONLY`.

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

Execution path: validate action -> `claimToolCall(parentConversationId, toolCallId)` before network launch -> create child -> report result. The replay test calls the same tool-call id twice and asserts one creation. CAP adapts claim-before-effect but rejects availability-first behavior when claim state is corrupt/unavailable.

## Failure/Crash Matrix

Every row names authoritative durable state, possible physical state, fresh evidence, retry/reconciliation permission and the shield that must falsify an unsafe implementation.

| Boundary / failure | Authoritative durable state | Possible physical state | Required fresh evidence | Retry / reconciliation permission | Invariant / shield / test | Max unauthorized additional effect |
|---|---|---|---|---|---|---:|
| malformed/missing exact launch identity | none | no operation state/effect | fresh live PR + schema validation | no retry until corrected immutable request | fixed-schema negatives | 0 effects |
| two concurrent local callers before genesis | operation OS lock | one winner, competitor alive | lock result + genesis/state/temp inspection | loser performs no create/nonce/launch | concurrent first-caller barrier | 0 extra launches |
| crash before genesis file is created | genesis/state absent | no browser launch | locked scan proves genesis/state/temp absent | clean first creation allowed | hard-crash-before-genesis-create | 0 effects |
| crash during exclusive genesis write | genesis may be partial/corrupt; state absent | no browser launch | strict genesis reload/validation | existing invalid genesis fails closed; never overwrite | genesis-write fault injection | 0 launches |
| genesis write/fsync failure | no valid genesis | no browser launch | exclusive-create result + strict reload | no automatic overwrite/retry if file exists; manual recovery | genesis persistence fault test | 0 launches |
| valid genesis but canonical state missing | immutable genesis proves prior creation | historical launch has not/has potentially progressed only if state was externally lost | locked genesis/state/temp inspection | **no automatic canonical recreation, no new nonce**; manual recovery | genesis-with-missing-state disappearance test | 0 launches |
| canonical state exists but genesis missing | canonical is untrusted because genesis invariant broken | historical state unknown | locked pair validation | fail closed; no launch | missing-genesis test | 0 launches |
| genesis/canonical identity or nonce mismatch | both files untrusted as a pair | historical effect unknown | strict pair validation | fail closed/manual recovery | pair-mismatch tests | 0 launches |
| crash during prepared-state temp write | valid genesis; canonical absent or old valid state; temp may exist | no browser launch by ordering | locked pair + temp scan | ambiguous temp with missing canonical -> manual only | temp-residue fault injection | 0 launches |
| prepared-state write/flush/fsync/replace failure | valid genesis + prior canonical or no canonical; temp may remain | no browser launch | persistence error + locked reload | no launch; ambiguous state manual only | persistence-step fault injection | 0 launches |
| canonical corrupt/schema/identity mismatch | valid genesis + invalid canonical bytes | historical effect unknown | strict pair/schema/state validation | never recreate/reset automatically | corrupt-record tests | 0 launches |
| valid canonical + sibling temp residue | valid genesis + valid canonical authority | stale temp may remain | strict pair validation + temp enumeration | follow canonical state only; temp never consumed | canonical-plus-temp test | 0 duplicate launches |
| crash after prepared state but before dispatch-attempted | genesis + canonical `prepared` same run id | external browser launch cannot have occurred by ordering | locked pair validation | same nonce may make one dispatch transition | crash-before-dispatch test | <=1 total launch |
| **crash/persistence failure while replacing dispatch-attempted checkpoint** | valid genesis + old `prepared` or new `dispatch-attempted`; temp may remain | browser launch only if replacement returned success | locked pair reload + temp scan + persistence result | valid prepared may attempt transition once; dispatch-attempted never relaunches; ambiguity manual only | **replacement fault injection** | <=1 total launch |
| dispatch-attempted durable then crash before/during browser open | genesis + canonical `dispatch-attempted` | browser may be unopened/opened/delivery unknown | locked state + optional browser diagnosis | no automatic relaunch | crash-after-dispatch test | 0 extra launches |
| existing `/c/...` route receives payload | dispatch-attempted; no browser claim | existing conversation visible | fresh route/root/composer observation | refuse claim/Send; manual fresh-review path | route refusal physical/DOM test | 0 Sends |
| claim schema/store missing/version mismatch | no trusted browser claim state | no Send | service-worker DB validation | no claim-time create/upgrade | schema/version negatives | 0 Sends |
| claim transaction aborts before commit | no committed claim | no Send authority | transaction result | no automatic Send; manual fallback | transaction-abort test | 0 Sends |
| two tabs request same run concurrently | one IndexedDB primary-key claim may commit | two prepared tabs | both transaction results + claim row | exactly one grant; loser never retries automatically | deterministic barrier + **two-real-tab physical gate** | **0 extra Sends** |
| claim commits but response lost/tab dies | durable claim exists | zero or one Send attempt | fresh claim-store/tab evidence | no regrant/reclaim; **manual fallback** | lost-response/tab-death test | 0 extra Sends |
| Send click/transport ambiguous | dispatch-attempted + durable claim | message may/may not be sent | fresh conversation/result evidence if obtainable | no automatic redelivery | ambiguous-Send physical test | 0 extra Sends |
| reviewer sees mutation-capable GitHub app/action or raw GitHub token | qualification invariant violated | forbidden GitHub mutations are technically possible | fresh tool/app inventory + credential boundary evidence | abort automatic review; no submission/publication | negative authority-surface physical test | 0 GitHub mutations |
| submit call has wrong/guessed/stale run id | private operation state does not match | no GitHub POST | locked genesis/state lookup + result identity validation | reject; no retry with guessed identity | submission-auth negative tests | 0 GitHub mutations |
| first valid submit reaches local procedure | state `open` -> durable `publication-attempted` with result digest | no comment yet before external POST | locked pair + structured result validation | consumes automatic submit authority before POST | single-use submission test | <=1 comment attempt |
| publisher asked for wrong repo/pr/method/path/body shape | publication-attempted; no allowed request | no GitHub mutation | deterministic allowlist validation | reject; never fall through to generic client | endpoint/method/path negative tests | 0 GitHub mutations |
| GitHub App token has broader provider permission bucket | token remains backend-only | publisher could technically call more endpoints only if code exposed them | code-path/allowlist tests + credential non-exposure evidence | no generic request API exists; only exact comment POST admitted | publisher authority test | 0 unauthorized GitHub mutations |
| result-comment POST returns ambiguous/crash after dispatch | durable `publication-attempted` + result digest | zero or one expected-bot comment may exist | complete top-level PR comment scan | **no automatic second POST**; reconcile evidence or manual fallback | API ambiguity/crash integration test | 0 extra comment attempts |
| valid POST returns success | publication-attempted then optional `published` receipt/comment id | one expected-bot comment exists | exact response + full comment scan | no second submit/publication | one-comment success test | 0 extra comments |
| malformed/wrong-author/edited/stale result comment | remote evidence non-authoritative | comment exists | parse + publisher author + metadata + exact refs | reject; explicit fresh review only | result-validation tests | 0 merge authority |
| valid result followed by **late duplicate**/edit/delete | accepted id/digest recorded | remote set changed | **full comment-set rescan** over all pages + sole-id re-fetch + live PR identity | fail closed; no merge | late-duplicate/edit/delete tests | 0 merge authority |
| live BASE/HEAD moves | retained result bound to old refs | PR points elsewhere | fresh PR identity | mark stale; new immutable review required | stale-head integration test | 0 stale merge authority |
| hostile/non-cooperating deletion of entire genesis+state root | no surviving local proof | history can be lost | outside declared v1 process-crash/cooperating-runner scope | no guarantee claimed; requires separate hardening/research | scope assertion test | no false guarantee |
| Harbor unavailable during evaluation | production review state unaffected | benchmark absent/failed | harness status | retry evaluation only | evaluation isolation test | 0 production effects |

No release-critical cell is left `unknown` within the declared cooperating process-crash/restart scope. Machine/power-loss durability, storage rollback and hostile deletion of the whole private state root remain outside the claimed guarantee.

## Fit to this architecture

The selected composition preserves current authority layers instead of importing a new agent runtime:

```text
fresh ordinary ChatGPT reviewer       -> semantic judgment / findings; no GitHub write credential
project code-review policy            -> exact review protocol + falsification
procedure_run launch                   -> bounded launch consequence
Stage 26.3C OS lock                   -> local live single-writer ownership
exclusive-created genesis             -> durable prior-creation evidence
Stage 26.3C checkpoint pattern        -> local mutable crash-safe operation state
MV3 service worker + IndexedDB        -> browser Send ownership only
procedure_run submit                  -> one-shot result submission capability
project-owned GitHub publisher        -> exact allowlisted comment POST only
GitHub PR comment                     -> mutable result transport evidence
development lifecycle                 -> result disposition + final live-ref/merge gate
Harbor                                -> evaluation only, not production
```

The reviewer does not hold a credential that can mutate GitHub. The publisher does hold the minimum provider permission needed to create a comment, but it is not a generic GitHub client: its code surface is deterministically constrained to the exact repository/PR/comment endpoint and body generated from validated `REVIEW_RESULT_V1`.

This architecture does **not** add a second planner, general scheduler/event bus, generic GitHub proxy, general browser database runtime, local callback service or broad native-host ingress.

## Reviewer evaluation method

Reviewer quality and automation reliability remain separate planes.

### Plane A — reviewer semantic quality

Measure benchmark-native precision/recall/F1/decision accuracy, false approve/reject behavior, revision resolution and signal/noise as applicable.

### Plane B — lifecycle reliability

Measure fresh-context success, exact-head binding, stale rejection, duplicate suppression, deterministic authority-surface enforcement, timeout/failure disposition, malformed/wrong-author/edited-result rejection, human interventions, wall time and cost where measurable.

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

1. fixed `launch_independent_review_v1` and `submit_independent_review_result_v1` schemas only; arbitrary URL/prompt/command/GitHub request rejected;
2. deterministic operation key + immutable genesis + one durable high-entropy `review_run_id`;
3. `review_run_id` is not returned to the development caller and is consumed as one-shot automatic submission authority before external publication;
4. OS lock acquired before genesis/state inspection or creation and no unlocked fallback;
5. genesis uses `_exclusive_create_file`-style exclusive create + `flush` + `os.fsync`, is strictly validated and is never automatically overwritten/deleted;
6. mutable operation writes use sibling-temp + `flush` + `os.fsync` + `os.replace`;
7. genesis-with-missing-state, state-with-missing-genesis, identity/nonce mismatch, invalid canonical and ambiguous temp residue all fail closed without new nonce;
8. `dispatch-attempted` replacement succeeds before browser launch; persistence failure produces no launch;
9. hard-crash tests cover before/during/after genesis creation, mutable checkpoint replacement and dispatch marker;
10. MV3 service worker is sole Send-claim owner and claim-time DB upgrade/recreation is forbidden;
11. deterministic concurrency test proves one IndexedDB committed grant;
12. **two real same-run tabs released concurrently prove exactly one service-worker IndexedDB claim grant and exactly one Send click**;
13. committed-claim/lost-response and tab-death cases do not re-grant;
14. fresh automatic reviewer context has no raw GitHub write credential and no selected mutation-capable GitHub app/action; approval prompts are not accepted as enforcement;
15. `submit_independent_review_result_v1` validates exact operation/result identity, persists `publication-attempted` before GitHub POST and rejects second/wrong/stale submissions;
16. dedicated GitHub App credential remains backend-only, repository-scoped/minimum-permission and short-lived where supported;
17. publisher has no generic HTTP/GitHub/GraphQL mutation surface and permits only `POST /repos/<exact owner>/<exact repo>/issues/<exact pr>/comments` with validated result body;
18. negative tests prove branch/file/review/label/merge/settings/comment-edit/delete/arbitrary-repo/arbitrary-endpoint mutations unreachable through automatic reviewer path;
19. ambiguous publication causes no automatic second POST;
20. stale/malformed/wrong-author/edited/duplicate result comments reject;
21. final gate rescans all top-level comments and **re-fetches that sole exact comment** after `matching-comment count == 1`;
22. existing public semantic tool surface remains unchanged; the new behavior is registered procedures/admission behind `procedure_run`;
23. no generic scheduler/event bus, generic GitHub proxy, general browser database/storage dispatcher, Native Messaging result bus or automatic developer wake is reachable;
24. mandatory fresh ordinary-Chat review + exact-head CI remain required;
25. target-Windows ordinary-Chat physical E2E proves zero routine launch/paste/result-copy intervention plus authority/genesis/crash/stale/duplicate negative cases fail closed.

## Architecture decision

**NARROW — proposed by this Brief; effective only after this PR is accepted and merged.**

If accepted, implementation authority is limited to:

```text
exact frozen review identity
 -> registered bounded procedure_run launcher
 -> Stage 26.3C OS-backed single-writer lock
 -> immutable exclusive-created genesis + private review_run_id
 -> Stage 26.3C crash-atomic mutable checkpoint
 -> durable dispatch-attempted before one browser launch
 -> fresh-root ChatGPT deep-link/autosend
 -> MV3 service-worker IndexedDB unique-key Send claim
 -> exactly one automatic Send attempt
 -> fresh ordinary-Chat reviewer with no GitHub write credential/action
 -> one fixed submit_independent_review_result_v1 call using private single-use run capability
 -> durable publication-attempted before external mutation
 -> project-owned allowlisted publisher with backend-only dedicated GitHub App credential
 -> at most one exact top-level PR result-comment POST
 -> complete-comment-set + live exact-ref validation
 -> manual fallback after ambiguity
```

After the first real E2E, the thin Harbor/ReviewBench/SWE-Review-Bench/CR-Bench evaluation seam may be added without granting benchmark infrastructure production authority.

Any requirement for a recurring/general scheduler, automatic developer wake, new public tool, arbitrary launcher, generic GitHub proxy/client exposed to Chat, reviewer-held GitHub write credential, new local DB/lease framework, general browser database runtime, Native Messaging/local result bus, blind retry after ambiguity, broader reviewer mutation authority, machine/power-loss transactional guarantee, worker rotation or multi-agent runtime invalidates this decision and requires Stage Research re-entry.

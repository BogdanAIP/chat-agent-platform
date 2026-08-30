# Automatic Independent Reviewer — Stage Research Brief

Status: **STAGE RESEARCH — NARROW**

This record governs the first production slice of automatic independent semantic review after accepted Stage 26.3C. It is deliberately narrower than general autonomous continuation, a generic scheduler/event bus, multi-worker orchestration, or a standalone review product.

Research baseline at entry:

```text
main = b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
Stage 26.3C declared production/restart scope = accepted / closed
PR #138 = experiment-only launch evidence
public Chat-facing surface = six canonical semantic tools
required primary semantic review = fresh ordinary ChatGPT
```

Exact upstream/source refs below are research evidence for this Brief, not dependency pins or live-state ownership.

## Goal

Remove routine user launch/copy-paste work from the repository's already-required independent review gate without weakening review independence or silently creating a general autonomous-agent scheduler.

The first production lifecycle is bounded to:

```text
review-ready PR exact head
 -> immutable REVIEW_REQUEST_V1
 -> one automatic launch attempt into a fresh ordinary-ChatGPT conversation
 -> independent repository review under code-review skill
 -> structured REVIEW_RESULT_V1
 -> one bounded result-evidence publication
 -> development lifecycle re-resolves the result + live PR identity
 -> accept CURRENT result or fail closed as stale/malformed/ambiguous
```

The user may still return to / resume the development conversation after review completion. Automatically waking and continuing that unfinished development conversation is explicitly outside this slice and remains a separate future same-task-continuation research seam.

## Non-goals

This Brief does **not** authorize:

- a recurring generic task scheduler;
- polling arbitrary GitHub events for arbitrary work;
- general `WAITING -> wake -> planner continuation` semantics;
- worker rotation or an Agent Session runtime;
- automatic same-run relaunch after ambiguous browser delivery;
- a second planner;
- a new public shell/Python/local-execution capability;
- automatic approval/merge by the reviewer;
- reviewer branch edits, labels, review approvals, requested-changes state or repository-setting changes;
- adopting Harbor as production runtime infrastructure;
- tuning the production reviewer directly against the complete public benchmark set;
- treating benchmark score as authorization or as a substitute for repository acceptance gates;
- extracting a standalone reviewer product in this stage.

## Problem evidence

The required review protocol already works, but the routine path has manual friction:

```text
development chat freezes exact refs
 -> user opens a fresh ordinary ChatGPT conversation
 -> user pastes REVIEW_REQUEST_V1
 -> reviewer performs independent semantic review
 -> user copies REVIEW_RESULT_V1 back
 -> development chat validates findings / exact identity
```

PR #139 made removal of this launch/result-handoff friction the current release-critical assurance task.

PR #138 physically demonstrated a narrower experimental route:

```text
one-shot local launch
 -> fresh run-id-bound ChatGPT deep link
 -> tiny content script validates URL/composer contract
 -> one bounded Send
```

The experiment proved useful mechanics but did not establish a production reviewer lifecycle, durable duplicate suppression, exact result handoff, stale-result rejection, or general scheduler authority.

## Current implementation evidence

### Existing six-tool / procedure boundary

`project-context/STAGE26_3A_PROCEDURE_RUN_SURFACE.md`, current `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs` and `runtime/control_plane/cli.py` show that the project already has one typed public `procedure_run` tool whose schemas admit only registered procedures. It does not expose arbitrary command/path/backend dispatch.

At the research baseline, the semantic projection registers bounded procedure schemas and the Python Control Plane CLI dispatches only known procedure IDs. This is the correct existing project-owned extension point for a bounded launch consequence; adding a seventh public tool or a generic launcher dispatcher would duplicate/erode the accepted surface.

### PR #138 deep-link/autosend experiment

The experimental `scripts/launch-chatgpt-deeplink-autosend.ps1` constructs a run-bound `chatgpt.com` URL and uses normal Windows shell URL launch. The experimental content script checks the URL contract, exact composer payload and Send readiness, writes an attempt ledger before the click, and refuses duplicate delivery within its experimental storage scope.

Production use needs stronger freshness and duplicate guarantees than that experiment:

- refuse delivery from an existing `/c/...` conversation route; the launch must begin from the new-chat/root route selected by the reviewed launcher;
- replace page/session-scoped duplicate state with extension-owned durable cross-tab state;
- write the extension attempt marker before Send;
- do not automatically retry after an attempted/ambiguous Send;
- bind both the local dispatch record and extension ledger to the exact automatic-review operation.

Chrome's current extension documentation states that content scripts run in an isolated world by default and that `chrome.storage.local` is extension-owned persistent local storage cleared when the extension is removed. Chrome explicitly recommends extension storage instead of page Web Storage for extension state because content-script Web Storage belongs to the host page. These properties fit a defense-in-depth duplicate-delivery ledger better than the experiment's page/session state.

Sources:

- https://developer.chrome.com/docs/extensions/reference/manifest/content-scripts
- https://developer.chrome.com/docs/extensions/reference/api/storage
- https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies

The authoritative automatic launch-at-most-once boundary remains the local durable launch record. Extension storage is a second cross-tab/browser-side guard, not a substitute for local operation ownership.

## Source-code revalidation

### Harbor

Revalidated source repository:

```text
repository = harbor-framework/harbor
ref = 389bd4f8ce796ef4a97de4b62675021e262c8e76
```

Inspected:

- `src/harbor/agents/base.py` — custom external-agent abstraction;
- `src/harbor/trial/single_step.py` — bounded environment/agent/verifier trial lifecycle and timeout/error collection;
- `src/harbor/models/agent/context.py` — agent context, rollout metadata, token/cost fields.

Conclusion: Harbor can host a thin custom CAP-reviewer evaluation adapter without modifying Harbor itself. That adapter is an **evaluation boundary only**. Harbor does not become production launch/correlation/authorization infrastructure.

### openai/codex

Current source reference revalidated at:

```text
repository = openai/codex
ref = 94cbbddafc1776d5e377bca1b05932c697e82238
```

The existing `CODEX_AGENT_HOST_SOURCE_REVIEW.md` lineage remains useful for thread/session lifecycle and explicit ownership comparisons. No complete public automatic wake/scheduler path satisfying this review lifecycle was located in the current targeted source recheck. Codex remains optional review evidence and a reference implementation, not the mandatory reviewer or selected launcher.

### OpenHands

Independent mature harness reference revalidated at:

```text
repository = OpenHands/OpenHands
ref = 1098d73df42351a31b2940557efb9fe8750365c4
```

Inspected:

- `src/services/child-conversation-launch.ts` — explicit child-conversation launch, bounded startup wait, parent/child record, and duplicate-launch claim logic;
- `src/api/agent-server-adapter.ts` — explicit conversation/status/runtime-service identity.

Useful lesson: OpenHands explicitly recognizes duplicate child launch/replay as a real lifecycle hazard. Its inspected client-side claim path intentionally proceeds when its local ledger is unavailable/corrupt, accepting replay risk over never launching. That availability-first tradeoff is **not** acceptable for this repository's required review gate. The selected CAP path remains fail-closed on ambiguous duplicate state.

## Architecture lineage comparison

| Role | Prior/source candidate | Decision | Reason |
|---|---|---|---|
| General planning / semantic review | ordinary ChatGPT | **KEEP** | Existing required reviewer remains fresh ordinary ChatGPT; automation must not substitute another planner/model/service. |
| Review protocol / exact identity / falsification | project `code-review` skill | **KEEP / REFINE AUTOMATIC ENVELOPE ONLY** | Accepted semantic-review protocol remains authoritative; automatic path adds bounded correlation/result-publication semantics without weakening falsification or exact-ref rules. |
| Chat reachability | current ChatGPT product/browser session | **KEEP** | No custom public ingress is required for reviewer evidence. |
| Bounded local launch consequence | canonical `procedure_run` registered-procedure boundary | **REUSE_MORE / NARROW** | Use one fixed `launch_independent_review_v1` procedure rather than a seventh tool or arbitrary launcher. Procedure input is exact review identity only, not arbitrary prompt/URL/command. |
| Deep-link + one bounded Send | PR #138 launcher/content-script experiment | **REFINE** | Keep the proved minimal browser mechanics; add fresh-route proof and extension-owned durable cross-tab attempt state; remove experiment-only `Chat Local Bridge Test` dependency from the reviewer prompt. |
| Windows Task Scheduler | existing supervisor use + #138 one-shot experiment | **DEFER for v1 reviewer** | Immediate review launch does not require a timer. Adding a scheduler owner would widen lifecycle scope without solving a current requirement. |
| ChatGPT Scheduled Tasks | product feature | **DEFER** | One-time task capability exists, but current evidence does not prove the exact ordinary-Chat isolation + GitHub tool contract required here; event-triggered product paths may require Work, which cannot substitute for the mandatory review. |
| Result handoff | GitHub top-level PR conversation comment | **REFINE / SELECT** | Reuses the review object's durable discussion channel; no local port/native host/result bus. Comment is treated as mutable transport evidence and must pass author/run-id/edit/duplicate/final-ref checks before acceptance. |
| Development continuation after result | current user-driven development conversation | **KEEP MANUAL / DEFER AUTOMATIC WAKE** | Result publication removes copy/paste; automatically resampling/waking the unfinished developer task is a separate future mechanism. |
| Duplicate/retry/reconciliation semantics | project stable operation identity / fail-closed recovery principles | **REUSE_MORE** | Exact review operation identity is durable; ambiguous dispatch/Send is not permission for blind redelivery. |
| Review evaluation harness | Harbor custom-agent/task/verifier interfaces | **REUSE_MORE / EVALUATION ONLY** | Avoid building a benchmark runner; custom CAP adapter can bridge frozen tasks to the reviewer evaluation path without making Harbor production authority. |
| Optional second reviewer | Codex Review | **KEEP OPTIONAL** | Useful independent signal when quota exists; never required for merge and never substitutes for fresh ordinary ChatGPT. |
| General scheduler/event bus/worker runtime | ADR-037 / future Track M concepts | **REJECT for this slice** | Current problem does not justify the authority/scope. |

## Selected production-v1 lifecycle

### 1. Freeze and call the bounded launcher

The development context first resolves the intended exact PR identity under the existing merge policy.

The caller-visible launch procedure accepts only the core immutable review identity:

```text
procedure = launch_independent_review_v1
repository = <owner/repo>
pr_number = <number>
base_sha = <40-hex>
head_sha = <40-hex>
review_skill = code-review
review_skill_version = <version>
```

It must not accept arbitrary prompt text, arbitrary URL, shell/command/backend selection, review findings, or developer correctness arguments.

The procedure derives the fixed reviewer instruction and ChatGPT launch URL from the typed review identity.

### 2. Stable operation key + private review nonce

Two identities are intentionally separate:

```text
review_operation_key
  deterministic from exact repository / PR / BASE / HEAD / review-skill identity
  local lifecycle ownership / duplicate suppression key

review_run_id
  high-entropy random nonce generated exactly once for that operation record
  durable local correlation value
  reused when the same operation is queried again
  not published to the PR before the result comment
```

The local procedure durably creates/loads the exact operation record and its once-generated `review_run_id` before external launch.

This avoids using a predictable public exact-head hash as the only result correlation secret. A public commenter who only knows the PR/base/head cannot preemptively fabricate the expected automatic result without the locally held nonce.

The actual reviewer receives:

```text
REVIEW_REQUEST_V1
repository=<owner/repo>
pr_number=<number>
base_sha=<40-hex>
head_sha=<40-hex>
review_skill=code-review
review_skill_version=<version>
review_run_id=<locally generated automatic-run nonce>
```

`review_run_id` is required only for the automatic path and does not replace repository/PR/base/head identity. Manual fallback remains valid under the existing core request contract.

### 3. Write-before-dispatch / no automatic ambiguous retry

The local launch record must transition to an irreversible automatic-dispatch-attempted state **before** invoking the OS/browser launch consequence.

Consequences:

- crash before durable dispatch-attempted state -> no external launch has been authorized; exact local state may permit the first attempt later;
- once dispatch-attempted is durable -> a repeated procedure invocation returns the existing run state / nonce and does not launch another Chat automatically;
- if the process/browser launch failed after the durable mark, v1 prefers manual fresh-review fallback over a duplicate automatic conversation;
- browser/transport failure after Send is always ambiguous delivery and never authorizes blind redelivery.

The content script also writes an extension-owned `chrome.storage.local` attempt marker before Send. This protects against duplicate tabs/browser-side replay for the same run, but the local durable record remains the primary operation owner.

### 4. Fresh ordinary-Chat proof boundary

The production content script must only dispatch from the expected new-chat/root route created by the launcher. An existing conversation route is not a valid launch target.

The request carries no development reasoning, suspected findings or correctness argument. The reviewer independently resolves GitHub evidence and returns `ABSTAIN` if fresh-context/evidence conditions cannot be established.

### 5. Reviewer authority

During semantic review the reviewer remains read-only to production code/branch/repository configuration.

The only new write allowed by the automatic-review protocol is **one top-level PR conversation comment** containing the structured result for the matching `review_run_id`. It must not:

- edit files/branches;
- submit APPROVE/REQUEST_CHANGES review state;
- change labels/assignees/milestones;
- merge/close/reopen the PR;
- change repository settings;
- patch findings itself.

This publication is result-evidence transport, not acceptance authority.

The automatic lifecycle has a configured expected GitHub result principal (for the current project, the account through which the ordinary-Chat GitHub connector is expected to publish). The development side rejects a matching-looking result from any other author. The exact configuration mechanism is implementation detail, but it may not be supplied by untrusted PR/page content.

### 6. Structured result publication and immutable-consumption check

The automatic result comment contains the normal `REVIEW_RESULT_V1` identity/result plus matching `review_run_id`.

GitHub conversation comments are treated as **mutable transport records**, not intrinsically immutable acceptance evidence. The development side accepts a result only after independently checking:

```text
exactly one matching result comment exists
comment.author == configured expected result principal
comment was not edited after creation
result.repository / pr / base / head == frozen request
result.review_run_id == locally expected run nonce
result.review_policy_ref == BASE_SHA
result.review_context == ordinary_chat_fresh
result status/validity/count fields parse under current contract
live PR base/head still match the reviewed identity when CURRENT is consumed
```

The development lifecycle records the accepted comment id + body digest/observed metadata for the final merge gate, then re-fetches that same comment before merge. Missing/deleted/edited/body-changed result evidence invalidates the automatic result and requires a safe fallback/fresh review.

Do not publish the automatic `review_run_id` in a public REVIEW_REQUEST comment before the reviewer result. The immutable core review identity may still be recorded publicly without the private automatic-run nonce when useful for audit.

Any second result comment carrying the same expected `review_run_id` is duplicate/ambiguous evidence, **even when its body is identical**. The automatic path fails closed rather than guessing which comment represents the one permitted publication. This is intentionally stricter than trying to infer idempotency from equal text because GitHub comment creation does not provide this protocol with an end-to-end idempotency key.

### 7. No hidden automatic developer continuation

Completion of the reviewer run does not automatically wake/replan/continue the unfinished development conversation in v1.

The GitHub result removes copy/paste. A user may return to the development conversation, which then reads the PR result itself. A future mechanism that proactively resamples the development planner must go through the separate same-task-continuation Stage Research seam.

## Failure / crash matrix

| Boundary / failure | Required behavior | Unauthorized duplicate/effect budget |
|---|---|---:|
| request missing exact repo/PR/base/head/skill/version | do not launch; ABSTAIN/error | 0 launches |
| arbitrary prompt/URL/command supplied to launch procedure | schema rejects; no browser launch | 0 launches |
| first exact operation record creation | generate one high-entropy `review_run_id`, persist before launch | 0 premature public effects |
| same exact automatic launch requested again before/after dispatch mark | return existing run state/nonce; never create a second automatic launch | 0 extra launches |
| crash before durable dispatch-attempted mark | no launch authorized; exact state may permit the first attempt | <= 1 total launch |
| crash/failure after durable dispatch-attempted mark but before browser actually opens | no automatic retry; manual fresh-review fallback | 0 extra launches |
| browser opens existing `/c/...` conversation | content script refuses Send | 0 Sends |
| extension duplicate ledger missing/corrupt/ambiguous | fail closed; no automatic Send; manual fallback | 0 Sends |
| same run appears in multiple tabs | extension/local run guards permit at most one automatic Send attempt | 0 extra Sends |
| browser/transport error after Send click | outcome ambiguous; do not auto-redeliver | 0 additional Sends |
| ChatGPT/tool/reviewer times out with no result | mark timeout operationally; manual fresh-review path | 0 automatic relaunches |
| reviewer cannot prove fresh ordinary context/evidence | publish/return ABSTAIN when possible; no PASS inference | 0 branch effects |
| arbitrary public commenter guesses repo/head but not private run nonce | result does not match expected `review_run_id`; reject | 0 merge authority |
| result author differs from configured expected principal | reject | 0 merge authority |
| reviewer posts malformed result | reject | 0 merge authority |
| reviewer result comment is edited after creation | reject automatic result | 0 merge authority |
| accepted result comment disappears/changes before merge | final re-fetch invalidates it; fresh/manual review required | 0 stale merges |
| reviewer posts result for stale head | retain only as historical evidence; reject as CURRENT | 0 merge authority |
| head moves after valid PASS but before merge | final identity gate rejects old result; fresh review required | 0 stale merges |
| any second matching result comment for same run | duplicate/ambiguous -> fail closed/manual fresh review | 0 merge authority |
| reviewer attempts branch/approval/config mutation | protocol violation; automatic result unacceptable; investigate | 0 accepted review authority |
| Codex quota exhausted | no effect on mandatory review; continue with ChatGPT path | 0 false evidence |
| Harbor unavailable | production reviewer unaffected; evaluation deferred/retried separately | 0 production effects |

No release-critical cell in the selected v1 review lifecycle is intentionally assigned blind automatic retry.

## Evaluation architecture — Harbor is not production authority

Harbor is selected as the **evaluation harness**, not as the reviewer launch/control plane.

A thin `Harbor -> CAP reviewer` adapter should be added only after the first production E2E reviewer exists. The adapter may transform Harbor's frozen task environment into a bounded reviewer-evidence input and return structured findings to Harbor's verifier. It must not force production GitHub lifecycle semantics into benchmark tasks or force benchmark-specific shortcuts into the production reviewer.

The evaluation must distinguish two planes.

### Plane A — reviewer semantic quality

Minimum durable metrics:

| Metric | Meaning |
|---|---|
| Precision | fraction of emitted findings that are valid |
| Coverage / Recall | fraction of known defects found |
| F1 | balance of coverage and precision |
| Decision Accuracy (DA) | correct approve/reject decision rate |
| False Approve Rate (FAR) | defective PRs incorrectly approved |
| False Reject Rate (FRR) | correct PRs incorrectly rejected |
| Resolve Rate after Revision (RRR) | whether review feedback enables actual repair |

### Plane B — CAP reviewer lifecycle reliability

Minimum durable metrics:

| Metric | Meaning |
|---|---|
| Launch success | fresh-review launch/delivery succeeded |
| Fresh-context proof | run satisfied the production freshness contract |
| Exact-head binding | request/result/live identity agreement |
| Stale rejection | stale result was never consumed as current |
| Duplicate suppression/rate | duplicate launch/result evidence and safe disposition |
| Timeout/failure disposition | bounded failure outcome, no blind rerun |
| Malformed-result rejection | parser/gate fails closed |
| Result-author/integrity rejection | wrong-author/edited/deleted result cannot authorize acceptance |
| Human interventions | routine manual actions needed per completed review |
| Wall time | elapsed time per completed review |
| Cost | measured when applicable; no paid infrastructure is assumed/required |

Do not collapse these planes into one score. A reviewer can improve semantic quality while lifecycle reliability regresses, or automation can improve while reviewer quality degrades.

## Benchmark plan

### First baseline — ReviewBench

ReviewBench is the preferred first semantic baseline because it is small enough for frequent iteration and already uses Harbor tasks.

Current primary source reports:

```text
59 tasks
64 curated baseline issues
frozen PR context
full seeded repository
Harbor task format
coverage + precision + F1
```

Primary source:

- https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench

ReviewBench compares the substantive underlying defect/code path rather than requiring wording identity. That is compatible with this project's falsification-first review philosophy.

### Larger control — SWE-Review-Bench

Use a bounded subset first, then larger runs for significant reviewer revisions.

Current benchmark source reports:

```text
1,384 AI-generated PRs
500 SWE-bench Verified issues
three patch-quality tiers
CR / DA / FAR / FRR / RRR
```

Primary source:

- https://github.com/SWE-Lego/SWE-Review/tree/main/SWE-Review-Bench

This is comparative evidence, not the sole release truth. Its SWE-bench lineage and task construction must be considered when interpreting results.

### Signal/noise control — CR-Bench / CR-Evaluator

CR-Bench is retained specifically because it makes false positives and signal-to-noise visible rather than rewarding issue volume alone.

Primary source:

- https://arxiv.org/abs/2603.11078

### Deferred breadth

Do not add all current review benchmarks to the first implementation. Keep these as later evaluation candidates after the initial ReviewBench/SWE-Review-Bench/CR-Bench loop is stable:

- MCR-Bench — multi-round defect-state review, 2,269 tasks across five languages: https://arxiv.org/abs/2608.27442
- AACR-Bench — holistic repository-level/multilingual context: https://arxiv.org/abs/2601.19494
- CodeFuse-CR-Bench / similar repository-level suites as later comparative breadth when they add a measured gap.

Decision for these in this slice: **DEFER**.

## Benchmark anti-overfit rule

Do not repeatedly inspect and tune against the complete public benchmark while treating the same examples as independent evidence.

Use three evidence classes:

```text
development set
  -> failures may be inspected and used to improve review strategy/skill

holdout set
  -> examples/results are not used for iterative prompt/skill tuning
  -> run at controlled checkpoints

CAP Review Regression Set
  -> real repository review defect classes from accepted PR history
  -> protects transfer back to actual project behavior
```

The CAP regression set may include defect classes such as stale exact-head evidence, contradictory document owners, provenance/Finish Gate mistakes, retry/reconciliation ambiguity and concrete false-positive reviewer candidates, but it must preserve the underlying defect class rather than encode the exact previous answer.

Benchmark-derived rules may enter `.agents/skills/code-review/SKILL.md` only when they express a general review invariant that also survives repository-level reasoning/falsification. Never add benchmark-specific filename/task hacks.

## Baseline before threshold

The first benchmark run is a **baseline, not a release exam**.

Do not invent an arbitrary target such as `F1 >= 0.80` before measuring the current reviewer under the selected harness. First measure:

1. current accepted `code-review` skill;
2. selected comparison reviewers where legally/operationally available under the same task evidence;
3. lifecycle metrics for the actual production automatic-review path.

Only then set evidence-based acceptance targets.

The automatic reviewer is not accepted merely because launch/result plumbing works. Semantic quality must not materially regress versus the current manual fresh ordinary-Chat reviewer process/control baseline. Conversely, benchmark quality cannot excuse stale/duplicate/ambiguous lifecycle failures.

## Harbor adapter seam

After the first production E2E reviewer is physically proven, implement a thin evaluation adapter against Harbor's public custom-agent interface.

The adapter should:

```text
Harbor frozen task / environment
 -> bounded CAP reviewer evidence adapter
 -> reviewer strategy / code-review skill
 -> structured findings
 -> Harbor verifier
```

It should not:

- grant Harbor production GitHub authority;
- require a live GitHub PR when the benchmark intentionally provides a frozen local stub;
- edit benchmark ground truth;
- silently change the production review strategy to fit one verifier;
- become a scheduler for ordinary CAP tasks.

Exact Harbor source inspected for this Brief:

- `harbor-framework/harbor@389bd4f8ce796ef4a97de4b62675021e262c8e76`
- `src/harbor/agents/base.py`
- `src/harbor/trial/single_step.py`
- `src/harbor/models/agent/context.py`

## Acceptance shields

### Deterministic / hosted shields before physical qualification

Tests must cover at least:

1. launch procedure schema contains only exact review identity; arbitrary URL/prompt/command rejected;
2. deterministic exact-review operation key plus once-generated high-entropy `review_run_id` persisted before launch;
3. repeated same-head invocation returns the existing run record/nonce and cannot produce a second automatic launch;
4. durable dispatch-attempted state is written before OS/browser launch and prevents automatic retry after uncertainty;
5. content script refuses an existing conversation route;
6. extension-owned ledger is written before Send and provides cross-tab/browser-side duplicate protection for the accepted scope;
7. missing/corrupt/ambiguous local or extension launch state fails closed;
8. malformed/missing/mismatched/wrong-author/edited result comment rejects;
9. any second matching result comment for the same run rejects as duplicate/ambiguous;
10. stale base/head result rejects;
11. accepted result comment id/body is re-fetched unchanged at final merge gate;
12. reviewer result publication cannot alter branch/review approval/labels/settings through the accepted protocol;
13. manual fresh-review fallback remains valid and Codex remains optional;
14. existing six-tool public inventory/runtime semantics remain unchanged except for the explicitly registered launch procedure behind `procedure_run`;
15. no generic scheduler/event bus/shell/Python/URL launcher is reachable from the new procedure.

### Physical ordinary-Chat gate

The production reviewer is not accepted until a target-Windows ordinary-Chat qualification proves, on frozen exact source/install/runtime bytes where applicable:

```text
one development-side automatic launch request
 -> no user opens/pastes the review request into a second chat
 -> a genuinely new ordinary-ChatGPT conversation receives exactly the immutable request + private run nonce
 -> reviewer independently reconstructs GitHub evidence
 -> reviewer returns a valid REVIEW_RESULT_V1 for the frozen head
 -> exactly one permitted result-evidence comment is published by the expected principal
 -> comment is unedited and carries the expected private run nonce
 -> development side reads it from GitHub without user copy/paste
 -> live PR identity + comment identity/body are independently rechecked
 -> stale/duplicate/edited/wrong-author/timeout negative cases fail closed
```

The gate must separately record whether the user had to intervene. Routine launch/paste/result-copy intervention must be zero for the successful path.

### Quality gate

After the first physically working E2E exists:

1. run ReviewBench baseline through the Harbor evaluation seam;
2. run a bounded SWE-Review-Bench subset and CR-Bench/CR-Evaluator comparison where practical;
3. record semantic metrics separately from lifecycle metrics;
4. establish an evidence-based target relative to the current/manual reviewer and comparison systems;
5. do not call automatic review accepted as stable development infrastructure if automation materially degrades review quality merely to remove UI friction.

The benchmark quality gate can mature after the first plumbing E2E, but it must be completed before the project treats the automatic reviewer as a stable replacement for the manual primary-review workflow.

## Stage decision

**NARROW.**

Production implementation may begin only for the bounded independent-review lifecycle described here:

```text
exact frozen review identity
 -> registered bounded launch procedure
 -> durable exact-operation record + private review nonce
 -> refined fresh-chat deep-link/autosend
 -> one automatic Send attempt
 -> fresh ordinary-Chat reviewer
 -> one structured top-level PR result comment by expected principal
 -> development-side run/comment/exact-ref validation
 -> manual fallback on ambiguous/failed automatic run
```

Allowed evaluation work after the first production E2E:

```text
Harbor custom-agent adapter
 -> ReviewBench baseline
 -> bounded SWE-Review-Bench / CR-Bench comparisons
 -> dev/holdout + CAP regression loop
```

Any material introduction of the following invalidates this implementation authority and requires Stage Research re-entry:

- recurring/general scheduler or GitHub event watcher;
- automatic wake/resampling of the unfinished development planner;
- Native Messaging/local callback server as production result transport;
- new public tool instead of registered `procedure_run` schema;
- automatic retry after ambiguous dispatch/Send;
- reviewer code/branch/approval mutation authority;
- generic benchmark-driven production tool authority;
- worker rotation/multi-agent runtime;
- broader result bus/event architecture.

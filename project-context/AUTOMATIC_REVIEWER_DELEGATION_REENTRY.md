# Automatic Reviewer -> Generic Delegation Re-entry

Status: **STAGE RESEARCH — NARROW**

Original research date: 2026-09-16.  
Security-boundary re-entry: 2026-09-21.

## Stage question

What is the smallest production change that lets the existing automatic independent-review consumer reuse the already accepted generic Delegation lifecycle and the qualified `chatgpt-temporary` adapter, while preserving every reviewer-specific guarantee and without turning Temporary Chat into a general CAP task mode?

The product policy for this slice is:

```text
ordinary CAP task
 -> ordinary ChatGPT
 -> canonical six-tool semantic route

independent code review only
 -> reviewer policy/state
 -> generic Delegation lifecycle
 -> chatgpt-temporary
 -> fresh isolated reviewer
 -> validated REVIEW_RESULT_V1
```

## Current project truth

Accepted mechanisms already present on `main`:

- reviewer-specific exact repository / PR / BASE / HEAD identity;
- reviewer immutable genesis, private `review_run_id`, durable dispatch/result state, manual fallback and stale-result fencing;
- fixed `launch_independent_review_v1`, `submit_independent_review_result_v1` and `reconcile_independent_review_result_v1` public procedures;
- provider-independent Delegation identity/state with no-blind-launch/no-blind-Send semantics;
- qualified `chatgpt-temporary` one-shot fresh read-only worker adapter;
- authenticated loopback controller, exact runtime-attestation checks, durable one-delivery claim and structured `WORKER_RESULT_V1` capture.

Current production gap:

`run_launch_independent_review()` intentionally returns `ABSTAIN / reviewer_authority_unqualified` and never starts a browser worker.

The current `launch-chatgpt-temporary-worker.ps1` is a qualification harness, not a production reviewer owner. It waits in the foreground for a terminal worker result and writes qualification artifacts.

The installed manager bundle currently contains reviewer state/procedures but does **not** install the generic Delegation/Temporary runtime family or the Temporary extension/controller assets required for production reuse.

## Current external product evidence

Current official OpenAI Temporary Chat documentation states that a non-personalized Temporary Chat does not use memories, custom instructions or plugins. Personalized Temporary Chat can use them. Therefore reviewer isolation must positively prove the **non-personalized** mode and no-plugin state rather than infer isolation from the word "temporary".

Current references:

- https://help.openai.com/en/articles/8914046-temporary-chat-faq
- https://help.openai.com/en/articles/11509118

The existing CAP adapter already requires `personalization_disabled=true` and an empty plugin marker set before worker binding. That remains the selected reviewer isolation evidence.

Temporary Chat product behavior is a closed provider boundary; the official product
documentation and target-browser qualification remain the applicable evidence for
that behavior. The generic Agent Session / Delegation and reviewer worker lifecycle
also trigger `source-code-research` v1.0, independently of which provider is used.
The original decision omitted the required source-code cohort. See the 2026-09-26
research re-entry below: the earlier NARROW decisions alone were incomplete
implementation authority for this migration.

## Architecture lineage decisions

| Role | Prior owner/source | Decision | Reason |
|---|---|---|---|
| Reviewer exact identity/result policy | reviewer-specific #140-#142 state | **KEEP** | Exact PR/BASE/HEAD, `REVIEW_RESULT_V1`, stale handling and manual fallback are specialist semantics. |
| Generic worker lifecycle | project Delegation state | **REUSE_MORE** | Do not duplicate launch/delivery/result identity in reviewer state. |
| Fresh reviewer browser transport | `chatgpt-temporary` | **REFINE** | Restrict the concrete adapter to reviewer use; preserve generic Delegation below it. |
| Transport Supervisor | existing transport-only supervisor | **REJECT for this role** | Its accepted contract explicitly says it is not a generic process manager. |
| Generic scheduler/event bus | none | **REJECT** | No recurring/background orchestration requirement exists for one review operation. |
| Persistent ChatGPT session/runtime | deferred research | **DEFER** | Reviewer needs one isolated fresh context, not a retained project chat. |
| Reviewer result storage | existing reviewer local state | **KEEP** | Already closes automatic/manual races and exact-result validation. |

## Alternatives

### A. Reuse generic Delegation + reviewer-owned one-shot background controller — SELECT / NARROW

```text
launch_independent_review_v1
 -> prepare exact reviewer operation
 -> prepare exact review task
 -> mark reviewer dispatch-attempted
 -> start one fixed reviewer-owned background worker process
 -> generic Delegation + chatgpt-temporary
 -> WORKER_RESULT_V1
 -> validate payload as REVIEW_RESULT_V1
 -> existing automatic reviewer result commit
```

The background process is operation-scoped and terminal. It is not restarted automatically. Loss or timeout leaves the reviewer operation open/pending and the existing manual fallback remains authoritative.

### B. Synchronous `procedure_run` waits for the whole review — REJECT

A review may take far longer than the normal procedure transport timeout. Keeping the semantic call open would mix long browser/session lifetime with the bounded request transport and make ordinary tunnel loss look like review ambiguity.

### C. Extend Transport Supervisor to own reviewer workers — REJECT

This would violate the supervisor's accepted transport-only scope and create a generic process-manager role without need.

### D. One-time Scheduled Task / general scheduler — REJECT for v1

A one-shot scheduler can detach work, but it introduces additional task registration/identity/cleanup semantics when a single fixed child process is sufficient. Re-enter only if direct process detachment proves unreliable on the target Windows environment.

### E. Keep reviewer-specific browser automation separate from generic Delegation — REJECT

This duplicates launch/delivery/result semantics that #149 deliberately generalized.

## Selected narrow implementation

### 1. Install the already accepted runtime assets

Extend the verified manager bundle with the exact generic Delegation/Temporary assets required by the reviewer consumer:

- `runtime/control_plane/delegation_state.py`;
- `runtime/agent_sessions/__init__.py`;
- `runtime/agent_sessions/chatgpt_temporary.py`;
- `runtime/agent_sessions/chatgpt_temporary_controller.py`;
- `runtime/agent_sessions/chatgpt_temporary_authenticated_controller.py`;
- `runtime/agent_sessions/source_attestation.py`;
- the five `chatgpt_temporary_extension/*` assets;
- one reviewer-specific fixed worker owner/launcher.

Reviewer-specific operation/result state remains under the existing procedure-runtime owner. Generic Delegation state remains under the already accepted `%LOCALAPPDATA%\ChatAgentPlatform\agent-sessions\private-state` owner; reviewer migration does not create a second Delegation store.

Installed-version provenance remains bound to the existing accepted-main update receipt. A feature checkout must not become production reviewer runtime authority.

The current narrow guarantee is **not** a signed-package or hostile-local-tamper guarantee. Bootstrap verifies source -> installed copies byte-for-byte at installation time; the updater receipt identifies the accepted-main commit installed; reviewer runtime attestation then proves that the executing MV3 bytes match the current installed AppRoot expectation. A later attacker or process with authority to modify both the installed AppRoot and its local expectation is outside this slice. Signed/package-level integrity, rollback and clean-machine distribution remain Stage 27 work and must not be falsely claimed here.

The unpacked MV3 extension also needs a stable browser installation/loading path. The existing physical qualification required loading the exact unpacked extension snapshot before the run. For this narrow pre-Stage-27 slice, production may require one explicit setup/reload of the extension from the stable installed CAP path; the reviewer runtime must still attest the executing bytes on every consequence-bearing exchange. Packaging/managed-extension distribution remains Stage 27 rather than being hidden inside reviewer launch.

### 2. Reviewer-specific task adapter

Build the review task from the immutable reviewer identity and the existing code-review contract. The generic worker uses:

```text
worker_kind=code-review
worker_profile=fresh_readonly_worker_v1
result_contract_id=review_result_v1
```

The generic lifecycle treats the payload as opaque. Reviewer-specific code validates the captured payload with the existing `parse_review_result(... automatic=True ...)` path before any reviewer result state closes.

### 3. One-shot process ownership

`launch_independent_review_v1` persists reviewer `dispatch-attempted` **before** the external worker process receives launch authority.

Then it starts exactly one fixed background reviewer worker. No caller-supplied executable, path, URL, provider or command is accepted.

No automatic relaunch is permitted after `dispatch-attempted`.

The worker:

1. starts the installed authenticated Temporary controller;
2. opens only the neutral preflight URL;
3. waits for the generic terminal result or timeout;
4. validates `WORKER_RESULT_V1` correlation;
5. if status is `COMPLETED`, validates payload as the exact automatic `REVIEW_RESULT_V1`;
6. commits through the existing reviewer result-state function;
7. exits.

`ABSTAIN`, `ERROR`, timeout, controller/browser loss or malformed payload never manufacture a successful reviewer result.

### 4. Temporary Chat remains reviewer-only

No ordinary CAP task, procedure, skill or non-review specialist route is added.

The earlier non-reviewer physical qualification remains evidence that generic Delegation itself is specialist-independent, not authorization to use the concrete Temporary adapter as a general product mode.

## Failure / crash matrix

| Boundary | Durable state | Possible physical state | Required behavior |
|---|---|---|---|
| before reviewer genesis | none | no worker | safe retry |
| reviewer prepared, before dispatch mark | prepared/open | no worker | one initial launch may still be authorized |
| dispatch mark committed, process spawn fails | dispatch-attempted/open | no worker | **no auto relaunch**; pending/manual fallback |
| process starts, launch response to caller is lost | dispatch-attempted/open | controller/browser may be active | no second launch; reconcile reviewer state later |
| controller commits generic launch, then dies | reviewer dispatch-attempted + Delegation launch state | child absent/present | generic no-blind-relaunch; reviewer manual fallback if no terminal result |
| Send outcome unknown | Delegation unknown | message may have been sent | no second Send; same-delivery reconciliation only |
| generic result recorded, reviewer bridge crashes before reviewer commit | Delegation terminal; reviewer open | valid payload may exist | fixed bridge may resume/read same terminal result and perform **result commit only**, never launch/Send again |
| reviewer automatic result commits, bridge response is lost | reviewer automatic-result-recorded | worker exits/unknown | repeat same result is reconciliation only |
| manual fallback wins before automatic reviewer commit | manual-fallback-recorded | late generic result may exist | automatic reviewer commit rejected |
| BASE/HEAD moves | old exact reviewer identity | review result may exist | existing stale policy blocks merge |
| complete browser/service-worker loss | generic state preserved | no live monitor authority | no reconstruction/relaunch; pending/manual fallback |

The only permitted post-crash automatic recovery is **terminal-result settlement** from an already recorded generic Delegation result into the still-open exact reviewer result slot. It grants no new browser launch or Send authority.

## Acceptance

### Deterministic / hosted

- installed bundle contains and verifies every required Delegation/Temporary/reviewer-worker asset;
- normal six-tool public inventory remains exactly unchanged;
- `chatgpt-temporary` has no non-review production entry point;
- reviewer task -> Delegation identity is deterministic and exact-ref bound;
- reviewer dispatch is durable before child process start;
- a second launch call after dispatch is rejected without spawning;
- process-spawn failure produces no relaunch authority;
- generic wrong delegation/delivery/contract result cannot close reviewer state;
- generic `ABSTAIN/ERROR` cannot become reviewer PASS/FINDINGS;
- valid generic COMPLETED payload must pass existing automatic `REVIEW_RESULT_V1` validation before reviewer commit;
- manual-fallback/late-automatic race remains closed by existing reviewer lock/state;
- already-recorded generic result can settle reviewer state after bridge restart without a new launch or Send;
- no arbitrary process/path/URL/provider/backend argument is added to `procedure_run`.

### Physical target-Windows gate

Pre-merge physical acceptance uses the existing exact-HEAD Temporary-worker qualification mechanics with a reviewer-specific task/result adapter so the PR branch is never mislabeled as installed accepted `main`. The production public launch remains fixed to the installed accepted-main bundle and is covered deterministically before merge; the first post-merge installed-main reviewer run must additionally confirm the same product path on the accepted commit.

The exact-head reviewer qualification must prove:

```text
reviewer qualification prepare
 -> no manual new-chat opening
 -> one non-personalized Temporary Chat reviewer
 -> plugin/app markers absent
 -> exactly one task Send
 -> reviewer independently reads the public target PR
 -> exact REVIEW_RESULT_V1 payload captured
 -> reviewer local state automatic-result-recorded
 -> reconcile_independent_review_result_v1 returns the same exact result
```

The qualification may require the operator to load/reload the exact unpacked reviewer extension from the path emitted by the existing exact-head launcher. It must never require a manual Send or manual result copy/paste.

Negative physical gate:

- force/observe unavailable reviewer isolation or browser/controller loss;
- prove no second Temporary Chat / no second Send;
- reviewer remains pending or requires manual fallback.

A fresh exact-head manual semantic review remains required for the PR that introduces this mechanism; the mechanism cannot bootstrap its own acceptance before merge.

## Decision

**NARROW**

Implement only:

1. installed Delegation/Temporary reviewer assets;
2. one reviewer-specific task adapter;
3. one operation-scoped background reviewer owner;
4. generic terminal-result -> existing reviewer-state settlement;
5. deterministic tests and one target-Windows physical E2E.

Do not implement persistent sessions, general worker scheduling, automatic parent wake, worker pools, generic provider framework, new public tools, GitHub mutation authority or general Temporary-Chat task routing.


## 2026-09-21 capability-location / browser-handoff re-entry

### Re-entry trigger

Fresh independent review of exact HEAD `bcd5c8ea8c413e69ecc6b3b66c075e6b2ec0b0ff`
exposed a failure class that the 2026-09-16 matrix did not cover: a reviewer task
contains the private `review_run_id`, and the selected provider adapter embedded the
entire `WORKER_TASK_V1` prompt in the ChatGPT navigation URL. Later URL cleanup
therefore occurred after the private reviewer capability had already crossed the
browser URL/history/navigation boundary.

The same review also exposed adjacent capability-location questions for qualification
artifacts, generic Delegation persistence and FilesRoot physical aliases. Those
filesystem/state placements were narrowed into already existing project-owned private
state roots; they did not create a new state owner. This re-entry covers the whole
discovered capability-location class before further production changes.

### Updated stage question

How should the accepted reviewer-specific private capability and the generic worker
prompt cross the provider-browser boundary without entering URLs, public metadata or
new durable browser storage, while preserving the already accepted one-owner /
one-Send / fail-closed Temporary Chat lifecycle?

### Current baseline and lineage

No role assignment from `ARCHITECTURE_REUSE_BASELINE.md` changes:

| Role | Existing owner | Re-entry decision |
|---|---|---|
| Reviewer exact identity/result capability | reviewer-specific local state | **KEEP** |
| Delegation lifecycle/private run capability | project `delegation_state` | **KEEP / REUSE_MORE** |
| First-provider browser launch/delivery ownership | project MV3 service worker + authenticated controller | **REFINE** |
| Browser URL/history | provider/browser transport only | **REJECT as capability store** |
| Durable prompt/capability cache in extension storage | none | **REJECT** |

The affected baseline browser-delivery role already says the live MV3 mapping is
ephemeral and loss of that owner fails closed. This re-entry refines what may be kept
in that live mapping; it does not add a persistent-session role or move authority out
of the Control Plane.

### Architecture primitives and adjacent domains

The refined design relies only on mechanisms already present in the selected adapter:

- opaque live `launch_handle` bound to one owner tab;
- authenticated loopback controller response;
- MV3 service-worker/content-script message passing;
- exact prompt digest/correlation;
- existing durable one-Send IndexedDB claim.

The new invariant is a **capability-location rule**, not a new persistence primitive:
the capability-bearing worker prompt may exist in protected local manager/delegation
state, an authenticated live extension handoff, the live composer, and the submitted
reviewer turn, but never in a navigation URL, browser-history projection, public
metadata or logs intentionally emitted by CAP.

Adjacent domains are bearer-capability handling, browser URL/referrer exposure,
extension trust boundaries and MV3 service-worker lifetime.

### Problem evidence

Repository evidence:

- `build_review_worker_task()` includes private `review_run_id`;
- `build_worker_prompt()` embeds that reviewer task verbatim;
- the previous task launch encoded the complete prompt as `?prompt=...`;
- the content script navigated with `location.replace(task_url)` and sanitized only
  after task navigation.

External mechanism evidence:

- RFC 6750 section 2.3/5 states that bearer credentials in URI query parameters are
  not recommended because URLs are likely to be logged and can survive in browser
  history and other data structures:
  https://www.rfc-editor.org/rfc/rfc6750.html
- MDN's Referrer-Policy security guidance notes that URL parameters can contain
  sensitive information and may be exposed through referrer behavior:
  https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/Referrer_policy
- Chrome documents extension message passing as the supported communication path
  between content scripts and the extension service worker, and explicitly warns
  that content scripts are less trustworthy and that data sent to them may leak to
  the web page. This is why the private prompt is withheld until the destination
  page has positively proved the required isolated Temporary profile:
  https://developer.chrome.com/docs/extensions/develop/concepts/messaging
- Chrome documents that MV3 service-worker global variables can disappear on
  termination. For this adapter that is a useful fail-closed boundary for live
  launch capability material, not a reason to persist the prompt:
  https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle

### Solution evidence and alternatives

#### A. Keep `?prompt=<worker task>` and sanitize immediately — REJECT

It preserves provider auto-fill mechanics but violates the new capability-location
invariant before cleanup can run. `replaceState` cannot retroactively prevent prior
URL/history/log observation.

#### B. Authenticated controller -> live MV3 owner -> content-script handoff — SELECT

The neutral preflight remains the only browser entry opened by PowerShell. The
authenticated controller returns the exact prompt and digest to the already attested
MV3 service worker, but the task navigation URL contains only non-secret correlation
metadata plus the opaque live `launch_handle`.

After navigation, the task content script first proves the empty target context is
fresh, Temporary, non-personalized and no-plugin using the existing positive provider
evidence. Only after that proof may it request the prompt from the same live owner.
The service worker must require:

- exact launch handle;
- exact delegation/delivery/task/prompt/head correlation;
- the exact original owner tab;
- the exact capability-free task-navigation URL shape for that live owner;
- an unconsumed prompt handoff.

The content script then recomputes `prompt_sha256`, validates the exact worker-task
markers and re-proves the isolated profile immediately before any DOM population.
Only an empty composer may receive the prompt. Immediately before Send it repeats the
positive Temporary/non-personalized/no-plugin qualification again and then obtains the
existing durable browser Send claim. Thus a wrong/personalized/unqualified page never
receives the private reviewer task at all.

This reuses the existing provider adapter and does not create another authority owner.

#### C. Persist the prompt in `chrome.storage` / IndexedDB for navigation recovery — REJECT

Chrome recommends storage when extension state must survive service-worker
termination, but persistence is the wrong guarantee for this authority artifact.
Persisting the reviewer capability-bearing prompt would introduce another durable
secret owner plus cleanup, replay, stale-generation and local-read exposure. The
accepted adapter already defines complete live-owner loss as fail closed.

#### D. Give the content script the private controller `run_id` and fetch the prompt directly — REJECT

This would widen the private Delegation capability into the renderer/content-script
boundary and undo the accepted opaque-`launch_handle` separation.

Fewer than three credible safe delivery designs were not assumed; four materially
different approaches were considered above.

### Capability storage / FilesRoot alias refinement

The same capability-location invariant applies before the browser handoff. The
September 21 review/fix sequence identified three concrete local placements:

- reviewer qualification capability artifacts:
  `%LOCALAPPDATA%\\ChatAgentPlatform\\state\\automatic-reviewer-qualification`;
- generic Temporary-worker qualification copies:
  `%LOCALAPPDATA%\\ChatAgentPlatform\\state\\agent-session-q`;
- accepted generic Delegation durable private state:
  `%LOCALAPPDATA%\\ChatAgentPlatform\\agent-sessions\\private-state`.

The first two are qualification-only material under the already protected manager
state hierarchy. The third remains under the already accepted Delegation persistence
owner rather than being moved merely for path uniformity.

For FilesRoot selection, lexical string comparison is insufficient on Windows because
a junction/symlink or a not-yet-created child can refer into a protected physical
tree. The selected rule is therefore physical/potential-path normalization followed
by **bidirectional overlap rejection**: a candidate FilesRoot is rejected if it is
the protected root itself, a descendant of it, or an ancestor that would expose it.

Material alternatives considered for this local-state part of the same failure class:

#### E. Leave qualification artifacts in their historical public-ish sibling roots — REJECT

That makes capability safety depend on every future FilesRoot caller remembering
special subdirectories and repeats the failure already observed by review.

#### F. Put qualification artifacts under manager state; retain Delegation private-state owner and protect both lifetime roots — SELECT

This reuses the existing state owners, requires no migration of accepted Delegation
persistence, and lets both the semantic launcher and legacy profile launcher enforce
the same disjointness property for current and future children.

#### G. Move generic Delegation persistence under manager state solely to obtain one root — REJECT

That would change an accepted persistence owner and migration/recovery boundary
without a correctness need. Path protection can provide the same isolation without
architecture churn.

Additional filesystem/alias failure cells:

| Boundary | Candidate / physical state | Required behavior |
|---|---|---|
| qualification output requested outside private manager state | no capability artifact yet | reject **before** reviewer genesis/task write |
| FilesRoot equals a protected root | exact private tree | reject |
| FilesRoot is a child of a protected root | direct private descendant | reject |
| FilesRoot is an ancestor of a protected root | would expose private subtree transitively | reject |
| FilesRoot is a symlink/junction alias into a protected root | lexical path appears disjoint; physical path overlaps | resolve physical target and reject |
| requested protected child does not yet exist | nearest existing ancestor + remaining path | resolve potential physical path and reject overlap before later creation |
| generic terminal Delegation result contains `REVIEW_RESULT_V1` / private `review_run_id` | durable `agent-sessions\\private-state` | keep under Delegation owner but lifetime-protect from FilesRoot |
| qualification copied task contains reviewer nonce | durable qualification evidence | keep only under manager state; never expose through supported FilesRoot |

These cells do not introduce a new filesystem sandbox primitive. They refine the
existing manager/semantic FilesRoot boundary so every capability-bearing placement is
covered by one explicit physical-overlap invariant.

### Updated failure / crash matrix

| Boundary | Capability location | Physical state | Required behavior |
|---|---|---|---|
| before authenticated preflight | protected local state only | neutral tab | no prompt/capability in URL |
| controller returns handoff, before commit | controller + live MV3 memory | neutral tab | exact owner/correlation only; retry same preflight is allowed while launch remains prepared |
| launch committed, before task navigation | live MV3 memory; durable launch-attempted | neutral tab | MV3 loss fails closed; no relaunch / no Send |
| task URL created/navigated | **no reviewer capability/prompt in URL** | one task tab | URL may contain only bounded public correlations + opaque live handle |
| after navigation, before prompt handoff | live MV3 memory | empty task composer | positively prove fresh Temporary/non-personalized/no-plugin state; wrong UI/tab/handle/correlation/task URL or lost owner => no prompt, no Send |
| prompt handoff to content script | live extension/content memory | already-qualified empty composer | one-shot owner-bound handoff; recompute digest + exact structural validation; re-prove isolation before DOM mutation |
| profile changes or composer becomes non-empty before population | prompt only in isolated extension/content memory | unsafe target DOM | fail closed; do not write prompt into DOM and never request Send authority |
| exact prompt visible, before Send claim | live composer | previously qualified Temporary UI | re-prove current isolation state before obtaining Send authority |
| browser claim/controller authority denied | live composer | no Send | stop; no second prompt handoff / no second Send |
| Send committed/visible | submitted reviewer turn | provider conversation | existing delivery/result lifecycle applies |
| MV3/browser loss at any pre-Send point after launch commit | protected durable state + possibly page | ambiguous/lost live owner | no reconstruction from durable prompt cache; pending/manual fallback |

All release-critical cells have a defined fail-closed outcome. No cell requires a
second launch or second Send.

### Failure shields / acceptance additions

Before this re-entry can be accepted, deterministic tests must prove with a known
private reviewer nonce that:

1. neither the neutral preflight URL nor the task navigation URL contains the nonce
   or the worker prompt;
2. the task URL contains no `prompt` query parameter at all;
3. an unqualified/personalized/non-Temporary page receives no prompt handoff at all;
4. the MV3 prompt handoff is exact-owner-tab, exact-handle, exact-task-URL,
   exact-correlation and one-shot/fail-closed;
5. the content script rejects a digest mismatch, a profile change after handoff and
   a non-empty unrelated composer before any prompt DOM population;
6. successful population still requires exact visible-composer equality and another
   positive isolation check before requesting Send authority;
7. no CAP URL/log/public metadata projection intentionally contains the private
   reviewer nonce;
8. service-worker/live-owner loss before Send produces no reconstruction, second
   navigation or second Send.

The existing target-Windows physical gate must additionally prove that the new
non-URL composer population works against the real ChatGPT UI and still produces
exactly one Send.

### Re-entry decision

**NARROW**

Proceed only with the provider-specific handoff refinement above and the already
identified private-state/FilesRoot guards. Do not add durable prompt storage,
persistent browser/session recovery, a generic secret broker, a new public semantic
tool, a new provider framework, or any second-launch recovery path.

This decision supersedes the 2026-09-16 browser task-delivery detail that allowed the
worker prompt in the task URL. All other scope limits of the original NARROW decision
remain in force.

## 2026-09-26 source-code-research gate re-entry

### Trigger, baseline and chronological limit

Fresh ordinary-Chat review of PR #159 at BASE
`24ed938c587c9d3e2288c92bc156ccc476c955f3` and HEAD
`78e28983eea3a184ee87bfc28356e19bf0fd22c6` found that this Brief
expressly skipped `.agents/skills/source-code-research/SKILL.md` v1.0. That
skill was already present on BASE. `AGENTS.md` requires both it and
`.agents/skills/stage-research/SKILL.md` v1.2 for production changes to worker
lifecycles, identity, recovery and authority, with a fail-closed gate when a
required output is missing. The earlier #159 NARROW decisions were therefore
insufficient to authorize acceptance of the production migration. This is a
fresh research decision **after** the implementation, not a claim that the
missing evidence existed before implementation; release/physical acceptance
remains blocked until this re-entry and a fresh exact-head independent review.

Live comparison point on 2026-09-26: accepted `main` at
`24ed938c587c9d3e2288c92bc156ccc476c955f3`, PR #159 at the HEAD above,
and the role assignments in `ARCHITECTURE_REUSE_BASELINE.md`. The baseline
assigns provider-independent delegation, exact reviewer closure and CAP
Control Plane authority to the project; Codex is a source-code reference,
not a runtime dependency; the first Temporary adapter is reviewer-only.
Earlier pinned research in `AGENT_SESSION_DELEGATION_REENTRY.md` and
`AUTOMATIC_REVIEWER_RESEARCH.md` informs this check but does not substitute
for rechecking the current implementation and recording evidence in this Brief.

### Problem evidence

The reviewed `run_launch_independent_review()` moves from the accepted
reviewer-only state/procedure foundation to a production background worker
using `delegation_state` and `chatgpt-temporary`. It persists reviewer
`dispatch-attempted` before starting that worker; its output may later cross
generic result storage into reviewer result state. A restart, lost browser
owner, duplicate delivery or manual/automatic race can therefore change
whether another effect is allowed. The original documentation's opt-out
failed to examine public implementations of those same lifecycle roles.
The 2026-09-21 URL/capability fix addresses a separate exposure class and
does not cure this omitted source-code gate.

### Source-code evidence

Research date: **2026-09-26**. The two external refs below were resolved to
exact commits and the named files refetched at those commits. These are
comparison sources, not proposed CAP dependencies or claims about private
ChatGPT implementation.

#### `openai/codex` — parent/child lifecycle reference

- Repository/ref: [`openai/codex@e72da2b53805894878023d01949a25a082e0a5cb`](https://github.com/openai/codex/tree/e72da2b53805894878023d01949a25a082e0a5cb).
- Inspected [`spawn.rs`](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs) (`spawn_agent`), [`wait.rs`](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/core/src/tools/handlers/multi_agents/wait.rs) (`wait_agent`), [`agent/control.rs`](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/core/src/agent/control.rs) (`prepare_thread_spawn_source`, `persist_thread_spawn_edge_for_source`) and [`thread_manager_tests.rs`](https://github.com/openai/codex/blob/e72da2b53805894878023d01949a25a082e0a5cb/codex-rs/core/src/thread_manager_tests.rs) (`live_fork_keeps_instructions_when_source_is_unloaded_during_setup`).
- Execution path: spawn computes and bounds child depth, prepares child
  configuration, and passes explicit caller/parent/root turn identity to
  `agent_control.spawn`. Control records `SubAgentSource::ThreadSpawn` with
  parent and depth; non-ephemeral child graph-edge persistence is attempted
  when a graph store exists, but persistence failure emits a warning rather
  than making the spawn impossible. Wait subscribes to status, reads the
  first status or subsequent updates, and bounds the wait. Inherited
  environments/exec policy also depend on parent/child configuration.
- Test/history limit: the inspected thread-manager test exercises a live
  fork while the source unloads; it is not proof of durable terminal status
  after restart. Public issue
  [#34220](https://github.com/openai/codex/issues/34220) reports a completed
  descendant reloaded as `PendingInit` and a subsequent wait missing its
  completion; [#38144](https://github.com/openai/codex/issues/38144) reports
  parent active-writer friction after fork. These are reported failure
  histories, not a claim that the inspected current commit reproduces them.
- Classification: `OPEN_IMPLEMENTED` for parent/depth/source and live wait;
  `OPEN_PARTIAL` as a reference for **guaranteed** durable child-result
  recovery, because the inspected spawn-edge persistence is best effort and
  the inspected wait/test do not establish that guarantee. Lesson:
  `REFERENCE_ONLY` for explicit child correlation; `REJECT_MECHANIC` for
  treating a live agent status subscription as CAP's durable reviewer
  result or inheriting a parent's broader execution policy.
- CAP mapping: `delegation_state` owns immutable identity, durable launch /
  delivery / terminal result; `independent_review_state` alone owns reviewer
  result/fallback. No Codex thread, tool, planner or status stream gets CAP
  consequence or independent-review acceptance authority. The corresponding
  shield is existing lost-worker / no-relaunch and terminal-result-only
  reconciliation coverage plus the pending target-Windows failure gate.

#### `OpenHands/OpenHands` — independently implemented child launch

- Repository/ref: [`OpenHands/OpenHands@47a10808d78561546a02555d0d2c7fa96fa96300`](https://github.com/OpenHands/OpenHands/tree/47a10808d78561546a02555d0d2c7fa96fa96300).
- Inspected [`src/services/child-conversation-launch.ts`](https://github.com/OpenHands/OpenHands/blob/47a10808d78561546a02555d0d2c7fa96fa96300/src/services/child-conversation-launch.ts) (`claimToolCall`, `launchLocalChild`) and [`__tests__/services/child-conversation-launch.test.ts`](https://github.com/OpenHands/OpenHands/blob/47a10808d78561546a02555d0d2c7fa96fa96300/__tests__/services/child-conversation-launch.test.ts) (`ignores a replayed tool call`, worktree/shared fallback tests).
- Execution/state path: the browser ledger checks a parent/tool-call key
  and writes it to `localStorage` before creating the child. The replay
  test observes one child creation and one parent message for the same
  tool call with working storage. Corrupt/unavailable/full storage instead
  resets or skips that claim and **continues**, accepting replay risk.
  `launchLocalChild` also switches from worktree to a shared workspace when
  parent metadata cannot host a worktree or worktree creation fails; its
  tests cover that fallback. The inspected tests do not establish an atomic
  cross-tab browser claim or fail-closed behavior when storage fails.
- Classification: `OPEN_IMPLEMENTED` for child launch, browser-ledger
  replay suppression on the tested path and workspace fallback;
  `NOT_FOUND_AFTER_TARGETED_SEARCH` for a storage-unavailable fail-closed
  test in the inspected child-launch tests (not a repository-wide absence
  claim). Lessons: `ADAPT_MECHANIC` for claim-before-external-effect and
  explicit parent link; `REJECT_MECHANIC` for accepting duplicate-launch
  risk on storage failure and silently weakening isolation to shared space.
- CAP mapping: reviewer dispatch plus generic `mark_launch_attempted`
  remain the only project launch authority; `chatgpt-temporary` uses a
  durable IndexedDB same-delivery unique claim before Send. An unavailable
  claim, lost MV3 owner, ambiguous Send or unsuitable isolated reviewer
  profile must fail closed and leave pending/manual fallback. The shields
  are existing duplicate-launch, same-delivery claim, profile isolation
  and negative physical tests. OpenHands's browser, workspace and agent
  authority never become CAP's owner.

#### CAP at the reviewed exact HEAD — selected owner, not external proof

- Repository/ref: [`BogdanAIP/chat-agent-platform@78e28983eea3a184ee87bfc28356e19bf0fd22c6`](https://github.com/BogdanAIP/chat-agent-platform/tree/78e28983eea3a184ee87bfc28356e19bf0fd22c6).
- Inspected `runtime/control_plane/independent_review_procedures.py`
  (`run_launch_independent_review`, `_settle_delegated_result`),
  `independent_review_delegation.py` (`review_delegation_identity`,
  `settle_review_from_delegation`, `spawn_review_worker`),
  `automatic_review_worker.py` (`_run`), `delegation_state.py`
  (`prepare_delegation`, `mark_launch_attempted`, `claim_delivery`,
  `record_worker_result`) and `independent_review_state.py`
  (`mark_dispatch_attempted`, `submit_independent_review_result`,
  `reconcile_independent_review_result`).
- Execution/state path: the fixed launch prepares exact reviewer identity
  and generic Delegation, marks reviewer dispatch before the one background
  process, and declines a second launch once dispatched. The worker
  revalidates installed runtime, runs the authenticated controller,
  receives generic `WORKER_RESULT_V1` in private Delegation storage,
  checks exact `REVIEW_RESULT_V1` identity/run capability, and submits
  through fixed `submit_independent_review_result_v1`. Reconciliation
  may settle an already recorded generic terminal result, with no new
  launch or Send. Reviewer state fences a manual fallback winner.
- Tests inspected: `tests/test_delegation_state.py`,
  `tests/test_independent_review_state_concurrency.py`,
  `tests/test_automatic_review_worker_contract.py`, and
  `tests/test_chatgpt_temporary_prompt_fail_closed_runtime.py` cover
  state transitions/races, fixed procedure wiring and browser refusal
  paths. Hosted green checks establish deterministic behavior only;
  required exact-head Windows/ChatGPT operation is still unproved.
- Classification: `OPEN_IMPLEMENTED` for the candidate production code;
  **physical reviewer acceptance pending**. Lessons: `REUSE_COMPONENT`
  for already accepted CAP Delegation/Temporary mechanics, `KEEP` reviewer
  result authority in its existing state/procedures. Neither external
  implementation establishes CAP's closed Temporary Chat UI behavior;
  official product documentation and physical isolation proof remain
  necessary. The two inspected external source repositories cannot prove
  closed ChatGPT Temporary provider internals; that provider boundary is
  `CLOSED_OR_UNKNOWN` from public source.

### Solution evidence, alternatives and failure shields

The existing CAP write ordering and private capability locations directly
answer the two important source-code failure classes: no attempt to infer
a durable reviewer result from live worker status (Codex comparison), and
no acceptance of a duplicate launch/Send when browser claim storage is
unavailable (OpenHands comparison). The earlier decision's alternatives
remain distinct: **A** reuse CAP Delegation and a bounded reviewer owner;
**B** synchronous long-running procedure; **C** repurpose Transport
Supervisor; **D** schedule a one-off task; **E** duplicate reviewer-specific
browser lifecycle. In light of the source comparison, importing either
upstream agent controller would add another planner/authority model and
still require CAP-specific reviewer closure, so it does not replace A.
No new role is assigned to either upstream system and no baseline lineage
changes. Persistent sessions, broad tool inheritance and a general
scheduler remain outside the narrowed reviewer slice.

| Boundary reassessed from source | CAP authoritative state | Ambiguous physical state | Retry/reconcile rule and shield |
|---|---|---|---|
| child status disappears after worker/controller restart | generic result may be recorded, reviewer result may remain open | prior worker may have run or completed | read exact recorded generic terminal result and submit through fixed reviewer procedure only; never launch/Send from status; existing result-settlement tests plus Windows loss case |
| reviewer dispatch is marked, process creation/ack fails | reviewer `dispatch-attempted` | zero or one worker | no relaunch; manual fallback; existing launch-failure contract |
| browser claim store fails/corrupts or two tabs race | Delegation delivery state + extension IndexedDB claim | Send outcome zero or one/unknown | no second Send without durable same-delivery authority; existing duplicate/refusal tests plus negative physical gate |
| wrong provider profile or lost live browser owner | protected local state; no trusted live owner | isolated conversation cannot be proved | no prompt/Send, no shared-context fallback; isolation checks plus target-Windows negative test |
| generic terminal result versus manual reviewer fallback | generic result + separate reviewer slot | either closure may win | exact result/capability validation under reviewer lock, manual winner rejects late automatic result; concurrency tests |

These cells add no retry, state owner or authority beyond the existing
failure/crash matrices. No unresolved required recovery cell was identified
within the stated process-restart and reviewer-only scope. A browser or
machine experiment must still falsify this decision if it demonstrates
extra launch/Send, an unqualified context, a stale accepted result or a
worker result bypassing the fixed reviewer procedure. Deterministic tests,
hosted exact-head CI, fresh independent semantic review and the scoped
target-Windows positive/negative physical gate remain required in that
order. A documentation-only re-entry does not retroactively make earlier
implementation authorized or waive later review/physical evidence.

### Reissued architecture decision

**NARROW**

After applying `stage-research` v1.2 **and** `source-code-research` v1.0,
keep the existing reviewer-only implementation scope and lineage choices;
no code alteration, new dependency, public tool or authority expansion is
selected by this re-entry. The source comparison supports preserving CAP's
durable generic lifecycle and independent reviewer result owner with strict
failure closure. Implementation may proceed under this corrected decision,
but #159 is still unaccepted until fresh exact-head review, successful
required checks and target-Windows physical evidence close their separate
gates. Later material architecture changes require another re-entry.

## 2026-09-26 review-result single-writer re-entry

### Trigger, goal and baseline lineage

The fresh independent review of #159 at
`f538fb38da66579a37b03603f66854f9cf74646d` reported P1: the
authenticated Temporary controller durably records complete `REVIEW_RESULT_V1`
in generic Delegation state and `result.json` *before* calling the fixed
`submit_independent_review_result_v1` procedure. BASE `code-review` v1.1 §14
requires that only this procedure record the automatic result locally. The
earlier result-recovery cells in this Brief are superseded here. Goal: keep
the existing browser, Delegation and one-Send lifecycle while making the
registered reviewer procedure the first and only durable writer of the
complete review result.

Baseline roles: project-owned generic Delegation **KEEP** for identity,
launch/delivery and terminal *receipt*; `chatgpt-temporary` **REFINE** as the
first reviewer-only capture adapter; project-owned reviewer identity/result
state, registered submit and manual fallback **KEEP**. Codex and OpenHands
remain reference-only, with no planner or result authority imported. No
baseline role changes owner or remains deferred.

### Architecture primitives; problem and solution evidence

Mechanism: single authoritative result writer, followed by a constant
opaque completion receipt. Domains: transaction write ordering, filesystem
durability, idempotency and authority. Assumption: reviewer and generic
checkpoints use separate files/locks and are not one transaction. Windows
[`ReplaceFile`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)
replaces one target file; SQLite's
[`Atomic Commit`](https://www.sqlite.org/atomiccommit.html) illustrates the
additional protocol required for multi-file atomicity. We do not claim such
atomicity or introduce a coordinator, journal, retry ledger or new result
store. The generic receipt is constant non-result text; its SHA only checks
the generic checkpoint, not the reviewer result.

**Problem evidence:** `chatgpt_temporary_controller._record_result_text` calls
`record_temporary_worker_result` → `delegation_state.record_worker_result`,
then writes `result.json`. The worker/reconcile path later reads the complete
generic `result_payload` and submits it. The review finding establishes that
labeling those copies transport does not satisfy BASE §14.

**Solution evidence:** existing `independent_review_state` parses exact
identity and `review_run_id`, serializes automatic/manual races and accepts
an identical repeated submit as `already_recorded`. The authenticated
`/capture` endpoint already holds validated worker output in process memory
after browser/profile/delivery attestation. Invoking the *same registered
submit CLI* there before any generic result write leaves one durable result
owner. Reconciliation reads that canonical owner even if the process dies
before the receipt. This depends on local owner ordering and existing reviewer
locks, not on an invented cross-file transaction.

### Source-code evidence and failure lessons

Research date **2026-09-26**; exact refs and detailed execution paths appear
in the preceding Source-code evidence block. Rechecked for this new boundary:

- [`openai/codex@e72da2b53805894878023d01949a25a082e0a5cb`](https://github.com/openai/codex/tree/e72da2b53805894878023d01949a25a082e0a5cb),
  `codex-rs/core/src/tools/handlers/multi_agents/{spawn.rs,wait.rs}`,
  `agent/control.rs` and `thread_manager_tests.rs`: explicit parent/source
  on spawn, live status on wait, a live fork test; public issue
  [#34220](https://github.com/openai/codex/issues/34220) reports a finished
  descendant reloaded pending. `OPEN_IMPLEMENTED` for live lifecycle,
  `OPEN_PARTIAL` for durable terminal result recovery, `REFERENCE_ONLY`:
  CAP must consult its canonical reviewer state, not worker status.
- [`OpenHands/OpenHands@47a10808d78561546a02555d0d2c7fa96fa96300`](https://github.com/OpenHands/OpenHands/tree/47a10808d78561546a02555d0d2c7fa96fa96300),
  `src/services/child-conversation-launch.ts::claimToolCall/launchLocalChild`
  and `__tests__/services/child-conversation-launch.test.ts`: browser ledger
  claim before child launch, replay test, but storage failure continues
  without the claim. `OPEN_IMPLEMENTED` for local claim, `ADAPT_MECHANIC`
  for effect ordering, `REJECT_MECHANIC` for fail-open. CAP keeps existing
  durable one-Send claims; a receipt/lost acknowledgement cannot grant Send.
- CAP at `f538fb38da66579a37b03603f66854f9cf74646d`:
  `delegation_state.record_worker_result`,
  `chatgpt_temporary_controller._record_result_text`,
  `independent_review_delegation.settle_review_from_delegation`,
  `independent_review_procedures._submit_delegated_result_via_registered_procedure`
  and `independent_review_state.submit_independent_review_result` show the
  forbidden early write and existing idempotent final commit. Tests
  `test_automatic_reviewer_qualification_contract.py` and
  `test_independent_review_procedure_wiring.py` intentionally modeled the
  early write and must change. `OPEN_IMPLEMENTED` for candidate code;
  physical Windows/Temporary behavior is pending and provider internals
  remain `CLOSED_OR_UNKNOWN` from public code.

### Distinct alternatives

| Approach | Authority, persistence and crash boundary | Fit / cost / failure |
|---|---|---|
| A. Canonical submit at capture, then opaque generic receipt — **SELECT** | Existing reviewer procedure first; generic receipt later; reconcile canonical. | Keeps one result writer and generic terminal lifecycle. Loss before submit needs manual fallback; loss afterward recovers from reviewer state. Small specialist adapter change. |
| B. Current generic full-result checkpoint, then submit — **REJECT** | Generic state and projection first, reviewer result later. | Recovers pre-submit crashes but violates BASE §14 and preserves a second durable result transport. |
| C. One new database for reviewer and Delegation — **REJECT** | Coordinated DB transaction across both owner roles. | Could close the gap atomically, but migrates established state/locks and adds a dependency for one review path; fixed reviewer procedure still required. |
| D. Omit generic reviewer result entirely — **REJECT** | Canonical reviewer result only; Delegation remains open. | One writer, but generic worker lifecycle never becomes terminal and browser readback becomes misleading. |

### Replacement failure / crash matrix

| Boundary | Authoritative durable / possible physical state | Evidence, retry/physical effect and shield |
|---|---|---|
| Before genesis or after dispatch, before Send | Existing exact reviewer dispatch and generic delivery; child absent/present. | Existing locks and claims allow only first launch/Send; no second attempt if ambiguous. |
| During Send/after ambiguous delivery | Generic claimed/unknown; physical Send zero/one/unknown. | Same-delivery evidence only; no relaunch/second Send; existing refusal tests. |
| After authenticated capture, before submit | Reviewer open; complete result only in volatile memory. | No local raw-result checkpoint or replay; loss → pending/manual fallback; fault injection. |
| Submit rejected or manual fallback wins | Reviewer open/manual; generic result open. | No completed receipt; manual result remains authoritative; race test. |
| Submit commits, acknowledgement lost | Canonical automatic result; generic open. | Canonical reconcile, at most identical idempotent in-process submit; no new browser effect. |
| Submit commits, generic checkpoint/projection fails | Canonical automatic result; generic open/receipt, projection missing. | Read canonical after restart; do not rebuild raw result; injected failure at both writes. |
| Receipt committed; controller/worker dies | Canonical automatic result and generic receipt. | Read canonical; receipt never submits or grants Send. |
| Receipt with missing canonical; legacy full payload | Reviewer open/manual; generic terminal untrusted. | Fail closed, never submit stored payload; manual fallback. |
| Concurrent capture/reconcile/manual or replaced identity | Exact reviewer nonce/identity lock selects one result. | Identical submit is idempotent, manual winner fences automatic, stale identity fails closed. |

No compensation or rollback of a committed review result. Missing receipt
after canonical commit is an allowed intermediate state, not a second result
owner. No cell permits a second physical launch or Send.

### Selected implementation, verification and decision

Bind reviewer capture to the exact prepared reviewer identity, task digest,
`dispatch-attempted` state and reviewer state root before browser preflight.
At authenticated capture, parse the complete in-memory result. For
`COMPLETED/PASS|FINDINGS/CURRENT`, call the fixed registered submit procedure
first, then write only a constant `REVIEW_SUBMITTED_V1` generic receipt and
projection. For noncompleting worker/review status, store only a constant
noncompleting marker/status. Forbid raw reviewer results in generic state,
reject legacy full payloads, and reconcile against canonical reviewer state
before reading generic receipts. Generic nonreview workers keep their prior
behavior. The exact-head qualification passes the same reviewer binding.

Verify the write order and no raw result in any generic checkpoint/projection
on success, submit failure, post-submit persistence failure, manual race and
restart; retain nonreviewer tests and run hosted CI. A fresh independent
exact-head review and physical positive/negative Windows gate remain required.
Any raw review checkpoint before submit, a receipt that can settle absent the
canonical result, a second Send or an overwritten manual winner falsifies the
design. Complexity budget: one narrow reviewer capture binding/receipt,
reusing existing procedure/state/controller; no new public tool, service,
store or generalized result framework.

**Reissued decision: NARROW.** Implement the write-order correction now;
no required baseline role is deferred.


## 2026-09-26 Temporary Chat personalization-control re-entry

### Re-entry trigger

Target-Windows qualification on exact HEAD `9c196c7d3951ca3d1c2b480076328027d7b6b6ad`
reached the provider Temporary Chat UI with zero task Send, but the fresh page
was explicitly `Personalized`. The adapter correctly refused prompt handoff
because the accepted `fresh_readonly_worker_v1` profile requires positive
`Temporary + fresh + non-personalized` evidence. Earlier physically passing
CAP heads only observed that state; they did not actively establish it.

OpenAI's current product documentation now exposes personalization as an
explicit pre-first-message Temporary Chat choice:

- https://help.openai.com/en/articles/8914046-temporary-chat-faq
- https://help.openai.com/en/articles/6825453-chatgpt-release-notes
  (2026-08-27, “More controls in temporary chat”)

A personalized Temporary Chat may use memory, custom instructions and plugins;
an unpersonalized Temporary Chat does not. The choice is made before the first
message and cannot be changed after the conversation starts.

### Lineage / scope decision

- Existing Temporary Chat adapter and closed-profile proof: **REFINE**.
- Existing one-Send, prompt-handoff, reviewer identity, Delegation and result
  ownership: **KEEP**.
- New provider framework, new public tool, persisted preference owner or
  browser-recovery authority: **REJECT**.
- Manual operator switching as acceptance: **REJECT** because the reviewer
  qualification contract requires no manual new-chat setup or Send.

### Alternatives

1. **Select the provider's visible “Unpersonalized / Без персонализации” option
   before prompt handoff — SELECT / NARROW.** Only the already-open empty
   Temporary Chat may be changed. Require one unambiguous visible personalized
   selector and one unambiguous visible unpersonalized option, then re-observe
   the page and prove the existing closed profile before any task prompt is
   released.
2. Accept personalized Temporary Chat — **REJECT**; weakens the reviewer
   isolation contract.
3. Ask the operator to switch manually — **REJECT**; makes physical acceptance
   environment-dependent and no longer automatic.
4. Persist or force an account-wide personalization preference — **REJECT**;
   crosses the bounded one-worker adapter scope and changes user-global state.

### Physical hydration evidence

The first exact-head retest after adding automatic personalization setup did
not reach that setup at all. On target Windows, the adapter emitted
`adapter-loaded` at 13:03:29.285996Z and stopped at 13:03:31.479343Z with
`temporary_mode=false`, `personalization_state=unknown`, no UI evidence,
zero prompt handoff and zero Send. The same tab visibly rendered
`Временный чат` and `Персонализированный` shortly afterward.

This proves a provider UI hydration race before the closed-profile observation,
not a Send or Delegation failure. The previous fast-fail assumption for a
fresh page with temporarily absent UI evidence is therefore too strong for the
current provider. A bounded pre-prompt settle window is safe because no task
prompt, Send authority, delivery claim or browser mutation is granted during
that window. After the existing 10-second bound, absence of positive Temporary
UI proof still fails closed.

### Failure boundaries and acceptance

The personalization click occurs before prompt handoff and before Send
authority. Ambiguous/missing controls, a menu that does not expose exactly one
unpersonalized option, a failed selection, profile drift, any existing
conversation turn or any non-empty composer all fail closed with zero task
prompt and zero Send. The adapter must never click a generic text match outside
the current visible Temporary Chat setup surface.

Regression coverage must execute production `content.js` and prove:
personalized -> one selector click -> one unpersonalized option click -> positive
closed-profile re-observation -> prompt handoff; ambiguous or missing controls
produce zero prompt handoff/Send; already-unpersonalized flow performs no setup
click; profile change after handoff still blocks prompt population.

**Reissued decision: NARROW.** Add only this bounded pre-prompt provider-state
establishment and its executable regressions. No new architecture owner or
post-Send recovery authority is introduced.


### Target-Windows personalization menu evidence

On exact-head physical run `b82b2129e45c36a79d5af7b1f182909abe61ab47`,
the provider state was positively identified as:

- `temporary_mode=true`;
- active page evidence `Временный чат` with all three policy signals;
- `fresh_context=true`;
- `personalization_state=personalized`;
- visible personalization evidence included
  `app-shell-header-context-menu-surface | Персонализированный`.

The adapter then timed out after entering its internal `menu-opened` state. Two
closure gaps were found in CAP itself:

1. the new `personalization-switch-*` diagnostic events were not present in
   the controller allowlist, so the physical run could not prove which setup
   step had completed;
2. post-open option discovery accepted `menuitem` and `option` but not the
   standard ARIA radio/checkbox menu-item variants used by selection menus.

The bounded setup surface therefore now accepts `menuitemradio` and
`menuitemcheckbox` in addition to the existing roles, while still requiring
exactly one visible non-personalized semantic match before clicking. The
controller records the setup events so later physical evidence distinguishes
menu-open, selection and fail-closed states. No task prompt or Send authority
is released before the existing closed-profile re-observation.


### Target-Windows send-control evidence

On exact-head physical run `2ceee2a41a416f224df89a1507ce7fa931107416`,
CAP proved the exact capability-bearing prompt was present in the live composer
on every pre-send observation, but `findSendBinding()` never found a send
control:

- `exact_prompt_match=true`;
- `send_binding_found=false`;
- `send_button_testid_count=0`.

The visible UI nevertheless showed the active arrow send control. The previous
adapter contract was therefore over-fitted to
`button[data-testid="send-button"]`. Current ChatGPT implementations also
expose the composer submit control structurally as
`#composer-submit-button` and/or `button[type="submit"]`.

NARROW closure: accept those structural submit identities only when the
candidate is visible/enabled, resolves to the already-proven current composer
form, and the resulting eligible set is exactly one. Do not use screen
coordinates, CSS layout classes, generic last-button heuristics, or localized
button text. Exact prompt match, closed-profile requalification, local send
authority and one-Send semantics remain unchanged.

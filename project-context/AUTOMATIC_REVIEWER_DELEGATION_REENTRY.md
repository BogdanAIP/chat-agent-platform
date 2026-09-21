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

No new external runtime is selected by this stage. `source-code-research` does not add a new implementation cohort because the selected production mechanisms are accepted project-owned code plus the closed ChatGPT product surface; current official product documentation is the relevant external evidence for Temporary Chat behavior.

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
  between content scripts and the extension service worker:
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

After navigation, the task content script requests the prompt from the same live
owner. The service worker must require:

- exact launch handle;
- exact delegation/delivery/task/prompt/head correlation;
- the exact original owner tab;
- an unconsumed prompt handoff.

The content script recomputes `prompt_sha256`, validates the exact worker-task
markers, populates only an empty composer, then retains the existing positive
Temporary/non-personalized/no-plugin qualification and durable browser Send claim
before clicking Send.

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
| after navigation, before prompt handoff | live MV3 memory | empty task composer | wrong tab/handle/correlation or lost owner => no prompt, no Send |
| prompt handoff to content script | live extension/content memory | empty composer | recompute digest + exact structural validation before DOM mutation |
| composer population fails or existing content is non-empty | live page only | unsatisfied binding | fail closed; never overwrite unrelated content and never request Send authority |
| exact prompt visible, before Send claim | live composer | qualified Temporary UI | existing positive isolation proof still required |
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
3. the MV3 prompt handoff is exact-owner-tab, exact-handle, exact-correlation and
   one-shot/fail-closed;
4. the content script rejects a digest mismatch and non-empty unrelated composer;
5. successful population still requires exact visible-composer equality before
   requesting Send authority;
6. no CAP URL/log/public metadata projection intentionally contains the private
   reviewer nonce;
7. service-worker/live-owner loss before Send produces no reconstruction, second
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

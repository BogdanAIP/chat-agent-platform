# Automatic Reviewer -> Generic Delegation Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-16.

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

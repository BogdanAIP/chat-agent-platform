# Automatic Independent Reviewer — Authority Qualification Re-entry

Status: **STAGE RESEARCH — NARROW (PROPOSED UNTIL THIS PR IS ACCEPTED)**

Research date: 2026-09-01

This is a focused Stage Research re-entry for the automatic-reviewer authority and result-handoff roles already owned by `AUTOMATIC_REVIEWER_RESEARCH.md`. It does not create a second lifecycle owner. Where this brief is accepted and conflicts with the 2026-08-31 authority/handoff choice, this brief supersedes only those authority/handoff mechanics; the accepted exact-operation state, OS-lock, genesis/checkpoint, reconciliation and MV3/IndexedDB Send-claim roles remain unchanged.

Research baseline:

```text
main = 90a8e16e6a1badecd3315968339ca691634b7ee4
PR #142 = merged / fixed review procedures wired behind procedure_run
public Chat-facing surface = exactly six canonical semantic tools
mandatory primary semantic reviewer = fresh ordinary ChatGPT
current personal ChatGPT development context = GitHub app reachable with mutation actions
current target plan = personal Plus, not a managed Business/Enterprise/Edu workspace
```

## Stage goal

Make the mandatory automatic fresh review usable on the user's actual ordinary-ChatGPT Plus environment while preserving the stronger accepted invariant:

> During semantic review, the reviewer security context has no reachable GitHub mutation action or raw GitHub write credential.

The target outcome is still one fresh ordinary-ChatGPT semantic review of exact BASE/HEAD followed by project-owned local result recording and development-side reconciliation. The user should not need a second ChatGPT account, a Business/Enterprise workspace, or manual result copy/paste merely to remove GitHub write authority.

This re-entry is necessary because the previously selected authority qualification — a dedicated reviewer account/workspace with GitHub unavailable, or managed-workspace read-only Action Control — is sound but is not directly usable in the current personal Plus environment. OpenAI's 2026-08-27 Temporary Chat update supplies a materially different platform primitive: a **non-personalized Temporary Chat has no plugins at all**. That removes the GitHub app rather than merely approval-gating or leaving it unselected.

Selected narrowed lifecycle if this brief is accepted:

```text
exact frozen review operation
 -> durable local prepared state + private review_run_id
 -> one bounded ChatGPT deep link using temporary-chat=true
 -> browser companion proves the page is still non-personalized Temporary Chat
 -> no ChatGPT plugins are available to that reviewer context
 -> MV3/IndexedDB exact-run Send claim
 -> exactly one review request Send
 -> fresh ordinary Temporary-Chat reviewer uses built-in web/public GitHub evidence
 -> complete CURRENT PASS or structurally complete CURRENT FINDINGS appears in final assistant turn
 -> browser companion extracts the exact structured result
 -> extension service worker sends one bounded native message
 -> project-owned submit-only native host validates the exact extension origin + schema
 -> native host invokes the existing local independent-review result state machine
 -> development reconciles the same local operation
 -> final exact-head/identity/result gates
```

The fresh semantic reviewer itself receives **no Local Bridge plugin and no GitHub plugin**. The browser companion/native host is deterministic transport, not a second reviewer and not a general local-agent channel.

## Current project baseline

### Accepted review state and public authority

PR #142 merged the three fixed review procedures behind the existing `procedure_run` and retained exactly six public semantic tools. The accepted local operation already provides:

- exact repository / PR / BASE / HEAD / skill identity;
- immutable genesis with private `review_run_id`;
- OS-backed single-writer ownership;
- crash-safe mutable state;
- capability-bound automatic result submission;
- same-lock manual fallback and late-submit rejection;
- workspace/private-state lifetime isolation.

Those mechanics remain the authoritative local result state. This research does not replace them with browser state, an external database, a GitHub comment, or a callback service.

### Current authority problem is real

The current development ChatGPT context was inspected on 2026-09-01. GitHub is present with the app-specific permission `Allow all actions`; `Chat Local Bridge Test` is also present. App permission mode is not action removal. Therefore this development security context is not an acceptable automatic reviewer environment under the accepted `code-review` v1.1 policy.

OpenAI product documentation distinguishes:

- **App permissions** — determine when ChatGPT asks before an available action;
- **Action control** — where supported, determines which actions are actually available;
- disconnect/disable — removes app access.

Personal Projects do not create a per-project app-action allowlist. Managed workspaces can use Action Control; the current personal Plus environment cannot rely on that administrator boundary.

### New platform evidence: non-personalized Temporary Chat

OpenAI's Temporary Chat documentation, updated after the original architecture choice, states:

- Temporary Chats start non-personalized by default;
- non-personalized Temporary Chats do not use memory, custom instructions, **or plugins**;
- plugins are available only in personalized Temporary Chats;
- personalization cannot be changed after the conversation begins.

OpenAI's current ChatGPT web surface also resolves `https://chatgpt.com/?temporary-chat=true` as a Temporary Chat page. The URL mechanic is still treated as a UI contract that requires physical target-machine verification; the authority guarantee is accepted only when the browser companion independently observes the expected Temporary-Chat/non-personalized state immediately before Send and before result extraction.

This is stronger than `@GitHub` non-selection because the entire plugin surface is absent from that conversation.

## Exact stage question

Can CAP replace the previously selected dedicated reviewer account/workspace requirement for the personal-Plus path with a non-personalized Temporary Chat, while retaining deterministic local result submission without giving the reviewer or browser companion broad Local Bridge authority?

Durable invariants that may not weaken:

1. reviewer remains a fresh ordinary ChatGPT conversation, not Work, Workspace Agent or Codex;
2. reviewer cannot reach GitHub mutation actions during the semantic review;
3. development caller never receives `review_run_id` while automatic submission remains open;
4. browser launch/Send remains exact-run bounded and at-most-once;
5. browser state never becomes authoritative review-result state;
6. automatic result state remains the accepted project-owned local state machine;
7. manual fallback and late automatic submit remain serialized by the same operation lock;
8. no seventh public Chat-facing semantic tool is added;
9. no generic browser-to-local command, shell, filesystem, URL, HTTP or procedure authority is introduced;
10. UI/product drift fails closed to manual fresh review.

Explicitly out of scope:

- general Native Messaging RPC;
- browser companion access to the existing six-tool Local Bridge endpoint;
- arbitrary native process launch;
- general localhost callback/result server;
- making Temporary Chat a general agent/session primitive;
- automating account connect/disconnect;
- bypassing managed-workspace Action Control when such a workspace is deliberately used;
- GitHub write publication;
- development-chat automatic wake;
- broad browser result scraping outside this exact review protocol.

## Architecture lineage comparison

| Role | Prior selected source / owner | Current evidence | Decision | Scope qualifier |
|---|---|---|---|---|
| primary semantic reviewer | fresh ordinary ChatGPT | Temporary Chat is still ordinary ChatGPT and is fresher because account personalization is absent | **KEEP** | review protocol/exact-ref/falsification unchanged |
| reviewer authority qualification | dedicated reviewer account/workspace with GitHub unavailable, or managed read-only Action Control | safe but operationally unavailable on the current personal Plus path; non-personalized Temporary Chat now removes all plugins | **REPLACE** | Plus v1 uses non-personalized Temporary Chat; managed read-only Action Control remains an allowed future deployment alternative |
| deep-link/composer mechanic | refined PR #138 ChatGPT deep-link | `temporary-chat=true` currently resolves to Temporary Chat and can carry a bounded prompt | **REFINE** | require live Temporary-Chat/non-personalized proof before Send; URL alone is not authority |
| browser Send ownership | MV3 service worker + extension-origin IndexedDB unique-key claim | still exactly the right cross-tab at-most-once domain | **KEEP** | no Send grant before authority/page-state proof |
| local result submission/reconciliation | accepted local independent-review state behind fixed procedures | state machine remains correct; reviewer can no longer call Local Bridge because plugins are absent | **REFINE** | keep state machine, replace model-mediated result transport with one submit-only deterministic native host |
| automatic launch/correlation | `procedure_run` + private operation state | unchanged exact-operation owner | **REFINE** | launch targets Temporary Chat and includes only the private exact-run review request |
| development continuation | current development chat | no change needed | **KEEP** | reconcile result locally; automatic wake remains out of scope |

New architecture role introduced by this re-entry:

- **submit-only Chrome Native Messaging host** between the project-owned reviewer browser companion and the existing local result state machine.

That role is covered by the Scope Expansion Gate below.

## Architecture primitives and adjacent domains

### Primitive A — non-personalized Temporary Chat capability isolation

Engineering domain: application capability isolation / least privilege.

Required guarantee: the semantic reviewer conversation has no ChatGPT plugin actions, therefore no GitHub app mutation actions.

Assumptions/boundary:

- the target ChatGPT web product preserves the documented non-personalized Temporary Chat behavior;
- account/workspace restrictions do not silently turn the conversation into a personalized/plugin-enabled context;
- the browser companion observes page state immediately before Send and result extraction;
- built-in web access remains available for public repository evidence.

If any assumption cannot be proved on the target machine, automatic Send is not granted.

### Primitive B — existing MV3/IndexedDB exact-run Send claim

Engineering domain: browser extension lifecycle + transactional IndexedDB.

No architecture change. The accepted service-worker/IndexedDB transaction remains the owner of the one automatic Send grant. Authority qualification becomes an additional precondition to claim/grant, not a substitute for the claim.

### Primitive C — submit-only Native Messaging host

Engineering domain: browser/native application IPC + least-privilege capability design.

Required guarantee: a project-owned extension can hand the already-computed structured review result to the accepted local result state machine without exposing the six-tool Local Bridge or a generic native command surface.

Chrome's documented Native Messaging model provides:

- a separately registered native host process communicating over stdin/stdout;
- a host manifest with `allowed_origins` containing exact extension origins and no wildcards;
- Windows HKCU/HKLM registration of the host manifest;
- the caller extension origin as the first host process argument;
- `sendNativeMessage()` launching a fresh host for one message;
- Native Messaging unavailable directly to content scripts, requiring the extension service worker as the bridge;
- a 64 MiB extension-to-host message ceiling and 1 MiB host-to-extension ceiling, both comfortably above CAP's existing bounded review result while still requiring CAP's smaller protocol limit.

CAP narrows this further:

```text
native host name = one fixed reviewed value
allowed_origins = exactly one deterministic reviewer-companion extension origin
accepted action = submit_independent_review_result_v1 only
accepted fields = schema_version, review_run_id, result only
review_run_id = exact 64 lowercase hex
result = decoded UTF-8 <= existing review-result bound
state root = installed private manager configuration, never caller supplied
procedure/action/path/command/url/backend/repository override = impossible by schema
host stdout = one bounded receipt only
host stderr = diagnostics only
```

The host invokes the existing independent-review result state machine. It does not expose the general Control Plane CLI, shell execution, arbitrary Python imports or arbitrary `procedure_run` variants to the extension.

### Primitive D — completed-review DOM extraction

Engineering domain: browser UI adaptation / structured output capture.

Required guarantee: only the completed final semantic result corresponding to the exact run is eligible for native submission.

The browser companion must require all of:

- still on the exact expected Temporary Chat/run;
- non-personalized Temporary Chat proof still present;
- assistant turn is no longer streaming;
- body contains one parseable `REVIEW_RESULT_V1` header;
- exact repository/PR/BASE/HEAD/skill/version/context/review_run_id match the immutable launch request;
- only `CURRENT PASS` with zero findings or structurally complete `CURRENT FINDINGS` is completing;
- `ABSTAIN`, `STALE`, malformed, oversized, duplicate or identity-mismatched outputs are not submitted as terminal automatic results;
- extraction failure has no retry that sends another review request.

The local state machine remains the final parser/validator; browser extraction is an admission prefilter, not result authority.

## Problem evidence

### Current personal account cannot satisfy the old qualifier in place

Current live ChatGPT app permissions show GitHub reachable with `Allow all actions`. Changing to `Allow read actions` would only change approval behavior; OpenAI documentation explicitly separates app permissions from action availability. Per-project isolation is not provided by Projects.

### Managed Action Control is sound but not the current product surface

OpenAI documents read-only/custom Action Control for managed workspaces. That remains a strong deployment option, but the project must not make a personal Plus user's mandatory review automation depend on an administrator surface they do not have.

### Temporary Chat removes the entire plugin class

Current OpenAI documentation states non-personalized Temporary Chats do not use plugins. This directly removes both GitHub and Local Bridge app authority from the semantic reviewer, rather than relying on the model to avoid invoking GitHub.

### Existing Local Bridge is too broad for browser-companion result handoff

CAP's current 1MCP runtime is bound to loopback but aggregates the semantic runtime. Current 1MCP documentation states authentication is disabled by default unless explicitly enabled. Giving the extension host permission to call the existing endpoint would therefore grant the browser companion a path to a broader runtime than the one fixed result submission needed. That violates least privilege even if extension source intends to call only one procedure.

### Manual copy/paste remains safe but defeats the stage goal

The current manual fresh-review handoff remains the fail-closed fallback and is not removed. It is not selected as the automatic path because it preserves the routine user work this capability is intended to eliminate.

## Solution evidence

### OpenAI product boundary

Primary evidence:

- OpenAI Temporary Chat FAQ: non-personalized Temporary Chats do not use memory, custom instructions or plugins; plugins are available only in personalized Temporary Chats; personalization is chosen at start and cannot be changed mid-conversation.
- OpenAI ChatGPT release notes, 2026-08-27: the new Temporary Chat personalization control explicitly distinguishes personalized chats that can use plugins from non-personalized chats that do not.
- OpenAI Apps documentation: app permissions govern approval prompts, while workspace Action Control governs which app actions exist; disconnect/disable removes app access.
- Current `https://chatgpt.com/?temporary-chat=true` surface resolves as Temporary Chat. This URL behavior remains a physical acceptance target rather than an undocumented guarantee assumed forever.

Project mapping:

```text
Temporary + non-personalized observed
 -> plugin class absent
 -> GitHub plugin mutation actions absent
 -> reviewer may proceed using built-in web/public repository evidence
else
 -> no Send claim
 -> manual fresh-review fallback
```

### Chrome Native Messaging boundary

Primary evidence: Chrome Extensions Native Messaging documentation.

Chrome requires a registered host manifest and permits `allowed_origins` to enumerate exact extension origins; wildcards are forbidden. Chrome starts the native application as a separate process and passes the caller extension origin as the first argument. Content scripts cannot call Native Messaging directly; they must message their extension service worker, which can call `sendNativeMessage()` when the extension declares the `nativeMessaging` permission.

This supports a narrow project mapping:

```text
isolated content script
 -> exact structured result candidate
 -> service worker validates sender/tab/origin/run
 -> sendNativeMessage(fixed_host_name, fixed_schema_message)
 -> Chrome enforces exact extension allowed_origin
 -> native host rechecks caller origin + message schema
 -> existing local result state machine validates nonce/result/state
```

No localhost host permission and no externally-connectable web-page entrypoint are required.

### Existing local state evidence

PR #141/#142 already proved the hard result-state properties: private capability, exact identity, single-writer lock, automatic/manual closure race, duplicate same-digest reconciliation, different-digest rejection, genesis/state recovery and late automatic-submit rejection. Native Messaging is only a deterministic transport into that accepted state machine.

## Best current approaches and alternatives

| Approach | Authority owner | Strengths | Known limitations / failure modes | Ongoing complexity | Fit |
|---|---|---|---|---|---|
| dedicated reviewer ChatGPT account/profile with GitHub disconnected | separate account security context | simple conceptual isolation; Local Bridge can remain connected if supported | second account/profile lifecycle; app can later be connected; fresh qualification still needed; operational burden | medium operational, low code | safe fallback, not selected for personal Plus default |
| managed workspace Action Control with GitHub read-only | workspace admin policy | strongest native action-level policy; GitHub reads can remain available | requires eligible managed workspace/admin controls; not current personal Plus surface | low code, external admin dependency | preferred managed-workspace deployment option |
| **non-personalized Temporary Chat + submit-only Native Messaging host** | ChatGPT Temporary-Chat plugin isolation + project extension/host | works on personal account; removes all plugins; no GitHub credential; no broad Local Bridge; deterministic local handoff | UI/product drift; native host install/extension ID coupling; DOM extraction must fail closed | medium code + one Windows install role | **selected Plus v1 path** |
| Temporary Chat + direct extension fetch to current 1MCP `/mcp` | browser extension + broad loopback MCP | superficially simple | extension gains broader semantic runtime; 1MCP auth is not enabled by default; CORS/localhost security and generic procedure authority expand attack surface | deceptively low code, high authority risk | **REJECT** |
| browser automation disconnects/reconnects GitHub around review | mutable ChatGPT account configuration | no second account | consequence-bearing account mutation, recovery ambiguity, races with development context, product UI fragility | high | **REJECT** |
| manual fresh review | user | already proven and safe | manual handoff remains | low | mandatory fallback |

## Failure lessons

### Do not equate permission prompts with capability removal

The existing account demonstrates why: GitHub is still technically reachable even if a stricter confirmation policy were chosen. Qualification must remove the plugin/action class from the reviewer context.

### Do not expose the six-tool bridge to the browser companion

Loopback binding is not capability narrowing. The extension must not gain a generic MCP client surface merely to submit one result.

### Do not keep result authority in service-worker globals

MV3 workers terminate. Existing research already selected IndexedDB for the one Send claim and project local state for result authority. The Native Messaging host is one-shot transport only.

### Do not accept URL intent as proof of Temporary Chat

`temporary-chat=true` is launch intent. The content script must observe the expected Temporary Chat/non-personalized state immediately before consequence. Product/UI drift yields no Send.

### Do not scrape partial model output

Streaming or duplicate assistant DOM nodes can look result-like. Native submission waits for a completed assistant turn and then still relies on the local state machine's exact structured-result validation.

### Do not let Native Messaging become a generic host

The host must reject unknown fields/actions and cannot accept arbitrary procedure names, state roots, command lines, repository identities, URLs or file paths. Its only effect is one call to the already accepted local result-state transition.

## Failure / Crash Matrix

| Boundary | Authoritative durable state | Possible physical state | Required fresh evidence | Retry / reconciliation | Shield / test | Max unauthorized additional effect |
|---|---|---|---|---|---|---|
| before Temporary Chat launch | local operation `prepared` | no reviewer page | live exact operation | launch may be attempted once under accepted operation lock | launch contract | 0 Sends, 0 submits |
| URL opens normal/personalized chat | local `prepared` or later `dispatch-attempted` only after launch intent | page exists with plugins/account personalization | live page-state proof | no Send; manual fallback | negative DOM fixture + physical gate | 0 Sends |
| Temporary Chat page state is ambiguous | same | UI partially loaded/drifted | positive non-personalized Temporary state | wait within bounded settle only; then abort | timeout/fail-closed test | 0 Sends |
| concurrent tabs reach Send | local dispatch state + extension IDB | two eligible tabs | committed IndexedDB unique-key transaction | loser never retries Send | existing MV3 claim tests | at most 1 Send |
| crash after claim before Send | committed browser claim; local dispatch-attempted | no Send or ambiguous pre-click state | no safe proof that Send did not occur | no blind retry; manual fallback | claim-before-effect fault test | 0 extra Sends |
| normal chat/product state changes after claim but before click | claim exists | page no longer qualified | recheck page state immediately before click | abort; claim stays consumed | pre-click revalidation | 0 Sends |
| reviewer cannot use built-in web/public GitHub | local dispatch-attempted/open | review may return ABSTAIN or no terminal result | structured completing result absent | no automatic terminal submit; manual fallback | non-completing result tests | 0 submits |
| assistant response still streaming | local result open | partial REVIEW_RESULT-like text | completed assistant-turn evidence | wait boundedly; never submit partial | DOM fixture tests | 0 submits |
| completed result malformed/stale/ABSTAIN | local result open | text exists | exact parse + identity + CURRENT completing status | do not submit terminal result | parser negatives | 0 submits |
| extension service worker terminates before native submit | local result open | completed result remains in DOM; no receipt | fresh completed-result re-observation + same run | one idempotent submit attempt may be retried only through same browser transport; local state decides duplicate | service-worker restart test | at most one local terminal result |
| native host missing/registry broken | local result open | review result exists only in Temporary Chat | native transport failure | no alternate broad transport; manual fallback | install/uninstall failure test | 0 local writes |
| wrong extension calls native host | local result open | hostile/other extension message | Chrome `allowed_origins` + host argv origin | reject | origin-negative integration test | 0 local writes |
| allowed extension sends malformed/extra-field message | local result open | arbitrary JSON | strict host schema | reject | fuzz/schema tests | 0 local writes |
| native host crashes before state commit | local result open | no result committed | local canonical state | same exact nonce/digest retry allowed | host crash fault test | 0 terminal duplicates |
| state commits but native response is lost | automatic-result-recorded | extension sees no receipt | canonical local result digest | same nonce/same digest returns already-recorded | existing idempotency + host integration | 0 additional terminal effects |
| manual fallback races late native submit | same accepted local operation lock | either contender starts first | canonical local result state | whichever commits first closes slot; late other path rejected | existing #141/#142 race tests | exactly one terminal local result |
| user saves/converts Temporary Chat before result extraction | local result open | plugins may become available in regular chat | Temporary/non-personalized state recheck | do not extract/submit automatically; manual fallback | negative physical/UI test | 0 automatic submits after conversion |
| extension/native-host source drifts after install | local result open | unreviewed transport bytes | installed source provenance/hash | fail installed-runtime gate; no automatic mode | installer/provenance contract | 0 authorized automation |
| host receives oversized result | local result open | large DOM text | protocol byte bound | reject; manual fallback | boundary tests | 0 writes |
| exact PR head changes while reviewer works | operation bound to old head | semantically valid stale review | final result identity + live PR identity | local parser/final gate rejects stale | existing exact-head tests | 0 merge authority |

No release-critical matrix cell is intentionally answered with blind retry.

## Fit to Chat Agent Platform

Direct fit:

- ordinary ChatGPT remains the semantic reviewer;
- the existing deep-link/browser-companion direction already owns ChatGPT UI adaptation;
- the accepted IndexedDB claim already belongs in the browser concurrency domain;
- the accepted local review state remains the only result authority;
- a one-shot Native Messaging host is a deterministic adapter, analogous to other bounded platform adapters, not a second planner/runtime;
- public Chat-facing semantic inventory remains unchanged.

Not adopted:

- browser extension as generic local Control Plane client;
- persistent native daemon;
- result database in Chrome;
- generic browser-to-host RPC;
- any GitHub write credential in reviewer or native host.

Long-horizon compatibility:

The native host contract is intentionally review-result-specific in v1. Do not generalize it into a cross-provider browser IPC framework until a second real consumer and a fresh Stage Research question justify that abstraction.

## Architecture decision

**Decision: NARROW.**

Replace the personal-Plus automatic reviewer authority qualifier with **non-personalized Temporary Chat**, while keeping managed-workspace read-only Action Control as a valid future deployment alternative.

For the personal-Plus v1 implementation, require:

1. exact-run ChatGPT Temporary Chat launch intent;
2. positive live proof of non-personalized Temporary Chat immediately before Send and result extraction;
3. existing MV3/IndexedDB unique-key Send claim;
4. semantic review using built-in web/public repository evidence with no plugins;
5. completed structured result extraction bound to exact `review_run_id` and review identity;
6. one project-owned **submit-only Native Messaging host** restricted to one deterministic extension origin and one strict result-submit schema;
7. reuse of the accepted local automatic-result state machine and manual-fallback reconciliation;
8. no broad Local Bridge/MCP authority in the extension or native host;
9. manual fresh review as fail-closed fallback whenever any page/transport/result condition is not proved.

Explicitly rejected for this path:

- direct browser access to current 1MCP `/mcp`;
- permission-prompt qualification;
- per-message GitHub non-selection;
- automated GitHub connect/disconnect;
- a generic Native Messaging command host;
- a second persistent local result service.

### Required policy refinement before automatic mode is accepted

`code-review` v1.1 currently describes automatic local submission as a `procedure_run` call made from the reviewer context. The Temporary Chat design deliberately removes all plugins from the reviewer. The implementation PR must therefore refine the target review protocol so that:

- semantic review remains entirely inside the fresh plugin-free ordinary Temporary Chat;
- the project-owned browser companion may transport the **unaltered completed reviewer output** through the fixed submit-only native host;
- the local state machine performs the same exact `review_run_id`/identity/schema/result validation;
- the browser companion/native host cannot edit the PR, GitHub state or reviewer output;
- manual review semantics remain unchanged.

The implementation PR itself remains governed by accepted BASE `code-review` v1.1 until that refinement is merged.

## Failure shields required before production Send authority

- `AR-AUTH-TEMP-001`: normal/personalized/plugin-enabled page gets zero Send grants.
- `AR-AUTH-TEMP-002`: exact Temporary/non-personalized page is positively identified, not inferred only from URL.
- `AR-AUTH-TEMP-003`: state is revalidated immediately before click and result extraction.
- `AR-HANDOFF-NM-001`: only the pinned extension origin can launch the native host.
- `AR-HANDOFF-NM-002`: host accepts exactly one schema/action and rejects unknown fields.
- `AR-HANDOFF-NM-003`: no caller-controlled command/path/state-root/procedure/backend/URL exists.
- `AR-HANDOFF-NM-004`: malformed/oversized/stale/non-completing result causes no state write.
- `AR-HANDOFF-NM-005`: lost native receipt after commit reconciles through existing same-nonce/same-digest semantics.
- `AR-HANDOFF-NM-006`: native host and extension installed bytes are provenance-bound and revalidated before physical acceptance.
- `AR-SURFACE-001`: public semantic inventory remains exactly six tools and current public procedure registry is not widened merely for native handoff.

## Acceptance ladder

### Research PR

- document/lineage contract tests;
- hosted CI/security;
- mandatory fresh ordinary-Chat review;
- no production/browser consequence claimed.

### Implementation slice 1 — native handoff + policy, no automatic Send

- pure result parser/identity tests;
- Native Messaging framing/schema/origin tests;
- Windows HKCU host registration/install/uninstall tests;
- installed-runtime/provenance checks;
- Chrome MV3 service-worker message tests;
- public six-tool/procedure inventory unchanged;
- launch still fail-closed before automatic Send.

### Implementation slice 2 — Temporary Chat qualification + Send claim

- DOM fixture tests for Temporary vs personalized/regular/ambiguous state;
- at-most-once cross-tab IndexedDB claim tests;
- terminate/restart service worker around claim and handoff;
- exact-run prompt/result binding;
- no blind Send retry after claim;
- hosted Chrome/Windows tests where practical.

### Target Windows physical gate

Using the user's real ordinary ChatGPT account and installed reviewed browser companion:

1. freeze exact BASE/HEAD operation;
2. launch `https://chatgpt.com/?temporary-chat=true` with exact bounded review request;
3. prove the chat is non-personalized Temporary Chat and plugin actions are unavailable;
4. prove public web/repository evidence is usable;
5. prove one and only one Send claim/click;
6. obtain a genuine fresh `REVIEW_RESULT_V1`;
7. prove extension/native host records the exact result in local state without exposing GitHub or six-tool Local Bridge authority;
8. reconcile from development context;
9. prove no GitHub mutation occurred;
10. exercise negative cases: normal/personalized page, duplicate tab, native host absent, malformed result and manual fallback.

If the actual ChatGPT UI cannot provide stable positive evidence of non-personalized Temporary Chat, or if built-in web evidence is insufficient for the mandatory review, this architecture is falsified and automatic Plus mode remains unavailable. Do not weaken the authority invariant to preserve automation.

## Implementation order after this research is accepted

1. refine the automatic `code-review` handoff contract and add submit-only Native Messaging host with no automatic Send;
2. bind native host + extension source/install provenance;
3. productionize the exact-run MV3/IndexedDB browser claim from the accepted research/PR #138 mechanics;
4. add Temporary Chat live qualification and pre-click/re-result checks;
5. wire one bounded browser launch only after durable dispatch-attempted;
6. run target-Windows ordinary-Chat E2E and negative authority tests;
7. only then call automatic reviewer production-ready;
8. proceed to Harbor reviewer-quality baselines after automatic transport/security is accepted.

Until those steps pass, `launch_independent_review_v1` remains fail closed and manual fresh ordinary-Chat review remains authoritative.
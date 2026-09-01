# Automatic Reviewer — Temporary Chat production re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-01

Research baseline:

```text
accepted main = 90a8e16e6a1badecd3315968339ca691634b7ee4
accepted automatic-review authority = merged PR #140 NARROW
accepted local state foundation = merged PR #141
accepted fixed procedure wiring = merged PR #142
experiment PR #145 = evidence only / never production authority
public semantic surface = exactly six tools
primary semantic reviewer = fresh ordinary ChatGPT
```

## 1. Why Stage Research re-entry is mandatory

Merged PR #140 selected an automatic reviewer environment that retained the local review bridge so the fresh reviewer itself could call `procedure_run -> submit_independent_review_result_v1`. The 2026-09-01 physical experiments found a materially stronger personal-Plus isolation primitive: a **non-personalized Temporary Chat**. Current OpenAI product documentation says that this mode starts without memory, custom instructions or plugins. That removes GitHub mutation actions deterministically on the tested personal-Plus surface, but also removes Chat Local Bridge and therefore removes the reviewer's direct `procedure_run` result-submission path.

The experiment also showed that public repository evidence can be reconstructed through built-in web/public GitHub, while a private repository needs an explicit read-only evidence delivery path. Both changes cross accepted #140 authority/evidence/result-handoff boundaries. #140 explicitly excluded a Native Messaging/local result bus and required research re-entry for a materially new result transport. Production implementation is therefore blocked until this Brief selects a bounded replacement/refinement.

## 2. Stage goal

Preserve the accepted exact-head, fresh-context, fail-closed review lifecycle while making the **CAP agent**, not a user-run PowerShell harness, own the complete bounded review dispatch/handoff path:

```text
development context
 -> procedure_run / launch_independent_review_v1
 -> exact operation + private review_run_id
 -> CAP-owned browser companion
 -> fresh non-personalized Temporary Chat
 -> public repository evidence OR bounded private evidence package
 -> one automatic Send
 -> REVIEW_RESULT_V1
 -> CAP-owned submit-only local handoff
 -> existing validated automatic-result-recorded state
 -> reconcile_independent_review_result_v1
```

The user must not routinely open a review chat, paste a request, attach/select evidence, click Send or copy the result.

This re-entry does **not** authorize automatic resampling/wake of the unfinished development conversation. The accepted current scope remains: the automatic reviewer can complete and store its result while the development conversation is inactive; the development context consumes it through `reconcile_independent_review_result_v1` on its next planner turn. General same-task wake remains separate future Stage Research.

## 3. Physical evidence already obtained

Experiment PR #145 produced three useful target-Windows observations using non-personalized Temporary Chat without plugins:

1. accepted PR #142 -> semantic `PASS`;
2. superseded PR #140 intermediate head -> correct `STALE / STALE_MATERIAL_CHANGE`;
3. live control PR #146 reproducing the known defective exact #140 range -> `CURRENT FINDINGS`, recovering the same four historical P1 defect categories without the answer being supplied.

The third control is evidence that plugin-free public-web review can recover real project defects, not merely produce a PASS-shaped response. PR #145 remains experiment-only and is not copied into production as authority.

The private-repository Library/direct-file paths added experimentally in #145 have **not** yet been physically accepted and are not treated as working production evidence.

## 4. Current product / engineering evidence

### OpenAI Temporary Chat

Current OpenAI Temporary Chat FAQ and 2026-08-27 release notes state that Temporary Chats start non-personalized by default; a non-personalized Temporary Chat does not use memory, custom instructions or plugins and does not create new memories. Personalization is selected only when starting the chat.

Sources:

- https://help.openai.com/en/articles/8914046-temporary-chat-faq
- https://help.openai.com/en/articles/6825453

Project implication: on the personal-Plus surface, non-personalized Temporary Chat is a stronger reviewer least-privilege primitive than per-message non-selection or approval prompts because the plugin surface itself is absent. Qualification still requires fresh physical UI/product evidence; a URL flag alone is not permanent authority proof.

### OpenAI app/action controls

Current OpenAI app documentation distinguishes app permissions (when approval is requested) from Action Control (which actions are actually available). Where supported, workspace admins can allow only read actions. Merely changing approval prompting does not remove write authority.

Sources:

- https://help.openai.com/en/articles/11487775
- https://help.openai.com/en/articles/11509118

Project implication: managed workspaces with proven read-only Action Control remain a valid alternate reviewer environment. For personal Plus, plugin-free non-personalized Temporary Chat is the preferred path when physically qualified.

### OpenAI Library / file lifetime

Current OpenAI Library documentation states that ordinary ChatGPT uploads are saved to Library, Library files persist until deletion, and files uploaded while using Temporary Chat are **not** saved to Library. Plus has a 20 GB Library quota and text/document files have a 2M-token/file limit.

Source:

- https://help.openai.com/en/articles/20001052

Project implication: Library is useful as a possible cache but it is a worse default private-review transport because it creates persistent account storage, cleanup/retention obligations and quota pressure. A direct bounded upload into the Temporary Chat has the narrower lifetime and is selected for the first private-repository consumer. Library remains deferred/optional until separately accepted cleanup semantics exist.

### Chrome Native Messaging

Current Chrome documentation states that extensions may communicate with a registered native host over stdin/stdout; host manifests bind exact `allowed_origins` (wildcards are not accepted), and Windows may register the host under HKCU/HKLM. Chrome limits a single host->extension native message to 1 MB and extension->host to 64 MiB.

Source:

- https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging

Project implication: Native Messaging is suitable for a **narrow submit-only / bounded-evidence bridge**, not a generic command bus. Host->extension evidence delivery must be bounded/chunked below the documented limit. Extension->host result submission comfortably fits the existing review-result bound.

### Chrome content-script security

Chrome documentation treats content scripts as less trustworthy than the extension service worker and requires validation/sanitization of messages plus narrow privileged actions. Sensitive privileged work should remain in the service worker/native host and a content script must not gain arbitrary URL/native command authority.

Sources:

- https://developer.chrome.com/docs/extensions/develop/concepts/messaging
- https://developer.chrome.com/docs/extensions/develop/security-privacy/stay-secure

Project implication: the ChatGPT content script owns only DOM observation/composer/file attachment and final-assistant extraction. Native-host calls originate from the extension service worker through fixed typed messages; the content script cannot supply arbitrary commands, paths, URLs, operation identities or state roots.

## 5. Source-code research

### nicepkg/ctxport

```text
repository = nicepkg/ctxport
exact ref = c4e3db1be3191d4167d2218c90dd9cfbea0dc924
research date = 2026-09-01
classification = OPEN_IMPLEMENTED / REFERENCE_ONLY
```

Inspected:

- `apps/browser-extension/src/entrypoints/content.tsx`
- `packages/core-plugins/src/plugins/chatgpt/plugin.ts`
- adapter QA reports / declarative-adapter architecture docs.

Useful mechanics:

- a browser extension content entrypoint with explicit SPA URL-change handling;
- platform adapter/selector fallbacks and live UI qualification expectations;
- separation between platform-specific adapter logic and shared extension infrastructure.

Rejected mechanics:

- CtxPort's ChatGPT plugin reads `https://chatgpt.com/api/auth/session`, obtains an access token and calls internal `backend-api/conversation/...` endpoints. CAP does **not** adopt this internal/private API coupling or token handling for reviewer authority/result extraction.

Lesson: **ADAPT_MECHANIC** for adapter/fallback organization only; do not reuse session-token/backend-API extraction.

### GoogleChrome/chrome-extensions-samples

```text
repository = GoogleChrome/chrome-extensions-samples
exact ref = d5202c365b9ade380dc5fb0762ea89d528eaa00d
research date = 2026-09-01
classification = OPEN_IMPLEMENTED / REFERENCE_ONLY
```

Inspected:

- `_archive/mv2/api/nativeMessaging/host/native-messaging-example-host`

Useful mechanics:

- explicit 32-bit length-prefixed JSON/stdin/stdout framing;
- Windows binary-mode stdin/stdout handling;
- host process lifecycle separated from the extension.

The archived sample is not adopted as a dependency and its GUI/echo behavior is irrelevant. CAP implements the protocol narrowly under current MV3 documentation and its own validators/tests.

## 6. Alternatives compared

### Approach A — keep accepted #140 reviewer environment + direct `procedure_run` submit

```text
fresh ordinary Chat
 -> GitHub read-only Action Control / disconnected GitHub
 -> Local Bridge remains available
 -> reviewer calls submit_independent_review_result_v1
```

Advantages:

- preserves accepted #140 result transport exactly;
- no new native host.

Failure / fit problem:

- the personal-Plus environment physically available to this project currently does not provide a proven separate read-only Action Control configuration while retaining the required bridge;
- the strongest proven fresh isolation primitive, non-personalized Temporary Chat, removes the bridge with the plugin surface.

Decision: **KEEP as an alternate managed-workspace qualification path, not the personal-Plus primary path.**

### Approach B — non-personalized Temporary Chat + loopback HTTP collector/result callback

Advantages:

- #145 physically proved the basic mechanism;
- easy browser development and diagnostics.

Failure / fit problem:

- creates a listening port, ownership/authentication/liveness/late-request surface;
- duplicates a generic local callback/result-bus shape that #140 deliberately excluded;
- less tightly bound to one installed browser extension origin than Native Messaging.

Decision: **REJECT for production result handoff. Keep as experiment harness only.**

### Approach C — non-personalized Temporary Chat + submit-only Native Messaging bridge

Advantages:

- exact installed extension origin can be allowlisted by the native host;
- no localhost listening socket;
- result can flow into the **existing** `submit_independent_review_result` validator/state machine rather than creating a second result authority;
- extension->host message limit is far above the accepted review-result bound;
- host can return only a small receipt, so host->extension 1 MB limit is not a result problem.

Costs:

- new installer/registry/host packaging primitive;
- strict message framing, origin binding and response-loss semantics are required;
- private evidence delivery needs chunking or a bounded small package because host->extension messages are limited to 1 MB each.

Decision: **SELECT / NEW_ARCHITECTURE, narrowly limited to reviewer dispatch evidence retrieval and final result submission.** It is not a generic native command bus.

### Private repository evidence: direct Temporary Chat file vs Library

Direct Temporary Chat upload:

- narrower retention: OpenAI says Temporary Chat uploads are not saved to Library;
- no persistent Library cleanup/quota state;
- requires browser-companion file attachment mechanics and a bounded evidence package.

Library staging:

- reusable cache and easy later selection;
- files persist until deletion and create cleanup/quota/data-control obligations;
- experiment path is not physically accepted yet.

Decision: **direct Temporary Chat upload is the first private-repository path; Library is DEFERRED as an optional cache optimization.** If direct upload cannot be made reliable within the bounded adapter, automatic private review returns `ABSTAIN`; Library is not silently promoted as fallback.

## 7. Architecture lineage

Every affected existing role receives one canonical decision:

| Existing role | Prior selection | Decision | Reason |
|---|---|---|---|
| primary semantic reviewer | fresh ordinary ChatGPT | **KEEP** | Temporary Chat is still ordinary ChatGPT; no second planner |
| review protocol | `code-review` skill | **REFINE** | keep exact refs/falsification/result schema; allow CAP companion to submit the already-computed automatic result because plugin-free reviewer cannot call Local Bridge |
| bounded launch consequence | `procedure_run` | **KEEP** | development caller still starts only fixed `launch_independent_review_v1` |
| local operation lock | accepted Stage 26.3C OS lock | **KEEP** | same exact-operation ownership |
| immutable genesis | accepted exclusive-create mechanic | **KEEP** | no replacement nonce/persistence framework |
| mutable review state | accepted checkpoint mechanic | **KEEP** | existing result authority remains canonical |
| deep-link/composer mechanics | #138 experiment | **REFINE** | refine with #145 Temporary Chat evidence and a production companion adapter |
| browser Send ownership | MV3 service worker + IndexedDB claim | **KEEP** | still needed across tabs/service-worker lifecycle |
| reviewer authority qualification | disconnected/read-only reviewer environment | **REFINE** | add physically-qualified non-personalized Temporary Chat as personal-Plus primary qualification; retain read-only Action Control alternate |
| local result submission/reconciliation | fixed submit/reconcile state machine | **KEEP** | native handoff invokes the same validator/state transition; no second result store |
| automatic launch/correlation | `procedure_run` + local state + browser mechanics | **REFINE** | CAP owns full dispatch rather than a user-run harness |
| multi-chat/provider browser adaptation | CtxPort-derived ideas + project adapter | **REFINE** | use adapter/fallback organization only; reject internal ChatGPT backend/session API |
| development continuation | user-driven next planner turn | **KEEP** | no automatic same-task wake in this stage |

New architecture roles:

- **NEW_ARCHITECTURE — CAP Reviewer Browser Companion production package**: fixed ChatGPT-origin adapter, fresh Temporary Chat qualification, bounded file attachment, one-Send claim and final assistant-result capture.
- **NEW_ARCHITECTURE — submit-only Native Messaging host**: extension-origin-bound bridge into existing review state only.
- **NEW_ARCHITECTURE — `REVIEW_EVIDENCE_PACKAGE_V1`**: bounded immutable read-only repository evidence for private/no-public-fetch review.

Library is not selected as a new production role in this stage.

## 8. Selected bounded architecture

```text
procedure_run: launch_independent_review_v1
 -> prepare exact operation under accepted lock
 -> private review_run_id retained in Control Plane
 -> choose evidence mode
      public: immutable request, reviewer independently fetches public repository
      private: CAP builds bounded REVIEW_EVIDENCE_PACKAGE_V1 from exact local/provider read evidence
 -> persist dispatch-attempted BEFORE any browser launch
 -> launch fresh non-personalized Temporary Chat
 -> production Browser Companion proves expected Temporary-Chat UI/intent
 -> MV3 IndexedDB unique-key claim for review_run_id
 -> if private: service worker obtains bounded/chunked evidence from native host; content adapter attaches one file
 -> one automatic Send
 -> reviewer performs code-review/falsification; generic public technical research allowed, repository truth remains exact request/package
 -> final assistant REVIEW_RESULT_V1 + review_run_id + run-bound terminal marker
 -> content adapter extracts only final assistant turn
 -> service worker validates fixed envelope and calls submit-only native host
 -> native host resolves local state by review_run_id and calls existing submit_independent_review_result validator/state transition
 -> host returns bounded recorded/already-recorded/rejected receipt
 -> development later uses reconcile_independent_review_result_v1
```

No GitHub write exists in the reviewer or browser companion. No generic command, shell, filesystem path, URL, MCP tool or state-root parameter is accepted from the page/content script.

## 9. Private evidence package contract

`REVIEW_EVIDENCE_PACKAGE_V1` is an immutable read-only package bound to the same review identity and private run. It may contain only repository/review evidence required by the governed review, for example:

```text
manifest: repository / PR / BASE / HEAD / review policy version / review_run_id hash / package digest
BASE AGENTS.md
BASE code-review skill
applicable HEAD skills
changed-file inventory
exact BASE..HEAD diff
bounded full changed files / directly required related files when selected by deterministic package builder
bounded CI/acceptance metadata when private web evidence is unavailable
```

The package must not contain development-chat reasoning, proposed findings or an argument for correctness.

Initial production bound: the automatic private-review package must fit the documented ChatGPT attachment/token limits and a project-defined transfer budget. Native host -> extension transfer is chunked with every chunk below Chrome's 1 MB message limit and bound to one immutable package digest/offset sequence. Oversize/incomplete/hash-mismatched evidence returns `ABSTAIN`; it is never silently truncated into a PASS-capable review.

The package builder may read only the exact repository/provider evidence already authorized to the development side. It must not expose the development side's provider write credential/token to the reviewer or extension.

## 10. Authority model

### Reviewer authority

For personal Plus automatic mode, qualification requires:

1. a fresh Temporary Chat opened explicitly in non-personalized mode;
2. current product/UI evidence that the chat is Temporary and non-personalized under the supported adapter;
3. no plugin/app selection or personalization action performed by CAP;
4. fresh ChatGPT product documentation/physical qualification remaining consistent with plugin absence.

If this cannot be proved, `launch_independent_review_v1` fails closed before Send.

Managed workspace alternate: existing #140 read-only Action Control qualification remains valid when physically proved.

### Browser companion authority

The service worker owns privileged operations. Content scripts are treated as untrusted inputs and may request only fixed state transitions for the exact run bound to the current ChatGPT tab. They cannot select arbitrary native-host operations, paths, URLs or review identities.

### Native host authority

Accepted message families are fixed and small:

```text
get_review_dispatch_v1(review_run_id, bounded cursor)
submit_review_result_v1(review_run_id, complete result)
```

`get_review_dispatch_v1` returns only immutable data already prepared for that exact review operation (request metadata and, when private, bounded package chunks). It does not accept repository paths or provider URLs from the extension.

`submit_review_result_v1` performs only the existing local automatic-result validation/recording transition. It cannot launch a process, mutate GitHub, write arbitrary files, call MCP, execute shell/code or select another state root.

## 11. Failure / crash / ambiguity matrix

| Failure boundary | Durable authority before failure | Required behavior | Automatic retry permission | Max extra external effect |
|---|---|---|---|---:|
| invalid launch identity | none | reject before operation/browser | no | 0 |
| concurrent launch callers | operation lock | one operation owner; other reconciles | no duplicate launch | 0 extra launches |
| crash before genesis/state | none/accepted existing rules | existing #141 behavior | only clean first creation | 0 |
| valid genesis, missing/corrupt state | genesis only/invalid pair | existing manual-only/fail-closed rules | no automatic relaunch | 0 |
| prepared state, evidence build fails/oversize | prepared | return `ABSTAIN`, no browser launch | same exact operation may be manually closed; automatic retry only if no dispatch consequence and policy explicitly permits a fresh deterministic pre-dispatch build | 0 launches |
| dispatch-attempted persistence fails | old prepared state | no browser launch | may retry state transition under lock | 0 launches |
| dispatch-attempted committed, process crashes before browser open | dispatch-attempted | ambiguous dispatch; no blind relaunch | no | 0 extra launches |
| browser launch/open ambiguous | dispatch-attempted | diagnose/reconcile only; manual fallback remains | no blind relaunch | 0 extra launches |
| Temporary Chat/non-personalized qualification absent | dispatch-attempted | no Send; record failure class; manual fallback | no same-run automatic Send elsewhere | 0 Sends |
| two tabs see same run | dispatch-attempted + IDB | exactly one committed Send claim | loser never Sends | 0 extra Sends |
| claim commit response lost/tab dies | committed IDB claim | no regrant; manual fallback | no | 0 extra Sends |
| private package chunk missing/out of order/hash mismatch | dispatch-attempted, no Send claim yet or claim not granted | no Send; fail closed | no blind new tab/run; same tab may continue only within deterministic pre-Send bounded transfer if ownership remains unambiguous | 0 Sends |
| private file attachment UI unsupported/ambiguous | dispatch-attempted | no Send; fail closed/manual fallback | no blind cross-route fallback to Library/web repository | 0 Sends |
| page changes after qualification before Send | claim/DOM evidence | revalidate route/composer/Temporary state immediately before click; otherwise no Send | no regrant | 0 Sends |
| reviewer uses generic web research | review in progress | allowed; repository/private identifiers must not be intentionally emitted by CAP research prompt; repository truth stays exact request/package | n/a | 0 repository mutations |
| reviewer returns STALE/ABSTAIN | no completing local result | do not close automatic result slot as completing; reconcile/manual fresh review required | no blind automatic relaunch | 0 repo effects |
| final assistant response lacks exact terminal marker/schema | no local result | do not submit; manual fallback/reconciliation | no arbitrary parser relaxation | 0 |
| content script forged/malformed submit request | existing local state | service worker/native host schema + exact-run validation rejects | no privileged fallback | 0 |
| native submit rejected before local state commit | result_state=open | no result authority | exact same complete result may be re-attempted only if extension/native acknowledgement proves no commit; otherwise reconcile local state first | 0 repo effects |
| local automatic-result commit succeeds, native acknowledgement lost | automatic-result-recorded | later same nonce/digest returns `already_recorded`; never create another result | reconciliation only | 0 repo effects |
| automatic submit races manual fallback | same operation lock | existing winner-commits semantics | loser cannot overwrite | 0 late accepted results |
| manual fallback commits first | manual-fallback-recorded | native late submit rejected | no | 0 |
| HEAD/base moves while reviewer works | old exact identity | result becomes stale/not merge-authoritative; fresh exact review required | new operation only for new exact identity | 0 stale merge authority |
| extension/native host unavailable | local operation state | fail closed/manual fresh review | no alternate broad bridge | 0 |
| Library unavailable | not selected production dependency | no effect | n/a | 0 |
| hostile deletion/storage rollback/power loss | outside accepted local guarantee | no stronger claim | outside scope | no false guarantee |

No release-critical cell is left `unknown` within the declared cooperating process-crash, installed-browser-companion and bounded target-Windows scope. UI/product drift is handled as `ABSTAIN`/manual fallback rather than optimistic continuation.

## 12. Verification plan

### Deterministic tests

- exact request schema remains fixed; no arbitrary URL/prompt/command inputs;
- `review_run_id` stays private from the development caller before result closure;
- `dispatch-attempted` persists before browser-launch call;
- production launcher cannot invoke browser after prepared->dispatch persistence failure;
- extension manifest exposes only ChatGPT origin + `nativeMessaging` permission required for the fixed host; no arbitrary host permissions;
- service worker validates sender origin/tab/run and owns native calls/IDB claim;
- content script cannot select native operation, path, URL or state root;
- native host validates caller origin supplied by Chrome and fixed exact message schemas;
- native host accepts only exact prepared review run; unknown/closed/mismatched run rejected;
- package chunk sequence/digest/bounds validated; no silent truncation;
- private evidence package contains no development reasoning/finding hints;
- direct file attachment happens before Send and is bound to the exact run/package digest;
- exactly one Send claim under deterministic and concurrent-tab tests;
- capture accepts only final assistant turn with exact run terminal marker and complete `REVIEW_RESULT_V1`;
- native result handoff reuses existing `submit_independent_review_result` validation/state machine;
- lost acknowledgement idempotence and manual-fallback race tests;
- `STALE`/`ABSTAIN` remain non-completing;
- existing six public tools remain exactly six;
- no generic scheduler/wake/result bus/GitHub writer appears.

### Source / installer provenance

Production acceptance must bind the installed Browser Companion files and Native Messaging host bytes/configuration to the exact reviewed source/install manifest. Existing Windows L3 provenance rules must be extended so a stale/foreign extension or native host cannot satisfy the review gate.

### Physical target-Windows gates

At minimum:

1. `procedure_run launch_independent_review_v1` from the ordinary development Chat, no user PowerShell harness;
2. automatic fresh non-personalized Temporary Chat opens and proves qualification;
3. one automatic Send;
4. accepted public control reaches exact semantic result and local `automatic-result-recorded` state;
5. known-finding control recovers real defects and records them through native handoff;
6. private bounded package control performs direct file attachment and review without repository web lookup;
7. duplicate-tab / lost-native-ack / stale-head / extension-host-unavailable negatives fail closed;
8. development `reconcile_independent_review_result_v1` retrieves the automatic result without user copy/paste.

After the first honest E2E, run the already-selected Harbor evaluation seam; semantic quality and lifecycle reliability stay separate.

## 13. Complexity budget

This NARROW permits only:

- one production ChatGPT Browser Companion adapter/package;
- one fixed Native Messaging host registration/entrypoint;
- two native message families (`get_review_dispatch_v1`, `submit_review_result_v1`);
- one bounded private evidence package schema/builder;
- refinements to `launch_independent_review_v1` and code-review automatic handoff language;
- focused installer/provenance/tests/docs.

Explicitly forbidden in this stage:

- generic native command bus;
- arbitrary filesystem/native execution;
- generic local HTTP callback server;
- reviewer GitHub write credential/action;
- internal ChatGPT session/backend API scraping;
- Library as mandatory production state;
- generic scheduler/event bus;
- automatic wake/resample of the development planner;
- seventh public semantic tool;
- second result persistence/state machine.

## 14. Architecture decision

**NARROW.**

Implementation may proceed only for this selected composition:

```text
existing exact review operation/state/reconcile
 + CAP-owned production Browser Companion
 + physically qualified non-personalized Temporary Chat for personal Plus
 + existing managed read-only Action Control path as alternate environment
 + MV3/IndexedDB one-Send claim
 + public web evidence for public repositories
 + bounded direct-upload REVIEW_EVIDENCE_PACKAGE_V1 for private/no-public-fetch repositories
 + submit-only Native Messaging handoff into the existing automatic-result validator/state
 + no GitHub write
 + no general developer wake
```

A later requirement for persistent Library caching, arbitrary evidence fetch, a generic native/local bus, broader native execution, automatic same-task developer wake, provider write authority, unbounded private-repository transfer or internal ChatGPT backend/session APIs invalidates this decision and requires Stage Research re-entry.

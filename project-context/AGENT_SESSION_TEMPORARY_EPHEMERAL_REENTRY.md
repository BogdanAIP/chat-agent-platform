# Agent Session Temporary-Chat ephemeral recovery re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-04**

Triggering PR: **#149**

Triggering HEAD: `339f2c44805994e6acff3be29da458b14ad0e1bb`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skills at the triggering HEAD:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

This brief is a physical-qualification-triggered re-entry for the first `chatgpt-temporary` adapter. It supersedes only the requirement that this specialized Temporary Chat worker provide positive same-conversation recovery across a complete Chrome/browser-context restart. It does not weaken the generic Delegation identity/state model, one-Send/no-blind-resend rules, runtime provenance, result correlation or future persistent-session architecture.

## 1. Triggering physical evidence

The exact-head target-Windows qualification on `339f2c44805994e6acff3be29da458b14ad0e1bb` established the following real behavior for one fresh `fresh_readonly_worker_v1` Temporary Chat run:

```text
initial launch authority = one
physical Send count = one
delivery-visible = observed
launch_state = child-bound
delivery_state = delivered
result_state = open
worker produced a valid terminal WORKER_RESULT_V1
```

However, the exact extension-origin IndexedDB claim for that same `delivery_id` retained:

```text
conversation_id = null
```

through the useful lifetime of the run. A previous complete-Chrome-restart-before-conversation-binding qualification also proved that the ephemeral live pre-Send witness disappears across browser/service-worker lifetime loss and no additional Send authority is reconstructed.

The prior `AGENT_SESSION_BROWSER_RECOVERY_HARDENING.md` explicitly required Stage Research re-entry if stable provider conversation identity could not be positively observed before useful restart recovery or if Temporary Chat did not preserve the assumed stable conversation route. That re-entry condition is now met by physical evidence rather than speculation.

## 2. Current external product evidence

OpenAI's current Temporary Chat FAQ (researched 2026-09-04) states that unsaved Temporary Chats do not appear in chat history; non-personalized Temporary Chats do not use memory, custom instructions or plugins; and saving a Temporary Chat converts it into a regular chat. Source: `https://help.openai.com/en/articles/8914046`.

This is product/documentation evidence, not open implementation evidence. ChatGPT's browser/server implementation is closed for this mechanism, so the exact cross-restart provider identity contract remains **CLOSED_OR_UNKNOWN** from source-code-research perspective. CAP therefore must not invent a release-critical persistent-session guarantee from an unobserved route convention.

The current product distinction also aligns with the accepted use of this profile: `fresh_readonly_worker_v1` exists to obtain an intentionally fresh/non-personalized bounded worker. Converting that conversation into a regular saved chat merely to gain durable history would change the profile semantics instead of proving the Temporary adapter.

## 3. Exact stage question

> What is the smallest safe recovery contract for the specialized `fresh_readonly_worker_v1` Temporary Chat adapter when physical evidence proves one-Send delivery/result capture in an uninterrupted browser context but does not prove a stable provider conversation identity across complete Chrome restart?

The selected answer must preserve:

- one deterministic delegation identity;
- one private durable run capability;
- one durable browser delivery claim;
- at most one physical Send authority;
- `unknown` after ambiguous Send and no blind resend;
- exact worker/result correlation;
- exact runtime/source provenance;
- fresh/non-personalized/no-plugin profile qualification;
- bounded durable local terminal closure when the task was definitely delivered but browser result capture is lost;
- the provider-neutral generic core and exactly-six public Chat-facing tools.

Out of scope:

- persistent ordinary-ChatGPT session implementation;
- generic existing-session delivery/wake;
- Prime integration;
- saving/converting Temporary Chat into a regular conversation;
- browser-session leases, recovery secrets or another provider-specific durable identity service;
- relaunching a second worker after an ambiguous or completed Send.

## 4. Architecture lineage

### Bounded Agent Session / Delegation lifecycle — `KEEP`

Keep generic deterministic delegation identity, private run capability, launch/delivery/result states, crash-safe persistence, one terminal result contract and exact correlation.

### First-provider browser delivery ownership — `KEEP`

Keep the extension-origin IndexedDB unique delivery claim and `LIVE_PRE_SEND_CLAIMS` witness. The durable claim prevents another Send; the ephemeral witness allows only the narrow same-service-worker pre-Send owner path and intentionally disappears across browser/service-worker lifetime loss.

### `chatgpt-temporary` provider/profile adapter — `REFINE`

Make its lifetime contract explicitly **ephemeral one-shot**:

```text
fresh qualified Temporary Chat
 -> one bounded Send
 -> uninterrupted observation/capture when available
 -> one correlated result
```

A complete browser-context loss does not create a recoverable persistent session promise.

### Provider-conversation post-restart recovery — `REJECT for this profile / DEFER to persistent-session research`

The prior provider `conversation_id` recovery mechanism is not justified for `fresh_readonly_worker_v1` because the required stable identity was not physically observable. The persistent-conversation problem remains real for future ordinary rich-context sessions and belongs to later Prime/existing-session Stage Research.

### Stable cleanup/capture token semantics — `KEEP`

Idempotent cleanup acknowledgement and two-phase capture remain useful in the uninterrupted/same-context path and for controller/network acknowledgement loss. They do not require cross-Chrome multi-monitor recovery.

### Capability authorization / Verification Kernel / Finish Gate — `KEEP`

Worker output remains data/evidence, not project authority. Nothing here widens child capabilities or changes completion authority.

No baseline role is replaced by a new external component and no new generic state owner is introduced.

## 5. Source-code research boundary

No new public runtime component is introduced by this decision. Existing exact-source Codex/OpenHands comparisons in `AGENT_SESSION_DELEGATION_REENTRY.md` remain applicable to generic parent/child/delegation mechanics.

For the changed mechanism, the strongest evidence is instead:

- exact current CAP source showing provider-conversation recovery is entirely inside the `chatgpt-temporary` browser adapter;
- exact current CAP tests/review lineage showing the generic delegation core does not require a provider conversation id;
- current official OpenAI Temporary Chat product behavior;
- target-Windows physical evidence showing the assumed stable provider identity was not observed.

Classification for the ChatGPT cross-restart provider identity mechanism: **CLOSED_OR_UNKNOWN** externally, and **physically unproven on the current target path**.

Lesson classification: **REJECT_MECHANIC for the current Temporary profile**, not because persistent conversation recovery is generally wrong, but because this provider/profile does not currently supply the release-critical identity evidence the mechanism requires.

## 6. Architecture primitives and adjacent domains

This re-entry removes a provider-specific recovery primitive rather than adding a replacement identity system.

One bounded behavior is tightened: **delivered-timeout terminalization**. If CAP has durable proof that the task was delivered, the result is still open, and the browser context can no longer provide terminal observation/capture by the configured timeout/grace boundary, the controller may record one correlated `ERROR` result through the existing result state machine. This is a local workflow timeout outcome, not evidence that the worker failed semantically and not permission to Send again.

Domain: durable workflow timeout/cancellation and terminal-state closure.

Required guarantees:

- terminalization is allowed only from `delivery_state=delivered` and `result_state=open`;
- it uses the existing exact delegation/delivery/run/result contract;
- it performs zero additional browser/worker effects;
- later duplicate/foreign results cannot replace the recorded terminal result;
- `claimed`/`unknown` delivery remains unresolved and cannot be falsely closed as a worker result because delivery itself is not proven.

No new queue, lease, journal, scheduler, registry or persistence framework is introduced.

## 7. Problem evidence versus solution evidence

### Problem evidence

The current positive recovery gate assumes a stable provider conversation identity that target-Windows physical evidence did not observe. Continuing to harden that recovery path would force CAP to invent another browser/provider identity mechanism for a specialized ephemeral profile.

The same physical run proved that the actual intended reviewer-style value still works without that identity: one fresh child, one Send, delivered task and a valid result in the uninterrupted path.

### Solution evidence

The durable IndexedDB claim already provides the safety property that matters after browser loss: the same logical delivery cannot regain blind Send authority. `LIVE_PRE_SEND_CLAIMS` deliberately loses liveness across browser/service-worker lifetime loss, which is the correct fail-closed behavior for pre-Send ambiguity.

The generic state machine already separates delivery from result and permits a terminal result only after `delivered`; therefore a controller-generated timeout `ERROR` can close a definitely delivered/open delegation without inventing a second physical action. No new state model is needed.

Current OpenAI Temporary Chat behavior supports treating the unsaved non-personalized chat as an independence mechanism rather than a durable history/session primitive.

## 8. Materially distinct approaches

### A — keep positive cross-Chrome recovery and invent another durable provider/browser identity

Possible mechanisms include a page secret, browser-session generation, controller lease or another recovery capability.

Strength: could retain same-conversation recovery despite current route behavior.

Failure/cost: introduces a new persistence/security/recovery primitive solely for an ephemeral specialist profile, with new duplication/ABA/secret-restoration questions and no current product need.

Decision: **REJECT for #149**. Reconsider only for the later persistent existing-session capability where recovery is an actual product requirement.

### B — save/convert the Temporary Chat into a regular chat before relying on restart

Strength: creates ordinary history/persistent-conversation semantics.

Failure: changes the worker profile being qualified. OpenAI documents that saving converts the Temporary Chat into a regular chat; this is not proof of the fresh Temporary adapter and can reintroduce persistent-context semantics the reviewer profile intentionally excludes.

Decision: **REJECT**.

### C — ephemeral one-shot Temporary adapter with fail-closed browser-loss semantics

Mechanism:

```text
one fresh Temporary Chat
 -> durable claim before Send
 -> one Send
 -> uninterrupted capture when available
 -> if complete browser context is lost: no recovery/no re-Send
 -> if delivery was proven and result cannot be captured before timeout: durable ERROR closure
```

Strengths:

- matches the actual specialist profile;
- uses existing state/claim mechanisms;
- preserves no-blind-resend;
- removes unproven provider identity assumptions;
- does not pre-empt future persistent-session architecture;
- is sufficient for MimiSeek-style fresh independent review launch/result when the browser remains available for the bounded run.

Decision: **SELECTED / NARROW**.

### D — automatically launch a replacement Temporary worker after browser loss

Strength: restores liveness.

Failure: creates a second reasoning execution for the same logical delegation after an already delivered or ambiguous Send, violating the no-blind-relaunch/no-duplicate-decision boundary.

Decision: **REJECT**.

## 9. Failure / crash matrix

| Boundary | Durable state | Possible physical state | Required rule | Additional Send authority |
|---|---|---|---|---|
| Before genesis | none | no child | normal new operation | one initial path only |
| Prepared -> launch-attempted | launch attempted | browser launch absent/present | no blind second launch | none from restart |
| Browser claim committed, before Send | claim exists + live witness only in current worker lifetime | Send not yet clicked | same live owner may complete narrow pre-Send path; browser/service-worker lifetime loss destroys witness | none after lifetime loss |
| Send clicked, delivery still claimed | claimed | message absent/present/unknown | observe/reconcile only; no second Send | none |
| Delivery unknown | unknown | message may exist | preserve unknown; no terminal worker result and no re-Send | none |
| Delivery proven, browser alive | delivered/open | worker running/result may appear | normal cleanup/capture path | none |
| Delivery proven, controller restarts while original browser context remains alive | delivered/open | original content context still carries exact run correlation | reconnect to controller/status/capture only; no new browser launch/Send | none |
| Delivery proven, complete Chrome/browser-context loss before capture | delivered/open | worker result may or may not have existed | no cross-browser recovery; after timeout/grace record one local correlated ERROR if still delivered/open | none |
| Complete Chrome restart opens same/foreign ChatGPT page | durable delivery claim persists | no trusted original content context | page has no recovery capability; extension must not disclose run_id or create monitor/send authority | none |
| Result already recorded | delivered/recorded | browser may disappear | terminal readback only | none |
| Runtime/HEAD changes | old durable state/claim | new extension/controller bytes | existing provenance/generation gates fail closed | none |

No release-critical cell requires restoration of a Temporary Chat conversation after complete browser-context loss.

## 10. Minimum implementation

Production changes are limited to:

1. remove provider-conversation binding/recovery as an accepted behavior of `chatgpt-temporary`;
2. remove `resume-intent` / post-restart provider-conversation recovery capability disclosure from the MV3 adapter;
3. stop persisting `conversation_id` in the browser Send claim for this profile; provider conversation data may remain an optional observation in generic child evidence but is not recovery authority;
4. preserve the durable unique delivery claim and same-live-worker pre-Send owner fence so complete browser/service-worker restart can never recreate Send authority;
5. preserve delivery ACK-loss reconciliation, controller status reconciliation, stable cleanup acknowledgement and two-phase result capture for the uninterrupted/original-context path;
6. add deterministic delivered/open timeout terminalization to one `ERROR` result through the existing result state machine when browser final observation/capture cannot close the run;
7. update adapter comments/docs/tests so `chatgpt-temporary` is explicitly ephemeral and future persistent/existing-session recovery is not implied;
8. do not add Prime, an existing-session adapter, a provider identity framework, a lease, another public tool or a new generic state field in PR #149.

## 11. Acceptance shields

Focused/adversarial tests must prove:

- first live browser context can still obtain at most one Send authority;
- same-worker duplicate tab cannot steal pre-Send ownership;
- loss of the MV3/background lifetime prevents prepared-claim Send recovery even if a numeric tab id is reused;
- no `resume-intent` or provider-conversation recovery path can disclose `run_id` after complete browser restart;
- claimed/unknown/delivered state never grants a second Send;
- delivery ACK-loss retry/reconciliation remains idempotent;
- controller transport interruption during capture still re-arms the original live context safely;
- stable cleanup acknowledgement remains idempotent;
- uninterrupted Temporary Chat launch -> one Send -> delivered -> exact structured result still succeeds;
- delivered/open timeout without final browser observation records one correlated `ERROR` and never performs another physical effect;
- unknown/undelivered timeout does not fabricate a worker result;
- cross-HEAD/runtime provenance protections remain intact.

Final target-Windows physical evidence for the eventual frozen HEAD is narrowed to the actual profile guarantee:

```text
A. normal bounded run
fresh non-personalized Temporary Chat
 -> exact runtime provenance
 -> exactly one Send
 -> delivered
 -> exact WORKER_RESULT captured/recorded

B. browser-loss fail-closed run
fresh qualified Temporary Chat
 -> exactly one Send / delivery proven
 -> complete Chrome close
 -> restart cannot obtain Send or monitor/recovery authority
 -> zero second Send
 -> local delivered-timeout ERROR closure or already-recorded terminal result
```

The earlier complete-Chrome pre-Send negative evidence remains relevant to the one-Send fence. The previous **positive conversation-bound restart recovery gate is superseded and removed** for this profile.

Any code/documentation change made under this brief moves HEAD and makes the semantic PASS on `339f2c44805994e6acff3be29da458b14ad0e1bb` stale. The final merge ladder is therefore:

```text
implement narrow change
 -> focused/adversarial tests
 -> preliminary exact-head hosted CI
 -> freeze BASE/HEAD
 -> genuinely fresh ordinary-ChatGPT code-review v1.1
 -> validate/fix findings; fresh review again if HEAD moves
 -> final target-Windows physical A+B qualification
 -> final exact-head hosted CI
 -> re-resolve BASE/HEAD unchanged
 -> mark ready and merge
```

## 12. Decision

**NARROW**.

Proceed with the ephemeral one-shot `chatgpt-temporary` adapter described above.

The generic Agent Session / Delegation foundation remains provider-neutral and reusable. `fresh_readonly_worker_v1` remains a specialized independent-worker profile. Persistent rich-context conversation identity, browser wake and cross-restart existing-session delivery remain separate later research, intentionally sequenced after #149 and after the Prime ownership decision.
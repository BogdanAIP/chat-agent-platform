# Agent Session Temporary-Chat capture linearization re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-08**

Triggering PR: **#149**

Triggering HEAD before this brief: `1f396ce08e3221a4e60ca2a55d3ea1ae27e3d2ff`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable skill: `.agents/skills/stage-research/SKILL.md` v1.2.

## 1. Triggering evidence

A fresh ordinary-ChatGPT semantic review of exact HEAD `1f396ce08e3221a4e60ca2a55d3ea1ae27e3d2ff` reported two surviving findings:

1. **P1 — ancestor mutation blind spot.** `authorityMutation()` classified an attribute mutation target only when that target was itself an authority node or a descendant of one. This did not mirror `guardVisible()` / `eligibleComposerEditor()`, which intentionally walk ancestors. Therefore a transient `hidden` / `inert` / `aria-hidden` / `disabled` / `readonly` / `class` / `style` transition on an ancestor containing the current correlated turn or composer could disappear before the 500 ms poll without advancing `guardEpoch`.
2. **P2 — post-dispatch revocation ambiguity.** `captureResult()` revalidated cleanup token, guard epoch and current browser result immediately before `chrome.runtime.sendMessage({kind:"capture"})`, but the controller durably records the already-dispatched immutable request later. A later provider DOM mutation cannot retroactively cancel a one-time extension message already sent to the service worker/controller.

The P1 mechanism is a narrow bug in the mutation classifier and does not require new architecture. The P2 question is architectural because it asks where the consequence-bearing result-capture operation linearizes across browser content script -> MV3 service worker -> authenticated loopback controller.

## 2. Exact stage question

> For the specialized ephemeral `fresh_readonly_worker_v1` Temporary Chat adapter, what is the smallest safe and reviewable linearization rule for one exact correlated result capture across an asynchronous browser/service-worker/controller boundary, without introducing a durable browser lease or another state service?

The decision must preserve:

- one fresh bounded worker and at most one physical Send;
- exact task/result correlation;
- exact current browser qualification before capture authority;
- mutation-driven revocation before capture linearization;
- no stale pre-prepare continuation after correlation/composer/result change;
- exact runtime/source provenance;
- no new persistent-session or cross-browser recovery promise;
- provider-neutral generic Delegation state;
- no fabricated worker result;
- project Verification Kernel / Finish Gate authority unchanged.

Out of scope:

- a generic browser lease service;
- WebSocket/session-stream infrastructure solely for Temporary Chat capture;
- making a provider DOM state transactionally participate in controller disk persistence;
- persistent ordinary-ChatGPT session identity;
- another Send/relaunch path;
- new public tools or generic scheduler/event bus.

## 3. Architecture lineage

Relevant baseline roles from `ARCHITECTURE_REUSE_BASELINE.md`:

- **Agent-session first-provider fresh-chat/composer mechanics** — prior posture `REUSE_MORE`.
- **Agent-session first-provider browser delivery ownership** — prior posture `REFINE`.
- **Bounded Agent Session / Delegation lifecycle** — prior posture `REFINE`.
- **Capability authorization / consequence policy** — project-owned.
- **Transition verification / Finish Gate** — project-owned.

Decision for this re-entry:

- first-provider browser capture mechanics: **REFINE** — make the browser capture linearization point explicit and executable;
- generic Delegation lifecycle: **KEEP** — no generic state field or controller service is added;
- capability/verification authority: **KEEP** — worker result remains data/evidence only.

No baseline role is replaced. No external runtime component is adopted.

## 4. Engineering evidence

### Linearizability

Herlihy and Wing define linearizability as the illusion that each concurrent operation takes effect instantaneously at some point between invocation and response. The important consequence for this adapter is that an asynchronous capture operation needs one explicit effect point; later state changes are ordered *after* that point and cannot retroactively revoke an already-linearized operation.

Primary bibliographic source:

- Maurice P. Herlihy, Jeannette M. Wing, **“Linearizability: A Correctness Condition for Concurrent Objects”**, ACM TOPLAS 12(3), 1990, DOI `10.1145/78969.78972`.

### Chrome extension messaging

Chrome documents `runtime.sendMessage()` / `tabs.sendMessage()` as one-time asynchronous JSON-serializable requests between extension contexts. The caller awaits a later response; the request and the response are therefore separated by an asynchronous boundary rather than a synchronous transaction with page DOM state.

Source:

- `https://developer.chrome.com/docs/extensions/develop/concepts/messaging`

### Mutation observation

The DOM Standard queues MutationObserver notification through the microtask mechanism. MutationObserver therefore provides a strong way to invalidate authority for qualifying DOM mutations that occur *before* capture linearization, but it is not a distributed transaction tying future page mutations to controller persistence.

Sources:

- `https://dom.spec.whatwg.org/#mutation-observers`
- `https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver/takeRecords`

`MutationObserver.takeRecords()` is especially relevant at the final browser boundary because it synchronously drains matching changes already detected but not yet delivered to the observer callback.

## 5. Problem evidence vs solution evidence

### Problem evidence

The review demonstrated two distinct TOCTOU classes:

- an ancestor-attribute mutation could be missed entirely by the previous classifier;
- a browser UI change can always occur after an asynchronous capture request has been sent but before a later controller acknowledgement/persistence completes.

The first is a production bug. The second is a boundary-definition problem: without a declared linearization point, “current until durable disk record” implicitly asks two independently scheduled systems (provider DOM and controller persistence) to behave as one transaction.

### Solution evidence

The existing adapter already has the right narrow ingredients before dispatch:

- exact current correlated user turn;
- exactly one eligible composer/editor;
- current assistant result text;
- Stop/generation rejection;
- stable cleanup token;
- guard epoch;
- two-phase prepare/capture token;
- authenticated one-time extension message;
- exact controller correlation and result validation.

The minimum sufficient refinement is therefore:

1. all authority-relevant DOM mutations before capture dispatch invalidate the browser guard epoch;
2. immediately before dispatch, synchronously drain pending MutationObserver records and re-evaluate exact current authority/result;
3. the **successful invocation of the one-time `capture` message after that final synchronous revalidation is the capture linearization point**;
4. the immutable `result_text` in that message is the authorized snapshot for that linearized operation;
5. controller persistence is completion/acknowledgement of the already-linearized capture operation, not a second browser-authority decision;
6. a mutation that occurs before dispatch must prevent that dispatch; a mutation that occurs after dispatch is ordered after the capture and cannot retroactively revoke it.

This does not make controller success equivalent to task completion. It only defines when the browser-authorized capture effect happens.

## 6. Materially distinct approaches

### A — Require browser authority to remain revocable until controller durable write

Mechanism: treat every provider DOM change until controller record completion as a retroactive veto.

Problem: content-script DOM state and controller persistence are not one transaction. A mutation can race with an already-dispatched request. Closing that race absolutely requires a stronger cross-context primitive than the current one-time message.

Fit: **REJECT** for #149. The requirement is not implementable by another local recheck alone.

### B — Introduce a controller-visible browser lease / streaming revocation channel

Mechanism: maintain a lease or long-lived channel whose revocation is visible to the controller before commit.

Strength: moves more authority state into a shared protocol.

Failure/cost: introduces lease identity, expiry, reconnection, ordering, browser-loss and ABA questions; still requires defining the final commit/linearization ordering. It materially enlarges the first-provider adapter and conflicts with the accepted ephemeral one-shot scope that explicitly rejected a new durable browser/session lease for this profile.

Fit: **DEFER / REJECT for #149**. Reconsider only if a future persistent-session capability has a real consumer for such a primitive.

### C — Final synchronous browser fence + one-time capture dispatch as linearization point

Mechanism: MutationObserver invalidates pre-dispatch authority; pending records are synchronously drained; current correlation/composer/result/Stop state and guard epoch are rechecked; one immutable `capture` message is then dispatched exactly once.

Strengths:

- uses current mechanisms;
- gives the operation one explicit effect point;
- closes stale pre-dispatch continuations;
- does not invent a distributed lease;
- preserves original-context ephemeral semantics;
- keeps provider DOM authority out of generic delegation state.

Fit: **SELECTED / NARROW**.

## 7. Failure / concurrency matrix

| Boundary | Browser state | Controller state | Required rule |
|---|---|---|---|
| Before cleanup qualification | mutable/dirty | delivered/open | no capture |
| Cleanup stable, before prepare | exact current authority | delivered/open | prepare may start |
| Prepare in flight, relevant DOM mutation | authority invalidated, epoch advances | capture token may exist/reuse | old continuation cannot dispatch capture |
| Prepare returns, pending MutationObserver records exist | not yet callback-delivered | capture prepared | drain records synchronously; invalidate/recheck before dispatch |
| Final synchronous recheck fails | dirty/mismatched/generating | capture prepared | zero capture dispatch; requalify from fresh epoch |
| Final synchronous recheck passes | exact current authority | capture prepared | one immutable capture request may linearize |
| DOM changes after capture dispatch | later browser state | capture request already linearized | later change does not retroactively revoke prior capture |
| Capture transport/ACK ambiguous | browser may still be alive | controller may have recorded or not | status reconciliation only; no duplicate Send; capture retry only under existing token/idempotency rules |
| Result recorded | any later browser state | delivered/recorded | terminal result readback only |
| Complete browser loss before dispatch | authority gone | delivered/open | unresolved fail-closed; no cross-browser recovery |

No cell grants another Send.

## 8. Minimum implementation / guards

P1 narrow fix:

- for attribute mutation records, classify an ancestor target as authority-relevant when its subtree contains a correlated turn, assistant turn, composer/editor or Stop control;
- preserve direct/descendant classification for child-list/character-data mutations;
- add production-policy regression covering ancestor `hidden` / `inert` / `aria-hidden` / `class` / `style` style eligibility transitions.

P2 boundary refinement:

- expose a synchronous policy fence that drains pending mutation records (`takeRecords()`) and applies the same authority mutation classifier before returning capture authorization;
- execute that fence immediately before the one-time capture dispatch;
- require the exact current assistant text to equal the immutable result being dispatched;
- keep cleanup-token + guard-epoch equality from the prior ABA closure;
- document/test that capture dispatch is the linearization point;
- do not add a lease, WebSocket, new persistent state owner or generic delegation field.

If implementation discovers that these guards cannot be expressed with the current browser policy/content boundary, this brief becomes invalid and production work must re-enter Stage Research before adding a new primitive.

## 9. Acceptance shields

Executable tests must prove production behavior for:

- ancestor attribute mutation around an eligible composer invalidates the current epoch even if restored before the 500 ms poll;
- ancestor attribute mutation around the correlated user turn invalidates the current epoch;
- a pending MutationObserver record is drained by the final capture fence before dispatch;
- result text changed before dispatch prevents capture;
- Stop/generation present before dispatch prevents capture;
- cleanup token or guard epoch changed before dispatch prevents capture;
- exactly one capture message is dispatched after the final clean fence;
- no test-only epoch increment substitutes for production mutation classification;
- unchanged one-Send/browser-loss/provenance contracts continue to pass.

Physical A0/A/B1/B2 from older HEADs remain stale after any runtime change.

## 10. Decision

**NARROW**.

Proceed with the ancestor-mutation fix and an explicit final browser capture fence. The one-time capture message dispatch after synchronous authority/result revalidation is the effect linearization point. Controller persistence is completion of that already-authorized immutable operation. Do not introduce a distributed browser lease or persistent-session mechanism in PR #149.

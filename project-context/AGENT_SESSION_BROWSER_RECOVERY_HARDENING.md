# Agent Session Browser Recovery Hardening

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-03**

Triggering reviewed HEAD: `a76007acf9c54a78d51ce183db0d4806b4e1add8`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable skills:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/code-review/SKILL.md` v1.1 for the triggering independent finding evidence

This brief is a review-triggered re-entry for the first `chatgpt-temporary` provider adapter. It revises only the browser-restart recovery/cleanup part of `AGENT_SESSION_DELEGATION_REENTRY.md`; the generic one-manager/one-read-only-worker scope remains unchanged.

## 1. Trigger and independently confirmed failures

The fresh ordinary-ChatGPT review of exact HEAD `a76007acf9c54a78d51ce183db0d4806b4e1add8` reported two concrete defects. Both survive development-side falsification against the exact code and tests.

### P1 — foreign ChatGPT conversation can recover the private run capability

Current `content.js::observedRecoveryClaims()` extracts only:

```text
delegation_id
delivery_id
task_sha256
```

from visible user turns. `background.js::observedClaimMatches()` matches only those same three visible values against extension-origin IndexedDB. When one active claim matches, `resumeIntent()` returns the claim's private `run_id`, `expected_runtime_head` and `prompt_sha256` to the requesting ChatGPT page.

Chrome's `sender.tab.id` cannot supply durable recovery identity because Chrome documents tab IDs as unique only within one browser session. The current code intentionally stopped persisting numeric tab IDs, but replaced them only with delivery correlation. A different ChatGPT conversation containing copied visible markers can therefore acquire the private controller capability and participate in result/final-observation authority.

### P2 — cleanup acknowledgement token has last-writer-wins ABA/liveness behavior

`TemporaryControllerState.record_event()` creates a new cleanup token for every valid post-delivery cleanup acknowledgement and unconditionally overwrites the one process-wide `self.cleanup_token`.

Browser restart can create multiple monitor-only content contexts for the same restored conversation. If A receives token A and B later receives token B, A's `prepare-capture(token A)` is rejected. The current browser guard does not learn that its server-side token was replaced, so a result-bearing tab can stay stuck with a locally valid but server-stale token until timeout.

These are release-critical identity/recovery/concurrency changes, so the prior 2026-09-01 Stage Research decision is insufficient for this subproblem until revised here.

## 2. Current project truth and lineage

Affected existing baseline roles:

### Multi-chat / provider conversation extraction and browser adaptation — `REFINE`

Keep provider-specific conversation identity below the generic delegation boundary. Do not promote ChatGPT conversation IDs into generic `DelegationIdentity`.

### Bounded Agent Session / Delegation lifecycle — `KEEP`

The generic deterministic delegation/run/delivery/result identities remain unchanged. The defect is in provider recovery authority, not the generic state model.

### Agent-session first-provider browser delivery ownership — `REFINE`

Keep the extension-origin IndexedDB unique delivery claim and one-Send ownership, but extend the claim with one provider-generated stable conversation binding before it can be used for post-restart recovery.

### Capability authorization / consequence policy — `KEEP`

The private `run_id` remains the controller capability. A provider conversation identifier is correlation/identity only and must never become authorization by itself.

### Agent-session local concurrent ownership — `KEEP`

Do not introduce a generic lease service or scheduler. Existing OS-backed delegation serialization remains the generic state owner; the browser claim continues to own browser-tab concurrency.

No baseline role is replaced or rejected.

## 3. Architecture primitives and adjacent domains

### Provider conversation binding

Domain: resource/session identity and recovery correlation.

Guarantee: a post-restart page may recover private run authority only when it represents the same provider conversation that previously owned the delivery claim.

The binding is provider-specific and stored with the browser delivery claim, not in generic delegation identity.

### Private capability disclosure gate

Domain: capability security / replay resistance.

Guarantee: visible delivery correlation is never sufficient to disclose `run_id`. The page must first match the bound provider conversation identity and the live exact claim/controller state.

### Idempotent cleanup acknowledgement

Domain: idempotency / concurrency control.

Guarantee: repeated equivalent cleanup acknowledgements for the same delivered/open delegation do not rotate authority and cannot invalidate a sibling monitor's already-issued token.

### Fail-closed unbound recovery

Domain: crash recovery.

Guarantee: if a browser crash occurs before a stable provider conversation identity was durably attached to the claim, restart recovery is unavailable. CAP accepts bounded loss of recovery rather than authorizing a foreign page.

## 4. External problem and solution evidence

Chrome documents that `tabs.Tab.id` values are unique only within one browser session. Therefore a numeric tab id cannot be the durable child identifier across complete browser restart.

Chrome's Manifest V3 guidance also says extension service workers are ephemeral and must persist important state rather than rely on globals; IndexedDB is explicitly supported for transactional structured storage. That supports keeping the provider recovery binding in the same extension-origin durable claim that already owns one-Send concurrency.

OWASP's IDOR guidance distinguishes an object identifier from authorization: even complex IDs do not replace an access-control check. CAP therefore uses a provider conversation ID only to identify the resource; the already-private `run_id` remains the actual controller capability and is disclosed only after the identity match plus live-claim checks.

NIST replay-resistance guidance reinforces that recorded/replayed public values are not sufficient authentication material. The current three visible prompt markers are therefore correlation data only, never recovery authentication.

RFC 9110's idempotency model captures the required cleanup-ack property: repeating the same logical request should have the same intended effect. Rotating the cleanup token on every equivalent acknowledgement violates that useful retry/concurrency property; returning one stable token for the same open cleanup generation avoids the ABA replacement.

A browser `history.state` secret was considered because some browsers may persist state to disk. MDN explicitly describes restart persistence as browser-dependent ("some browsers"), so it is not a sufficient release-critical cross-restart identity primitive for this first adapter.

## 5. Materially distinct approaches

### A — keep visible delivery correlation as restart identity

Owner: visible conversation text + IndexedDB claim.

Strength: no extra binding step.

Failure: copied markers in an unrelated ChatGPT conversation can recover `run_id`.

Decision: **REJECT** for recovery authority.

### B — bind provider conversation ID into the existing IndexedDB delivery claim

Owner: existing extension-origin browser claim.

Mechanism:

```text
initial exact claim + Send
 -> provider assigns stable conversation route/id
 -> exact current content context binds that conversation id to the existing claim
 -> restart page supplies current provider conversation id + visible delivery correlation
 -> service worker matches claim conversation id + exact visible correlation + live controller state
 -> only then disclose run_id for monitor-only recovery
```

Strengths:

- survives numeric tab-id replacement;
- a different conversation with copied markers fails identity match;
- no new generic persistence service;
- keeps provider identity out of generic delegation identity;
- reuses the already-authoritative browser claim store.

Failure boundary: if no stable provider conversation ID was bound before crash, recovery fails closed.

Decision: **SELECTED / NARROW**.

### C — page-local random recovery secret in `history.state` / session storage

Owner: page session history/web storage.

Strength: cryptographic page secret can distinguish copied visible markers.

Weaknesses:

- restart persistence is not a guaranteed cross-browser contract;
- duplication/restoration semantics are browser-managed and harder to prove;
- service-worker code cannot treat web page storage as durable authority without another reconciliation layer.

Decision: **REJECT for release-critical restart recovery**.

### D — controller-side durable monitor lease/election

Owner: new provider-specific controller persistence/lease state.

Strength: could elect exactly one monitor and scope cleanup/capture authority to it.

Weaknesses:

- adds a new durable state owner and lease expiry/recovery problem;
- duplicates the browser claim store for the current one-provider/one-child scope;
- unnecessary if stable provider conversation binding plus idempotent cleanup acknowledgement closes the observed failures.

Decision: **DEFER**. Re-enter research only if a real multi-monitor consequence requires single-monitor election later.

## 6. Cleanup-token alternatives

### Rotating singleton token — reject

Every equivalent ACK replaces the previous token and creates the confirmed ABA/liveness failure.

### Per-tab/per-document token map — defer

It scopes authority but reintroduces unstable tab/document identity and requires cleanup/expiry semantics across restart.

### Stable token for one delivered/open cleanup generation — selected

The controller creates the cleanup token once and returns that same token for later equivalent valid cleanup acknowledgements while the delegation remains `delivered/open`.

The token does **not** waive the browser-side safety window. Each content context must still:

1. observe its own launch URL/composer clean;
2. maintain the uninterrupted 8-second clean window;
3. receive an ACK;
4. synchronously recheck current UI before capture.

If one legitimate duplicate tab is dirty while another copy of the same provider conversation is clean, the clean tab may proceed; sibling UI state is not global child state.

## 7. Failure / crash matrix

| Boundary | Durable/browser state | Physical state | Rule | Additional Send authority |
|---|---|---|---|---|
| Before browser delivery claim | no claim | child absent/present | existing launch rules | at most the original bounded initial path |
| Claim committed, no provider conversation bound | exact claim, conversation unbound | Send may be in flight | no restart capability disclosure | none |
| Provider conversation bound, browser alive | exact claim + conversation id | original child active | normal path | none after claim |
| Complete Chrome restart, exact conversation restored under new tab id | exact claim + conversation id | same provider conversation | match current conversation id + visible correlation + live controller before disclosing run_id | none |
| Complete Chrome restart before conversation binding | exact claim, no conversation id | page may restore | fail closed; no run_id recovery | none |
| Foreign conversation copies visible markers | exact claim bound to another conversation id | unrelated chat | conversation mismatch; do not disclose run_id | none |
| Duplicate tabs of same provider conversation | one exact bound claim | multiple monitors, same underlying child | monitor-only allowed; no second Send | none |
| Two valid cleanup ACKs race | delivered/open | same child in duplicate monitors | return the same cleanup token; no last-writer replacement | none |
| Local UI becomes dirty after ACK | cleanup token may remain server-valid | that monitor is unsafe | local guard resets epoch; require fresh 8-second clean interval + ACK + synchronous recheck | none |
| Controller restarts, browser claim persists | exact claim + provider conversation id + private run id | restored same conversation | live controller status must authenticate exact run/delegation/delivery before recovery | none |
| HEAD/runtime changes | old claim + bound conversation | old/new extension mix | existing exact HEAD/prompt/generation/runtime provenance gates fail closed | none |
| Result already recorded | terminal durable state | one or many tabs | terminal readback only; recovery result authority unnecessary | none |

No cell permits a second physical Send after the browser delivery claim exists.

## 8. Minimum implementation

Must have now:

- add a bounded optional `conversation_id` field to the existing IndexedDB claim record;
- allow the exact already-authorized content context to bind that field once a provider conversation route exists;
- binding is monotonic/idempotent: same value may repeat, different value is rejected;
- restart `resume-intent` must include the requesting page's current provider conversation id;
- `resumeIntent()` must reject missing/unbound/mismatched conversation identity before any `run_id` disclosure;
- retain visible delegation/delivery/task markers as secondary correlation, not authority;
- keep exact live-controller state and execution-generation checks;
- make valid repeated cleanup ACKs idempotently return one stable cleanup token while `delivered/open`;
- no new public tool, scheduler, lease service or generic session field.

Explicitly deferred/rejected:

- random page secret as the primary restart identity;
- per-tab durable leases;
- provider conversation identity in generic deterministic delegation identity;
- any automatic re-Send/relaunch to compensate for unbound recovery.

## 9. Acceptance shields

Focused deterministic tests must prove:

- copied visible markers in a different conversation cannot recover `run_id`;
- missing provider conversation identity cannot recover;
- a bound exact conversation can recover after numeric tab id changes;
- claim conversation binding is one-time/idempotent and rejects replacement;
- recovery still requires exact live claim/controller correlation and current execution generation;
- duplicate monitors of the same bound conversation never obtain Send authority;
- concurrent/repeated cleanup acknowledgements return the same cleanup token;
- a result-bearing monitor cannot be stranded by a sibling's later cleanup ACK;
- dirty local UI still forces a fresh uninterrupted 8-second guard window before capture;
- single-context two-phase prepare/capture replay protections remain intact;
- cross-HEAD/runtime stale claim protections remain intact.

Final target-Windows physical evidence for the eventual frozen HEAD must include a complete Chrome close/reopen recovery path, not only an in-tab reload, and must show:

```text
old numeric tab identity gone
 -> same provider conversation restored
 -> exact conversation-bound claim recovered
 -> zero second Send
 -> terminal result captured/closed or terminal readback preserved
```

A negative foreign-conversation replay fixture should also prove copied visible markers do not disclose recovery authority.

## 10. Architecture decision

**NARROW — implementation may proceed** with provider-conversation binding inside the existing MV3 IndexedDB delivery claim plus idempotent cleanup acknowledgement.

This is a refinement of the already-selected first-provider browser ownership boundary, not a new generic Agent Session primitive. The generic delegation identity/state model, six-tool public surface, Control Plane authority, Verification Kernel and Finish Gate remain unchanged.

Re-enter Stage Research again if stable provider conversation identity cannot be positively observed before useful restart recovery, if ChatGPT Temporary Chat does not preserve a stable conversation route across full browser restart, or if physical evidence shows that duplicate same-conversation monitors require an actual lease/election mechanism.

## 11. Fresh-review follow-up — exact HEAD `3e0ecd2438d96e48bc404bf041d5ba17f26c891e`

A later fresh ordinary-ChatGPT review on 2026-09-04 reported three additional concrete defects. Development-side falsification confirmed all three and they remain inside this brief's already-selected browser ownership/recovery boundary:

1. **Original claim-owner pre-Send fence.** A tab that lost the IndexedDB `store.add()` race could enter the existing-claim `prepared` recovery branch and request project-local Send authority before tab ownership was checked. The selected browser-claim ownership model requires that only the exact `claim_tab_id` owner may recover pre-Send authority within the same browser session; a losing tab is never an alternate Send owner.
2. **Delivered commit / acknowledgement loss.** A durable `claimed -> delivered` write could succeed while its HTTP acknowledgement was lost. Browser retries used a new observation-derived `evidence_ref`, conflicting with the already-durable evidence and wedging local state. The selected idempotency/recovery model requires one stable evidence reference for retries of the same observed outcome plus reconciliation from authenticated controller status.
3. **Final capture transport interruption.** A controller/network interruption after successful capture preparation could stop the content loop on a generic transport error before re-arm. The selected controller-restart behavior requires transport loss to invalidate local capture authority, require a new clean interval after recovery, and reconcile terminal durable state from authenticated controller status if the capture commit actually succeeded before the acknowledgement was lost.

These findings do **not** require a new architecture owner, scheduler, lease, provider identity field, or generic delegation state. They tighten the already-selected one-Send ownership, idempotency and restart-recovery semantics. Focused adversarial regressions must therefore prove:

- a losing duplicate tab cannot reach local Send authority while the original browser claim owner can recover it;
- delivery outcome retry after acknowledgement loss reuses the same evidence identity and can reconcile a durable delivered state;
- capture transport loss does not terminate the content recovery loop, and authenticated terminal status closes an already-recorded result without duplicate capture authority.

Any implementation or documentation commit made in response to this follow-up supersedes the `3e0ecd...` review for merge acceptance. The next semantic gate must therefore be a genuinely fresh ordinary-ChatGPT review against the final exact HEAD after hosted checks are green; only a PASS on that exact HEAD may be followed by the final target-Windows physical qualification and final exact-head CI.

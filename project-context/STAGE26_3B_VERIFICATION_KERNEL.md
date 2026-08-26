# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B is converting capability/procedure-specific success checks into one reusable deterministic verification contract before broader recovery or computer-use authority is added.

Current state:

- Verification Kernel foundation: **MERGED #99**;
- file/artifact production integration: **PHYSICALLY ACCEPTED / MERGED #102**;
- Browser observation foundation: **MERGED #106**;
- production `web_open` final-state integration: **IMPLEMENTED IN PR #107, hosted CI green, pending final exact-head ordinary-Chat target-Windows physical acceptance**;
- production `web_interact` postcondition verification: **IMPLEMENTED IN STACKED PR #109, pre-documentation code head hosted CI green, pending final exact-head CI + base/physical acceptance**;
- Windows/application/process verification: not yet implemented;
- Stage 26.3B overall: **not yet accepted**.

No Browser production-path PR is accepted from hosted CI alone. Exact accepted heads/evidence belong in `EVIDENCE_INDEX.md` and physical stage records after the relevant gate passes; this durable implementation contract records the required semantics rather than duplicating transient evidence dumps.

## Core contract

```text
ExpectedEffect
 -> one concrete before-observation reference
 -> bounded action occurs elsewhere under existing authorization
 -> fresh after-observation
 -> PASS | FAIL | UNKNOWN
```

Whole-task completion remains independent from planner self-assessment:

```text
planner: candidate_done
        |
        v
independent Finish Gate
  goal evidence
  constraint/freshness evidence where required
  unresolved ambiguity/confirmation state
  safety/policy evidence
  one evidence_batch_id
        |
        v
DONE | NOT_DONE | UNKNOWN
```

## Shared Verification Kernel

Internal module: `runtime/control_plane/verification.py`.

Shared concepts:

- `ObservationRef` — capability, subject, stream identity, monotonic sequence, fingerprint;
- `ObservationSnapshot` — bounded normalized immutable state plus completeness/ambiguity flags;
- `StatePredicate` — bounded declarative `equals`, `present`, `absent` predicates;
- `ExpectedEffect` — expected post-action predicates bound to a concrete prior observation;
- `VerificationStatus` — `pass`, `fail`, `unknown`;
- independent evidence-batch-bound Finish Gate.

The kernel is deterministic infrastructure. It adds no public tool and grants no action authority.

## Freshness rule

Verification freshness is valid only for the same stream/capability/subject with a strictly higher sequence:

```text
after.stream_id == before.stream_id
after.capability == before.capability
after.subject == before.subject
after.sequence > before.sequence
```

Wall-clock plausibility alone is not freshness proof.

Stale, mismatched-stream, ambiguous or incomplete required evidence becomes `UNKNOWN`, never success.

## Accepted file/artifact production integration

`runtime/control_plane/file_artifact_observation.py` is the first physically accepted capability adapter.

Normalized evidence includes bounded path state such as:

```text
exists / kind / size / sha256 / filesystem identity
complete / ambiguous
same-stream monotonic sequence + canonical fingerprint
```

`verified_workspace_artifact_v1` uses the common kernel for all three transition postconditions and the independent Finish Gate for target-goal plus staging-absence safety evidence.

PR #102 physical acceptance proved:

```text
first call: completed, action_count=3
all three kernel transition statuses: pass
Finish Gate: done
independent final read: exact match

second call on protected target: abstained, action_count=0
target_already_exists
independent reread: unchanged
zero overwrite proved
```

Exact accepted heads/evidence belong in `EVIDENCE_INDEX.md` and accepted stage evidence, not duplicated here.

## Browser observation foundation

`runtime/control_plane/browser_observation.py` provides bounded Browser state:

```text
capability = browser.page
subject = one bound page/session identity
canonical url + origin
document title/id/digest evidence
settled state
bounded semantic control state
control collision/ambiguity state
complete / ambiguous
same-stream monotonic sequence
```

It rejects unreviewed/unbounded evidence and reduces bounded document snapshot text to digest evidence before normalized verifier state.

PR #106 merged this observation foundation without changing production Browser behavior.

## Production `web_open` integration — PR #107

PR #107 is the first production Browser action-path integration with the shared kernel.

Current path:

```text
validate target URL/network policy
 -> fresh read-only browser snapshot BEFORE
 -> browser_navigate
 -> fresh read-only browser snapshot AFTER
 -> normalize through BrowserObservationStream
 -> ExpectedEffect(
      exact requested canonical final URL,
      document snapshot evidence present,
      settled == true
    )
 -> PASS | FAIL | UNKNOWN
```

Important semantics:

- action delivery is not verification;
- a delivered navigation whose final state is `FAIL` or `UNKNOWN` is not returned as verified success;
- redirects are intentionally fail-closed in this first slice: wrong final canonical URL => verification failure;
- no arbitrary JavaScript/browser evaluation is introduced;
- no generic backend/tool selector is introduced;
- Browser verification code is shipped in the installed semantic bundle for this production integration;
- public semantic inventory remains exactly six tools.

## PR #107 merge gate

Because PR #107 changes an accepted production action path, hosted CI alone is insufficient.

Required sequence:

```text
final exact PR head
 -> hosted CI green on that exact head
 -> ordinary-Chat target-Windows Browser physical regression on same exact head
 -> no unresolved review/security/contract finding
 -> merge
```

Do not reuse physical evidence from an older head after the branch changes.

## Production `web_interact` integration — stacked PR #109

PR #109 extends the same deterministic Browser observation/verifier contract to production click/type interaction without adding a new public tool.

Current path:

```text
validate bounded web_interact request
 -> normalize or derive ExpectedEffect request
 -> fresh read-only browser snapshot BEFORE
 -> deterministic pre-action delta check
 -> existing semantic-first / reviewed visual-fallback routing
 -> one bounded click/type delivery
 -> fresh read-only browser snapshot AFTER
 -> shared Python Browser transition verifier
 -> ExpectedEffect over BrowserObservationStream
 -> PASS | FAIL | UNKNOWN
```

### Bounded interaction postconditions

The public/internal `web_interact.expected` contract admits only:

```text
exact final HTTP/HTTPS URL
and/or
one control-ref state:
  present
  value
  checked
  selected
  enabled
```

It does **not** admit JavaScript, selectors, expressions, arbitrary code, raw CDP, backend names or generic downstream tool dispatch.

For `type` without submit, the runtime may safely derive:

```text
expected.control.value == typed text
```

when the target/text fit the bounded verifier representation.

For generic `click` and `type+submit`, an explicit observable `expected` result is required before any mutation is delivered.

### Pre-action delta guard

A postcondition proves an action only when the fresh pre-action observation can distinguish the requested future state from the current state.

Therefore PR #109 fails closed before delivery when:

```text
all declared expected predicates are already satisfied BEFORE
```

or when:

```text
no declared predicate is proven different
and required pre-action state is not safely observable/unambiguous
```

If at least one declared predicate is definitely not yet satisfied, the action may proceed; final success still depends on the fresh AFTER observation and the shared Python Verification Kernel.

This prevents a no-op/repeated click from being labelled successful merely because an unrelated or already-true postcondition remains true.

### Browser observation parser hardening

The Playwright accessibility snapshot adapter normalizes only role-owned state:

- checkbox/radio/switch-family roles may infer `checked=false` when the positive marker is absent;
- selected-state roles may infer `selected=false` when the positive marker is absent;
- generic controls retain `null` for states they do not own;
- observable empty value-state controls such as empty textbox/searchbox are normalized to `value=""`, not `null`.

The empty-value distinction is required so pre-action verification can distinguish an observed empty field from an unknown/unobserved value.

### Hosted interaction evidence

Real Playwright fixture coverage in PR #109 proves the intended contracts before physical acceptance:

```text
type -> expected value                         PASS
checkbox click -> expected checked state      PASS
click -> expected control disappearance       PASS
click without expected                        zero action
type+submit without expected                  zero action
already-satisfied expected before click       zero action
delivered action + wrong postcondition         FAIL, not success
semantic ambiguity                             ABSTAIN / zero arbitrary selection
```

Six-tool, Direct Tunnel, semantic/vision and security regressions remain part of the hosted gate. Hosted evidence is necessary but does not replace target-Windows ordinary-Chat acceptance.

## PR #109 merge/physical gate

PR #109 is intentionally stacked on PR #107 while #107 retains its exact physical-gate head.

Required sequence:

```text
#107 final exact head hosted CI green
 -> #107 ordinary-Chat target-Windows physical Browser gate
 -> merge #107
 -> rebase/retarget #109 onto accepted main/base
 -> #109 final exact head hosted CI green
 -> ordinary-Chat target-Windows web_interact physical regression
 -> no unresolved review/security/contract finding
 -> merge #109
```

The #109 physical regression should cover at minimum:

```text
verified type -> actual value changed + PASS
verified click -> declared state changed + PASS
wrong expected -> FAIL
missing expected -> zero action
already-satisfied expected -> zero action
semantic-first / visual-fallback safety behavior preserved
```

Do not reuse hosted or physical evidence from an older #109 head after rebase/document/code changes.

## Finish Gate contract

`candidate_done` is only a planner proposal.

Only observation-bound verification results from the requested evidence batch may contribute to completion.

Minimum completion dimensions:

```text
goals
constraints where declared
freshness/reconciliation where declared
unresolved confirmation/ambiguity
safety/policy
```

Task success and safety remain separate results. Missing required evidence yields `UNKNOWN`; failed required evidence yields `NOT_DONE`; only same-batch verified goal/safety state with no unresolved requirement may yield `DONE`.

## Remaining Stage 26.3B work

1. complete PR #107 final exact-head physical Browser gate and merge;
2. rebase/retarget PR #109, obtain final exact-head hosted + physical `web_interact` evidence and merge;
3. add Windows/application/process verification over accepted `DesktopState`/identity evidence;
4. add cross-capability completion predicates only where real procedures require them;
5. run physical gates whenever those integrations change production action/completion behavior;
6. only then declare Stage 26.3B accepted and advance Stage 26.3C.

ADR-036 / Browser Harness-derived wider browser authority does not bypass this sequence. Future trusted-site JS/CDP/full-browser capabilities remain above the same ExpectedEffect, authorization, fresh re-observation and Finish Gate rules.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
already-true postcondition != action success
unobservable pre-action delta -> zero mutation
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete required evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure/page content != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. The Verification Kernel and observation adapters are deterministic execution-state machinery, not a second planner or critic model.

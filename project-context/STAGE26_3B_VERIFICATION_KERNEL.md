# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B is converting capability/procedure-specific success checks into one reusable deterministic verification contract before broader recovery or computer-use authority is added.

Current state:

- Verification Kernel foundation: **MERGED #99**;
- file/artifact production integration: **PHYSICALLY ACCEPTED / MERGED #102**;
- Browser observation foundation: **MERGED #106**;
- production `web_open` final-state integration: **IMPLEMENTED IN PR #107, pending final exact-head physical acceptance**;
- `web_interact` postcondition verification: not yet implemented;
- Windows/application/process verification: not yet implemented;
- Stage 26.3B overall: **not yet accepted**.

The pre-documentation-sync PR #107 head `08671b5a8763d589bcd16da69e8ed70bcb5f9509` had all 11 PR-triggered hosted workflows green. Documentation synchronization changes the branch head, so acceptance requires green hosted CI and the target-Windows physical Browser regression on the **final exact PR head**.

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

## Next Browser slice

After PR #107 is accepted/merged, implement `web_interact` postcondition verification.

Target properties:

- bind click/type delivery to fresh before/after observations;
- verify the intended control/result state rather than delivery alone;
- preserve existing semantic-first and reviewed visual fallback guards;
- ambiguous control identity -> `UNKNOWN`/ABSTAIN, never arbitrary selection;
- no arbitrary JavaScript or generic tool dispatch;
- production-path changes require appropriate physical evidence.

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

1. complete PR #107 final exact-head hosted + physical Browser gate and merge;
2. migrate `web_interact` click/type/control-result verification to the shared kernel;
3. add Windows/application/process verification over accepted `DesktopState`/identity evidence;
4. add cross-capability completion predicates only where real procedures require them;
5. run physical gates whenever those integrations change production action/completion behavior;
6. only then declare Stage 26.3B accepted and advance Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete required evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure output != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. The Verification Kernel and observation adapters are deterministic execution-state machinery, not a second planner or critic model.

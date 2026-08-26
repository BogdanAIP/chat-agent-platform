# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B is converting capability/procedure-specific success checks into one reusable deterministic verification contract before broader recovery or computer-use authority is added.

Current state:

- Verification Kernel foundation: **MERGED #99**;
- file/artifact production integration: **PHYSICALLY ACCEPTED / MERGED #102**;
- Browser observation foundation: **MERGED #106**;
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**;
- Browser Harness / ADR-036 architecture docs: **MERGED #110**;
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**;
- first Browser L3 real-task harness: **ACTIVE DRAFT PR #113**, clean replay of superseded stacked PR #112;
- Windows/application/process verification: not yet implemented;
- Stage 26.3B overall: **not yet accepted**.

PR #111 was physically accepted on exact head `1521e3128a7694be43518c3ee0188cb79f0ca0f5` and squash-merged into `main` as `f7bba9eddd7c449306b7c9de18bc9e19849fd86f`.

The first physical #111 attempt failed because the already-bound ChatGPT app definition rejected the new `expected` field before the call reached the runtime. The exact runtime head was unchanged, a full app rebind made the field available, and the complete interaction gate then passed. Acceptance comes from that final complete PASS, not from the failed first attempt.

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

## Acceptance depth

Stage 26.3B distinguishes three evidence levels:

```text
L1 — primitive / contract proof
L2 — multi-step workflow/component integration
L3 — ordinary user goal + independent final-state proof
```

L1/L2 remain mandatory for diagnosis and regression. L3 is required because many passing primitive tests do not prove that the planner can identify the correct target, choose a route, compose several verified transitions and stop on independently verified completion.

Canonical acceptance-depth contract: `REAL_TASK_ACCEPTANCE.md`.

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

PR #102 physical acceptance proved fresh create, all three kernel transition checks `pass`, cleanup Finish Gate `done`, independent reread exactness, and zero-overwrite on a repeated target.

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

## Accepted production `web_open` verification — PR #107

Accepted path:

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

Accepted semantics include `action delivery != verification`, fail-closed wrong final URL handling, no arbitrary JavaScript/browser evaluation, no generic backend selector, and exactly six public semantic tools.

## Accepted production `web_interact` verification — PR #111

Accepted path:

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

`web_interact.expected` admits only an explicit observable result:

```text
exact final HTTP/HTTPS URL
and/or
one bound control state:
  present
  value
  checked
  selected
  enabled
```

It does **not** admit arbitrary JavaScript, selectors, expressions, code, raw CDP, backend names or generic downstream dispatch.

For `type` without submit, the runtime may derive `expected.control.value == typed text` when target/text fit the bounded verifier representation. Generic `click` and `type+submit` require an explicit observable `expected` result before mutation.

A postcondition can prove an action only when the fresh pre-action observation can distinguish the requested future state from the current state. Therefore mutation is refused before delivery when all declared expected predicates are already satisfied or when the expected result cannot be safely distinguished from fresh pre-action state.

The accepted physical regression covered:

```text
type -> expected value                         PASS
checkbox click -> expected checked state      PASS
click without expected                        zero action
already-satisfied expected before click       zero action
delivered action + wrong postcondition        FAIL, not success
semantic ambiguity                            ABSTAIN / zero arbitrary selection
```

Independent observation after the deliberately wrong `enabled=false` expectation proved that the click was physically delivered, the checkbox toggled, the control remained enabled, and verification returned `expected_effect_failed`. This is direct physical evidence that delivery is not success.

## First Browser L3 real-task gate — PR #113

The primitive #111 gate proves the interaction mechanism. It does not by itself prove that ordinary ChatGPT can use the mechanism to solve a normal task.

PR #113 adds the clean post-#111 replay of a stateful local `Case Desk` fixture with multiple similar records and randomized task identity/data on every physical run.

The user-facing task is natural-language outcome/constraint text. The harness does **not** prescribe the sequence of clicks or field operations.

Independent fixture evidence lives outside Chat `FilesRoot` and includes persisted state, audit history and the Finish Gate. The Finish Gate requires all of:

```text
target case exists
address == requested address
status == Approved
comment == requested comment
old target address no longer used in target
similar non-target records unchanged
only the target case was ever mutated
```

Initial state must be `not_done`. Only the correct persisted target state with preserved decoys and target-only mutation history becomes `done`.

The planner may inspect the UI and use the accepted six-tool surface. It must not mutate fixture state through a hidden administrative/test API or rewrite Finish Gate evidence through `workspace_write`.

Hosted fixture smoke validates the harness itself. It is not L3 acceptance. Actual L3 acceptance requires ordinary Chat on target Windows against the randomized fixture on the final exact PR #113 head, followed by the external checker reading the independent fixture evidence.

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

1. freeze one final PR #113 head and require fresh hosted harness/contract checks;
2. prepare a randomized Case Desk run, pass the ordinary-Chat target-Windows Browser L3 task, and pass the external Finish Gate;
3. merge PR #113 if clean;
4. add Windows/application/process verification over accepted `DesktopState`/identity evidence;
5. add a representative Windows/application L3 task after that verifier exists;
6. add cross-capability completion predicates only where real procedures require them;
7. run physical gates whenever those integrations change production action/completion behavior;
8. only then declare Stage 26.3B accepted and advance Stage 26.3C.

ADR-036 / Browser Harness-derived wider Browser authority does not bypass this sequence. Future trusted-site JS/CDP/full-browser capabilities remain under the same authorization, ExpectedEffect, fresh re-observation, Finish Gate and representative L3-evidence boundaries.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
many primitive PASS results != realistic user-task acceptance
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

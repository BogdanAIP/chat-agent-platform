# Windows Case Core Grant Binding Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-23.

## Re-entry trigger

The CAP Core-v1 authorization contract and enforcement path now exist, and the
workspace artifact consumer has already migrated onto exact concrete grants.
windows_case_update_v1 is still consequence-bearing but currently relies on:

- fixed procedure admission;
- bounded user-level request validation;
- one externally prepared Windows session;
- per-transition fresh Verification Kernel checks;
- a fixed five-action budget;
- an external L3 Finish Gate.

It does **not** yet bind each physical Windows mutation to an active
CapabilityGrant / AuthorizationRequest / AttemptIntent before delivery.

That is now the remaining Core-v1 consumer gap for this accepted Windows slice.

## Exact stage question

How should the existing bounded Case Desk procedure consume the already-selected
Core authorization/WorkingState contracts without inventing a Windows-specific
policy engine, retry subsystem, provider framework or second execution state
owner?

The stage must preserve:

- exactly five fixed transition ids;
- the current OpenAdapt/UIA/guarded-input mechanics;
- exact session/run/process/window binding;
- fresh same-target verification after every action;
- no blind retry;
- external independent Finish Gate ownership;
- unchanged six-tool public schema.

## Existing failure/evidence model

The current procedure performs real UI consequences in this order:

    select_case
     -> focus_note
     -> enter_note
     -> set_status
     -> save_case

Each transition is separately verified, but current admission
stage26-3b-windows-l3 proves only that the procedure family is admitted. It does
not prove that one exact task/request/session authorizes one exact transition.

The procedure has no automatic restart/resume or retry path. A failed or
uncertain transition abstains and the external L3 state/history checker remains
the final completion authority. This stage therefore must **not** introduce a
new durable retry/recovery protocol merely to adopt Core authorization.

## Architecture lineage

| Role | Existing owner | Decision |
|---|---|---|
| General planning | ordinary ChatGPT | **KEEP** |
| Windows physical mechanics | current OpenAdapt Flow/WindowsBackend + project window-scoped UIA/guarded input | **KEEP** |
| Capability authorization | project Core CapabilityGrant / AuthorizationRequest / LoopGuard | **REUSE_MORE** |
| Capability-spanning operational state | project WorkingState | **REUSE_MORE** for this bounded run |
| Transition verification | project Verification Kernel | **KEEP / REUSE_MORE** through one persistent Windows observation stream |
| Procedure-local resume | none for this one-shot procedure | **KEEP absent**; do not add resume/retry |
| Task completion | external Stage 26.3B Finish Gate | **KEEP** |

No baseline role is replaced. OpenAdapt remains execution mechanics only; it does
not gain grant, WorkingState, verification or completion authority.

## Current external authorization evidence

The selected model remains consistent with current mature authorization
practice:

- Cedar models authorization as a request over principal, action, resource and
  request context, with exact action/resource mapping done by the application:
  https://docs.cedarpolicy.com/auth/authorization.html
- Cedar recommends mapping application/business actions to specific resources
  and normalizing request inputs before authorization:
  https://docs.cedarpolicy.com/bestpractices/bp-authorization-patterns.html
  https://docs.cedarpolicy.com/bestpractices/bp-overview.html
- OPA separates the policy decision point from the enforcement point and makes
  fail-open/fail-closed behavior the responsibility of the integrating
  application:
  https://www.openpolicyagent.org/docs/deploy
  https://www.openpolicyagent.org/docs/operations

This stage does not adopt Cedar or OPA. CAP already has the required exact-match
decision primitive; adding another policy engine would duplicate project-owned
authority.

## Approaches compared

### A. Keep fixed procedure admission only — REJECT

stage26-3b-windows-l3 admits the procedure family but does not bind the exact
case, requested note/status, active run, source head or transition to a Core
grant.

### B. One broad Windows grant unrelated to the exact request — REJECT

A grant such as "windows_case_update_v1 may use windows.desktop" would preserve
ambient authority and make request changes invisible to Core authorization.

### C. One deterministic exact-task grant + five fixed action refs — SELECT

Derive one grant from already trusted/validated inputs:

    procedure id/version
    + qualification admission
    + task_id
    + active run_id
    + exact source head
    + case_id
    + note SHA-256
    + requested status

The grant allows only:

    select_case
    focus_note
    enter_note
    set_status
    save_case

Each action gets a fresh AttemptIntent from the current persistent Windows
observation, then:

    Core evaluate_authorized()
     -> physical action
     -> fresh persistent-stream observation(s)
     -> Verification Kernel
     -> record_authorized_attempt()
     -> advance WorkingState observation

A non-PASS final verification records OUTCOME_UNKNOWN and the procedure stops.
No second physical attempt is authorized.

### D. Add a general policy engine / Windows grant registry — REJECT

This would add storage, lifecycle, discovery and another authority boundary
without solving a problem not already covered by Core.

## Selected grant shape

    principal_ref =
      procedure:windows_case_update_v1

    capability =
      windows.desktop

    resource_scope_ref =
      exact digest-bound identity of:
      run_id + expected_head + case_id + note_sha256 + requested_status

    allowed_action_refs =
      select_case
      focus_note
      enter_note
      set_status
      save_case

    execution_environment_ref =
      exact accepted Windows-case environment/source identity

    evidence_scope_ref =
      one persistent task-local WindowsDesktopObservationStream

The fixed profile admission remains an upstream prerequisite. It is not
reinterpreted as the concrete grant.

## Observation/verification refinement

Current windows_case_update_v1 creates a fresh verifier stream for each
transition. WorkingState requires one monotonic evidence stream across its
attempt history.

Selected refinement:

- instantiate one WindowsDesktopObservationStream per Case Desk task;
- every live UI observation enters that same stream and receives a monotonically
  increasing sequence;
- expose a small verifier helper that consumes already-normalized
  ObservationSnapshot values;
- keep the existing raw verify_windows_desktop_transition() API as a
  compatibility wrapper.

This changes no DesktopState semantics and introduces no provider mechanics into
Core.

## Persistence and crash boundary

This stage deliberately does **not** add restart/resume.

The procedure continues to checkpoint its bounded run for evidence/diagnostics,
and the checkpoint additionally carries current WorkingState. There is no public
or internal API that resumes a partially executed Windows case update.

If the process dies after a physical action but before the final record:

- the old task is not auto-resumed;
- no retry is issued;
- a new invocation receives a new task identity;
- the fixture/live state must independently satisfy the existing clean-preflight
  contract or the new invocation abstains;
- the external Stage 26.3B state/history checker remains the final authority.

If future work adds restart/resume or automatic retry, Stage Research must
re-enter before implementation.

## Failure / authority matrix

| Boundary | Failure | Required behavior |
|---|---|---|
| profile admission | wrong/missing admission | block before task/grant creation |
| request/session binding | case does not belong to active run | abstain before grant/action |
| concrete grant | task/run/head/case/note/status mismatch | Core BLOCK |
| transition | action ref outside fixed five | Core BLOCK |
| pre-action state | unresolved prior Core attempt | block next physical action |
| authorization | grant/request/intent mismatch | zero physical action |
| physical delivery | exception before/after possible effect | fresh observation; never blind retry |
| final observation | PASS | record VERIFIED_APPLIED, advance WorkingState |
| final observation | FAIL/UNKNOWN after settle | record OUTCOME_UNKNOWN, stop |
| process crash after effect | receipt/state record missing | no auto-resume/replay; next invocation must pass clean preflight |
| provider receipt says success | final state disagrees | no Core success |
| local bounded execution completes | external evidence not checked | Finish Gate remains unresolved/not-DONE |

## Failure shields

Implementation must prove:

1. exact task/run/head/case/note/status changes change the grant identity;
2. every physical transition calls evaluate_authorized() before delivery;
3. wrong grant/action/resource/attempt fingerprint produces zero physical call;
4. all five successful transitions are recorded through record_authorized_attempt();
5. one persistent Windows observation stream advances monotonically through the
   whole procedure;
6. postcondition polling performs observations only and never repeats an action;
7. FAIL/UNKNOWN records unresolved Core outcome and prevents later transitions;
8. OpenAdapt/UIA mechanics do not receive or mint Core grants;
9. external Finish Gate remains required;
10. public six-tool schema is unchanged.

## Acceptance

L1:

- deterministic grant/resource/action fingerprint tests;
- authorization mismatch/zero-delivery tests;
- WorkingState history/budget tests;
- persistent-stream monotonicity tests;
- non-PASS blocks next transition;
- compatibility tests for existing Windows transition verifier.

L2:

- existing Stage 26.3B Windows application tests;
- six-tool semantic acceptance;
- installed-layout/manager bundle tests;
- full hosted CI/security.

L3:

Because this changes the authority path immediately before real Windows effects,
the accepted target-Windows Case Desk L3 must be rerun on the final reviewed
head before this consumer migration is accepted.

## Decision

**NARROW**

Implement only exact Core authorization + WorkingState binding for the existing
five-action windows_case_update_v1 procedure.

Do not add:

- restart/resume;
- automatic retry;
- a Windows policy/grant registry;
- a generic provider API;
- a new public tool;
- Rust Native Host;
- new OpenAdapt ownership;
- a replacement Finish Gate.

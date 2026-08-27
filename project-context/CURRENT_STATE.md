# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose. Ranked engineering risks live in `PROJECT_RISKS.md`; release-stage order lives in `ROADMAP.md`.

## Current live integration line

At the 2026-08-27 Track M documentation replay point:

```text
main = 500bfc646a14892ea655369c20c8f8d725fccfeb
       PR #117 — CAP-M0 Verification Kernel mutation pilot
       ACCEPTED / MERGED

PR #115 — Windows/application real-task L3
       PHYSICALLY ACCEPTED / MERGED
       merge = e965e7b5466446c9f065f6b57f438f25168bed9a

active architecture/docs PR = #116
       Track M Agent Session / Delegation + ADR-037
       no runtime/public-tool authority
```

## Accepted Browser L3 evidence and remaining provenance work

PR #113 was physically accepted on exact head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf` for its historical gate scope. The randomized Case Desk task was given to ordinary Chat as a natural user goal, not a click recipe. The independent checker reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

A later Source Provenance review found that the historical #113 harness did not independently bind a clean working tree and all executed source bytes under the stronger methodology. #113 is not retroactively failed. One representative Browser L3 repeat with the stronger Source Provenance Gate remains the release-critical Stage 26.3B evidence gap.

## Accepted Windows shared-kernel verification — PR #114

PR #114 was physically accepted on exact head `ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e` and merged as `cc0fa3d1b7afe9d833334ae68482d2d3dca4b818`.

It connected bounded live `DesktopState` evidence to the shared Verification Kernel:

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef
 -> bounded expected final state
 -> stable process/native-window continuity
 -> DesktopState AFTER
 -> ExpectedEffect verifier
 -> PASS | FAIL | UNKNOWN
```

Accepted continuity/evidence includes Windows session, application identity, executable name, PID, process generation, HWND, coordinate space, canonical control fingerprints, frame digest and advancing observation time. `window_instance` is snapshot-validated but not treated as immutable continuity because legitimate title changes alter that digest.

#114 added no public Windows action tool and no generic code execution authority.

## Accepted Windows/application L3 — PR #115

The public semantic inventory stayed exactly six tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

`procedure_run` gained the bounded registered `windows_case_update_v1` branch. It accepts only user-level:

```text
case_id
note
status = Approved | Needs Review
```

It does not expose PID/HWND/backend/interpreter/command/Python/arbitrary filesystem paths/fixture-state/audit paths/raw action sequences.

Final physical acceptance used exact frozen head:

`5ae5d5ac52f391b1a58662e94a976c6ab8d48c62`

Ordinary Chat completed five bounded transitions with all shared-kernel postconditions PASS:

```text
select_case
focus_note
enter_note
set_status
save_case
```

Local evidence:

```text
status=completed
action_count=5
local_execution_verified=true
local_goal_verification.status=pass
local_safety_verification.status=pass
```

Independent frozen Finish Gate evidence:

```text
SOURCE_PROVENANCE_REVALIDATED=PASS
INSTALLED_RUNTIME_REVALIDATED=PASS
WINDOWS_RUNTIME_REVALIDATED=PASS
PROVENANCE_REVALIDATION=PASS
EVIDENCE_OUTSIDE_CHAT_WORKSPACE=True
TARGET_FINAL_STATE=True
DECOYS_UNCHANGED=True
ONLY_TARGET_EVER_MUTATED=True
AUDIT_TARGET_SAVE_EXACTLY_ONCE=True
AUDIT_BEFORE_MATCHES_SEED=True
AUDIT_AFTER_MATCHES_FINAL=True
FIXTURE_PROCESS_WAS_LIVE=True
EXTERNAL_FINISH_GATE=DONE
FIXTURE_CLEANUP_PASS=True
ACTIVE_SESSION_CLEANUP_PASS=True
STAGE26_3B_WINDOWS_APPLICATION_L3=PASS
```

#115 was squash-merged as `e965e7b5466446c9f065f6b57f438f25168bed9a`.

## Accepted mutation-assurance pilot — PR #117

CAP-M0 was replayed onto post-#115 `main`, accepted on exact head `e99de4ea89e6a763e3db6671e710cf06c4e5bb17`, and squash-merged as current `main=500bfc646a14892ea655369c20c8f8d725fccfeb`.

It adds five test/docs files and does **not** modify production Verification Kernel behavior. The runner mutates isolated temporary copies only.

Curated acceptance contract:

```text
12 deterministic mutants
baseline PASS
KILLED only by named detector assertion failure
exact mutated-source binding required
12 / 12 KILLED
0 SURVIVED
0 ERROR
```

Fresh final-head evidence passed dedicated `CAP-M0 Verification Mutation Pilot`, general `ci`, CodeQL and Secret History Scan.

Canonical direction: `MUTATION_ASSURANCE.md`.

## Accepted foundation relevant to current work

```text
Stage 26.3A canonical six-tool runtime             ACCEPTED / MERGED #92
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                 PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                    MERGED #110
web_interact postcondition verification           PHYSICAL ACCEPTED / MERGED #111
Browser real-task L3                              PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification   PHYSICAL ACCEPTED / MERGED #114
Windows/application real-task L3                  PHYSICAL ACCEPTED / MERGED #115
CAP-M0 Verification mutation assurance            ACCEPTED / MERGED #117
```

These are scoped evidence, not universal Browser/Windows accuracy claims.

## Normal public route

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

1MCP remains optional internal Extension Manager infrastructure.

## Stage 26.3B — ACTIVE, final evidence gap

Accepted/implemented:

```text
shared Verification Kernel
ObservationRef / ObservationSnapshot
ExpectedEffect + bounded predicates
same-stream fresh verification
PASS | FAIL | UNKNOWN
independent Finish Gate
file/artifact production integration + physical acceptance
Browser observation foundation
web_open verification + physical acceptance
web_interact verification + physical acceptance
Browser L3 real-task acceptance + independent Finish Gate for historical scope
Windows DesktopState shared-kernel verification + physical acceptance
Windows/application L3 + independent frozen Finish Gate
```

Remaining recorded Stage 26.3B direction:

```text
1. repeat one representative Browser L3 under the stronger Source Provenance Gate
2. add cross-capability completion predicates only if a real procedure requires them
3. run any additional physical gate required by a production-path change
4. declare 26.3B accepted only when required evidence gaps are closed
```

## Acceptance depth

```text
L1 primitive / contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state/history
```

Transition PASS, procedure completion and worker-reported completion are all weaker than independent task-level DONE.

## Planner / Control Plane boundary

Ordinary ChatGPT remains the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions.

Registered procedures are deterministic bounded execution paths, not second planners and not generic dispatch.

## Stage 26.3C — next release-critical prerequisite

WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport remain the next runtime target after 26.3B closes. Never persist private chain-of-thought.

WorkingState remains project-owned and capability-spanning. It must not be replaced by OpenAdapt procedure-local resume state or future vendor session/task state.

26.3C should avoid hard-coding `one task -> one procedure -> one executor`. Optional planner-neutral seams may include `actor_ref`, `delegation_ref`, `execution_environment_ref`, budget refs and evidence refs.

Ambiguous mutating outcomes should support:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` requires reconciliation of the same logical operation from fresh authoritative state before retry.

## Track M / ADR-035 boundary

Track M is future/parallel architecture, not current runtime authority.

Object identities remain separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

The primary cross-provider product target is authenticated web-AI conversations through Browser Companion / DOM-accessibility adapters, with stronger reviewed native/host interfaces preferred per exact target surface when available.

Track M requires explicit ownership, stable operation identity, ambiguous-outcome reconciliation, result correlation to DelegationTask, minimum worker authority, bounded fan-out and independent Finish Gate. Initial nested spawn depth defaults to 1.

Canonical future detail: `CONVERSATION_BRIDGE_ARCHITECTURE.md` and ADR-035 in `DECISIONS.md`.

## ADR-037 boundary

`CapabilityRegistry`, `TypedEventBus` and registered `PolicyHooks` are future project-owned substrate:

- capability discovery/health/trust metadata != authorization;
- events trigger fresh observation but do not prove effect success;
- hooks are bounded deterministic handlers, not arbitrary shell/Python and not a second planner;
- hook/event output cannot upgrade FAIL/UNKNOWN or widen grants;
- 26.3C may adopt only minimal typed internal seams required by existing recovery/LoopGuard/Finish Gate goals.

Canonical detail: `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` and ADR-037.

## Broad real-application coverage

Representative L3 gates are vertical proofs. After 26.3C, broader coverage still needs multiple native Windows, Browser, Electron, office-style and file/dialog task families across DPI/focus/dialog/noisy-state variants.

## Browser Harness / ADR-036 boundary

ADR-036 is future architecture direction, not current expanded authority. Trusted-site JS/CDP/full-browser authority remains gated by separate network/Site Capability policy, security review, physical acceptance and representative L3 evidence.

## Current priority

```text
finish/review PR #116 documentation replay
 -> representative Browser L3 provenance repeat
 -> close remaining 26.3B evidence
 -> Stage 26.3C WorkingState + recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage
 -> bounded OpenAdapt spike
 -> Stage 26.4 / 26.5
```

Track M remains parallel future work and must not displace this sequence.

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page/worker output is not authorization;
- every state-changing production action requires explicit ExpectedEffect + fresh verification;
- action/message delivery != transition success;
- ambiguous mutating outcome must be reconciled before unsafe retry;
- transition `PASS` != task `DONE`;
- procedure/worker completion != independent task completion;
- realistic user-task acceptance requires independent final-state/history evidence;
- stale/mismatched/ambiguous/incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- session discoverability does not imply lifecycle authority;
- generic Windows/local/harness execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

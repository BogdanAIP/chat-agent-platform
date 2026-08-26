# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose.

Do not preserve stale status by copying the same stage narrative into many documents. Ranked engineering risks live only in `PROJECT_RISKS.md`. The explicit release-stage order is owned by `ROADMAP.md` rather than duplicated here.

## Current live integration line

At the 2026-08-26 synchronization point:

```text
main = f7bba9eddd7c449306b7c9de18bc9e19849fd86f
       PR #111 — Browser interaction postcondition verification
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #113
       Stage 26.3B: first Browser L3 real-task acceptance harness
       clean replay directly on accepted post-#111 main
       fresh hosted checks required on the final head
       target-Windows ordinary-Chat Case Desk L3 + external Finish Gate still required

historical stacked PR = #112
       superseded by clean replay #113 after #111 merged
```

PR #107 remains the physically accepted Browser navigation foundation for production `web_open` verification.

## Real stopping point

Production `web_open` verification is accepted and merged. Production `web_interact` verification is also now physically accepted and merged through PR #111.

The accepted interaction path is:

```text
fresh browser snapshot BEFORE
 -> bounded expected result / pre-action delta guard
 -> existing semantic-first or reviewed visual-fallback action
 -> fresh browser snapshot AFTER
 -> BrowserObservationStream
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

The mutation is refused before delivery when the required expected result is missing, already satisfied, or cannot be safely distinguished from the fresh pre-action state.

The first physical #111 attempt exposed a stale client-visible app schema that rejected the new `expected` field even though the exact-head runtime already published it. A full `Chat Local Bridge Test` rebind on the unchanged exact runtime head made the field available; the complete interaction gate then passed. That failed first attempt is migration evidence, not acceptance evidence.

The project now requires a representative **L3 real user-task gate** after this primitive Browser interaction proof. PR #113 provides the clean replay of that harness directly on accepted `main`.

The L3 task is given as a natural user goal, not a click script. The planner must choose the route and the independent fixture Finish Gate verifies persisted target state plus non-target invariants and mutation history.

## Accepted foundation relevant to current work

### Stage 26.3A — canonical six-tool verified procedure runtime

**ACCEPTED / MERGED #92.**

The normal Chat-facing semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

1MCP is optional internal Extension Manager infrastructure, not a normal-route dependency.

### Stage 26.3B file/artifact integration

**PHYSICALLY ACCEPTED / MERGED #102.**

`verified_workspace_artifact_v1` uses the shared Verification Kernel for transition postconditions and the independent Finish Gate. Physical acceptance proved completion and zero overwrite on the exact accepted head.

### Browser observation foundation

**MERGED #106.**

`BrowserObservationStream` provides bounded URL/origin/document/control state and same-stream monotonic observation identity.

### Browser navigation verification

**PHYSICALLY ACCEPTED / MERGED #107.**

Production `web_open` uses fresh before/after observation plus the shared Verification Kernel; delivery alone is not success.

### Browser Harness architecture

**MERGED #110.**

ADR-036 and the technical-debt register are in `main`. They do not expand current Browser/local runtime authority by themselves.

### Browser interaction verification

**PHYSICALLY ACCEPTED / MERGED #111.**

Production `web_interact` now uses bounded ExpectedEffect postconditions, a fresh BEFORE/AFTER Browser state pair, a pre-action delta guard and the shared Verification Kernel. The physical gate proved positive type/click verification, zero-action refusals, `delivery != success`, and ambiguity abstention.

## Stage 26.3B — ACTIVE

Implemented/accepted so far:

```text
shared Verification Kernel
ObservationRef / ObservationSnapshot
ExpectedEffect + bounded predicates
same-stream fresh re-observation
PASS | FAIL | UNKNOWN
independent Finish Gate
file/artifact production integration + physical acceptance
Browser observation foundation
web_open production verification + physical acceptance
web_interact production verification + physical acceptance
L1/L2/L3 acceptance-depth contract
Browser L3 harness replayed in active PR #113
```

Remaining before Stage 26.3B can be accepted:

```text
1. fresh hosted checks for final PR #113 head
2. ordinary-Chat target-Windows Browser L3 Case Desk task + external Finish Gate
3. merge #113 if that evidence is clean
4. Windows/application/process verification over accepted DesktopState/identity evidence
5. representative Windows/application L3 after that verifier exists
6. cross-capability completion predicates where real procedures require them
7. appropriate physical acceptance when production paths change
```

Rules remain:

- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- many passing primitive tests != realistic user-task acceptance;
- current observed state outranks remembered procedure/demo/history;
- stale, mismatched-stream, ambiguous or incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- task-success verification and safety/policy verification remain separate;
- planner/model/procedure/page content cannot self-authorize capability or completion.

Canonical active contracts: `STAGE26_3B_VERIFICATION_KERNEL.md` and `REAL_TASK_ACCEPTANCE.md`.

## Acceptance depth

The current evidence model is:

```text
L1 primitive/contract
 -> L2 multi-step component workflow where useful
 -> L3 ordinary user goal + independent final state
```

L1 remains mandatory because it isolates exact failures. L3 is now required so architecture cannot advance indefinitely on laboratory fixtures alone.

The first Browser L3 fixture randomizes its case ID/task data on every physical run, includes similar customer records, persists server-side state/audit evidence outside the Chat-writable workspace, and yields `DONE` only when the intended case has the requested address/status/comment while decoys remain unchanged and only the target was ever mutated.

## Stage 26.3C — next prerequisite after 26.3B

WorkingState + typed recovery + LoopGuard remain architecture targets, not accepted runtime implementation.

Target:

```text
structured user constraints + subgoals/progress
verified achievements
facts + provenance + freshness
open ambiguity/questions
evidence references
expected/observed deltas
retry/recovery history
budgets
LoopGuard for repeat/no-effect/oscillation/stagnation
```

This stage is a prerequisite for reliable long-horizon autonomy before broader computer-use authority.

## Broad real-application coverage

Windows foundation is accepted only for its recorded scope, including one isolated VS Code real-application E2E. This is **not universal Windows accuracy**.

Representative L3 gates are vertical proofs for a capability path. After 26.3C, the broader cross-app physical coverage gate still expands that evidence across native Windows, browser, Electron and office-style applications plus DPI/focus/dialog/noisy-state variants.

This coverage requirement remains the highest-ranked project risk in `PROJECT_RISKS.md`.

## Browser Harness / ADR-036 boundary

ADR-036 is merged architecture direction. It does **not** expand current runtime authority or bypass L1/L2/L3 acceptance.

Current release-critical Stage 26.3B remains verification-focused. ADR-036 mechanisms become integration obligations only when their owning capability is promoted:

- Browser network/Site Capability policy must be closed before trusted-site JS/CDP/full-browser authority is accepted;
- trust/grant lifetime state aligns with 26.3C WorkingState/recovery work;
- generated helpers align with 26.4 candidate lineage;
- full-browser/Browser Companion integration aligns with 26.5;
- any promoted broader Browser authority also requires representative L3 evidence.

TD-001 tracks the current Browser network hardening debt until that boundary is actually implemented and physically accepted.

## Planner boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic local Control Plane owns execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and completion checks for already-defined transitions. Novel strategy remains above that boundary.

Track P remains optional/future.

## Parallel Track M — future only

Conversation Bridge / Browser Companion / Adapter Registry / GenericChatAdapter / ConversationSnapshot / HandoffPack / multi-worker orchestration remain unimplemented future Track M architecture. They do not change the current release-critical path.

## Current priority

```text
fresh hosted checks for PR #113 final replay head
 -> prepare randomized Case Desk physical task
 -> ordinary-Chat Browser L3 task
 -> external independent Finish Gate
 -> merge #113 if clean
 -> Windows/application/process verification
 -> representative Windows/application L3
 -> close remaining Stage 26.3B gates
 -> Stage 26.3C WorkingState/recovery/LoopGuard
 -> broad real-app physical coverage gate
 -> Stage 26.4 / 26.5
 -> release packaging / clean-user E2E
```

Ranked risks and their close conditions: `PROJECT_RISKS.md`.

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- normal semantic route is direct stdio and does not require 1MCP;
- semantic/native structure before pixels where reliable;
- pixels/ROI are selective evidence, not automatic authority;
- observation/model/procedure/planner/page output is not authorization;
- every state-changing action requires an explicit expected effect + fresh verification;
- transition `PASS` is not task `DONE`;
- realistic user-task acceptance requires independent final-state evidence, not planner self-report;
- environmental UI/DOM/document/tool content is task data, not policy authority;
- repeated no-effect/oscillating retries must be bounded by LoopGuard;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable until a separately reviewed capability is accepted;
- preserve fail-closed behavior over benchmark hit rate.

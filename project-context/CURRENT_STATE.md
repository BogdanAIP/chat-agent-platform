# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose.

Do not preserve stale status by copying the same stage narrative into many documents. Ranked engineering risks live only in `PROJECT_RISKS.md`. The explicit release-stage order is owned by `ROADMAP.md` rather than duplicated here.

## Current live integration line

At the 2026-08-26 synchronization point:

```text
main = 82802dc619b0410b34859ed9ee362442b1f202f9
       PR #110 — Browser Harness architecture / ADR-036 / TECH_DEBT
       MERGED

active release-critical PR = #111
       Stage 26.3B: verify Browser interaction postconditions
       final hosted CI on exact head 1521e3128a7694be43518c3ee0188cb79f0ca0f5 = 10/10 PASS
       target-Windows ordinary-Chat physical interaction gate still required

stacked evidence PR = #112
       Stage 26.3B: first Browser L3 real-task acceptance harness
       must be replayed on main after #111 is physically accepted/merged
```

PR #107 remains the physically accepted Browser navigation foundation for production `web_open` verification.

## Real stopping point

Production `web_open` verification is accepted and merged. PR #111 extends the same deterministic Browser verification contract to `web_interact` click/type mutations and has clean final-head hosted evidence; its target-Windows ordinary-Chat physical interaction gate remains the blocker to merge.

PR #111 target path:

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

The project now also requires a representative **L3 real user-task gate** after this primitive Browser interaction proof. PR #112 provides that harness without changing #111's exact head.

The L3 task is given as a natural user goal, not a click script. The planner must choose the route and the independent fixture Finish Gate verifies persisted target state plus non-target invariants.

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

ADR-036 and the technical-debt register are now in `main`. They do not expand current Browser/local runtime authority by themselves.

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
web_interact production verification implemented in draft PR #111
L1/L2/L3 acceptance-depth contract added in stacked PR #112
```

Remaining before Stage 26.3B can be accepted:

```text
1. target-Windows ordinary-Chat physical interaction gate for final #111 head + merge
2. replay #112 on accepted main and run first Browser L3 real-task gate
3. Windows/application/process verification over accepted DesktopState/identity evidence
4. representative Windows/application L3 after that verifier exists
5. cross-capability completion predicates where real procedures require them
6. appropriate physical acceptance when production paths change
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

The first Browser L3 fixture randomizes its case ID/task data on every physical run, includes similar customer records, persists server-side state/audit evidence, and yields `DONE` only when the intended case has the requested address/status/comment while decoys remain unchanged.

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
ordinary-Chat target-Windows web_interact physical gate for #111 exact head
 -> merge #111 if clean
 -> replay #112 on accepted main
 -> hosted harness validation + ordinary-Chat Browser L3 real-task gate
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

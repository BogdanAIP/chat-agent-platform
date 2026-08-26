# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose.

Do not preserve stale status by copying the same stage narrative into many documents. Ranked engineering risks live only in `PROJECT_RISKS.md`. The explicit release-stage order is owned by `ROADMAP.md` rather than duplicated here.

## Current live integration line

At the 2026-08-26 documentation synchronization point:

```text
main = 20d06e8311ef65ee04b9a8a940c4f0d5725de0e0
       PR #106 — Browser observation foundation

active release-critical PR = #107
       Stage 26.3B: verify Browser navigation final state
```

The pre-documentation-sync PR #107 head:

```text
08671b5a8763d589bcd16da69e8ed70bcb5f9509
```

had all 11 pull-request-triggered hosted workflows green.

This documentation synchronization changes the PR head. Therefore the **final exact PR head must have green hosted CI again**, then pass the required ordinary-Chat target-Windows physical Browser regression before merge. Do not reuse the older head as physical acceptance evidence for a newer commit.

## Real stopping point

Development stopped after implementing production `web_open` final-state verification and completing hosted CI, immediately before the target-Windows physical Browser gate.

PR #107 changes the production navigation path to:

```text
validate URL/network policy
 -> fresh browser snapshot BEFORE
 -> browser_navigate
 -> fresh browser snapshot AFTER
 -> BrowserObservationStream
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

Current first-slice policy is intentionally fail-closed on redirects: a delivered navigation to a different final URL is not reported as verified success.

`web_interact` click/type postcondition verification is **not** part of PR #107 and remains the next Browser slice after #107 is accepted and merged.

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

`verified_workspace_artifact_v1` uses the shared Verification Kernel for all three transitions and the independent Finish Gate for final target-goal plus staging-absence safety evidence. Physical acceptance proved completion and zero overwrite on the exact accepted head.

### Browser observation foundation

**MERGED #106.**

`BrowserObservationStream` provides bounded URL/origin/document/control state and same-stream monotonic observation identity. PR #106 itself was source-only; PR #107 is the first production semantic-browser action-path integration.

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
web_open production integration in PR #107, pending final physical acceptance
```

Remaining before Stage 26.3B can be accepted:

```text
1. final exact-head hosted + ordinary-Chat target-Windows gate for PR #107
2. web_interact click/type/control-result verification
3. Windows/application/process verification over accepted DesktopState/identity evidence
4. cross-capability completion predicates where real procedures require them
5. appropriate physical acceptance when those production paths change
```

Rules remain:

- action delivery != transition success;
- transition `PASS` != task `DONE`;
- current observed state outranks remembered procedure/demo/history;
- stale, mismatched-stream, ambiguous or incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- task-success verification and safety/policy verification remain separate;
- planner/model/procedure `candidate_done` cannot self-authorize completion.

Canonical active contract: `STAGE26_3B_VERIFICATION_KERNEL.md`.

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

After 26.3C, the next major evidence objective is a broad cross-app physical coverage gate, not another large architecture expansion. It should include representative native Windows, browser, Electron and office-style applications plus DPI/focus/dialog/noisy-state variants.

This coverage requirement is tracked as the highest-ranked project risk in `PROJECT_RISKS.md`.

## Planner boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic local Control Plane owns execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and completion checks for already-defined transitions. Novel strategy remains above that boundary.

A future planner-neutral proposal/escalation contract is a mitigation target, not current runtime capability. Track P remains optional/future.

## Parallel Track M — future only

Conversation Bridge / Browser Companion / Adapter Registry / GenericChatAdapter / ConversationSnapshot / HandoffPack / multi-worker orchestration remain unimplemented future Track M architecture. They do not change the current release-critical path.

## Current priority

```text
PR #107 final hosted CI
 -> ordinary-Chat target-Windows Browser physical gate on same exact head
 -> merge if all findings/gates are clean
 -> web_interact verification slice
 -> remaining Stage 26.3B integrations
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
- observation/model/procedure/planner output is not authorization;
- every state-changing action requires an explicit expected effect + fresh verification;
- transition `PASS` is not task `DONE`;
- environmental UI/DOM/document/tool content is task data, not policy authority;
- repeated no-effect/oscillating retries must be bounded by LoopGuard;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

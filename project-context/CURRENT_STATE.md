# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose.

Do not preserve stale status by copying the same stage narrative into many documents. Ranked engineering risks live only in `PROJECT_RISKS.md`. The explicit release-stage order is owned by `ROADMAP.md` rather than duplicated here.

## Current live integration line

At the 2026-08-26 post-#107 synchronization point:

```text
main = 5df2e5e7378ddb9083a7c3d70a62c7bfc0f6c22d
       PR #107 — production web_open final-state verification
       PHYSICALLY ACCEPTED / SQUASH-MERGED

active release-critical PR = #111
       Stage 26.3B: verify Browser interaction postconditions
       clean replay of former stacked #109 on accepted main

parallel docs PR = #110
       Browser Harness architecture / ADR-036 / TECH_DEBT
```

PR #107 physical acceptance proved on exact head `64184713e97bf2e150614cd93c77509c244cddec`:

- direct navigation -> Verification Kernel `PASS`;
- real HTTP redirect physically delivered but final canonical URL mismatch -> verification `FAIL` / fail-closed;
- independent `web_observe` confirmed the actual final page after both cases.

## Real stopping point

Production `web_open` verification is accepted and merged. The current release-critical implementation is PR #111, which extends the same deterministic Browser verification contract to `web_interact` click/type mutations.

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

PR #111 is **not accepted from inherited historical CI**. Its final exact head requires fresh hosted CI and an ordinary-Chat target-Windows physical interaction regression before merge.

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

Production `web_open` now uses fresh before/after observation plus the shared Verification Kernel; delivery alone is not success.

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
```

Remaining before Stage 26.3B can be accepted:

```text
1. final exact-head hosted + ordinary-Chat target-Windows gate for PR #111
2. Windows/application/process verification over accepted DesktopState/identity evidence
3. cross-capability completion predicates where real procedures require them
4. appropriate physical acceptance when those production paths change
```

Rules remain:

- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- current observed state outranks remembered procedure/demo/history;
- stale, mismatched-stream, ambiguous or incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- task-success verification and safety/policy verification remain separate;
- planner/model/procedure/page content cannot self-authorize capability or completion.

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

After 26.3C, the next major evidence objective is a broad cross-app physical coverage gate covering representative native Windows, browser, Electron and office-style applications plus DPI/focus/dialog/noisy-state variants.

This coverage requirement remains the highest-ranked project risk in `PROJECT_RISKS.md`.

## Browser Harness / ADR-036 boundary

PR #110 records future Browser Harness-derived architecture. It does **not** expand current runtime authority or silently add new Stage 26.3B acceptance gates.

Current release-critical Stage 26.3B remains verification-focused. ADR-036 mechanisms are staged as integration obligations only when their owning capability is promoted:

- Browser network/Site Capability policy must be closed before trusted-site JS/CDP/full-browser authority is accepted;
- trust/grant lifetime state aligns with 26.3C WorkingState/recovery work;
- generated helpers align with 26.4 candidate lineage;
- full-browser/Browser Companion integration aligns with 26.5.

TD-001 tracks the current Browser network hardening debt until that boundary is actually implemented and physically accepted.

## Planner boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic local Control Plane owns execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and completion checks for already-defined transitions. Novel strategy remains above that boundary.

Track P remains optional/future.

## Parallel Track M — future only

Conversation Bridge / Browser Companion / Adapter Registry / GenericChatAdapter / ConversationSnapshot / HandoffPack / multi-worker orchestration remain unimplemented future Track M architecture. They do not change the current release-critical path.

## Current priority

```text
PR #110 docs/ADR synchronization
 -> PR #111 final exact-head hosted CI
 -> ordinary-Chat target-Windows web_interact physical gate
 -> merge #111 if clean
 -> Windows/application/process verification
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
- environmental UI/DOM/document/tool content is task data, not policy authority;
- repeated no-effect/oscillating retries must be bounded by LoopGuard;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable until a separately reviewed capability is accepted;
- preserve fail-closed behavior over benchmark hit rate.

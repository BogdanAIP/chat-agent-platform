# Current State

## Repository-state rule

Always resolve live `main`, open PRs, exact PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose. `ROADMAP.md` owns release-stage order; `PROJECT_RISKS.md` owns ranked risks; `EVIDENCE_INDEX.md` owns exact accepted heads and machine-local evidence locators.

## Current accepted boundary

Stage 26.3B is **ACCEPTED / CLOSED for the recorded representative scope**.

Accepted lineage now includes:

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
Track M + ADR-037 architecture                    MERGED #116 / FUTURE AUTHORITY ONLY
Browser L3 stronger source-provenance repeat      PHYSICAL ACCEPTED / MERGED #118
post-26.3B adversarial assurance plan             MERGED #119
```

These are scoped proofs, not universal Browser/Windows accuracy claims.

## What #118 closed

Historical Browser L3 #113 remains valid for its original functional/final-state/history scope. #118 repeated one randomized ordinary-Chat Browser L3 task under the stronger Source Provenance methodology and independently proved:

- exact clean source head at prepare and Finish Gate;
- installed semantic runtime and complete Node dependency-tree binding to the exact committed lock;
- byte-lock guardian continuity while the Browser task ran;
- exact target final state with decoys unchanged;
- exactly one target save and one audit mutation;
- independent `EXTERNAL_FINISH_GATE=DONE` only after cleanup/provenance checks passed.

Exact accepted head, qualification root and full markers live in `EVIDENCE_INDEX.md` and PR #118.

The accepted Browser L3 path is the real target-Windows semantic Browser route backed by headless Playwright/Chrome. It does **not** claim that a visible headed Chrome window was driven on the Windows desktop. Visible-desktop Browser control would be a different acceptance claim.

Physical qualification also found three harness/runtime defect classes before the accepted run: locale-sensitive timestamp parsing, producer/consumer manifest-field mismatch, and Playwright runtime output contaminating a source worktree through inherited process CWD. The first two are regressed in #118; the runtime-output ownership issue remains explicit hardening debt and is represented in `MUTATION_ASSURANCE.md` as a permanent adversarial case.

## Normal public route

Exactly six Chat-facing tools remain accepted:

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
 -> canonical six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

1MCP remains optional internal Extension Manager infrastructure.

Ordinary ChatGPT is the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions. It is not a second planner.

## Stage 26.3C — current release-critical runtime target

Stage 26.3C is now the next implementation stage: project-owned WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport.

WorkingState v1 must be capability-spanning structured operational state, never private chain-of-thought. It must not be replaced by OpenAdapt procedure-local checkpoint state or by future provider/session task state.

Initial mutating-outcome vocabulary:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` requires reconciliation of the **same logical operation** from fresh authoritative state before retry. Ambiguous delivery is not permission to redeliver.

Mandatory 26.3C guarantees include:

- structured failure reasons survive retry/replan handoff;
- repeated physical attempt fingerprints trip LoopGuard before blind redelivery;
- task/procedure/strategy budgets are distinct and fail closed on exhaustion;
- stale WorkingState/evidence cannot authorize a new effect;
- recovery after restart cannot replay a proven committed effect;
- StagnationReport is diagnostic/escalation data, not a grant or second planner;
- phases/checkpoint nodes are introduced where useful for `procedure_run` / resumable procedures, not imposed as a universal planner hierarchy.

Adversarial contracts for these guarantees are defined in `MUTATION_ASSURANCE.md` and should land with the first runtime slice rather than afterward.

## Track M / ADR-035 boundary

Track M remains future/parallel architecture, not current public authority.

Keep identities separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Browser Companion remains the primary cross-provider adapter family for authenticated web AI conversations, with stronger reviewed native/host interfaces preferred per exact target when available. `GenericChatAdapter` provides common structural extraction/normalization, while thin provider adapters remain necessary for exact selectors, quirks and identity.

Track M requires stable operation identity, ambiguous-outcome reconciliation, result correlation, minimum worker authority, bounded fan-out and independent Finish Gate. Initial nested spawn depth defaults to 1.

## ADR-037 boundary

`CapabilityRegistry`, `TypedEventBus` and registered `PolicyHooks` remain future project-owned substrate:

- discovery/availability/health/trust metadata != authorization;
- events may trigger fresh observation but do not prove effect success;
- hooks are bounded deterministic handlers, not arbitrary shell/Python and not a second planner;
- hook/event output cannot upgrade FAIL/UNKNOWN/DONE semantics or widen grants;
- 26.3C may adopt only minimal typed internal seams directly needed by WorkingState/recovery/LoopGuard/Finish Gate.

## Broad coverage and later work

Representative L3 gates are vertical proofs. After 26.3C, broader real-app physical coverage still needs multiple native Windows, Browser, Electron, office-style and file/dialog task families across DPI/focus/dialog/noisy-state variants.

Then follow the bounded OpenAdapt spike, Stage 26.4 candidate skills, Stage 26.5 hybrid integration, distribution and clean-user release according to `ROADMAP.md`.

## Current priority

Do not reconstruct a competing stage list here; `ROADMAP.md` owns the release order. Immediate work is:

```text
Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
```

Before or alongside that first runtime slice, close the small Browser runtime-output ownership hardening and convert the Stage 26.3B defect classes into deterministic adversarial regressions where feasible.

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page/worker output is not authorization;
- every state-changing production action requires explicit ExpectedEffect + fresh verification;
- action/message delivery != transition success;
- ambiguous mutating outcome must be reconciled before unsafe retry;
- transition `PASS` != task `DONE`;
- procedure/worker completion != independent task completion;
- stale/mismatched/ambiguous/incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- session discoverability does not imply lifecycle authority;
- generic Windows/local/harness execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

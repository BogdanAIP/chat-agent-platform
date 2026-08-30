# Current State

## Repository-state rule

Resolve live `main`, relevant open PRs/exact heads, hosted checks and required physical evidence before new work. Current code/tests/current CI/current physical evidence outrank prose.

Ownership:

- `CURRENT_STATE.md` = accepted/current boundary + immediate work;
- `ROADMAP.md` = release order;
- `PROJECT_RISKS.md` = ranked risks;
- `EVIDENCE_INDEX.md` = exact accepted physical heads/result locators;
- `ARCHITECTURE_REUSE_BASELINE.md` = prior component/reuse lineage for applicable Stage Research.

## Current accepted boundary

Stage 26.3B is **ACCEPTED / CLOSED for its recorded representative scope**.

The next stage has already started: Stage 26.3C is **partially accepted**, not a blank future stage.

Accepted foundation now includes:

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
Track M + ADR-037 future architecture             MERGED #116 / NO CURRENT AUTHORITY
CAP-M0 Verification mutation assurance            ACCEPTED / MERGED #117
Browser stronger source-provenance L3 repeat      PHYSICAL ACCEPTED / MERGED #118
post-26.3B adversarial assurance direction        MERGED #119
WorkingState + LoopGuard L1 foundation             ACCEPTED / MERGED #124
stage-research mechanism-depth hardening           MERGED #127
```

These are scoped proofs. They do not imply universal Browser/Windows/application reliability.

## Current public route

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

Ordinary ChatGPT is the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, recovery/reconciliation budgets and independent completion checks for already-selected transitions. It is not a second planner.

## Stage 26.3C — accepted foundation

PR #124 merged the L1 project-owned WorkingState/LoopGuard foundation without wiring it into a new production consequence path.

The accepted foundation includes capability-spanning structured operational state, typed failures/reconciliation, distinct task/procedure/strategy budgets, LoopGuard decisions and diagnostic StagnationReport semantics.

WorkingState is not private reasoning and must never persist chain-of-thought.

Mutating outcomes include:

```text
VERIFIED_APPLIED
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

Key accepted invariants include:

- mutating intent is bound to current concrete observation/provenance;
- physical attempts consume bounded budgets and are rechecked by LoopGuard;
- unresolved ambiguous outcome blocks further mutation until reconciled;
- reconciliation requires fresh same-stream evidence;
- durable history cannot switch actor/environment/evidence provenance or create impossible attempt/reconciliation chronology;
- stale/non-advancing evidence cannot authorize another physical mutation;
- `StagnationReport` is diagnostic/escalation data, never authority or a second planner.

This L1 acceptance does **not** prove crash-safe production integration of every existing capability/procedure.

## Current release-critical work

The active Stage 26.3C problem is now **production integration and restart-safe recovery**, not invention of WorkingState from scratch.

At this snapshot, draft PR #126 is the first bounded production consumer proposal for `verified_workspace_artifact_v1`. Resolve its live head/body before acting; its current fresh Stage Research decision is `NARROW`.

The selected scope is deliberately limited to process crash/restart on the supported local Windows filesystem. It does not claim machine/power-loss transactional durability.

Current researched design direction for that draft includes:

```text
existing procedure checkpoint
 + procedure-local non-authoritative prepared intent
 + one cooperating runner/task via OS lock
 + same-stream fresh reconciliation
 + stable logical operation identity
 + reconstructible file identity
 + hard-link final create on supported local NTFS
 + fail-closed ambiguous/missing/corrupt state
```

The draft must still earn its required exact-head deterministic/fault-injection CI, independent review and target-Windows physical `procedure_run` acceptance before merge because it changes a real consequence-bearing path.

No draft PR text or implementation is accepted merely because it appears here; live code/evidence remains authoritative.

## Post-26.3C immediate priority — automatic independent review

After the current 26.3C production integration is accepted/closed, the next immediate development priority is to productionize the **bounded automatic independent-review path** proven experimentally by PR #138 before beginning the broad real-application coverage gate.

The immediate product/process problem is narrow and concrete:

```text
PR reaches review-ready exact head
 -> freeze BASE_SHA + HEAD_SHA
 -> launch a fresh ordinary-ChatGPT context without a user click
 -> run the repository code-review contract with GitHub read-only evidence
 -> return REVIEW_RESULT_V1 to the development/review lifecycle
 -> reject stale-head results and repeat after material fixes
```

This exists because fresh ordinary-ChatGPT semantic review is the required primary review gate in `AGENTS.md`, while Codex Review is valuable but optional and may be unavailable because of quota. Automating the required reviewer must preserve fresh-context independence, exact-ref binding, read-only review authority, fail-closed result handling and the current `code-review` skill contract; it must not turn the reviewer into another developer context.

PR #138's successful one-shot deep-link/autosend/scheduler probes are evidence for this next bounded consumer, not themselves production acceptance. Before productionizing the review lifecycle, rerun fresh Stage Research against the then-current repo/harness state and define the minimum scheduler/result-handoff/staleness semantics required for the reviewer.

Review-automation runs should retain bounded non-secret operational evidence useful for later qualification: run/correlation identity, trigger reason, exact reviewed refs, launch/delivery outcome, fresh-context proof where available, result disposition, stale detection, duplicate/missed wake, timeout/failure class and whether manual intervention was required. This evidence is intended to build a real test corpus during development.

The reviewer use case does **not** by itself authorize general same-task autonomous continuation. General `unfinished task -> WAITING -> wake -> planner continuation` remains a separate future Stage Research seam; experience from the bounded reviewer may later inform that research.

## Architecture research rule now in force

Merged #127 strengthened `stage-research` so materially new persistence/recovery/retry/concurrency/identity/authority mechanisms require direct solution-domain evidence, materially distinct alternatives and a complete failure/crash matrix before production code.

PR #128 adds the canonical architecture/reuse comparison baseline. When that process applies, research must explicitly compare affected prior component/project-owned roles rather than silently rebuilding or replacing them.

## Browser accepted scope and remaining hardening

The accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. It does not prove visible headed desktop-browser control.

The stronger #118 qualification also proved that independent provenance/Finish Gate evidence outranks planner self-report. Invalid attempts exposed real harness/runtime defect classes and were rejected rather than waived.

One small implementation debt remains relevant: Playwright runtime output ownership must be explicit so Browser runtime artifacts cannot escape into an arbitrary caller/source working directory. `TECH_DEBT.md` owns the close condition.

## Future/parallel boundaries

Track M Agent Session / Delegation and ADR-037 CapabilityRegistry/Event/Policy Hooks remain future/parallel architecture only. They add no current public tool or runtime authority.

OpenAdapt remains a selected source of procedure-local compiler/resume/effect-evidence mechanics where fresh Stage Research shows they fit. It does not replace project WorkingState, Verification Kernel, Control Plane authority or Finish Gate.

UFO/UFO²-derived Windows/Office mechanics remain selective adapter sources, not a second planner/AgentOS.

## Immediate critical path

Do not reconstruct another stage list here; `ROADMAP.md` owns release order.

Immediate work is:

```text
finish the researched Stage 26.3C production WorkingState/reconciliation integration
 -> prove restart/no-duplicate-effect behavior on the real procedure path
 -> productionize bounded automatic fresh-ChatGPT review infrastructure from the #138 evidence
```

Then continue according to `ROADMAP.md` with broader real-app physical coverage, bounded OpenAdapt integration, 26.4 candidate skills and 26.5 hybrid integration.

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page/worker output is evidence/data, not authorization;
- every state-changing production action requires explicit ExpectedEffect + fresh verification;
- action/message delivery != transition success;
- ambiguous mutating outcome must be reconciled before unsafe retry;
- transition `PASS` != task `DONE`;
- procedure/worker completion != independent task completion;
- stale/mismatched/ambiguous/incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- generic Windows/local/harness execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

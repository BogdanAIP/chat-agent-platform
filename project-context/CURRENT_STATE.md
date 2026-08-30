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

Stage 26.3B remains **ACCEPTED / CLOSED for its recorded representative scope**.

Stage 26.3C is now also **ACCEPTED / CLOSED for its declared production/restart scope** through merged PR #126.

Relevant accepted progression now includes:

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
WorkingState + LoopGuard L1 foundation            ACCEPTED / MERGED #124
stage-research mechanism-depth hardening          MERGED #127
Stage 26.3C production WorkingState integration   PHYSICAL ACCEPTED / MERGED #126
```

These remain scoped proofs. They do not imply universal Browser/Windows/application reliability or machine/power-loss transactional durability.

## Stage 26.3C accepted production scope

PR #126 is merged and accepted. Exact commit, reviewed-head and physical-evidence locators belong in `EVIDENCE_INDEX.md` and PR history rather than this live-status document.

The accepted first bounded production consumer is `verified_workspace_artifact_v1` on the supported local Windows workspace path.

Accepted behavior includes:

```text
WorkingState + stable logical mutating-operation identity
procedure-local durable checkpoint + prepared intent
bounded task/procedure/strategy budgets + LoopGuard
fresh same-stream reconciliation before unsafe retry
per-task cooperating-runner serialization
generation-bound file identity for consequence-bearing resume
Windows file/namespace pinning around path-based consequences
three-action stage_create -> final_create -> staging_cleanup graph
fail-closed corrupt/missing/inconsistent checkpoint handling
public task correlation only when durable resumable state exists
```

Historical weak schema-1 consequence-bearing checkpoints that cannot prove generation identity remain fail-closed rather than being upgraded from current filesystem state.

The accepted guarantee is **process crash/restart within the declared local-Windows workspace scope**. It does not claim atomic machine/power-loss durability.

Release evidence for #126 included exact-head hosted CI/security, all review-thread dispositions, mandatory fresh ordinary-ChatGPT independent semantic review with zero surviving findings, and target-Windows physical `procedure_run` qualification. Exact physical locators belong in `EVIDENCE_INDEX.md` / PR history.

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

WorkingState is capability-spanning structured operational state, not private reasoning, and must never persist chain-of-thought.

## Current release-critical work — bounded automatic independent review

With 26.3C closed, the next immediate development priority is to productionize the **bounded automatic independent-review path** before the broad real-application coverage gate.

The target lifecycle is narrow:

```text
PR reaches review-ready exact head
 -> freeze BASE_SHA + HEAD_SHA
 -> launch a genuinely fresh ordinary-ChatGPT context without a routine user click
 -> run repository `.agents/skills/code-review/SKILL.md` with GitHub read-only evidence
 -> return REVIEW_RESULT_V1 to the development/review lifecycle
 -> reject stale/malformed/ambiguous results
 -> repeat after any material head change
```

This exists because fresh ordinary-ChatGPT semantic review is the required primary semantic review gate in `AGENTS.md`, while Codex Review is useful optional evidence and may be quota-limited.

PR #138 is **experimental evidence**, not production acceptance. Its one-shot deep-link/autosend/scheduler probes demonstrated that a fresh ChatGPT context can be launched and can reach the bridge without a routine user click. It does not yet establish the production reviewer scheduler/result-handoff/staleness contract.

Before production implementation of this reviewer lifecycle, rerun fresh Stage Research against the current post-26.3C repository/harness state. Define the minimum launch, correlation, result-handoff, duplicate/missed wake, timeout and stale-head semantics required for this bounded consumer.

Reviewer automation must preserve:

- genuinely fresh ordinary-ChatGPT context;
- exact repository / PR / BASE_SHA / HEAD_SHA binding;
- independent evidence reconstruction;
- read-only reviewer authority over repository production state;
- fail-closed missing/malformed/stale/ambiguous result handling;
- no false representation of unavailable Codex Review as completed;
- no promotion into a second developer/planner context.

Review runs should retain bounded non-secret operational evidence useful for later qualification: run/correlation identity, trigger reason, exact refs, launch/delivery outcome, fresh-context evidence where available, result disposition, stale detection, duplicate/missed wake, timeout/failure class and whether manual intervention was required.

The bounded reviewer does **not** authorize general same-task autonomous continuation. General `unfinished task -> WAITING -> wake -> planner continuation` remains a separate future Stage Research seam.

## Architecture research rule now in force

Merged #127 strengthened `stage-research` so materially new persistence/recovery/retry/concurrency/identity/authority mechanisms require direct solution-domain evidence, materially distinct alternatives and a complete failure/crash matrix before production code.

PR #128 added the canonical architecture/reuse comparison baseline. When that process applies, research must explicitly compare affected prior component/project-owned roles rather than silently rebuilding or replacing them.

The automatic-review production implementation therefore requires a fresh Stage Research re-entry before runtime edits.

## Browser accepted scope and remaining hardening

The accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. It does not prove visible headed desktop-browser control.

The stronger #118 qualification also proved that independent provenance/Finish Gate evidence outranks planner self-report. Invalid attempts exposed real harness/runtime defect classes and were rejected rather than waived.

One small implementation debt remains relevant: Playwright runtime output ownership must be explicit so Browser runtime artifacts cannot escape into an arbitrary caller/source working directory. `TECH_DEBT.md` owns the close condition.

## Future/parallel boundaries

Track M Agent Session / Delegation and ADR-037 CapabilityRegistry/Event/Policy Hooks remain future/parallel architecture only. They add no current public tool or runtime authority.

OpenAdapt remains a selected source of procedure-local compiler/resume/effect-evidence mechanics where fresh Stage Research shows they fit. It does not replace project WorkingState, Verification Kernel, Control Plane authority or Finish Gate.

UFO/UFO²-derived Windows/Office mechanics remain selective adapter sources, not a second planner/AgentOS.

General same-task wake/resume, a generic scheduler/event bus, worker rotation and broad autonomous continuation remain unaccepted future mechanisms unless separately researched and reviewed.

## Immediate critical path

Do not reconstruct another stage list here; `ROADMAP.md` owns release order.

Immediate work is:

```text
fresh Stage Research for bounded automatic independent-review infrastructure
 -> productionize fresh-context launch + exact-ref/result handoff
 -> prove stale/duplicate/failure handling fail-closed
 -> remove routine user click/copy-paste from required review lifecycle
```

Then continue according to `ROADMAP.md` with the broad real-application physical coverage gate, bounded OpenAdapt integration, 26.4 candidate skills and 26.5 hybrid integration.

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

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

With 26.3C closed, the next immediate development priority is the **bounded automatic independent-review path** before the broad real-application coverage gate.

The target lifecycle is now deliberately local-result-only:

```text
PR reaches review-ready exact head
 -> freeze BASE_SHA + HEAD_SHA
 -> launch a genuinely fresh ordinary-ChatGPT context without routine user launch/paste work
 -> require a reviewer security context where GitHub mutation actions are unavailable
 -> run `.agents/skills/code-review/SKILL.md` with independent repository evidence
 -> submit REVIEW_RESULT_V1 through fixed local procedure
 -> reconcile automatic/manual result under the same local operation lock
 -> reject stale/malformed/pending/ambiguous state
 -> merge only after final live-identity + local-result reconciliation
```

There is **no automated GitHub write in v1**. The earlier PR-comment publisher design was removed after review exposed two avoidable problems: a broad provider permission bucket and an ambiguous POST that could complete after a zero-result scan/manual fallback.

This exists because fresh ordinary-ChatGPT semantic review is the required primary semantic review gate in `AGENTS.md`, while Codex Review remains useful optional evidence and may be quota-limited.

PR #138 is **experimental evidence**, not production acceptance. Its one-shot deep-link/autosend probes demonstrated that a fresh ChatGPT context can be launched without a routine user click. It does not authorize a production scheduler or general continuation runtime.

PR #140 records the current **proposed `NARROW` Stage Research decision** in `AUTOMATIC_REVIEWER_RESEARCH.md`. Production implementation is **still blocked** until #140 itself passes exact-head hosted gates, mandatory fresh ordinary-ChatGPT independent semantic review with all findings dispositioned, and merge into `main`.

If #140 is accepted, selected v1 implementation is bounded to:

```text
exact frozen REVIEW_REQUEST_V1
 -> registered launch_independent_review_v1 behind existing procedure_run
 -> accepted Stage 26.3C OS-backed single-writer operation lock
 -> immutable exclusive-created genesis with private review_run_id
 -> accepted-style crash-safe mutable operation/result checkpoint
 -> durable dispatch-attempted before one browser launch
 -> refined fresh-new-chat deep-link/autosend
 -> qualified ordinary-Chat reviewer environment where GitHub mutation actions are unavailable
 -> MV3 service-worker IndexedDB unique-key Send claim
 -> one automatic Send authority grant
 -> submit_independent_review_result_v1 stores validated result locally
 -> reconcile_independent_review_result_v1 returns automatic result or atomically records manual fallback
 -> final live PR identity + local result-state validation
```

The immutable genesis and mutable checkpoint are separate. `genesis exists + mutable state missing`, the inverse, identity/nonce mismatch, invalid state or ambiguous temp residue fail closed without manufacturing a replacement nonce. Hostile deletion of the whole private state root, storage rollback and machine/power-loss loss remain outside the declared v1 guarantee.

Reviewer authority is now an explicit environment qualification. Accepted automatic environments are those where GitHub mutation actions are **actually unavailable**: for example GitHub app disconnected/disabled, or supported workspace Action Control exposing only read actions. Per-message non-selection and approval prompts are not accepted as the security boundary. If this cannot be proved while preserving the required ordinary-Chat + bridge/read path, automatic launch fails closed and manual fresh review remains required.

Automatic result handoff is local. `submit_independent_review_result_v1` validates the private nonce/exact refs/policy/context/result and atomically records `automatic-result-recorded`. `reconcile_independent_review_result_v1`, under the same operation lock, either returns that result or can atomically record a valid manual fresh-review fallback, permanently closing later automatic submission. This removes the late external-comment race structurally.

Automatic wake/resampling of the unfinished development conversation after the reviewer finishes is **not** part of this slice. The development conversation still resumes when the user returns; result copy/paste is removed because the development side reads the local review operation state itself. General same-task continuation remains separate future Stage Research.

The same research makes quality measurement part of the reviewer work:

- Harbor is an **evaluation harness only**, not production runtime/authority;
- ReviewBench is the first small baseline;
- SWE-Review-Bench provides a larger decision/revision control;
- CR-Bench/CR-Evaluator provides false-positive / signal-to-noise control;
- semantic reviewer quality and CAP lifecycle reliability remain separate planes;
- development and holdout benchmark evidence remain separated;
- a CAP Review Regression Set should retain real repository defect classes without encoding task-specific answers.

The first benchmark run establishes a baseline; it is not an invented fixed release threshold. Automatic review is not stable infrastructure if UI friction decreases while semantic review quality materially regresses versus the manual reviewer control.

Reviewer automation must preserve:

- genuinely fresh ordinary-ChatGPT context;
- exact repository / PR / BASE_SHA / HEAD_SHA binding;
- independent evidence reconstruction;
- deterministic write-action unreachability in the qualified reviewer environment;
- no reviewer-held GitHub write credential/action and no automated GitHub publisher/comment path;
- local crash-safe automatic-result recording and same-lock manual fallback closure;
- fail-closed missing/malformed/pending/stale/ambiguous result handling;
- no blind automatic relaunch after ambiguous launch/claim/Send;
- no false representation of unavailable Codex Review as completed;
- no promotion into a second developer/planner context.

Review runs should retain bounded non-secret operational evidence useful for qualification: run/correlation identity, trigger reason, exact refs, launch/delivery outcome, authority-qualification evidence, fresh-context evidence, result disposition, stale detection, duplicate/missed delivery, timeout/failure class and manual-intervention requirement. The private run capability must not be exposed to the development caller before automatic result closure.

## Architecture research rule now in force

Merged #127 strengthened `stage-research` so materially new persistence/recovery/retry/concurrency/identity/authority mechanisms require direct solution-domain evidence, materially distinct alternatives and a complete failure/crash matrix before production code.

PR #128 added the canonical architecture/reuse comparison baseline. When that process applies, research must explicitly compare affected prior roles and assign exactly one canonical lineage decision per existing role; new roles are `NEW_ARCHITECTURE` and use the Scope Expansion Gate.

PR #140 is currently the **open acceptance gate** for automatic-review research. Its revised Brief now records direct filesystem, IndexedDB/service-worker and ChatGPT action-control solution evidence, plus the local result-reconciliation design selected after the latest review findings.

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
finish #140 Stage Research acceptance on a frozen exact head
 -> require exact-head CI/security + zero unresolved review findings
 -> require mandatory fresh ordinary-ChatGPT semantic review
 -> merge #140 only if the proposed NARROW contract is accepted
 -> only then implement that accepted bounded automatic-review lifecycle
 -> prove immutable-genesis + mutable-state crash/restart invariants
 -> prove qualified reviewer environment removes GitHub mutation actions
 -> prove MV3/IndexedDB one-claim Send behavior
 -> prove local submit/reconcile + manual-fallback race closure
 -> prove crash/corrupt/stale/malformed/pending state fail closed
 -> run target-Windows ordinary-Chat E2E with zero routine launch/paste/result-copy intervention when authority qualification succeeds
 -> attach Harbor evaluation seam after the first honest E2E
 -> establish ReviewBench + bounded larger/signal-noise baselines
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

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

Stage 26.3C remains **ACCEPTED / CLOSED for its declared production process-restart/local-Windows scope** through merged PR #126.

Relevant accepted progression includes:

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
Track M future architecture                       MERGED #116 / DESIGN ONLY AT THAT POINT
CAP-M0 Verification mutation assurance            ACCEPTED / MERGED #117
Browser stronger source-provenance L3 repeat      PHYSICAL ACCEPTED / MERGED #118
WorkingState + LoopGuard L1 foundation            ACCEPTED / MERGED #124
Stage 26.3C production WorkingState integration   PHYSICAL ACCEPTED / MERGED #126
stage-research mechanism-depth hardening          MERGED #127
automatic-review Stage Research / local-result v1 ACCEPTED NARROW / MERGED #140
automatic-review local state foundation           ACCEPTED / MERGED #141
automatic-review fixed procedure wiring           ACCEPTED / MERGED #142
```

These are scoped proofs. They do not imply universal Browser/Windows/application reliability, machine/power-loss transactional durability, or a generally accepted multi-agent runtime.

## Stage 26.3C accepted production scope

The first accepted consequence-bearing production consumer remains `verified_workspace_artifact_v1` on the supported local Windows workspace path.

Accepted behavior includes:

```text
WorkingState + stable logical mutating-operation identity
procedure-local durable checkpoint + prepared intent
bounded task/procedure/strategy budgets + LoopGuard
fresh same-stream reconciliation before unsafe retry
per-task cooperating-runner serialization
generation-bound file identity for consequence-bearing resume
Windows file/namespace pinning around path-based consequences
fail-closed corrupt/missing/inconsistent checkpoint handling
```

The accepted guarantee is process crash/restart within the declared local-Windows scope. It does not claim machine/power-loss atomicity.

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
 -> canonical six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

Ordinary ChatGPT remains the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, recovery/reconciliation budgets and independent completion checks for already-selected transitions. It is not a second planner.

WorkingState is capability-spanning structured operational state, never private chain-of-thought.

## Current release-critical work — bounded Agent Session / Delegation

Fresh Stage Research in PR #149 re-entered Track M and selected **NARROW** rather than continuing reviewer-specific launch/state mechanics as the product-level architecture.

The selected first product mechanism is exactly:

```text
one ordinary-ChatGPT manager
 -> one genuinely fresh read-only worker
 -> one bounded delegation identity
 -> one initial delivery
 -> one correlated structured terminal result
 -> durable local closure when that result is captured
```

This does **not** accept broad multi-agent orchestration. It deliberately excludes nested/fan-out workers, mutating children, project/worktree/environment creation, a scheduler/event bus, worker rotation, long-lived background workers and automatic same-task parent wake/resampling.

PR #149 is the active implementation PR and remains **UNACCEPTED / DRAFT until its required review and physical evidence pass**.

Its implementation currently contains two layers:

### L1 — generic delegation state

```text
provider-independent deterministic delegation identity
immutable private genesis + private run capability
one delivery identity
accepted OS-backed single-writer locking
crash-safe mutable state replacement
launch-attempt committed before physical launch authority
child/session binding
one delivery claim
prepared | claimed | unknown | delivered delivery state
unknown -> delivered reconciliation only from fresh evidence
one correlated terminal WORKER_RESULT_V1
bounded payload + adapter-computed SHA-256
fail-closed corrupt/missing/foreign/temp-residue state
```

A restart never manufactures a replacement run/delivery identity and never regains blind launch/Send authority.

### L2 candidate — first `chatgpt-temporary` provider adapter

The first concrete adapter is intentionally provider-specific rather than a premature generic provider framework.

Candidate path:

```text
generic delegation state
 -> durable launch-attempt
 -> ChatGPT Temporary Chat adapter
 -> positive fresh/non-personalized/no-plugin child qualification
 -> extension-origin IndexedDB unique delivery claim across tabs
 -> project-local delivery claim
 -> exactly one Send authority
 -> visible delivery observation
 -> delivered | unknown
 -> same-delivery reconciliation after ambiguity
 -> exact WORKER_RESULT_V1 capture when the original browser context remains available
 -> durable terminal result
```

The MV3 extension has no `nativeMessaging`, GitHub, filesystem, cookies, downloads, management or generic network authority. Its only host permission is the pinned loopback controller at `127.0.0.1:3078`.

Target-Windows physical qualification proved that the specialized Temporary Chat path can produce one fresh qualified worker, exactly one Send, visible delivery and a valid terminal worker result, but did **not** positively expose a stable provider conversation identity suitable for complete-Chrome restart recovery. The earlier browser-recovery research explicitly required re-entry in that case.

`AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md` is therefore the current adapter-specific NARROW authority. `fresh_readonly_worker_v1` is now explicitly an **ephemeral one-shot independence profile**, not a persistent Agent Session. The durable IndexedDB delivery claim and same-live-service-worker pre-Send owner witness remain, but provider-conversation restart recovery is disabled. A complete browser/service-worker lifetime loss never reconstructs Send or monitor authority. If trustworthy result capture was not already completed, the durable delegation remains fail-closed/open rather than fabricating a result or relaunching another worker.

The private durable `run_id` is not present in the worker prompt and is not placed in the HTTP query. The launch bootstrap carries it in the URL fragment for the initial project extension context, and the model-facing task receives only bounded delegation/delivery/task correlation. A later ordinary ChatGPT page cannot recover that private capability through `resume-intent`.

The physical qualification launcher binds the runtime/extension assets to a clean exact repository HEAD before execution, opens a browser only when durable `launch_now=true`, and rechecks source provenance after terminal result capture. This is qualification infrastructure, not a new public tool or scheduler.

Persistent rich-context ordinary-ChatGPT conversation identity, automatic browser wake and cross-restart existing-session delivery remain separate future research. The parked Prime research branch is the next decision point after #149 for determining which durable session/runtime mechanics should be project-owned versus adapted from Prime before a generic existing-session implementation is selected.

## Automatic reviewer status

The accepted reviewer-specific local state and fixed `launch_independent_review_v1`, `submit_independent_review_result_v1` and `reconcile_independent_review_result_v1` procedures from #141/#142 remain intact.

They are **not deleted or silently replaced by #149**. Reviewer methodology, exact PR/BASE/HEAD semantics, read-only GitHub authority qualification, `REVIEW_RESULT_V1`, Harbor/ReviewBench evaluation and manual-fallback rules remain specialist policy.

The architecture direction is now:

```text
generic bounded Agent Session / Delegation lifecycle
 -> fresh Temporary Chat reviewer-style consumer
 -> reviewer-specific task/result/authority policy above it
```

MimiSeek may later consume the same fresh-worker capability for its independent reviewer while keeping review-job semantics outside CAP. Returning a result to an existing persistent project chat is a separate existing-session delivery capability and is not smuggled into the Temporary adapter.

Migration occurs only after the generic worker path is physically accepted and can preserve all existing reviewer guarantees. Until then, the accepted reviewer procedures remain the release-assurance fallback.

PR #138 and #145 remain experiment evidence only; they do not become production authority. Reusable fresh-chat/Send observations may be adapted, while reviewer-specific experiment code does not define generic Agent Sessions.

## Acceptance required for PR #149

Before #149 can merge, require:

```text
focused generic state-machine tests
 -> deterministic first-adapter/controller/extension tests
 -> duplicate-tab/process/restart/unknown-delivery adversarial tests
 -> preliminary exact-head hosted CI/security and six-tool regressions
 -> freeze exact BASE/HEAD
 -> fresh ordinary-ChatGPT exact-BASE/exact-HEAD semantic review
 -> disposition/fix every surviving finding; fresh review again if HEAD moves
 -> target-Windows/Plus physical qualification on the reviewed exact HEAD
 -> exact source/runtime provenance for the physical claim
 -> normal uninterrupted fresh-worker result capture
 -> complete-Chrome browser-loss fail-closed proof with zero second Send/recovery authority
 -> final exact-head hosted CI
 -> re-resolve BASE/HEAD unchanged before merge
```

The normal physical E2E must be a **non-reviewer** task. A code-review run does not count as proof that the generic lifecycle is truly specialist-independent.

The browser-loss physical case does not require restoration of the Temporary conversation. It proves the opposite safety boundary: after complete browser-context loss the ephemeral profile cannot regain Send/monitor authority, cannot blindly relaunch, and preserves truthful durable state unless a result was already recorded.

A worker result is evidence/data. It does not grant a capability, self-authorize a consequence, or by itself make the manager's whole user task `DONE`.

## Architecture research rule now in force

Merged #127 requires Stage Research re-entry for materially new persistence/recovery/retry/concurrency/identity/security/authority mechanisms.

`AGENT_SESSION_DELEGATION_REENTRY.md` remains the generic NARROW foundation authority for #149. `AGENT_SESSION_PROFILE_BOUNDARY_REENTRY.md`, `AGENT_SESSION_PRE_SEND_RESTART_FENCE.md` and `AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md` refine the active first-adapter boundary. The latest ephemeral re-entry supersedes the prior positive provider-conversation restart-recovery requirement for `fresh_readonly_worker_v1` while preserving the earlier one-Send and fail-closed ownership findings.

If implementation requires nested/fan-out workers, a new scheduler/event bus, mutating children, environment creation, broad provider authority, automatic parent wake or a materially different durability/concurrency mechanism, stop and re-enter Stage Research rather than widening #149 silently.

## Browser accepted scope and remaining hardening

The previously accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. The `chatgpt-temporary` adapter is a separate headed authenticated-browser qualification path and is not accepted merely because earlier Browser L3 passed.

One existing Browser implementation debt remains: Playwright runtime output ownership must be explicit so runtime artifacts cannot escape into arbitrary caller/source working directories. `TECH_DEBT.md` owns that close condition.

## Future/parallel boundaries

ADR-037 CapabilityRegistry/Event/Policy Hooks remains future/parallel architecture only.

General same-task wake/resume, generic existing-session delivery, a generic scheduler/event bus, worker pools, worker rotation and broad autonomous continuation remain unaccepted future mechanisms.

OpenAdapt remains a selected source for procedure-local compiler/resume/effect-evidence mechanics when revalidated for the concrete consumer. UFO/UFO²-derived Windows/Office mechanics remain selective adapter sources, not a second planner/AgentOS.

## Immediate critical path

```text
finish deterministic L2 ephemeral chatgpt-temporary adapter/controller/extension tests and docs
 -> obtain preliminary exact-head hosted CI/security
 -> freeze BASE/HEAD
 -> obtain fresh exact-head ordinary-ChatGPT semantic review
 -> fix/falsify findings and repeat fresh review after any HEAD movement
 -> run final target-Windows/Plus normal + browser-loss physical qualification
 -> run final exact-head hosted checks
 -> re-resolve exact BASE/HEAD and merge #149
 -> refresh parked Prime research from accepted main
 -> exact-source Prime Stage Research and CAP/Prime ownership decision
```

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- ordinary ChatGPT remains the only current general planner;
- observation/model/procedure/page/worker output is evidence/data, not authorization;
- action/message delivery != transition success;
- ambiguous outcome must be reconciled before unsafe retry;
- `UNKNOWN` never authorizes blind continuation;
- transition `PASS` != task `DONE`;
- worker completion != manager task completion;
- environmental content is task data, not policy authority;
- private capabilities must not be disclosed to the worker/model prompt or reconstructed by an unrelated browser context;
- preserve fail-closed behavior over convenience or benchmark hit rate.

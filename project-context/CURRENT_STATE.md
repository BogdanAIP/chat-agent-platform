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

## Accepted bounded Agent Session / Delegation

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

PR #149 is **MERGED**. The bounded worker path has recorded target-Windows
A0/A/B1/B2 acceptance; PR #154 subsequently fixed initial claim ownership and
hidden Stop handling and requalified that scope. `EVIDENCE_INDEX.md` records
exact evidence and the historical #149 review waiver; that waiver does not
change review requirements for later work.

PR #150 is also merged and ships the bounded one-click main updater. Its recorded
physical proof covers installation and a blocked pre-updater-main target across
a tray restart; it does not prove a successful accepted-main update transition.
The #150 final fresh-review result was not found in the inspected PR timeline;
merge metadata alone must not be described as proof that review passed.

PR #155 documents the existing delegation/provider ownership boundary and #156
adds documentation contract guards. They do not implement a general provider
API or a WorkspaceProvider. See `DELEGATION_PROVIDER_CONTRACT.md`.

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

### L2 — accepted `chatgpt-temporary` provider adapter

The first concrete adapter remains accepted as a provider-specific **ephemeral clean-room profile** and as physical evidence for the generic Delegation lifecycle. It is no longer selected as the universal delegated-worker route or as a prerequisite for automatic review. Ordinary CAP tasks stay in the user's ordinary ChatGPT conversation through the canonical six-tool route. `AGENT_SESSION_FRESH_CHAT_REENTRY.md` records the superseding direction for the next provider stage: fresh ordinary ChatGPT with separately qualified read-source/mutation authority.

Accepted bounded path:

```text
generic delegation state stays prepared/open
 -> neutral ChatGPT preflight URL with one preflight nonce only
 -> exact runtime-attested MV3 service worker receives private run/correlation handoff
 -> one live owner record binds owner_tab_id + private run + exact correlation + task URL
 -> controller commit is attempted
 -> success OR ambiguous commit acknowledgement
 -> same live owner reconciles exact committed state through private-token /status
 -> only that neutral preflight tab location.replace() navigates to the task URL
 -> task-bearing Temporary Chat URL carries only the opaque live handle
 -> same live MV3 lifetime resolves handle -> private run capability
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

`AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md` therefore made `fresh_readonly_worker_v1` an **ephemeral one-shot independence profile**, not a persistent Agent Session. The durable IndexedDB delivery claim and same-live-service-worker pre-Send owner witness remain, but provider-conversation restart recovery is disabled. A complete browser/service-worker lifetime loss after a committed task launch never reconstructs Send or monitor authority. If trustworthy result capture was not already completed, the durable delegation remains fail-closed/open rather than fabricating a result or relaunching another worker.

A later fresh semantic review found a pre-first-claim gap: a task bootstrap carrying the private durable `run_id` could be restored from browser session history after complete Chrome loss and recreate first-Send authority before the existing-claim fence applied. Development-side falsification confirmed that P1. `AGENT_SESSION_TEMPORARY_BOOTSTRAP_LIFETIME_REENTRY.md` narrowed the adapter to a neutral preflight plus an opaque task launch handle held against private authority only in live MV3 memory.

A subsequent fresh review found two additional release-critical crash/acknowledgement gaps in that preflight boundary: commit-response ACK loss could delete the sole live mapping after the controller had durably committed, and controller crash after durable `launch-attempted` but before projection/activation could strand the one launch even while the original MV3 owner survived. Development-side falsification confirmed both findings.

`AGENT_SESSION_TEMPORARY_PREFLIGHT_COMMIT_REENTRY.md` and the narrower superseding `AGENT_SESSION_TEMPORARY_PREFLIGHT_OWNER_REBIND_REENTRY.md` are now the latest adapter authority for those gaps. The selected mechanism keeps browser launch ownership entirely inside one MV3 lifetime:

```text
one neutral preflight tab owns navigation
 -> LIVE_LAUNCHES keeps private run + exact correlation + owner_tab_id + current handle/task URL
 -> commit transport failure is UNKNOWN, not rollback
 -> live mapping survives ambiguity
 -> exact private-token /status reconciles a committed launch
 -> owner tab alone receives navigate_url
 -> owner tab location.replace(task URL)
```

If the controller restarts **after** durable launch commit, the surviving owner can reconcile the restarted controller from generic durable launch/delivery/result state plus exact head/prompt/generation and its private run token; the controller does not need to reproduce the old opaque handle. If the controller restarts **before** commit while durable state remains `prepared/open`, a later neutral preflight may refresh the current handle/task URL/preflight capability into the same existing live record only after exact run/delegation/delivery/task/head/prompt correlation. `owner_tab_id` is preserved and the later preflight tab never gains navigation authority. If the original owner tab is gone, ownership is not transferred.

Complete MV3/browser loss remains intentionally fail closed. No durable browser lease, provider-conversation identity or persistent handle registry was introduced.

The earlier fresh review finding that final observation could synthesize an ERROR worker result was also confirmed and fixed: `terminal_result_visible=false` is now only an unresolved observation. It does not create `WORKER_RESULT_V1`, `result.json`, `result_state=recorded` or controller `done`; later genuine capture remains possible while the original context is alive, otherwise controller exit may be nonzero with truthful durable `delivered/open` state.

The physical qualification launcher binds the runtime/extension assets to a clean exact repository HEAD before execution and opens **only the neutral preflight URL** for a genuinely new prepared delegation. It never independently opens the task-bearing URL. The same preflight tab owns the task navigation through `location.replace()` only after exact commit/reconciliation proof. `launch.json` remains evidence/status projection, not physical browser-launch authority. Source provenance is rechecked after terminal result capture.

Persistent rich-context conversation identity, automatic browser wake and cross-restart existing-session delivery remain separate future research. Fresh ordinary-chat **one-shot** delegation is now the selected next provider direction, but implementation is deferred by `AGENT_SESSION_FRESH_CHAT_REENTRY.md` until after Core v1 freeze or a concrete release-critical second consumer. This does not weaken or rewrite the accepted `fresh_readonly_worker_v1` Temporary evidence.

## Automatic reviewer status

The accepted reviewer-specific local state and fixed
`launch_independent_review_v1`, `submit_independent_review_result_v1` and
`reconcile_independent_review_result_v1` procedures from #141/#142 remain intact.

Reviewer methodology, exact repository/PR/BASE/HEAD identity, read-only GitHub
authority qualification, `REVIEW_RESULT_V1`, stale handling and manual fallback
remain specialist policy above generic Delegation.

PR #159 attempted to migrate automatic review through the non-personalized
`chatgpt-temporary` profile. Its target-Windows qualification ultimately proved the
browser lifecycle through one Send, delivered state, cleanup and structured terminal
capture, but the fresh worker returned `ABSTAIN` because the no-plugin profile could
not obtain the exact full repository diff required by the governing review policy.

`AGENT_SESSION_FRESH_CHAT_REENTRY.md` classifies that as a provider-profile design
failure rather than a reason to weaken review evidence. Current direction is:

```text
manual release assurance now
 -> fresh ordinary ChatGPT review
 -> exact repository evidence
 -> reviewer-specific result/fallback state

future automatic worker, only after re-entry
 -> generic Delegation
 -> fresh ordinary ChatGPT session
 -> positively qualified read-only evidence source
 -> reviewer-specific REVIEW_RESULT_V1
```

Automatic reviewer migration is therefore **not a Core v1 freeze prerequisite**.
PR #159 must not merge in its current Temporary-reviewer form. Its useful browser
delivery/capture lessons may be selectively reused later, but the reviewer-specific
branch is not the basis of the next generic provider implementation.

Do not replace the current manual fresh-review path with a regular chat that merely
promises not to write. For automatic review, the actual GitHub/evidence action surface
must be positively read-only; if that cannot be proven, ABSTAIN/manual fallback
remains correct.

## Bounded worker acceptance scope

The historical qualification ladder below describes the worker scope. It is not
an instruction to reopen merged PR #149. Its recorded evidence and review
disposition are indexed in `EVIDENCE_INDEX.md`; future material changes remain
subject to the current `AGENTS.md` policy. The ladder includes:

```text
focused generic state-machine tests
 -> deterministic first-adapter/controller/extension tests
 -> duplicate-tab/process/restart/unknown-delivery adversarial tests
 -> deterministic fault injection for preflight commit ACK loss + controller commit/projection crash
 -> prove non-owner preflight cannot gain navigation authority
 -> preliminary exact-head hosted CI/security and six-tool regressions
 -> freeze exact BASE/HEAD
 -> fresh ordinary-ChatGPT exact-BASE/exact-HEAD semantic review
 -> disposition/fix every surviving finding; fresh review again if HEAD moves
 -> target-Windows/Plus physical qualification on the reviewed exact HEAD
 -> exact source/runtime provenance for the physical claim
 -> normal uninterrupted fresh-worker result capture
 -> complete-Chrome browser-loss fail-closed proof at both pre-first-claim and post-claim boundaries
 -> zero second Send/recovery authority
 -> final exact-head hosted CI
 -> re-resolve BASE/HEAD unchanged before merge
```

The normal physical E2E must be a **non-reviewer** task. A code-review run does not count as proof that the generic lifecycle is truly specialist-independent.

The browser-loss physical case does not require restoration of the Temporary conversation. It proves the opposite safety boundary: after a committed task launch, complete browser-context loss cannot resolve the live launch handle, regain Send/monitor authority, blindly relaunch, or fabricate a result. The pre-first-claim subcase is mandatory because that was the exact interleaving missed by the earlier claim-exists restart gate.

The two preflight commit/restart P1s are covered by deterministic runtime fault injection because their required positive recovery exists only while the original MV3 owner lifetime survives. If a deterministic target-Windows fault can be injected without changing reviewed source, it may be added as evidence; it does not replace the mandatory normal run plus browser-loss B1/B2 gates.

A worker result is evidence/data. It does not grant a capability, self-authorize a consequence, or by itself make the manager's whole user task `DONE`.

## Architecture research rule now in force

Merged #127 requires Stage Research re-entry for materially new persistence/recovery/retry/concurrency/identity/security/authority mechanisms.

The bounded Agent Session design authority chain is:

```text
AGENT_SESSION_DELEGATION_REENTRY.md
 -> AGENT_SESSION_PROFILE_BOUNDARY_REENTRY.md
 -> AGENT_SESSION_PRE_SEND_RESTART_FENCE.md
 -> AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_BOOTSTRAP_LIFETIME_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PREFLIGHT_COMMIT_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PREFLIGHT_OWNER_REBIND_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PROMPT_SOURCE_PROVENANCE_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_LOOPBACK_AUTH_REENTRY.md
 -> AGENT_SESSION_FRESH_CHAT_REENTRY.md
```

The owner-rebind re-entry supersedes only the unnecessary deterministic-handle subproposal from the preceding preflight-commit brief. The later prompt/source-provenance re-entry requires exact worker-visible prompt equality before authority and immediately before Send while binding effectful controller/extension expectations to exact reviewed source. The authenticated-loopback re-entry is the latest adapter authority and requires consequence-relevant extension/controller exchanges to authenticate the intended local controller rather than trusting fixed port ownership. These refinements preserve the generic Delegation model, one-Send guarantees and complete-browser-loss fail-closed profile.

If implementation requires nested/fan-out workers, a new scheduler/event bus, mutating children, environment creation, broad provider authority, automatic parent wake, durable browser identity, provider-conversation recovery, a persistent handle registry, or another materially different durability/concurrency mechanism, stop and re-enter Stage Research rather than widening #149 silently.

## Browser accepted scope and remaining hardening

The previously accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. The `chatgpt-temporary` adapter is a separate headed authenticated-browser qualification path and is not accepted merely because earlier Browser L3 passed.

One existing Browser implementation debt remains: Playwright runtime output ownership must be explicit so runtime artifacts cannot escape into arbitrary caller/source working directories. `TECH_DEBT.md` owns that close condition.

## Future/parallel boundaries

ADR-037 CapabilityRegistry/Event/Policy Hooks remains future/parallel architecture only.

General same-task wake/resume, generic existing-session delivery, a generic scheduler/event bus, worker pools, worker rotation and broad autonomous continuation remain unaccepted future mechanisms.

OpenAdapt remains a selected source for procedure-local compiler/resume/effect-evidence mechanics when revalidated for the concrete consumer. UFO/UFO²-derived Windows/Office mechanics remain selective adapter sources, not a second planner/AgentOS.

## Immediate critical path

`ROADMAP.md` owns the release order. The fresh-chat re-entry removes automatic
reviewer migration from the critical path rather than replacing it with another
provider-adapter project.

Current development work:

1. Return to the already-defined **CAP Core v1 freeze** chain.
2. Use the accepted manual fresh ordinary-ChatGPT review path for exact-head semantic
   review while Core freeze branches are being accepted.
3. Keep PR #159 unmerged/superseded; do not spend more physical cycles making
   non-personalized Temporary Chat satisfy repository-evidence tasks.
4. After Core v1 is frozen, re-enter the fresh ordinary-chat adapter only if a concrete
   consumer justifies it; the first acceptance must include a non-reviewer read-only
   task so review does not define the generic session abstraction.
5. Continue the finite broad real-application coverage gate and later roadmap stages
   in their recorded order.

Do not implement Prime, persistent ChatGPT sessions, shared-memory multi-agent runtime,
WorkspaceProvider, a generic Provider framework, generic permission language, skill
catalogs or bulk external-skill import merely because research branches discuss them.

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
- private capabilities must not be disclosed to the worker/model prompt, persisted in task browser-history URL state, or reconstructed by an unrelated/restarted browser context;
- one live preflight owner may reconcile only its own exact committed launch; ownership is never transferred to a later tab;
- PowerShell/controller projections are not a second task-navigation authority;
- preserve fail-closed behavior over convenience or benchmark hit rate.

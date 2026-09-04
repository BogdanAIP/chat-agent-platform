# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory, selective specialist perception and narrowly bounded worker delegation.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required. A delegated worker is likewise a bounded specialist, not a second project planner.

`ROADMAP.md` owns **release order and stage-level completion conditions**, not active PR mechanics, exact accepted SHAs or machine evidence. Use `CURRENT_STATE.md` for the live boundary/active work and `EVIDENCE_INDEX.md` for accepted physical evidence.

## Accepted public semantic surface

Exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal transport is direct stdio through the Secure MCP Tunnel and official tunnel-client. 1MCP remains optional internal Extension Manager infrastructure.

A new registered procedure may extend `procedure_run` only through bounded reviewed schemas. A genuinely new consequence class requires a truthful public-contract/security/physical-acceptance decision rather than generic dispatch.

## Acceptance-depth rule

```text
L1 — primitive / contract proof
 -> L2 — multi-step workflow integration where useful
 -> L3 — ordinary user-task E2E with independent Finish Gate
```

Release-critical physical acceptance also binds executed/installed source/runtime provenance when that is part of the claim. One L3 pass is scoped evidence, not universal reliability.

## Foundation already completed

Relevant accepted progression:

```text
Stage 24/24.1 typed file/browser foundation                 ACCEPTED
Stage 25/25.1/25.2 Browser + local vision                   ACCEPTED
Stage 26.1A-E / 26.2A-E Windows foundation                 ACCEPTED FOR RECORDED SCOPE
Stage 26.3A canonical six-tool Verified Procedure Runtime  ACCEPTED
Transport Supervisor                                       ACCEPTED
Stage 26.3B Verification Kernel + Finish Gate              ACCEPTED / CLOSED FOR RECORDED SCOPE
CAP-M0 Verification mutation pilot                         ACCEPTED
Stage 26.3C WorkingState / reconciliation / LoopGuard L1   ACCEPTED FOUNDATION
Stage 26.3C consequence-bearing production integration     ACCEPTED / CLOSED FOR DECLARED SCOPE
automatic-review specialist state/procedure foundation     ACCEPTED / MERGED #140-#142
```

Exact PR/physical evidence belongs in `CURRENT_STATE.md` / `EVIDENCE_INDEX.md`, not here.

## Current release-critical sequence

```text
bounded Agent Session / Delegation first slice
 -> automatic reviewer migration as first specialist consumer + reviewer quality baseline
 -> broad real-application physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill / skill lineage
 -> 26.5 Hybrid Computer-Use Integration + selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The current Agent Session item is a **bounded product mechanism**, not broad multi-agent orchestration. Its first accepted scope is exactly one ordinary-ChatGPT manager -> one genuinely fresh read-only worker -> one bounded delegation/delivery -> one correlated durable result **only when that worker result is actually captured and validated**. Timeout/final-observation metadata does not create worker-result authority.

Automatic review remains important developer/release-assurance infrastructure, but its reusable session/delivery lifecycle is no longer the generic product owner. The accepted reviewer-specific #140-#142 state/procedures remain fallback until a later consumer migration proves that reviewer freshness, exact PR/BASE/HEAD identity, least privilege, `REVIEW_RESULT_V1`, stale handling and manual fallback survive unchanged above the generic worker lifecycle.

Broad real-app coverage is an acceptance objective, not a new architecture family.

Nested/fan-out Agent Sessions, same-task automatic manager wake/resampling and Track P local general planner remain future. UFO³ Galaxy remains deferred until multi-device orchestration is an observed bottleneck.

---

# 26.3B — Verification Kernel + independent Finish Gate — ACCEPTED / CLOSED

Recorded representative scope is complete.

Accepted shared contract includes:

```text
ObservationRef / ObservationSnapshot
same-stream capability + subject identity
monotonic fresh re-observation
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN
independent evidence-batch-bound Finish Gate
separate task-success and safety/policy result dimensions
```

Accepted representative production/evidence slices cover Files, Browser and Windows/application paths. The accepted Browser route is headless Playwright/Chrome on target Windows and does not claim visible headed desktop-browser control.

Do not reopen 26.3B merely to add another variant. New completion predicates or physical gates belong to the stage/capability that introduces the new requirement.

---

# 26.3C — WorkingState + recovery/reconciliation + LoopGuard — ACCEPTED / CLOSED

## Foundation — ACCEPTED

The L1 project-owned state-machine foundation is accepted.

WorkingState remains **capability-spanning structured operational state**, not private chain-of-thought and not a vendor procedure/session store.

Accepted foundation covers:

```text
constraints / subgoals / progress
facts + provenance + freshness
evidence refs
stable mutating-operation identity
AttemptIntent / AttemptRecord
verified-applied / not-applied / ack-failed / unknown outcomes
fresh same-stream reconciliation
task / procedure / strategy budgets
LoopGuard
StagnationReport
fail-closed durable history validation
```

The L1 foundation alone did not prove restart-safe delivery on production consequence paths; that gap is now closed for the first declared bounded production consumer below.

## Production integration — ACCEPTED / CLOSED for declared scope

Merged PR #126 integrates the accepted WorkingState/reconciliation/LoopGuard semantics into `verified_workspace_artifact_v1` for the supported local Windows workspace process-restart scope.

Accepted production semantics include:

```text
procedure-local durable checkpoint + prepared intent
stable logical operation identity
bounded budgets + LoopGuard
fresh same-stream reconciliation before unsafe retry
cooperating-runner serialization
generation-bound file identity
Windows file/namespace pinning around consequence windows
three-action stage_create -> final_create -> staging_cleanup graph
fail-closed weak/corrupt/inconsistent retained evidence
public resume correlation only when durable resumable state exists
```

Acceptance required focused deterministic/fault-injection and hard-crash tests, exact-head hosted CI/security, fresh ordinary-ChatGPT independent semantic review and target-Windows physical `procedure_run` qualification. The accepted scope is process crash/restart on the declared local-Windows path; it does not claim machine/power-loss transactional durability or universal application reliability.

## 26.3C completion condition — MET

The project now has an accepted consequence-bearing production consumer using WorkingState/reconciliation/LoopGuard without blind duplicate effects across its declared restart/failure scope, with enough evidence to reuse the same semantics in later capabilities.

Do not reopen 26.3C merely to add another consumer or variant. Material new persistence/recovery/concurrency/identity/authority mechanisms still require fresh Stage Research. The current Agent Session mechanism was therefore re-entered separately in `AGENT_SESSION_DELEGATION_REENTRY.md`; its acceptance does not retroactively broaden the declared 26.3C scope.

---

# Post-26.3C — bounded Agent Session / Delegation — CURRENT

Fresh Stage Research in `AGENT_SESSION_DELEGATION_REENTRY.md` selected **NARROW**.

First topology:

```text
one ordinary-ChatGPT manager
 -> one genuinely fresh read-only worker
 -> one bounded delegation identity
 -> one initial delivery
 -> one correlated generic terminal result when captured
 -> durable local closure only from that captured result
```

Generic lifecycle must provide:

```text
provider-independent deterministic delegation identity
private durable run capability
immutable genesis + crash-safe mutable state
one-shot launch-attempt before physical child launch
stable child/session binding
one provider/browser delivery claim
one project-local delivery claim
prepared | claimed | unknown | delivered
no blind second Send
unknown -> delivered only for the same delivery from fresh evidence
one WORKER_RESULT_V1 when actually captured
COMPLETED | ABSTAIN | ERROR
bounded payload + adapter-computed SHA-256
foreign/corrupt/missing/temp-residue state fails closed
```

The first provider adapter is intentionally concrete: `chatgpt-temporary`. Do not build a large provider framework before a second real consumer/provider proves a shared abstraction is needed.

First-provider constraints:

- positively prove fresh/non-personalized/no-plugin Temporary Chat before Send;
- keep private run capability out of the model prompt/query;
- extension/browser delivery ownership is separate from project-local durable delivery ownership;
- duplicate tabs cannot get a second Send;
- a controller restart may finish the same already-committed pre-Send browser claim only while project delivery is still `prepared` and the same live MV3 witness survives;
- `claimed | unknown | delivered` never regain Send authority;
- complete browser/service-worker lifetime loss never gains monitor/recovery authority for `fresh_readonly_worker_v1`;
- a final observation with no conforming terminal worker block remains non-terminal and cannot synthesize `WORKER_RESULT_V1`;
- running extension bytes must match exact expected source before Send and be revalidated before terminal browser-result capture;
- provider adapter has no project/GitHub/filesystem mutation authority;
- accepted six-tool public surface remains unchanged.

First physical L3 is deliberately **non-reviewer**. It must prove generic delegation rather than code-review semantics:

```text
clean exact source HEAD
 -> exactly one fresh Temporary Chat child
 -> exact running-extension provenance
 -> exactly one task delivery
 -> bounded non-reviewer read-only task
 -> correlated WORKER_RESULT_V1
 -> durable result closure/readback
 -> no unintended second child/message
 -> post-action source/runtime revalidation
```

The accompanying browser-loss gate must prove complete Chrome/context loss cannot recover Send/monitor authority or fabricate closure; truthful unresolved state is acceptable when no genuine result was captured.

Completion condition for this first Agent Session slice: the deterministic L1/L2 contract and target-Windows ordinary-Plus L3 pass on the same reviewed final design, canonical lineage/owners are synchronized, and the required fresh exact-head semantic review reports no unresolved acceptance finding.

This completion does **not** authorize nested/fan-out workers, mutation, worker-created environments, general scheduling, long-lived worker pools or same-task manager wake/resampling.

---

# Automatic reviewer — first specialist consumer after generic Agent Session acceptance

The accepted reviewer-specific local state and fixed `launch_independent_review_v1`, `submit_independent_review_result_v1` and `reconcile_independent_review_result_v1` procedures from #141/#142 remain valid fallback until migration is separately proven.

Fresh reviewer policy remains owned by `AUTOMATIC_REVIEWER_RESEARCH.md` and `.agents/skills/code-review/SKILL.md`.

A migration over the generic Agent Session lifecycle must preserve at minimum:

- genuinely fresh ordinary-ChatGPT review context;
- exact repository / PR / BASE_SHA / HEAD_SHA binding;
- independent reconstruction of repository evidence;
- deterministic reviewer least privilege: GitHub mutation actions unavailable, not merely unselected;
- exact `REVIEW_RESULT_V1` parsing/content rules;
- fail-closed missing/malformed/pending/stale/corrupt/ambiguous result handling;
- atomic manual-fallback closure against late automatic result;
- no blind launch/Send retry;
- no representation of unavailable Codex Review as completed.

Generic `WORKER_RESULT_V1` is lifecycle transport. Reviewer `PASS/FINDINGS/ABSTAIN/STALE`, findings structure, governing BASE policy and review authority remain specialist semantics above it.

There is **no automated GitHub write in reviewer v1**. The selected reviewer result remains project-local; external POST publication is not introduced merely because a generic worker session exists.

After a physically working reviewer consumer exists over the accepted generic lifecycle, run the **Harbor evaluation seam** before treating it as stable replacement infrastructure. Harbor remains evaluation-only. Use ReviewBench as the first small baseline, then bounded SWE-Review-Bench and CR-Bench/CR-Evaluator controls as defined in `AUTOMATIC_REVIEWER_RESEARCH.md`. Keep reviewer semantic-quality metrics separate from CAP lifecycle-reliability metrics, with development/holdout separation.

Functional reviewer completion condition: the required fresh ordinary-ChatGPT review can be launched through the accepted bounded worker lifecycle and its exact-head reviewer result returned/validated without routine user launch/paste/result-copy, while unqualified authority environments and stale/failed/ambiguous runs remain fail-closed and manual fallback remains available.

Stable reviewer-infrastructure completion condition: functional E2E plus recorded Harbor baseline/quality comparison with no material semantic-quality regression accepted merely for automation convenience.

---

# Broad real-application physical coverage gate

Representative L3 gates are vertical proofs. Broaden coverage across multiple task/application classes and environmental variants.

Minimum families should include multiple examples from:

- native Win32 application state/change verification;
- Browser navigation and bounded interaction;
- Electron/application-shell workflows;
- Office-style application/document workflows;
- standard Windows file/dialog interaction;
- mixed structural + selective visual verification paths.

Vary at least:

- DPI/scaling;
- window placement/overlap;
- transient dialogs;
- focus changes;
- unrelated visual noise;
- delayed postconditions;
- unsupported-state fail-closed behavior.

Do not infer universal reliability from one application or one happy-path layout.

---

# OpenAdapt bounded integration spike

Revalidate OpenAdapt against the exact current stage before implementation.

Intended bounded reuse remains:

- `Workflow` / `ProgramGraph` procedure IR;
- demonstration compile / deterministic replay;
- procedure-local checkpoint/resume where the failure model fits;
- effect-verifier evidence through a narrow project adapter.

Do not delegate:

- project WorkingState;
- project capability authority;
- project Verification Kernel / Finish Gate;
- planner authority;
- capability-spanning recovery policy.

The spike completes only if OpenAdapt reduces project-owned complexity without weakening current verification/provenance/recovery semantics.

---

# 26.4 — Human Demonstration -> verified candidate skill

Use accepted capture/procedure IR only after the bounded integration decision above.

Required flow:

```text
human demonstration
 -> structured capture
 -> compile candidate procedure
 -> bounded replay
 -> fresh ExpectedEffect verification
 -> candidate skill lineage
 -> explicit promotion policy
```

Demonstration does not grant trust automatically.

---

# 26.5 — Hybrid Computer-Use Integration + selective Office reuse

Integrate structural/browser/UIA/native/visual paths behind stable project capability contracts. Revalidate selective UFO/UFO² Office/Windows mechanics per app and import only mechanics that remain stronger than project-owned alternatives.

Do not import UFO HostAgent/AppAgent planner hierarchy or Galaxy orchestration as current authority.

---

# 27 — Distribution & Maintenance

Close packaging/update/rollback/operability requirements only after core runtime acceptance is materially broader than the current developer-machine path.

---

# 28 — Clean User E2E / stable release

Require a clean-user installation and ordinary task flow without developer-machine assumptions, while preserving the accepted security/authority/verification boundaries.

Stable release is not declared from hosted CI alone.

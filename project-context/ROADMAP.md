# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general planning layer** while the local platform becomes a deterministic execution system with bounded capabilities, verified state, authorization, recovery, procedural memory and selective specialist perception.

The deterministic Control Plane is not a second planner. It may advance already-selected known transitions under explicit authorization/verification and must escalate when a new strategy is required.

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

Release-critical physical acceptance also binds executed source/runtime provenance when that is part of the claim. One L3 pass is scoped evidence, not universal reliability.

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
```

Exact PR/physical evidence belongs in `CURRENT_STATE.md` / `EVIDENCE_INDEX.md`, not here.

## Current release-critical sequence

```text
bounded automatic independent-review infrastructure
 -> broad real-application physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill / skill lineage
 -> 26.5 Hybrid Computer-Use Integration + selective Office reuse
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The automatic-review item is **developer/release assurance infrastructure**, not a new product capability family or a general autonomous-wake stage. It is placed immediately after accepted 26.3C because fresh ordinary-ChatGPT semantic review is already the required primary merge gate, while Codex Review is optional and quota-dependent. The bounded reviewer path should remove the current manual launch/result-handoff friction before the larger coverage/skill/hybrid work multiplies review cycles.

Broad real-app coverage is an acceptance objective, not a new architecture family.

Parallel Track M Agent Session / Delegation remains future/non-release-critical. Track P local general planner remains optional future research. UFO³ Galaxy remains deferred until multi-device orchestration is an observed bottleneck.

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

Do not reopen 26.3C merely to add another consumer or variant. Material new persistence/recovery/concurrency/identity/authority mechanisms still require fresh Stage Research, and Track M, a generic event bus, broad scheduler authority, a second planner or a new persistence framework remain outside this accepted scope.

---

# Post-26.3C — bounded automatic independent-review infrastructure

Productionize the smallest reliable path that automates the repository's already-required fresh ordinary-ChatGPT semantic review. PR #138's one-shot deep-link/autosend/scheduler work is experimental evidence for this item, not automatic production acceptance.

Fresh Stage Research for this item is owned in `AUTOMATIC_REVIEWER_RESEARCH.md`. Its current decision is **NARROW**: implementation may proceed only for the bounded exact-head reviewer launch/result lifecycle defined there. A material new scheduler, result bus, automatic same-task developer wake, reviewer mutation authority or equivalent new mechanism requires research re-entry rather than silent scope expansion.

Target lifecycle:

```text
review-ready PR / intended exact head
 -> freeze BASE_SHA + HEAD_SHA
 -> bounded automatic launch operation + private run correlation
 -> fresh ordinary-ChatGPT context
 -> repository code-review skill + independent GitHub evidence
 -> REVIEW_RESULT_V1
 -> one bounded result-evidence handoff
 -> development-side result + live-identity revalidation
 -> stale/duplicate/malformed/ambiguous result rejection
```

The implementation must preserve the existing review contract rather than weakening it for automation. At minimum preserve:

- a genuinely fresh ordinary-ChatGPT review context;
- exact repository / PR / BASE_SHA / HEAD_SHA binding;
- independent reconstruction of evidence from the repository;
- reviewer read-only authority over production code/branch/configuration, with only the bounded result-publication seam selected by the research contract;
- fail-closed handling of missing, malformed, stale, edited, wrong-author, duplicated or otherwise ambiguous review results;
- no blind automatic relaunch after ambiguous dispatch/Send;
- no representation of unavailable Codex Review as completed.

Codex Review remains useful optional independent evidence when quota is available. It is not the primary required reviewer and quota exhaustion must not stop the release process when the required ChatGPT review and all other gates pass.

Keep the first production consumer narrow: automatic code review. Do not silently generalize the mechanism into recurring arbitrary task execution, worker rotation, a generic scheduler/event bus or broad same-task autonomous continuation.

Instrument review launches so development naturally accumulates a bounded acceptance corpus for later continuation research. Useful non-secret evidence includes correlation/run identity, trigger reason, exact refs, launch/delivery result, fresh-context proof where available, result disposition, stale detection, duplicate/missed delivery, timeout/failure class and manual-intervention requirement.

After the first physically working automatic-review E2E, add the **Harbor evaluation seam** before treating the automatic reviewer as stable replacement infrastructure. Harbor remains evaluation-only, not production runtime/authority. Use ReviewBench as the first small baseline, then bounded SWE-Review-Bench and CR-Bench/CR-Evaluator controls as defined in `AUTOMATIC_REVIEWER_RESEARCH.md`. Keep reviewer semantic quality metrics separate from CAP lifecycle reliability metrics, and preserve development/holdout separation so benchmark tuning does not masquerade as independent evidence.

The first benchmark run establishes a baseline rather than an invented fixed threshold. A later acceptance target must be evidence-based relative to the current/manual fresh reviewer and available comparison reviewers. Removing UI friction is not sufficient if semantic review quality materially regresses.

Functional E2E completion condition: the required fresh ordinary-ChatGPT review can be launched and its exact-head `REVIEW_RESULT_V1` can be returned/validated through the normal development lifecycle without a routine user launch/paste/result-copy step, while stale/duplicate/failed/ambiguous runs remain fail-closed.

Stable-infrastructure completion condition: the functional E2E condition is met **and** the Harbor-backed baseline/quality comparison has been recorded with semantic-quality and lifecycle-reliability evidence kept separate, with no material semantic-quality regression accepted merely for automation convenience.

---

# Broad real-application physical coverage gate

Representative L3 gates are vertical proofs. Broaden coverage across multiple task/application classes and environmental variants.

Minimum families should include multiple examples from:

- native Windows/Win32;
- Browser;
- Electron;
- office-style applications;
- standard file/dialog flows.

Variants should include DPI, moved/resized windows, focus changes, similar windows/records, unexpected dialogs/overlays/noise and reviewed structure-to-vision fallback where applicable.

Define a finite acceptance matrix before expanding this gate so it cannot become open-ended application testing. Success means a materially broader characterized accepted scope, not universal Windows accuracy.

---

# Pre-26.4 — bounded OpenAdapt integration spike

After the project-owned 26.3C production state/recovery shape is accepted, revalidate selected OpenAdapt roles through `ARCHITECTURE_REUSE_BASELINE.md` and fresh Stage Research rather than assuming prior selection is sufficient.

Target bounded spike:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> upstream effect evidence
 -> project evidence adapter
 -> project ObservationSnapshot / ExpectedEffect
 -> PROJECT Verification Kernel
 -> PROJECT independent Finish Gate
```

No upstream verdict becomes unconditional project `PASS`/`DONE`. No raw workflow catalog, generic desktop executor, shell/Python authority or second planner is introduced merely for the spike.

Before implementation, define a bounded exit decision such as `ADOPT`, `ADAPT` or `REJECT` for each evaluated role. If upstream mechanics do not fit the exact current failure/authority model, keep them qualified but outside the production path rather than extending the spike indefinitely.

---

# 26.4 — Human Demo -> verified candidate skill / lineage

Before broad candidate-skill accumulation, freeze the minimum stable contract for subtask goal, completion criteria, applicability/preconditions, evidence references and candidate lineage so 26.5 does not require avoidable migration of accumulated skills.

Compile demonstrations into:

```text
subtask goals
verifiable completion criteria
applicability / preconditions
advisory target/action evidence
versioned candidate lineage
```

Live state outranks demonstration history. Blind coordinate/action replay is not accepted. One demonstration creates at most a CANDIDATE; promotion requires independent replay/regression/variant evidence.

Prefer mature selected capture/compile/ProgramGraph/replay/checkpoint/certification mechanics when fresh evidence confirms fit rather than rebuilding them locally.

Project trust still requires project verification and Finish Gate evidence.

---

# 26.5 — Hybrid Computer-Use Integration

Converge accepted Browser/Windows/application mechanisms on common cross-capability semantics without flattening rich native state:

```text
capability-native observation identity
semantic/native vs reviewed GUI routing
grounding identity/confidence/ambiguity evidence
selective visual fallback
fresh visual post-action verification for visual/spatial predicates
cross-app provenance
WorkingState/reconciliation/recovery
independent completion
```

A required visual/spatial postcondition must not be declared `PASS` from DOM/accessibility/UIA/native state alone when those channels cannot prove the rendered result. In those cases, verification requires fresh screenshot/ROI evidence bound to the post-action observation. Visual contradiction produces `FAIL` when conclusive; required but stale/unavailable/ambiguous visual evidence produces `UNKNOWN`. This does **not** require a screenshot after every action and does not make pixels an authority source.

Representative visually significant failures include clipping outside the viewport/window, occlusion by overlays/dialogs, invalid overlap, off-screen placement, task-relevant rendered size/alignment and other rendered-state predicates that structural state cannot establish.

For Office/Windows breadth, evaluate focused UFO/UFO²-derived UIA/Win32/WinCOM/application mechanics one application at a time behind project-owned capability, identity, observation, ExpectedEffect and verification boundaries.

Do not adopt UFO HostAgent/AppAgent planner hierarchy or UFO³ Galaxy as the current production planning layer.

Trusted-site full-browser/JS/CDP authority may be promoted only after its Site Capability/network/security boundary is implemented, reviewed and physically accepted.

Before 26.5 acceptance, rerun a representative regression subset of the earlier broad real-application physical matrix because hybrid routing/cross-capability changes can invalidate assumptions established before integration.

---

# Future research seam — same-task continuation / wake

This is **not a new roadmap stage, not current architecture acceptance and not part of 26.3C implementation**.

The bounded automatic reviewer is an intentional first real consumer of some adjacent launch/correlation mechanics and should accumulate evidence useful here, but reviewer automation does **not** by itself authorize general continuation of unfinished user tasks.

Now that consequence-bearing 26.3C restart/reconciliation behavior is accepted for its declared scope, wait until enough bounded reviewer evidence exists to sharpen the question, then run separate Stage Research before adding any mechanism that can automatically continue the **same unfinished task** without a new user message.

Keep the semantic distinction explicit:

```text
ScheduledTask
  schedule triggers a new TaskRun / AgentSession

same-task continuation
  existing task remains unfinished
  -> WAITING
  -> future wake/readiness condition
  -> fresh observation + current authority/grant revalidation
  -> planner continuation
```

The future research question may examine concepts such as:

```text
continuation state = WAITING | READY | BLOCKED | COMPLETE
reason_for_wait
desired_outcome / stopping_condition
last_observation_ref
wake_condition and/or next_check_at
user_attention_required
current scope/grant references
```

Do **not** preselect `TypedEventBus`, `ScheduledTask`, a new scheduler service or any other substrate merely because those future seams are adjacent. Stage Research must compare existing architecture/reuse lineage and current platform/harness capabilities before choosing the mechanism.

At minimum, research must cover wait/sleep/wake semantics, duplicate wake, cancellation/replacement, missed wake, crash during wake, concurrent resume, grant expiry/authority after sleep, backoff/timed checks and what happens when the ordinary-ChatGPT harness cannot actually resample the planner without a new user turn.

A local runtime being able to mark a task `READY` is not proof that the product can autonomously obtain another planner turn. Treat planner resampling/proactive delivery as a separate harness/product capability boundary.

---

# Future research seam — Physical Device / IoT Capability Family

This is **not a new release-critical stage, not an accepted production backend and not part of Stage 26.3C**. It does not change the current release-critical sequence.

A future Physical Device / IoT family may reuse the existing project consequence model across smart-home, generic IoT and later laboratory/device adapters:

```text
identify
 -> observe
 -> authorize
 -> act
 -> fresh re-observe
 -> verify
 -> reconcile/recover
```

`project-context/IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md` records the current research direction:

- Home Assistant is the **preferred first backend candidate for future re-entry**, not an accepted dependency;
- Home Assistant may normalize state/events/actions across Matter, MQTT and other vendor/protocol integrations while project Control Plane, WorkingState, Verification Kernel and Finish Gate remain authoritative;
- HA service/action completion is delivery/execution evidence, not project `PASS`; fresh post-action observation is required for the declared ExpectedEffect;
- a human-facing `entity_id` must not be the only durable project subject identity;
- direct Matter, direct MQTT and vendor-specific adapters are considered only for a **measured gap** in the aggregator path, not built in parallel by default;
- generic raw `call_service(anything)` is not the intended Chat-facing semantic authority;
- higher-consequence actuators require stronger scope/freshness/preconditions, and hazardous equipment requires independent/device/process safety interlocks below LLM authority;
- MHS is a reference-only future laboratory/hardware standard until its public specification/implementation can be independently revalidated.

Before production adoption, re-run Stage Research on the then-current concrete device/user scope, backend versions, identity/security/recovery semantics and any new idempotency/resource-lock/interlock mechanism. A lamp proof cannot authorize locks, water, boilers, gas or laboratory equipment.

The same research also records a separate future **experience -> validated deterministic procedure** seam:

```text
adaptive attempts
 -> verified successful traces
 -> candidate procedure
 -> independent validation
 -> bounded deterministic procedure
 -> versioned procedure / skill lineage
```

Successful traces are evidence, not automatic self-modification. Promotion requires independent replay/regression/variant evidence; timing-sensitive or safety-critical inner loops should move to a qualified deterministic runtime rather than query an LLM on every control step.

---

# Local Execution Kernel — adjacent future consequence class

Arbitrary Python/program execution may be useful later, but it is not Browser authority and must not be hidden in `web_interact` or generic `procedure_run` dispatch.

It requires a separate grant/security/public-contract/physical-acceptance decision.

Generated code remains proposal data; deterministic Control Plane policy remains authoritative.

---

# 27 — Distribution & Maintenance

After core reliability and broad physical scope are credible:

- simplify install/update/repair/uninstall paths;
- remove developer-machine assumptions;
- make dependency/runtime ownership explicit;
- close/reassess release-relevant `TECH_DEBT.md`;
- preserve fail-closed security boundaries.

Run an earlier non-blocking clean/isolated packaging smoke once the post-26.3C runtime is stable enough to expose hidden developer-machine assumptions. Fundamental packaging blockers discovered there must be fixed before they contaminate later stages, but full installer/update/repair/uninstall work remains Stage 27.

Current implementation remains primarily Python + Node/MJS + PowerShell/Windows glue. Rust is not a release prerequisite.

---

# 28 — Clean User E2E / stable release

Target:

```text
clean supported Windows machine/account
 -> install
 -> connect/authenticate
 -> approve required capability scope
 -> normal semantic route ready
 -> representative user task succeeds with verification
 -> restart/recovery/update behavior remains understandable
```

Stable release requires accepted core behavior, clean install evidence, current documentation and no known P0/P1 debt required for shipped authority.

---

# Parallel Track M — Agent Sessions / Delegation

Track M is a future work-distribution capability below the ordinary-ChatGPT manager and deterministic Control Plane boundary. It must not displace release-critical Stage 26 prerequisites.

Keep separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Canonical progression remains:

```text
M0 object model + fixture contracts
 -> M1 read-only Session Observer
 -> M2 Manager -> one EXISTING Worker with verified delivery/correlation
 -> M3 WorkingState/HandoffPack + recovery/event monitoring
 -> M4 bounded session lifecycle + operation idempotency/reconciliation
 -> M5 manager-created Worker + ownership/WorkerLease/cleanup
 -> M6 multiple workers + bounded fan-out, default max_spawn_depth=1
 -> M7 separate Project / ExecutionEnvironment lifecycle
 -> M8 broader cross-harness/provider adoption
```

Track M may reuse accepted WorkingState/logical-operation/reconciliation/LoopGuard semantics later; it does not justify broadening 26.3C solely for future orchestration.

---

# Parallel Track P — optional future local planner

A future local general planner is not banned, but it is not release-critical now.

Research order remains:

```text
shadow/proposal-only
 -> measured bounded subtask role
 -> optional local general planner only after parity/safety/resource evidence
```

It always remains above the same deterministic authorization, Verification Kernel and Finish Gate boundaries.
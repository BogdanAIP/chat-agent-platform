# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register**. Other current documents may link to these risks but must not maintain competing rankings/scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when current code, CI, physical evidence or product constraints materially change the risk. Resolve live `main` and relevant open PRs first.

## Current execution boundary

Stage 26.3B is accepted/closed for its recorded representative scope.

Stage 26.3C is **accepted/closed for its declared production process-restart/local-Windows scope through #126**. The accepted first consequence-bearing production consumer is `verified_workspace_artifact_v1`; broader cross-capability continuation/recovery remains unproven and stays represented in risk #2.

The current release-critical prerequisite is the bounded **Agent Session / Delegation** mechanism selected by fresh Stage Research in `AGENT_SESSION_DELEGATION_REENTRY.md` and implemented as a Draft candidate in PR #149. It intentionally promotes one manager -> one fresh read-only worker -> one delivery -> one correlated durable result before reviewer-specific automation is generalized further.

PR #149 is not accepted merely because its L1/L2 deterministic tests and hosted checks pass. Its target-Windows ordinary-Plus non-reviewer physical L3, canonical owner synchronization and mandatory exact-head semantic review are still required.

Exact accepted physical heads/result locations live in `EVIDENCE_INDEX.md`.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open; representative Browser + Windows L3 verticals accepted | After the bounded Agent Session / Delegation prerequisite, run a deliberate cross-app physical matrix across native Win32, Browser, Electron, office-style apps and standard file/dialog flows with DPI/focus/dialog/noise variants. Close only when accepted scope is materially broader and failures are characterized. |
| 2 | Long-horizon verified continuation/recovery is not yet production-complete across capabilities | **8/10** | Open; L1 WorkingState/LoopGuard foundation accepted #124 and first consequence-bearing production consumer physically accepted #126; PR #149 adds a bounded one-worker delegation candidate but not general continuation | Reuse the accepted state/reconciliation/LoopGuard model in later real consequence paths, preserving bounded crash/restart and ambiguous-outcome handling without blind redelivery. Do not treat one manager->worker delegation as same-task automatic planner continuation. Close when relevant long tasks across the supported capability set can survive failed/ambiguous steps and still reach independently verified completion without duplicate effects. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do not build a second planner merely to reduce this score. A delegated fresh worker is a bounded specialist whose result is data, not another general project planner. Any future second planner begins shadow/proposal-only above the same deterministic Control Plane. |
| 4 | Architecture/process/documentation complexity can grow faster than user-visible capability | **7/10** | Open; repeated live-doc drift was found during #128/#139 and PR #149 required explicit re-entry to stop reviewer-specific lifecycle mechanics becoming the generic agent runtime | Keep owners narrow (`CURRENT_STATE`, `ROADMAP`, `PROJECT_RISKS`, `EVIDENCE_INDEX`, reuse baseline), remove duplicated stage snapshots, make Stage Research compare prior reuse lineage, and convert defect classes into executable tests/review checks. Close when status/ownership drift is routinely caught before merge and current work no longer requires reconstructing overlapping prose. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep packaging behind core reliability/coverage. Close with clean-machine install/connect/permissions/ready/update/rollback evidence and Stage 28 clean-user E2E without developer-machine assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open; PR #149 keeps its first worker adapter deliberately narrow and loopback-only | Close Site Capability/network debt before trusted-site JS/CDP/full-browser authority; add environmental-injection coverage, authenticated-session credential isolation, sensitive capture policy and representative L3 evidence before widening authority. Agent-session browser adaptation must remain bounded and may not become generic browser mutation authority. |
| 7 | Runtime/process state ownership still has small hardening gaps | **5/10** | Open; #118 fail-closed qualification exposed runtime-CWD output ownership | Make Browser/Playwright runtime output directories explicit under project-owned state/log roots and keep process-generation/cleanup tests. Close when runtime artifacts cannot escape into arbitrary caller/source CWD and ownership regressions fail deterministically. |

## Why the risk picture changed

Representative Browser/Windows L3 evidence reduced uncertainty that accepted primitives can compose into useful real work, but it did not close broad-coverage risk #1.

PR #124 reduced the design risk around WorkingState/LoopGuard by accepting the L1 state-machine foundation. PR #126 then accepted the first consequence-bearing production integration for the declared local-Windows process-restart scope, including reconciliation/no-blind-redelivery physical evidence. That materially reduces the earlier 26.3C production-integration gap, but it does **not** close risk #2 because broader cross-capability continuation/recovery remains unproven.

Automatic-review research/implementation in #140-#142 proved useful specialist local-state/procedure boundaries, but subsequent research showed that reviewer-specific launch/session/result lifecycle should not become the generic worker architecture. PR #149 therefore re-entered Stage Research and selected the narrower generic Agent Session / Delegation seam while preserving accepted reviewer-specific procedures until migration is separately proven safe.

The PR #149 candidate reduces design uncertainty around one fresh read-only second worker: deterministic delegation identity, durable launch/delivery/result state, no-blind-relaunch/no-blind-re-Send semantics, provider-specific Temporary Chat adaptation and exact runtime/source provenance checks are now covered by deterministic tests and hosted CI. Its latest Temporary profile re-entry also requires unresolved timeout/final-observation states to remain open rather than being promoted into synthetic worker results. This does **not** reduce the risk register as if L3 were accepted; the final target-Windows generic worker physical proof is still pending.

PR #118 also demonstrated that provenance/Finish Gate mechanisms are live: invalid physical attempts were rejected for real harness/runtime defects before a final accepted run succeeded. Those defect classes belong in deterministic assurance, not in a waiver list.

## L1/L2/L3 interpretation

```text
L1 primitive / contract proof
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final-state/history proof
```

Passing L1/L2 is necessary but insufficient for risks #1/#2. Physical release evidence additionally needs source/runtime provenance where the claim depends on exact executed or installed bytes.

One accepted production consumer, one delegated-worker task or one L3 vertical is scoped evidence, not universal reliability.

## Architecture/process risk rule

Future architecture documents do not automatically reduce risk. A future ADR or selected upstream component is a hypothesis/boundary input until the relevant Stage Research and acceptance evidence prove the concrete mechanism.

When `stage-research` applies, `ARCHITECTURE_REUSE_BASELINE.md` must be used so new work explicitly checks whether it is duplicating/replacing an already selected mechanism or crossing a deliberately project-owned boundary.

Provider/browser adaptation is below generic Agent Session identity/state. A provider adapter proving one fresh Temporary Chat does not authorize a provider-specific planner hierarchy, generic browser database, scheduler/event bus, nested workers or arbitrary worker mutation.

## Repository metadata / branch hygiene

Repository metadata may still describe the project as `Rust-first` although current runtime is primarily Python + Node/MJS + PowerShell/Windows glue. This is technical-debt metadata, not a reason to rewrite working code.

Historical branch refs may also look graph-ahead after squash merge or intentional supersession. Classify branches by associated PR/content before deletion; ahead/behind counts alone do not prove unfinished work. `TECH_DEBT.md` owns these close conditions.

## What is not currently a core problem

These remain deliberate strengths unless evidence changes:

- small project-owned public semantic surface;
- semantic/native structure before pixels where reliable;
- selective visual fallback;
- shared Verification Kernel;
- independent Finish Gate;
- explicit `PASS | FAIL | UNKNOWN` and fail-closed continuation;
- project-owned WorkingState/LoopGuard semantics with an accepted first production consumer;
- provider-independent delegation identity/state with a narrow first provider adapter candidate;
- L1 deterministic tests as diagnostic foundation;
- L3 natural-language tasks with external evidence as realistic vertical proof;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked actionable risk without skipping prerequisites. `ROADMAP.md` owns exact order.

Current immediate sequence:

```text
physically accept bounded Agent Session / Delegation
 -> migrate automatic reviewer as the first specialist consumer only if generic semantics preserve reviewer guarantees
 -> broad real-app physical coverage gate
 -> reuse accepted WorkingState/reconciliation semantics across later consequence-bearing capabilities as those stages require
```

The Agent Session item is a bounded product mechanism, not a general multi-agent platform: exactly one manager, one fresh read-only worker, one delivery and one durable result in the first accepted scope.

The existing automatic-review procedures remain release-assurance fallback until a generic consumer migration is separately accepted. Reviewer semantics do not become generic lifecycle semantics, and delegated workers do not acquire GitHub mutation authority merely because reviewer automation later consumes the mechanism.

The small Browser runtime-output ownership hardening may land alongside the relevant runtime touch because it protects the qualification/runtime substrate already in use.

Nested/fan-out agent orchestration, same-task automatic wake/resampling and Track P local-planner work remain future and must not displace the release-critical path solely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. identify the code/CI/physical/product evidence that changed it;
2. update score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. keep exact accepted heads/result paths in `EVIDENCE_INDEX.md`;
5. do not copy this ranking into README, Roadmap, continuation notes or Stage records.

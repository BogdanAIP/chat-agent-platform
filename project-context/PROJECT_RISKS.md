# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register**. Other current documents may link to these risks but must not maintain competing rankings/scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when current code, CI, physical evidence or product constraints materially change the risk. Resolve live `main` and relevant open PRs first.

## Current execution boundary

Stage 26.3B is accepted/closed for its recorded representative scope.

Stage 26.3C WorkingState/LoopGuard **L1 foundation is accepted through #124**. The active release-critical reliability gap is production integration/restart reconciliation on consequence-bearing paths; concrete active PR/design status belongs in `CURRENT_STATE.md`.

Exact accepted physical heads/result locations live in `EVIDENCE_INDEX.md`.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open; representative Browser + Windows L3 verticals accepted | After the current 26.3C reliability integration, run a deliberate cross-app physical matrix across native Win32, Browser, Electron, office-style apps and standard file/dialog flows with DPI/focus/dialog/noise variants. Close only when accepted scope is materially broader and failures are characterized. |
| 2 | Long-horizon verified continuation/recovery is not yet production-complete across capabilities | **8/10** | Open; L1 WorkingState/LoopGuard foundation accepted #124, production integration remains active work | Integrate the accepted state/reconciliation/LoopGuard model into real consequence paths, prove crash/restart and ambiguous-outcome handling without blind redelivery, then expand cross-capability. Close when long tasks can survive failed/ambiguous steps and still reach independently verified completion without duplicate effects. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do not build a second planner merely to reduce this score. After WorkingState production semantics stabilize, define the smallest planner-neutral proposal/escalation contract; any future second planner begins shadow/proposal-only above the same deterministic Control Plane. |
| 4 | Architecture/process/documentation complexity can grow faster than user-visible capability | **7/10** | Open; repeated live-doc drift was found during the #128 documentation coherence sweep | Keep owners narrow (`CURRENT_STATE`, `ROADMAP`, `PROJECT_RISKS`, `EVIDENCE_INDEX`, reuse baseline), remove duplicated stage snapshots, make Stage Research compare prior reuse lineage, and convert defect classes into executable tests. Close when status/ownership drift is routinely caught by CI/review and current work no longer requires reconstructing overlapping prose. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep packaging behind core reliability/coverage. Close with clean-machine install/connect/permissions/ready/update/rollback evidence and Stage 28 clean-user E2E without developer-machine assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Close Site Capability/network debt before trusted-site JS/CDP/full-browser authority; add environmental-injection coverage, authenticated-session credential isolation, sensitive capture policy and representative L3 evidence before widening authority. |
| 7 | Runtime/process state ownership still has small hardening gaps | **5/10** | Open; #118 fail-closed qualification exposed runtime-CWD output ownership | Make Browser/Playwright runtime output directories explicit under project-owned state/log roots and keep process-generation/cleanup tests. Close when runtime artifacts cannot escape into arbitrary caller/source CWD and ownership regressions fail deterministically. |

## Why the risk picture changed

Representative Browser/Windows L3 evidence reduced uncertainty that accepted primitives can compose into useful real work, but it did not close broad-coverage risk #1.

PR #124 reduced the design risk around WorkingState/LoopGuard by accepting the L1 state-machine foundation. It did **not** close risk #2 because production consequence paths still need integration, crash/restart reconciliation and physical proof.

PR #118 also demonstrated that provenance/Finish Gate mechanisms are live: invalid physical attempts were rejected for real harness/runtime defects before a final accepted run succeeded. Those defect classes belong in deterministic assurance, not in a waiver list.

## L1/L2/L3 interpretation

```text
L1 primitive / contract proof
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final-state/history proof
```

Passing L1 is necessary but insufficient for risks #1/#2. Physical release evidence additionally needs source/runtime provenance where the claim depends on exact executed bytes.

One L3 vertical is scoped evidence, not universal reliability.

## Architecture/process risk rule

Future architecture documents do not automatically reduce risk. A future ADR or selected upstream component is a hypothesis/boundary input until the relevant Stage Research and acceptance evidence prove the concrete mechanism.

When `stage-research` applies, `ARCHITECTURE_REUSE_BASELINE.md` must be used so new work explicitly checks whether it is duplicating/replacing an already selected mechanism or crossing a deliberately project-owned boundary.

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
- project-owned WorkingState/LoopGuard foundation;
- L1 deterministic tests as diagnostic foundation;
- L3 natural-language tasks with external evidence as realistic vertical proof;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked actionable risk without skipping prerequisites. `ROADMAP.md` owns exact order.

Current immediate sequence:

```text
finish Stage 26.3C production WorkingState/restart-reconciliation integration
 -> broad real-app physical coverage gate
```

The small Browser runtime-output ownership hardening may land alongside the relevant runtime touch because it protects the qualification/runtime substrate already in use.

Track M multi-chat and Track P local-planner work remain future/parallel and must not displace the release-critical path solely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. identify the code/CI/physical/product evidence that changed it;
2. update score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. keep exact accepted heads/result paths in `EVIDENCE_INDEX.md`;
5. do not copy this ranking into README, Roadmap, continuation notes or Stage records.

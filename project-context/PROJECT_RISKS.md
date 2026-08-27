# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register** for the current project. Other current documents may link to these risks but should not copy the full ranking or maintain competing scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when new code, CI, physical evidence or product constraints materially change the risk. Always resolve live `main` and open PRs before acting.

## Current execution stop

Stage 26.3B is accepted for the recorded representative scope. Browser and Windows representative L3 paths now have independent final-state/history evidence, and the Browser path has been repeated under the stronger source/install/full-dependency provenance methodology.

The current release-critical runtime target is Stage 26.3C: WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport. Exact accepted heads and physical result locations live in `EVIDENCE_INDEX.md`.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open; representative Browser + Windows L3 verticals accepted | After 26.3C, run a deliberate cross-app physical matrix covering native Win32, Browser, Electron, office-style apps and standard file/dialog flows across DPI/focus/dialog/noise variants. Close only when accepted scope is materially broader and failures are characterized. |
| 2 | Long-horizon verified continuation/recovery is not yet complete across capabilities | **8/10** | Open; now the active Stage 26.3C target | Implement project-owned WorkingState, typed failure/outcome classes, reconciliation, distinct budgets, LoopGuard and StagnationReport with deterministic adversarial tests. Close when a long task can survive ambiguous/failed steps without blind redelivery and still reach independently verified completion. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do not build a second planner now. After WorkingState v1 stabilizes, define a narrow planner-neutral proposal/escalation contract; a future second planner first runs shadow/proposal-only above the same deterministic Control Plane. |
| 4 | Architecture/process/documentation complexity can grow faster than user-visible capability | **7/10** | Open; current docs drift confirmed after #118 | Keep live context small, keep exact evidence in `EVIDENCE_INDEX.md`, convert discovered defect classes into permanent tests, and require capability work to progress toward representative L3 rather than accumulating architecture-only layers. Close when status drift and duplicated invariants are routinely caught by CI/review. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep release packaging behind core reliability work. Close with clean-machine install/connect/permissions/ready/update/rollback evidence and Stage 28 clean-user E2E without developer-machine assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Close Browser network/Site Capability debt before trusted-site JS/CDP/full-browser authority; add environmental-injection coverage, authenticated-session credential isolation, sensitive capture/demo policy and representative L3 evidence before widening authority. |
| 7 | Runtime/process state ownership still has small hardening gaps | **5/10** | Open; fail-closed qualification caught one CWD-output issue | Make Browser/Playwright runtime output directories explicit under project-owned state/log roots, strengthen remaining local endpoint/session ownership where needed, and keep exact process-generation/cleanup tests. Close when runtime artifacts cannot escape into arbitrary caller/source CWD and ownership regressions fail deterministically. |

## Why 26.3B evidence changed the risk picture

Representative Browser and Windows L3 proofs reduce uncertainty that the existing primitives can compose into useful work, but they do not close broad-coverage risk #1.

More importantly, #118 demonstrated that independent verification/provenance gates are live: several invalid physical attempts were rejected for harness/runtime defects before a final accepted run succeeded. That is positive assurance behavior, not evidence that the defects should be ignored. Their classes are now represented in `MUTATION_ASSURANCE.md` for deterministic regression/adversarial expansion.

The accepted Browser route is headless Playwright/Chrome on target Windows. It proves the semantic Browser consequence path, not visible headed desktop-browser control.

## L1/L2/L3 risk interpretation

Passing primitive tests remains necessary but insufficient for risks #1, #2 or #4.

```text
L1 primitive / contract proof
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final-state/history proof
```

Physical release evidence also needs source provenance when applicable. One L3 vertical remains scoped evidence, not a universal reliability claim.

## Browser Harness / ADR-036 risk interpretation

ADR-036 remains architecture direction, not evidence that wider Browser authority is already safe or useful.

Trusted-site JS/CDP/full-browser authority cannot be accepted until the Site Capability / Browser Network Gate boundary is implemented and physically verified.

```text
verification correctness now
 != automatic authority expansion

future trusted-site authority
 -> lower-level network/site policy
 -> security/physical acceptance
 -> representative L3 evidence
```

`trust destination != trust instructions` remains binding even for allowlisted sites.

## Messaging / repository hygiene issue

GitHub repository metadata may still describe the project as `Rust-first` although the current runtime is primarily Python + Node/MJS + PowerShell/Windows glue. Change repository metadata when settings write access is available; do not rewrite working code merely to satisfy stale metadata. This remains technical debt.

The repository also retains many historical branch refs. Two maintenance branches still contain graph-unique old commits, but their content is substantially stale/superseded. Port only still-valid ideas through fresh reviewed PRs before deleting those refs; do not merge old branches wholesale merely because they are ahead of an old merge base.

## What is not currently considered a core problem

The following remain deliberate strengths unless evidence changes:

- small project-owned public semantic surface;
- semantic/native structure before pixels when reliable;
- selective visual fallback rather than screenshot-only control;
- shared Verification Kernel;
- independent Finish Gate;
- explicit `PASS | FAIL | UNKNOWN` and fail-closed continuation;
- L1 deterministic tests as diagnostic foundation;
- L3 natural-language tasks with external evidence as realistic vertical proof;
- UIA as one bounded Windows mechanism;
- Python as a current implementation language;
- PowerShell as Windows lifecycle/bootstrap glue;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked actionable risk **without skipping an unfinished prerequisite**. `ROADMAP.md` owns detailed stage order.

Current immediate sequence:

```text
Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage gate
```

A small Browser runtime-output ownership hardening and deterministic adversarial regressions for Stage 26.3B findings should land before or alongside the first 26.3C runtime slice because they directly protect the qualification/runtime substrate being reused.

Track M multi-chat and Track P local-planner work remain future/parallel and must not displace the release-critical path merely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. cite the code/CI/physical/product evidence that changed it;
2. update score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. keep exact accepted heads/result paths in `EVIDENCE_INDEX.md`;
5. do not copy the entire table into README, Roadmap, continuation notes or stage contracts.

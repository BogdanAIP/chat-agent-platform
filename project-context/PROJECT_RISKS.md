# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register** for the current project. Other current documents may link to these risks but should not copy the full ranking or maintain competing scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when new code, CI, physical evidence or product constraints materially change the risk.

Current snapshot basis: 2026-08-26. Always resolve live `main` and active PR heads before acting.

## Current execution stop

At this snapshot:

- live `main` is `82802dc619b0410b34859ed9ee362442b1f202f9`, the squash-merge of PR #110 (Browser Harness/ADR-036 architecture and technical-debt synchronization);
- PR #107 remains physically accepted Browser navigation evidence;
- active release-critical Browser PR is draft #111, `Stage 26.3B: verify Browser interaction postconditions`;
- #111 final hosted CI is 10/10 PASS on exact head `1521e3128a7694be43518c3ee0188cb79f0ca0f5`; ordinary-Chat target-Windows physical interaction acceptance remains required;
- stacked draft PR #112 adds the first Browser L3 real-task harness without changing #111's exact head.

After #111 is physically accepted/merged, #112 must be replayed on accepted `main` and pass its own hosted + ordinary-Chat physical L3 evidence before the release-critical line moves on to Windows/application/process verification.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open | Add representative L3 tasks as each major capability path becomes usable, then after 26.3C run a deliberate cross-app physical acceptance matrix covering native Win32, browser, Electron and office-style apps plus DPI/focus/dialog/noise variants. Close only when failures are characterized and accepted scope is materially broader than isolated examples. |
| 2 | The verified long-horizon control loop is not yet complete across capabilities | **8/10** | Open, actively reducing | Finish 26.3B Browser + Windows verification adapters and representative L3 tasks, then 26.3C WorkingState + typed recovery + LoopGuard. Close when one long task crosses relevant capabilities with fresh verification, bounded recovery and independently verified completion. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do **not** build a second planner now. After WorkingState v1 stabilizes, define a narrow planner-neutral proposal/escalation contract so a future ChatGPT/Qwen/Claude/local adapter can be swapped above the same Control Plane without lower-core redesign. Close when a second planner can run shadow/proposal-only through that contract. |
| 4 | Architecture/process complexity can grow faster than user-visible capability | **7/10** | Open, mitigation strengthened | Enforce a complexity budget, prefer shared invariants over per-capability duplication, and require material capability growth to progress from L1 contract proof to representative L3 user-task evidence. Do not accept more architecture as evidence of progress when no realistic task improves. Close when capability additions are routinely justified by measured L3/real-user outcomes rather than broad document/status growth. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep release packaging behind core reliability work. Close with a clean-machine install/connect/permissions/ready path and Stage 28 clean-user E2E without developer environment assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Close Browser network/Site Capability debt before trusted-site JS/CDP/full-browser authority is accepted; add environmental-injection coverage, authenticated-session credential isolation for future Browser Companion, sensitive capture/demo retention policy, and representative L3 evidence before those authorities widen. |
| 7 | Documentation/status drift can misdirect fresh sessions | **5/10** | Mitigation in progress | Keep current status concise, keep this ranking only here, resolve live GitHub first, and update active stage/current-state docs in the same PR when production behavior changes. Close when stale status contradictions are caught by routine review/CI rather than user discovery. |

## L1/L2/L3 risk interpretation

Passing primitive tests is necessary but not sufficient evidence for risks #1, #2 or #4.

The project now uses:

```text
L1 primitive / contract proof
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final-state proof
```

Representative L3 tasks are vertical evidence that the planner can compose accepted mechanisms into useful work. The later broad real-app matrix remains necessary because one L3 pass is scoped evidence, not a universal accuracy claim.

## Browser Harness / ADR-036 risk interpretation

ADR-036 is an architecture direction, not evidence that wider Browser authority is already safe or useful.

The current Browser network weakness is tracked as TD-001. The project may finish current verification-focused 26.3B without pretending TD-001 is closed, but **trusted-site JS/CDP/full-browser authority cannot be accepted until the Site Capability / Browser Network Gate boundary is implemented and physically verified**.

This keeps the roadmap honest:

```text
verification correctness now
 != automatic authority expansion

future trusted-site authority
 -> requires lower-level network/site policy
 -> requires representative L3 evidence
```

`trust destination != trust instructions` remains binding even for allowlisted sites.

## Messaging / repository hygiene issue

### `Rust-first` repository description mismatch

**Technical risk: 3/10. Messaging risk: 8/10.**

The current runtime is primarily Python for Control Plane/verification/Windows, Node/MJS for semantic projection, and PowerShell for Windows lifecycle/operations. Rust is not a current runtime requirement.

Repository-facing documentation must describe the implementation truthfully. If the GitHub repository metadata still says `Rust-first local execution core`, change that metadata when repository-settings write access is available. Do **not** rewrite working code into Rust merely to satisfy an old description.

This is tracked as TD-009.

## What is not currently considered a core problem

The following are deliberate strengths unless evidence changes:

- small project-owned public semantic surface;
- semantic/native structure before pixels when reliable;
- selective visual fallback rather than screenshot-only control;
- shared Verification Kernel;
- independent Finish Gate;
- explicit `PASS | FAIL | UNKNOWN` and fail-closed continuation;
- L1 deterministic tests as a diagnostic foundation;
- UIA as one bounded Windows observation/action mechanism;
- Python as a current implementation language;
- PowerShell as Windows lifecycle/bootstrap glue;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked risk that is actionable **without skipping an unfinished prerequisite**.

Current order therefore remains:

```text
physical acceptance + merge of PR #111
 -> replay/hosted validation + Browser L3 physical acceptance for PR #112
 -> Windows/application/process verification
 -> representative Windows/application L3
 -> 26.3C WorkingState + recovery + LoopGuard
 -> broad real-app physical coverage gate
 -> 26.4 candidate-skill work
 -> 26.5 hybrid integration / any promoted Browser Harness authority
 -> packaging / clean-user release
```

Track M multi-chat and Track P local-planner work remain parallel/future and must not displace the current critical path merely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. cite the code/CI/physical/product evidence that changed it;
2. update the score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. do not copy the entire table into README, Roadmap, continuation notes or stage contracts.

# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register** for the current project. Other current documents may link to these risks but should not copy the full ranking or maintain competing scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when new code, CI, physical evidence or product constraints materially change the risk.

Current snapshot basis: 2026-08-26. Always resolve live `main` and active PR heads before acting.

## Current execution stop

At this snapshot:

- live `main` is `4319278cbc3b27de3f5c18d159aa3f8f3b9a4c6e`, squash-merge of physically accepted Browser L3 PR #113;
- Browser verification is physically accepted through `web_open` (#107), `web_interact` (#111), and the first natural-language Case Desk L3 (#113);
- PR #113 independent evidence reported `SAVE_COUNT=1`, `AUDIT_COUNT=1`, `FINISH_GATE=done`, `NON_TARGET_MUTATION=none`;
- active release-critical PR is draft #114, Windows `DesktopState` shared-kernel verification;
- #114 must pass fresh hosted checks and target-Windows physical verifier qualification on one final exact head before merge;
- representative Windows/application L3 follows only after the verifier is accepted.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open; one Browser L3 now accepted | Add representative L3 tasks as each major capability path becomes usable, beginning with Windows after #114. Then after 26.3C run a deliberate cross-app physical matrix covering native Win32, browser, Electron and office-style apps plus DPI/focus/dialog/noise variants. Close only when failures are characterized and accepted scope is materially broader than isolated examples. |
| 2 | The verified long-horizon control loop is not yet complete across capabilities | **8/10** | Open, actively reducing | Physically accept Windows shared-kernel verification + representative Windows L3, close any real cross-capability 26.3B completion gaps, then implement 26.3C WorkingState + typed recovery + LoopGuard. Close when a long task crosses relevant capabilities with fresh verification, bounded recovery and independently verified completion. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do **not** build a second planner now. After WorkingState v1 stabilizes, define a narrow planner-neutral proposal/escalation contract so a future ChatGPT/Qwen/Claude/local adapter can be swapped above the same Control Plane without lower-core redesign. Close when a second planner can run shadow/proposal-only through that contract. |
| 4 | Architecture/process complexity can grow faster than user-visible capability | **6/10** | Open; first realistic Browser L3 materially improved evidence | Keep a complexity budget, prefer shared invariants over per-capability duplication, and require material capability growth to progress from L1 to representative L3. PR #113 is evidence that the new acceptance discipline works; close only when this becomes routine across Windows and cross-capability work rather than a one-off success. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep release packaging behind core reliability work. Close with a clean-machine install/connect/permissions/ready path and Stage 28 clean-user E2E without developer environment assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Close Browser network/Site Capability debt before trusted-site JS/CDP/full-browser authority is accepted; add environmental-injection coverage, authenticated-session credential isolation for future Browser Companion, sensitive capture/demo retention policy, and representative L3 evidence before those authorities widen. |
| 7 | Documentation/status drift can misdirect fresh sessions | **5/10** | Mitigation in progress | Keep current status concise, keep this ranking only here, resolve live GitHub first, and update active stage/current-state docs in the same PR when the critical path changes. Close when stale status contradictions are caught routinely by review/CI rather than user discovery. |

## L1/L2/L3 risk interpretation

Passing primitive tests is necessary but not sufficient evidence for risks #1, #2 or #4.

```text
L1 primitive / contract proof
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final-state proof
```

PR #113 provides the first accepted Browser L3 vertical proof. It lowers uncertainty that the Browser primitives can be composed into useful work, but one randomized task does not close broad coverage risk #1.

The current Windows #114 work is deliberately L1 verifier infrastructure. It must be followed by representative Windows/application L3 rather than treated as user-value proof by itself.

## Browser Harness / ADR-036 risk interpretation

ADR-036 remains architecture direction, not evidence that wider Browser authority is already safe or useful.

The current Browser network weakness is tracked as TD-001. Trusted-site JS/CDP/full-browser authority cannot be accepted until the Site Capability / Browser Network Gate boundary is implemented and physically verified.

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

### `Rust-first` repository description mismatch

**Technical risk: 3/10. Messaging risk: 8/10.**

The current runtime is primarily Python for Control Plane/verification/Windows, Node/MJS for semantic projection, and PowerShell for Windows lifecycle/operations. Rust is not a current runtime requirement.

Repository-facing documentation must describe the implementation truthfully. If GitHub metadata still says `Rust-first local execution core`, change that metadata when repository-settings write access is available. Do not rewrite working code into Rust to satisfy stale metadata. This is tracked as TD-009.

## What is not currently considered a core problem

The following are deliberate strengths unless evidence changes:

- small project-owned public semantic surface;
- semantic/native structure before pixels when reliable;
- selective visual fallback rather than screenshot-only control;
- shared Verification Kernel;
- independent Finish Gate;
- explicit `PASS | FAIL | UNKNOWN` and fail-closed continuation;
- L1 deterministic tests as a diagnostic foundation;
- L3 natural-language tasks with external evidence as realistic vertical proof;
- UIA as one bounded Windows observation/action mechanism;
- Python as a current implementation language;
- PowerShell as Windows lifecycle/bootstrap glue;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked risk that is actionable **without skipping an unfinished prerequisite**.

Current order:

```text
PR #114 fresh hosted checks + target-Windows physical verifier acceptance
 -> merge #114 if clean
 -> representative Windows/application L3
 -> close any remaining real 26.3B cross-capability completion gap
 -> 26.3C WorkingState + recovery + LoopGuard
 -> broad real-app physical coverage gate
 -> 26.4 candidate-skill work
 -> 26.5 hybrid integration / promoted Browser Harness authority
 -> packaging / clean-user release
```

Track M multi-chat and Track P local-planner work remain future/parallel and must not displace the critical path merely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. cite the code/CI/physical/product evidence that changed it;
2. update score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. do not copy the entire table into README, Roadmap, continuation notes or stage contracts.

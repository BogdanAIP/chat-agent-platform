# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register** for the current project. Other current documents may link to these risks but should not copy the full ranking or maintain competing scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when new code, CI, physical evidence or product constraints materially change the risk.

Current snapshot basis: 2026-08-26. Always resolve live `main` and active PR heads before acting.

## Current execution stop

At this snapshot:

- live `main` is `20d06e8311ef65ee04b9a8a940c4f0d5725de0e0` (PR #106, Browser observation foundation);
- active release-critical PR is #107, `Stage 26.3B: verify Browser navigation final state`;
- pre-documentation-sync PR head `08671b5a8763d589bcd16da69e8ed70bcb5f9509` had all 11 pull-request-triggered hosted workflows green;
- PR #107 is intentionally **not mergeable by evidence policy yet**: the next required gate is an ordinary-Chat target-Windows physical Browser regression on the final exact PR head;
- after any branch change, hosted CI must be green on that new exact head before the physical gate is treated as merge evidence.

The next functional slice after accepted `web_open` verification is `web_interact` click/type postcondition verification.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open | After 26.3C, run a deliberate cross-app physical acceptance matrix covering native Win32, browser, Electron and office-style apps plus DPI/focus/dialog/noise variants. Close only when failures are characterized and the accepted scope is materially broader than one VS Code task. |
| 2 | The verified long-horizon control loop is not yet complete across capabilities | **8/10** | Open, actively reducing | Finish 26.3B Browser + Windows verification adapters, then 26.3C WorkingState + typed recovery + LoopGuard. Close when one long task crosses relevant capabilities with fresh verification, bounded recovery and independently verified completion. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do **not** build a second planner now. After WorkingState v1 stabilizes, define a narrow planner-neutral proposal/escalation contract so a future ChatGPT/Qwen/Claude/local adapter can be swapped above the same Control Plane without lower-core redesign. Close when a second planner can run shadow/proposal-only through that contract. |
| 4 | Architecture/process complexity can grow faster than user-visible capability | **7/10** | Open | Enforce a complexity budget: reuse common invariants, avoid new stages/docs/kernels without a measured need, prefer one shared contract over per-capability duplication, and require each major architecture addition to name the concrete failure it prevents. Close only when capability additions no longer routinely require broad document/status duplication. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep release packaging behind core reliability work. Close with a clean-machine install/connect/permissions/ready path and Stage 28 clean-user E2E without developer environment assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Finish browser DNS/rebinding/redirect/private-network policy, environmental-injection coverage, authenticated-session credential isolation for future Browser Companion, and sensitive capture/demo retention policy before those authorities widen. |
| 7 | Documentation/status drift can misdirect fresh sessions | **5/10** | Mitigation in progress | Keep current status concise, keep this ranking only here, resolve live GitHub first, and update active stage/current-state docs in the same PR when production behavior changes. Close when stale status contradictions are caught by routine review/CI rather than user discovery. |

## Messaging / repository hygiene issue

### `Rust-first` repository description mismatch

**Technical risk: 3/10. Messaging risk: 8/10.**

The current runtime is primarily Python for Control Plane/verification/Windows, Node/MJS for semantic projection, and PowerShell for Windows lifecycle/operations. Rust is not a current runtime requirement.

Repository-facing documentation must describe the implementation truthfully. If the GitHub repository metadata still says `Rust-first local execution core`, change that metadata when repository-settings write access is available. Do **not** rewrite working code into Rust merely to satisfy an old description.

## What is not currently considered a core problem

The following are deliberate strengths unless evidence changes:

- small project-owned public semantic surface;
- semantic/native structure before pixels when reliable;
- selective visual fallback rather than screenshot-only control;
- shared Verification Kernel;
- independent Finish Gate;
- explicit `PASS | FAIL | UNKNOWN` and fail-closed continuation;
- UIA as one bounded Windows observation/action mechanism;
- Python as the current implementation language;
- PowerShell as Windows lifecycle/bootstrap glue;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked risk that is actionable **without skipping an unfinished prerequisite**.

Current order therefore remains:

```text
finish PR #107 exact-head hosted + physical gate
 -> finish remaining 26.3B verification integrations
 -> 26.3C WorkingState + recovery + LoopGuard
 -> broad real-app physical coverage gate
 -> 26.4 candidate-skill work
 -> 26.5 hybrid integration
 -> packaging / clean-user release
```

Track M multi-chat and Track P local-planner work remain parallel/future and must not displace the current critical path merely because they are architecturally interesting.

## Update policy

When a risk materially changes:

1. cite the code/CI/physical/product evidence that changed it;
2. update the score/status/close condition here;
3. update `CURRENT_STATE.md` only if the live critical path changed;
4. do not copy the entire table into README, Roadmap, continuation notes or stage contracts.

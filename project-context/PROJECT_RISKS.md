# Project Risk Register

## Purpose

This is the **single authoritative ranked risk register** for the current project. Other current documents may link to these risks but should not copy the full ranking or maintain competing scores.

Risk scores are engineering priority estimates, not claims of failure. Re-score only when new code, CI, physical evidence or product constraints materially change the risk.

Current snapshot basis: 2026-08-26. Always resolve live `main` and active PR heads before acting.

## Current execution stop

At this snapshot:

- live `main` is `5df2e5e7378ddb9083a7c3d70a62c7bfc0f6c22d`, the squash-merge of physically accepted PR #107 (`web_open` final-state verification);
- PR #107 physical acceptance used exact head `64184713e97bf2e150614cd93c77509c244cddec` and proved direct navigation `PASS` plus delivered redirect `FAIL`-closed with independent final-page observation;
- active release-critical Browser PR is draft #111, `Stage 26.3B: verify Browser interaction postconditions`;
- #111 is a clean replay on accepted `main`; final acceptance requires fresh hosted CI and an ordinary-Chat target-Windows physical interaction regression on the final exact head;
- docs/architecture PR #110 records ADR-036 and the technical-debt register without expanding current runtime authority.

The next functional slice after accepted `web_interact` verification is Windows/application/process verification over accepted DesktopState/identity evidence.

## Ranked risks

| Rank | Risk | Score | Current status | Primary mitigation / close condition |
|---|---|---:|---|---|
| 1 | Broad real-application Windows/computer-use coverage is not yet proven | **9/10** | Open | After 26.3C, run a deliberate cross-app physical acceptance matrix covering native Win32, browser, Electron and office-style apps plus DPI/focus/dialog/noise variants. Close only when failures are characterized and the accepted scope is materially broader than one VS Code task. |
| 2 | The verified long-horizon control loop is not yet complete across capabilities | **8/10** | Open, actively reducing | Finish 26.3B Browser + Windows verification adapters, then 26.3C WorkingState + typed recovery + LoopGuard. Close when one long task crosses relevant capabilities with fresh verification, bounded recovery and independently verified completion. |
| 3 | Ordinary ChatGPT is the only current general planner | **7/10** | Accepted current dependency | Do **not** build a second planner now. After WorkingState v1 stabilizes, define a narrow planner-neutral proposal/escalation contract so a future ChatGPT/Qwen/Claude/local adapter can be swapped above the same Control Plane without lower-core redesign. Close when a second planner can run shadow/proposal-only through that contract. |
| 4 | Architecture/process complexity can grow faster than user-visible capability | **7/10** | Open | Enforce a complexity budget: reuse common invariants, avoid new stages/docs/kernels without a measured need, prefer one shared contract over per-capability duplication, and require each major architecture addition to name the concrete failure it prevents. Close only when capability additions no longer routinely require broad document/status duplication. |
| 5 | Packaging and clean-user installation are not release-grade | **6/10** | Open, intentionally deferred | Keep release packaging behind core reliability work. Close with a clean-machine install/connect/permissions/ready path and Stage 28 clean-user E2E without developer environment assumptions. |
| 6 | Browser/computer-use security hardening is incomplete for broader authority | **6/10** | Open | Close Browser network/Site Capability debt before trusted-site JS/CDP/full-browser authority is accepted; add environmental-injection coverage, authenticated-session credential isolation for future Browser Companion, and sensitive capture/demo retention policy before those authorities widen. |
| 7 | Documentation/status drift can misdirect fresh sessions | **5/10** | Mitigation in progress | Keep current status concise, keep this ranking only here, resolve live GitHub first, and update active stage/current-state docs in the same PR when production behavior changes. Close when stale status contradictions are caught by routine review/CI rather than user discovery. |

## Browser Harness / ADR-036 risk interpretation

ADR-036 is an architecture direction, not evidence that wider Browser authority is already safe.

The current Browser network weakness is tracked as TD-001. The project may finish current verification-focused 26.3B without pretending TD-001 is closed, but **trusted-site JS/CDP/full-browser authority cannot be accepted until the Site Capability / Browser Network Gate boundary is implemented and physically verified**.

This keeps the roadmap honest:

```text
verification correctness now
 != automatic authority expansion

future trusted-site authority
 -> requires lower-level network/site policy first
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
- UIA as one bounded Windows observation/action mechanism;
- Python as a current implementation language;
- PowerShell as Windows lifecycle/bootstrap glue;
- disabled/unreachable generic shell/Windows code execution;
- `ABSTAIN` instead of guessing under unresolved evidence.

## Priority rule

Release-critical work should reduce the highest-ranked risk that is actionable **without skipping an unfinished prerequisite**.

Current order therefore remains:

```text
finish/synchronize docs PR #110
 -> final hosted + physical acceptance for PR #111
 -> finish remaining 26.3B Windows/application/process verification
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

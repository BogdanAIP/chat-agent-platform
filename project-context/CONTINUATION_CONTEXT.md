# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-26 synchronization point:

```text
main = 4319278cbc3b27de3f5c18d159aa3f8f3b9a4c6e
       PR #113 — first Browser L3 real-task acceptance
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #114
       Windows DesktopState shared-kernel verification
       no public Chat/MCP surface change
       no new Windows action authority
       final hosted checks + target-Windows verifier qualification required
```

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- Browser Harness / ADR-036 docs: **MERGED #110**.
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**.
- first Browser L3 real-task acceptance: **PHYSICALLY ACCEPTED / MERGED #113**.
- accepted Windows `DesktopState`/resolver/guarded-action foundations: **accepted for their recorded Stage 26.2 scope**.
- Windows shared-kernel verifier: **ACTIVE PR #114**.
- WorkingState + typed recovery + LoopGuard: Stage 26.3C target, not yet accepted runtime.

## Browser L3 evidence now accepted

PR #113 physical run used randomized Case Desk data and gave ordinary Chat only the natural-language outcome/constraints.

The external checker outside Chat `FilesRoot` reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

That is scoped evidence that the accepted Browser primitives can be composed into one normal multi-step task with independent completion proof.

## Active PR #114 contract

PR #114 connects accepted `DesktopState.to_mapping()` evidence to `runtime/control_plane/verification.py` through:

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(capability=windows.desktop)
 -> bounded expected final state
 -> mandatory exact process/window identity continuity
 -> DesktopState AFTER
 -> shared ExpectedEffect verifier
 -> PASS | FAIL | UNKNOWN
```

Every PASS requires the same:

```text
Windows session
application identity
executable name
PID
process generation
HWND
window instance
coordinate space
```

This prevents a replacement/restarted process or reused PID/HWND from satisfying a similar-looking final state.

The adapter is data-only and non-authorizing. It cannot enumerate windows, invoke UIA, deliver input, launch a process or run arbitrary code. Live Windows evidence is still collected by the already accepted `runtime/windows/observation.py` path.

The older `runtime/windows/verifier.py` API is preserved unchanged for Stage 26.2 compatibility.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Current public semantic surface

Exactly:

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
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

## Acceptance depth

```text
L1 primitive/contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state
```

PR #114 is the Windows verifier L1 slice. It must be accepted before the representative Windows/application L3.

## Critical-path continuation

```text
1. finish PR #114 code/docs
2. freeze one final exact #114 head
3. require fresh hosted checks on that exact head
4. run target-Windows shared-kernel verifier qualification
5. merge #114 only if physical evidence/review remain clean
6. add representative Windows/application L3 with an independent Finish Gate
7. close any remaining real cross-capability 26.3B completion requirement
8. declare 26.3B accepted only after those required evidence gaps are closed
9. implement Stage 26.3C WorkingState + typed recovery + LoopGuard
10. run broad real-app Windows/computer-use coverage matrix
11. continue 26.4 / 26.5, then packaging/clean-user release
```

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not hidden current authority. The Browser network/Site Capability boundary must be implemented and accepted before trusted-site JS/CDP/full-browser authority is promoted. Any materially widened authority also requires representative L3 evidence.

## Fresh-chat read order

1. live GitHub `main`, open PRs and checks;
2. `START_HERE.md`;
3. `CURRENT_STATE.md`;
4. `PROJECT_RISKS.md`;
5. `STAGE26_3B_VERIFICATION_KERNEL.md`;
6. `STAGE26_3B_WINDOWS_VERIFICATION.md` while #114 is active;
7. `REAL_TASK_ACCEPTANCE.md`;
8. `ARCHITECTURE.md`;
9. `CONTROL_PLANE.md`;
10. `COMPUTER_USE_ARCHITECTURE.md`;
11. `SECURITY_POLICY.md`;
12. `ROADMAP.md`;
13. `BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 work;
14. `TECH_DEBT.md`;
15. `DOCUMENT_STATUS.md`;
16. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- current observed state outranks remembered procedure/demo/history;
- every production mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- many primitive `PASS` results != realistic user-task acceptance;
- only independent Finish Gate evidence verifies task completion;
- semantic/native identity precedes pixels where reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows/local code execution remains disabled until separately accepted;
- future public Windows/computer-use authority requires its own reviewed contract and physical evidence.

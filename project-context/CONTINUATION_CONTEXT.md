# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

Current release-critical work is PR #107:

`Stage 26.3B: verify Browser navigation final state`

At the 2026-08-26 documentation synchronization point:

```text
main = 20d06e8311ef65ee04b9a8a940c4f0d5725de0e0
pre-doc-sync PR #107 head = 08671b5a8763d589bcd16da69e8ed70bcb5f9509
```

That pre-doc-sync head had all 11 pull-request-triggered hosted workflows green.

The branch now also receives documentation synchronization, so do **not** treat `08671b5...` as the final acceptance head. Resolve the new exact PR head, require hosted CI green on that exact head, then run the ordinary-Chat target-Windows physical Browser regression on the same exact head.

If that physical gate passes and there are no unresolved findings/conflicts, merge PR #107 under the normal merge policy.

The next functional slice after #107 is accepted is `web_interact` click/type/control-result postcondition verification.

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **implemented in PR #107, pending final exact-head physical acceptance**.
- Windows/application/process Verification Kernel adapter: not yet implemented.
- WorkingState + typed recovery + LoopGuard: Stage 26.3C target, not yet accepted runtime.

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

## Current Browser verification contract

PR #107 changes `web_open` from delivery-only success semantics to:

```text
network/URL policy
 -> fresh browser snapshot BEFORE
 -> browser_navigate
 -> fresh browser snapshot AFTER
 -> BrowserObservationStream
 -> ExpectedEffect(exact canonical URL + document evidence + settled)
 -> PASS | FAIL | UNKNOWN
```

Delivery is not verification. Redirects are intentionally fail-closed in this first production navigation slice.

## Critical-path continuation

```text
1. resolve live PR #107 exact head
2. verify hosted CI on that head
3. run ordinary-Chat target-Windows Browser physical regression on the same head
4. merge #107 only if evidence is clean
5. implement web_interact postcondition verification
6. implement Windows/application/process verification
7. close remaining Stage 26.3B integration/physical gates
8. implement Stage 26.3C WorkingState + recovery + LoopGuard
9. run broad real-app Windows/computer-use coverage matrix
10. continue 26.4 / 26.5, then packaging/clean-user release
```

## Risk priority

Do not reconstruct project priorities from scattered prose. The authoritative ranked risk register is:

`project-context/PROJECT_RISKS.md`

Current top three are:

1. broad real-application Windows/computer-use coverage not yet proven;
2. verified long-horizon loop not yet complete across capabilities;
3. sole current general-planner dependency on ordinary ChatGPT.

The full scores, evidence and close conditions live only in the risk register.

## Fresh-chat read order

1. live GitHub `main`, open PRs and checks;
2. `START_HERE.md`;
3. `CURRENT_STATE.md`;
4. `PROJECT_RISKS.md`;
5. `STAGE26_3B_VERIFICATION_KERNEL.md` while 26.3B is active;
6. `ARCHITECTURE.md`;
7. `CONTROL_PLANE.md`;
8. `COMPUTER_USE_ARCHITECTURE.md`;
9. `SECURITY_POLICY.md`;
10. `ROADMAP.md`;
11. `DOCUMENT_STATUS.md`;
12. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- current observed state outranks remembered procedure/demo/history;
- every mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- transition `PASS` != task `DONE`;
- only the independent Finish Gate verifies task completion;
- semantic/native structure precedes pixels when reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows code execution remains disabled/unreachable;
- public Windows/computer-use authority requires its own reviewed contract and physical evidence.

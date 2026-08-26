# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-26 post-#107 synchronization point:

```text
main = 5df2e5e7378ddb9083a7c3d70a62c7bfc0f6c22d
       PR #107 — web_open final-state verification
       PHYSICALLY ACCEPTED / SQUASH-MERGED

active release-critical PR = #111
       web_interact postcondition verification
       draft; final exact-head hosted + physical acceptance required

parallel docs PR = #110
       Browser Harness architecture / ADR-036 / TECH_DEBT
```

PR #107 was physically accepted on exact head `64184713e97bf2e150614cd93c77509c244cddec` before merge. Direct navigation verified `PASS`; a real HTTP redirect physically delivered but final canonical URL mismatch verified `FAIL`/fail-closed, followed by independent observation of the actual final page.

The current functional slice is PR #111, a clean replay of the former stacked interaction branch directly on accepted `main`. Its initial runtime/test tree matched the previous final green interaction tree byte-for-byte, but acceptance still requires fresh CI and target-Windows ordinary-Chat evidence on the final PR #111 head.

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- production `web_interact` postcondition verification: **implemented in draft PR #111, not yet physically accepted**.
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

Accepted `web_open`:

```text
network/URL policy
 -> fresh browser snapshot BEFORE
 -> browser_navigate
 -> fresh browser snapshot AFTER
 -> BrowserObservationStream
 -> ExpectedEffect(exact canonical URL + document evidence + settled)
 -> PASS | FAIL | UNKNOWN
```

PR #111 extends that model to interaction:

```text
fresh BEFORE
 -> bounded expected result
 -> pre-action delta guard
 -> semantic-first / reviewed visual-fallback click or type
 -> fresh AFTER
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

Missing expected state, already-satisfied expected state, or an unobservable/ambiguous pre-action delta must produce zero mutation rather than guessed success.

## Critical-path continuation

```text
1. finish/synchronize docs PR #110
2. rebase PR #111 cleanly on the resulting main without changing its bounded runtime contract
3. require all hosted checks green on final exact PR #111 head
4. run ordinary-Chat target-Windows web_interact physical regression on that same head
5. merge #111 only if evidence/reviews are clean
6. implement Windows/application/process verification
7. close remaining Stage 26.3B integration/physical gates
8. implement Stage 26.3C WorkingState + recovery + LoopGuard
9. run broad real-app Windows/computer-use coverage matrix
10. continue 26.4 / 26.5, then packaging/clean-user release
```

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not a hidden expansion of the current Stage 26.3B gate.

```text
current 26.3B = verification correctness
26.3C alignment = trust/grant lifetime in structured state
26.4 alignment = generated helper candidate lineage
26.5 alignment = trusted-site full-browser / Browser Companion integration
```

The Browser network/Site Capability boundary must be implemented and accepted **before** trusted-site JS/CDP/full-browser authority is promoted. TD-001 tracks that debt. The current six-tool surface and runtime authority do not expand merely because ADR-036 exists.

## Risk priority

Do not reconstruct project priorities from scattered prose. The authoritative ranked risk register is:

`project-context/PROJECT_RISKS.md`

Current top three remain:

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
11. `BROWSER_HARNESS_ARCHITECTURE.md` when working on ADR-036 future authority;
12. `TECH_DEBT.md` for maintenance debt;
13. `DOCUMENT_STATUS.md`;
14. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- current observed state outranks remembered procedure/demo/history;
- every mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- only the independent Finish Gate verifies task completion;
- semantic/native structure precedes pixels when reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows/local code execution remains disabled/unreachable until separately accepted;
- public Windows/computer-use authority requires its own reviewed contract and physical evidence.

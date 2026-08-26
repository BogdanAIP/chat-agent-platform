# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-26 synchronization point:

```text
main = 82802dc619b0410b34859ed9ee362442b1f202f9
       PR #110 — Browser Harness architecture / ADR-036 / TECH_DEBT
       MERGED

active release-critical PR = #111
       web_interact postcondition verification
       exact head 1521e3128a7694be43518c3ee0188cb79f0ca0f5
       final hosted CI = 10/10 PASS
       ordinary-Chat target-Windows physical interaction acceptance pending

stacked evidence PR = #112
       first Browser L3 real-task acceptance harness
       must be replayed on accepted main after #111 merges
```

PR #107 remains physically accepted/merged Browser navigation evidence. Do not repeat its gate as current work.

The next decision point is physical acceptance of #111. If that passes, merge #111, replay #112 on the new `main`, require fresh hosted checks, then run the first natural-language Browser L3 task before starting the Windows/application/process verifier.

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- Browser Harness / ADR-036 architecture docs: **MERGED #110**.
- production `web_interact` postcondition verification: **implemented in draft PR #111; hosted CI green; physical acceptance pending**.
- Browser L3 real-task harness: **stacked draft PR #112**.
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

## Real-task acceptance contract

The project now distinguishes:

```text
L1 primitive/contract
 -> L2 multi-step workflow integration
 -> L3 ordinary user goal + independent final state
```

L1 remains mandatory and diagnosable. L3 is the proof that ordinary ChatGPT can choose a route through several accepted transitions and reach independently verified completion rather than merely passing laboratory primitives.

PR #112's `Case Desk` fixture randomizes task/case identity, contains similar customer records, persists server-side state/audit evidence, and has an independent Finish Gate that requires the exact requested target changes while proving decoys stayed unchanged.

Canonical detail: `REAL_TASK_ACCEPTANCE.md`.

## Critical-path continuation

```text
1. keep PR #111 exact head unchanged
2. run ordinary-Chat target-Windows web_interact physical regression on 1521e3128a7694be43518c3ee0188cb79f0ca0f5
3. merge #111 only if physical evidence/reviews remain clean
4. replay stacked PR #112 directly on the new accepted main
5. require fresh hosted harness/contract checks on final #112 head
6. run ordinary-Chat target-Windows Browser L3 real-task gate on that same head
7. merge #112 only if independent Finish Gate and non-target checks pass
8. implement Windows/application/process verification
9. add representative Windows/application L3 after that verifier exists
10. close remaining Stage 26.3B integration/physical gates
11. implement Stage 26.3C WorkingState + recovery + LoopGuard
12. run broad real-app Windows/computer-use coverage matrix
13. continue 26.4 / 26.5, then packaging/clean-user release
```

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not a hidden expansion of the current Browser authority.

```text
current 26.3B = verification correctness + representative L3 evidence
26.3C alignment = trust/grant lifetime in structured state
26.4 alignment = generated helper candidate lineage
26.5 alignment = trusted-site full-browser / Browser Companion integration
```

The Browser network/Site Capability boundary must be implemented and accepted **before** trusted-site JS/CDP/full-browser authority is promoted. TD-001 tracks that debt. Any materially widened authority must also pass representative L3 evidence rather than only primitive tests.

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
6. `REAL_TASK_ACCEPTANCE.md`;
7. `ARCHITECTURE.md`;
8. `CONTROL_PLANE.md`;
9. `COMPUTER_USE_ARCHITECTURE.md`;
10. `SECURITY_POLICY.md`;
11. `ROADMAP.md`;
12. `BROWSER_HARNESS_ARCHITECTURE.md` when working on ADR-036 future authority;
13. `TECH_DEBT.md` for maintenance debt;
14. `DOCUMENT_STATUS.md`;
15. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- current observed state outranks remembered procedure/demo/history;
- every mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- many primitive `PASS` results != realistic user-task acceptance;
- only the independent Finish Gate verifies task completion;
- semantic/native structure precedes pixels when reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows/local code execution remains disabled/unreachable until separately accepted;
- public Windows/computer-use authority requires its own reviewed contract and physical evidence.

# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-26 synchronization point:

```text
main = f7bba9eddd7c449306b7c9de18bc9e19849fd86f
       PR #111 — web_interact postcondition verification
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #113
       first Browser L3 real-task acceptance harness
       clean replay directly on accepted post-#111 main
       fresh hosted checks required on final head
       ordinary-Chat target-Windows Case Desk L3 still required

historical stacked PR = #112
       superseded by clean replay #113 after #111 merged
```

PR #107 remains physically accepted/merged Browser navigation evidence. Do not repeat its gate as current work.

The next decision point is acceptance of the first Browser L3 task. Freeze #113 on a final exact head, require fresh hosted checks, prepare one randomized Case Desk run, let ordinary Chat solve only the natural-language goal, then run the external Finish Gate. Only after that may #113 merge and the release-critical line move to Windows/application/process verification.

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- Browser Harness / ADR-036 architecture docs: **MERGED #110**.
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**.
- Browser L3 real-task harness: **ACTIVE DRAFT PR #113**, clean replay of superseded stacked #112.
- Windows/application/process Verification Kernel adapter: not yet implemented.
- WorkingState + typed recovery + LoopGuard: Stage 26.3C target, not yet accepted runtime.

## PR #111 physical-schema finding

The first ordinary-Chat #111 gate failed because the already-bound ChatGPT app definition rejected the new `expected` field even though the exact-head six-tool runtime already published it. The exact runtime head was kept unchanged, `Chat Local Bridge Test` was fully rebound, and a fresh conversation then accepted `expected` and passed the diagnostic checkbox interaction.

The complete physical interaction gate was rerun on that same exact head and passed all required cases, including positive type/click verification, zero-action preflight refusals, delivered-but-wrong-postcondition failure, and ambiguity abstention. This is the acceptance evidence for #111; the first failed run is only migration evidence.

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

Accepted `web_interact`:

```text
fresh BEFORE
 -> bounded expected result
 -> pre-action delta guard
 -> semantic-first / reviewed visual-fallback click or type
 -> fresh AFTER
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
```

Missing expected state, already-satisfied expected state, or an unobservable/ambiguous pre-action delta produces zero mutation rather than guessed success.

## Real-task acceptance contract

The project distinguishes:

```text
L1 primitive/contract
 -> L2 multi-step workflow integration
 -> L3 ordinary user goal + independent final state
```

L1 remains mandatory and diagnosable. L3 proves that ordinary ChatGPT can choose a route through several accepted transitions and reach independently verified completion rather than merely passing laboratory primitives.

PR #113's `Case Desk` fixture randomizes task/case identity, contains similar customer records, persists server-side state/audit evidence outside the Chat-writable workspace, tracks every mutated case, and has an independent Finish Gate that requires the exact requested target changes while proving decoys stayed unchanged and only the target was ever mutated.

Canonical detail: `REAL_TASK_ACCEPTANCE.md`.

## Critical-path continuation

```text
1. freeze the clean post-#111 PR #113 replay on one exact head
2. require fresh hosted checks on that head
3. prepare a randomized Case Desk physical run
4. ordinary Chat uses only the accepted six semantic tools to solve the natural-language task
5. run the external Finish Gate against fixture evidence outside Chat FilesRoot
6. merge #113 only if independent state + mutation-history evidence passes
7. implement Windows/application/process verification
8. add representative Windows/application L3 after that verifier exists
9. close remaining Stage 26.3B integration/physical gates
10. implement Stage 26.3C WorkingState + recovery + LoopGuard
11. run broad real-app Windows/computer-use coverage matrix
12. continue 26.4 / 26.5, then packaging/clean-user release
```

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not a hidden expansion of current Browser authority.

```text
current 26.3B = verification correctness + representative L3 evidence
26.3C alignment = trust/grant lifetime in structured state
26.4 alignment = generated helper candidate lineage
26.5 alignment = trusted-site full-browser / Browser Companion integration
```

The Browser network/Site Capability boundary must be implemented and accepted **before** trusted-site JS/CDP/full-browser authority is promoted. TD-001 tracks that debt. Any materially widened authority must also pass representative L3 evidence rather than only primitive tests.

## Risk priority

Do not reconstruct project priorities from scattered prose. The authoritative ranked risk register is `project-context/PROJECT_RISKS.md`.

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

# CAP Mutation Assurance

Status: **pilot / provisional**. This document defines the mutation-testing and adversarial-verification direction for Chat Agent Platform. It does not change production authority, public Chat-facing tools, or current Stage 26 acceptance semantics.

## Purpose

Chat Agent Platform needs more than a generic mutation score. The important question is whether a concrete weakening of a verification, provenance, recovery, or completion guarantee is detected by an independent test or gate.

The project therefore uses three complementary layers:

1. **Generic source mutation testing** — useful for finding unexpected weak spots in ordinary Python tests.
2. **Curated Guarantee Mutation Suite** — explicit mutants tied to named architectural guarantees and expected detectors.
3. **Adversarial behavioral verification** — deterministic fault injection and hostile state/action sequences that exercise multiple individually-correct components together.

The primary project metric is **Verification Guarantee Coverage**, not raw mutation percentage. Behavioral adversarial cases are tracked as named guarantees with explicit independent oracles rather than folded into a single opaque coverage percentage.

## Sequence and merge ordering

PR #115 completed its target-Windows ordinary-Chat physical L3 acceptance and was merged into `main` as `e965e7b5466446c9f065f6b57f438f25168bed9a`. CAP-M0 was then accepted through PR #117.

PR #118 completed the remaining representative Browser L3 source-provenance repeat on exact head `e29517fdf1c940d36bc822cfcc1a729ed7dd9574` and was squash-merged as `b3a23e34f6b550146e3169707f795a193e76eaf9`.

The accepted independent frozen Finish Gate proved clean-tree/source/install/full Node dependency revalidation after ordinary-Chat Browser actions, exactly one target save and audit mutation, unchanged decoys, `EXTERNAL_FINISH_GATE=DONE`, and fixture/guardian cleanup PASS. Earlier qualification attempts exposed real harness defects and were rejected rather than waived: culture-sensitive guardian READY parsing, a manifest producer/consumer process-generation field mismatch, and Playwright runtime output contaminating the source worktree when the qualification process inherited that CWD.

Current order:

1. merge this documentation-only adversarial-assurance replay onto accepted post-#118 `main` after hosted checks pass;
2. convert already-discovered defect classes into deterministic permanent adversarial/guarantee tests rather than relying on future review rediscovery;
3. implement the first Stage 26.3C WorkingState / typed Recovery / reconciliation / LoopGuard slice with CAP-M7 adversarial contracts designed alongside the guarantees;
4. keep expensive physical mutation/adversarial execution for consequence boundaries that deterministic evidence cannot faithfully represent;
5. do not widen the accepted six-tool public surface merely to implement assurance or recovery internals.

CAP-M0 remains independent from Browser/Windows physical consequence paths: it mutates isolated temporary verifier copies during tests and does not modify accepted production verifier behavior.

## CAP-M0 — Verification Kernel pilot

Production mutation target is intentionally limited to:

`runtime/control_plane/verification.py`

The pilot does not mutate Browser E2E, Windows physical qualification, PowerShell gates, or application fixtures.

The initial curated suite contains 12 deterministic mutants covering:

- FAIL precedence;
- UNKNOWN never becoming PASS;
- strict observation sequence freshness;
- capability identity;
- subject identity;
- observation-stream identity;
- ambiguity handling;
- missing fields on complete observations;
- Finish Gate evidence-batch binding;
- `candidate_done` not self-authorizing completion;
- unresolved completion requirements;
- safety failure independently blocking DONE.

Each mutant records:

- stable ID;
- guarantee being violated;
- mutation anchor and replacement;
- human-readable expected detector;
- exact `unittest` detector selector used to prove the kill.

The runner copies `runtime/control_plane` into an isolated temporary overlay and applies exactly one source mutation. The unmutated baseline still runs the full bounded Verification Kernel test modules and must pass. Each mutant then runs only its named detector test through a structured `unittest.TestResult` protocol.

A mutant is `KILLED` only when exactly one named detector test ran and that test produced an ordinary assertion failure with zero test errors, skips, expected failures, or unexpected successes. A passing named detector is `SURVIVED`. Import/load/runtime errors, wrong detector cardinality, timeouts, mutation-anchor drift, compile failures, malformed detector results, or non-zero detector-harness process exits are `ERROR`, never `KILLED`.

The detector process must also report the resolved `runtime.control_plane.verification` module path, and the runner requires it to equal the exact mutated overlay target. External `PYTHONPATH` state is not inherited into detector resolution. This prevents tests accidentally importing the unmutated checkout while a mutation is applied elsewhere.

These distinctions are required so unrelated test-process failures or source-resolution mistakes cannot inflate Verification Guarantee Coverage.

## Metric

For curated critical guarantees:

`Verification Guarantee Coverage = killed curated mutants / total curated mutants`

CAP-M0 acceptance target is `12 / 12 KILLED` with zero `SURVIVED`, zero `ERROR`, a passing unmutated baseline, and exact mutated-source binding for every detector run.

`KILLED` means **named detector assertion failure against the mutated target**, not merely a non-zero test-process exit code.

Raw mutation score from a future generic engine is secondary and must not replace this guarantee-oriented report.

## Adversarial verification model

The next expansion must target defects that ordinary unit/contract tests and happy-path physical tests are structurally weak at detecting: stale evidence, trust-boundary composition, time-of-check/time-of-use races, process-generation confusion, cleanup ordering, mutate-and-restore history, incomplete provenance closure, and runtime artifacts escaping their intended state directory.

A behavioral adversarial test should state four things explicitly:

1. **Guarantee** — the architectural promise being tested.
2. **Fault/attack** — the minimum deliberate weakening or hostile sequence.
3. **Independent oracle** — evidence not controlled by the mutated component.
4. **Required result** — FAIL / UNKNOWN / NOT_DONE / no delivery / no unrelated mutation, as appropriate.

A failure of the test harness, missing fixture, import error, timeout without a classified expected outcome, or wrong source binding is never evidence that the guarantee held.

## Concrete post-26.3B adversarial catalog

The following catalog is derived from real Stage 26.3B review and physical-gate failure classes. IDs are stable planning identifiers; implementation may split one row into multiple platform-specific cases while preserving the guarantee.

### Source Provenance / executed-byte closure — CAP-M6

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `SRC-001` | qualification starts from the wrong exact HEAD | provenance gate FAIL before consequence path |
| `SRC-002` | tracked staged/unstaged source is dirty | provenance gate FAIL |
| `SRC-003` | untracked runtime artifact appears inside the source worktree during qualification | provenance revalidation FAIL; runtime output must be isolated outside source |
| `SRC-004` | installed runtime is already modified before first local measurement | independently materialized exact-lock/source reference disagrees; FAIL |
| `SRC-005` | a directly imported runtime helper is omitted from attestation | provenance-closure meta-test FAIL |
| `SRC-006` | a transitive Node dependency is omitted from an allowlist-style proof | full installed-tree vs fresh exact-lock materialization FAIL |
| `SRC-007` | committed lock remains correct but installed package bytes are modified | installed-byte proof FAIL |
| `SRC-008` | source bytes change after prepare but before Finish Gate | Finish Gate provenance revalidation FAIL/NOT_DONE |
| `SRC-009` | installed semantic-runtime bytes change after prepare | guardian/revalidation FAIL/NOT_DONE |
| `SRC-010` | an intervening Chat action invalidates provenance freshness and old evidence is reused | old evidence is rejected; no DONE |

`SRC-005` and `SRC-006` must not regress into manually maintained package/file allowlists. The detector should derive or compare the complete runtime load/install closure so adding a new executed dependency without provenance coverage makes the test fail automatically.

### Finish Gate / stale evidence — CAP-M5/M6

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `FINISH-101` | reuse a previously valid evidence batch after an invalidating action | `NOT_DONE` or `UNKNOWN`, never DONE |
| `FINISH-102` | implementation emits authoritative PASS/DONE before cleanup completes | independent detector rejects ordering |
| `FINISH-103` | final-state verification passes but cleanup fails | no authoritative PASS/DONE survives |
| `FINISH-104` | final state matches after target mutate -> restore history | history-sensitive predicate still reports forbidden mutation |
| `FINISH-105` | a decoy/non-target is mutated and restored | Finish Gate rejects despite equal final bytes/state |

### Process / fixture ownership and cleanup — CAP-M5

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `PROC-101` | recorded PID exits and is reused by an unrelated process before cleanup | unrelated process is never killed; generation mismatch is detected |
| `PROC-102` | harness crashes immediately after spawning one or more owned children | all actually-owned children are cleaned or explicitly reported unresolved; no false PASS |
| `PROC-103` | semantic transport or fixture dies/restarts between prepare and Finish Gate | process-generation continuity fails |
| `PROC-104` | cleanup executes against stale ownership metadata | fail closed; no kill of unowned generation |
| `PROC-105` | serialized process-start timestamp is reparsed through locale-sensitive text conversion | deterministic numeric/generation identity path must reject or avoid locale-dependent ambiguity |

### Fixture freeze / atomic evidence — CAP-M5

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `FIX-101` | late or in-flight save races with fixture freeze | save is blocked or excluded before authoritative snapshot; no split-brain PASS |
| `FIX-102` | final evidence write is interrupted halfway | partial snapshot is never accepted as authoritative |
| `FIX-103` | freeze endpoint is replayed with stale/wrong authentication material | no state transition/final snapshot |
| `FIX-104` | fixture used by checker is dead/unreferenced while a decoy fixture remains live | fixture-liveness/identity contract rejects the run |
| `FIX-105` | manifest producer and frozen checker use different field names/schema versions | contract/meta-test fails before physical acceptance |

### Action/observation timing — CAP-M3/M5

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `OBS-101` | physical action is delivered once but UI postcondition appears only after a short delay | bounded fresh re-observation may verify; action is not blindly redelivered |
| `OBS-102` | BEFORE and AFTER resolve to same/non-advancing observation | UNKNOWN/stale; never PASS |
| `OBS-103` | subject/capability/stream changes between delivery and verification | UNKNOWN/FAIL; never PASS |
| `TIME-101` | outer timeout is shorter than delivery + verification grace | contract test rejects configuration rather than producing ambiguous duplicate attempts |

### Public authority / surface — CAP-M4/M5

| ID | Adversarial fault | Required oracle/result |
| --- | --- | --- |
| `AUTH-101` | seventh/raw Chat-facing tool or generic dispatch surface is added | public-surface contract fails |
| `AUTH-102` | backend/executor/PID/HWND/selector authority leaks into a bounded public procedure schema | schema/authority contract fails |
| `AUTH-103` | evidence object is treated as a grant/authorization token | independent policy/authority test rejects the operation |

## Meta-tests: prove the assurance system itself is live

The adversarial suite must contain tests of its own liveness so a refactor cannot leave a green but disconnected qualification fixture or mutation detector.

Required meta-guarantees:

- every curated mutant changes exactly the intended source anchor or structured fault point;
- every named detector proves it loaded/observed the mutated target, not the checkout baseline;
- every evidence-corpus case has a known expected result independent from the implementation being tested;
- adding a new runtime dependency causes provenance-closure tests to fail until it is covered;
- removing an adversarial fixture from the production/qualification path causes a fixture-liveness test to fail;
- producer/consumer evidence schemas are checked for field/version parity before physical qualification;
- runtime/browser diagnostic output is directed to owned state locations rather than the source checkout;
- an intentionally weakened reference implementation for each major family is rejected by at least one named detector.

## Codex Review -> permanent guarantee workflow

Codex Review remains an additive independent reviewer, not a release oracle and not an excuse for weak executable assurance.

Every concrete review finding that identifies a new defect class should follow this conversion path:

`finding -> minimal fix -> focused regression -> named guarantee -> curated mutant and/or adversarial case -> permanent suite`

The goal is that Codex Review increasingly searches for **new classes of defects**. Previously discovered classes should be caught deterministically before review.

Physical qualification findings follow the same rule. A physical gate that catches a harness/runtime defect is useful evidence that the gate is live, but that run is not acceptance; the defect class must be converted into a deterministic regression whenever feasible.

If Codex Review is unavailable because of quota or service availability, the project may continue according to its documented acceptance policy only when required hosted/physical gates pass. The unavailable independent-review layer must not be represented as completed.

## Planned expansion

After CAP-M0:

- **CAP-M1**: extend Verification Kernel guarantee catalog and optionally compare against a generic Python mutation engine.
- **CAP-M2**: observation adapters (`browser_observation.py`, `file_artifact_observation.py`, `windows_observation.py`).
- **CAP-M3**: transition verification (`browser_transition.py`, `windows_transition.py`), including delayed observation/no-redelivery timing cases.
- **CAP-M4**: expand the curated Guarantee Mutation Suite and registry/reporting, including public-authority invariants.
- **CAP-M5**: acceptance-system mutants and behavioral adversarial cases against deterministic evidence corpora; reserve real physical mutants for guarantees that cannot be faithfully represented without a live consequence boundary.
- **CAP-M6**: Source Provenance mutants and closure meta-tests: exact HEAD, clean tree, untracked/runtime-output isolation, full runtime/dependency closure, installed AppRoot binding, OpenAdapt/runtime binding, frozen qualification code, and Finish Gate revalidation.
- **CAP-M7**: Stage 26.3C mutants designed together with WorkingState, Recovery, reconciliation and LoopGuard.
- **CAP-M8**: CI tiers — deterministic critical mutants on PRs, larger state-machine/generic mutation runs scheduled/manual, and physical mutation-contract checks only for release/acceptance consequence boundaries.

## Stage 26.3C design obligations — CAP-M7

WorkingState / Recovery / LoopGuard should land with adversarial contracts from the first implementation PR. At minimum plan for:

- stale WorkingState cannot authorize a new physical effect;
- a structured failure reason survives handoff/retry and changes the next strategy rather than causing an identical blind attempt;
- ambiguous delivery is reconciled by observation before retry;
- repeated physical attempt fingerprints trip LoopGuard before unbounded redelivery;
- task/procedure/strategy budgets are distinct and exhaustion is fail-closed;
- recovery after process restart does not replay a proven committed effect;
- recovery cannot attach another actor/session/process generation's evidence to the current work item;
- `candidate_done` and stale success evidence remain non-authoritative after recovery;
- StagnationReport is diagnostic/escalation data, not a grant or second planner.

These guarantees should be implemented as deterministic state-machine/fault-injection tests where possible, with physical qualification only for consequence boundaries that deterministic evidence cannot faithfully model.

## CI tiers

Do not run every expensive assurance mechanism on every commit.

- **T0 — every PR:** ordinary unit/contract tests plus fast P0 curated guarantee mutants/adversarial cases for changed critical modules.
- **T1 — critical-path PR:** relevant CAP-M family, deterministic evidence corpus and source/provenance closure checks selected by changed paths.
- **T2 — scheduled/manual:** broader state-machine sequences, generic mutation engine experiments and extended adversarial corpus.
- **T3 — release/qualification:** exact-head target-Windows / Browser / application physical gates for guarantees requiring real consequences.

A T2/T3 test is not automatically a required repository status check unless it is guaranteed to run for every PR in the protected scope. Conditional/path-filtered assurance should instead be summarized by a stable required aggregator if it later becomes merge-critical.

## Future ID families

- `VK-*` — Verification Kernel
- `OBS-*` — observation integrity
- `BROWSER-*` — browser transition verification
- `WIN-*` — Windows transition verification
- `FINISH-*` — Finish Gate
- `SRC-*` — Source Provenance
- `PROC-*` — process ownership/cleanup
- `FIX-*` — qualification fixture/freeze/atomic evidence
- `AUTH-*` — public/internal authority boundaries
- `TIME-*` — timeout/retry timing contracts
- `WS-*` — WorkingState
- `REC-*` — recovery/reconciliation
- `LOOP-*` — LoopGuard and budgets
- `SESSION-*` — future Track M agent-session/delegation guarantees

## Independence rule

A mutated verifier/checker cannot be its own oracle.

Acceptance-system mutation tests must use an independent known-result corpus or meta-oracle. Physical mutation runs are justified only when the guarantee depends on a real delivery/target/freshness/identity consequence that cannot be proven from deterministic evidence alone.

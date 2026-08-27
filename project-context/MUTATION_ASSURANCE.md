# CAP Mutation Assurance

Status: **pilot / provisional**. This document defines the mutation-testing direction for Chat Agent Platform. It does not change production authority, public Chat-facing tools, or current Stage 26 acceptance semantics.

## Purpose

Chat Agent Platform needs more than a generic mutation score. The important question is whether a concrete weakening of a verification, provenance, recovery, or completion guarantee is detected by an independent test or gate.

The project therefore uses two complementary layers:

1. **Generic source mutation testing** — useful for finding unexpected weak spots in ordinary Python tests.
2. **Curated Guarantee Mutation Suite** — explicit mutants tied to named architectural guarantees and expected detectors.

The primary project metric is **Verification Guarantee Coverage**, not raw mutation percentage.

## Sequence

Do not modify or delay the exact-head physical acceptance of PR #115 for this work.

Planned order:

1. finish target-Windows physical L3 acceptance for PR #115 and merge it;
2. land the CAP-M0 Verification Kernel pilot;
3. implement Stage 26.3C WorkingState / typed recovery / LoopGuard with mutation contracts designed alongside the new guarantees;
4. expand mutation assurance outward only after the Kernel pilot demonstrates useful signal.

The CAP-M0 branch may be developed as a stacked draft on top of #115, but #115 remains independently frozen for physical acceptance.

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

## Planned expansion

After CAP-M0:

- **CAP-M1**: extend Verification Kernel guarantee catalog and optionally compare against a generic Python mutation engine.
- **CAP-M2**: observation adapters (`browser_observation.py`, `file_artifact_observation.py`, `windows_observation.py`).
- **CAP-M3**: transition verification (`browser_transition.py`, `windows_transition.py`).
- **CAP-M4**: expand the curated Guarantee Mutation Suite and registry/reporting.
- **CAP-M5**: acceptance-system mutants against deterministic evidence corpora; reserve real physical mutants for guarantees that cannot be faithfully represented without a live consequence boundary.
- **CAP-M6**: Source Provenance mutants (exact HEAD, clean tree, untracked files, critical hashes, installed AppRoot binding, OpenAdapt version/server/lock binding, frozen qualification code).
- **CAP-M7**: Stage 26.3C mutants designed together with WorkingState, Recovery and LoopGuard.
- **CAP-M8**: CI tiers — deterministic critical mutants on PRs, larger generic mutation runs scheduled/manual, and mutation-contract checks for release/acceptance.

## Future ID families

- `VK-*` — Verification Kernel
- `OBS-*` — observation integrity
- `BROWSER-*` — browser transition verification
- `WIN-*` — Windows transition verification
- `FINISH-*` — Finish Gate
- `SRC-*` — Source Provenance
- `WS-*` — WorkingState
- `REC-*` — recovery/reconciliation
- `LOOP-*` — LoopGuard and budgets
- `SESSION-*` — future Track M agent-session/delegation guarantees

## Independence rule

A mutated verifier/checker cannot be its own oracle.

Acceptance-system mutation tests must use an independent known-result corpus or meta-oracle. Physical mutation runs are justified only when the guarantee depends on a real delivery/target/freshness/identity consequence that cannot be proven from deterministic evidence alone.

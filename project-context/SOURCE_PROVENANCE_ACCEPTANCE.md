# Source Provenance Acceptance Contract

Status: **AUTHORITATIVE / ACCEPTED PHYSICAL-PROVENANCE METHODOLOGY**.

The common methodology was introduced around the Stage 26.3B Windows qualification work and subsequently exercised/strengthened by accepted target-Windows Browser/Windows gates. The stronger #118 Browser repeat is the current reference evidence that exact source/install/runtime/dependency provenance can invalidate an otherwise plausible run and be revalidated after consequence-bearing actions.

Exact accepted heads/result locators belong in `EVIDENCE_INDEX.md`.

## Purpose

A physical acceptance claim must bind not only a named Git commit but the actual relevant bytes/runtime closure used by the qualification.

```text
git rev-parse HEAD == EXPECTED_HEAD
```

is necessary but insufficient because tracked modifications, untracked files, installed runtime copies, helper scripts or transitive dependencies may influence execution while `HEAD` remains unchanged.

## SourceProvenanceGate

Every release-critical target-machine qualification whose claim depends on exact executed source/runtime bytes should bind a provenance result containing the relevant subset of:

```text
expected_head
actual_head
source_root
working_tree_clean
tracked_diff_empty
untracked/influencing-file status
critical project source hashes / Git blobs
qualification driver hashes
fixture/checker hashes
relevant lock/config hashes
installed runtime hashes
runtime helper/dependency closure hashes
runtime/tool versions where material
captured_at / provenance generation
```

The exact evidence shape may evolve by capability, but missing required provenance must fail closed rather than be guessed.

## Clean-source rule

For the source root used by release-critical qualification, the equivalent of a reviewed clean-tree check must establish that no tracked/untracked state can influence the claim unexpectedly.

Prefer generated runtime/result artifacts outside the source checkout. If a reviewed generated path is excluded, the exclusion must be narrow and part of the qualification contract; broad wildcard exceptions are not acceptable substitutes for a clean source tree.

The #118 Browser qualification demonstrated why this matters: an invalid attempt wrote Playwright runtime artifacts into the frozen source worktree through inherited CWD, and provenance revalidation correctly failed. The later accepted run isolated runtime CWD. Permanent product hardening of runtime output ownership is tracked separately in `TECH_DEBT.md`.

## Git content vs local raw bytes

On Windows, Git filters such as line-ending normalization can make raw bytes differ from committed blob representation without implying an unauthorized source edit.

Where relevant record both:

```text
expected Git blob from EXPECTED_HEAD
local clean-filtered Git blob
local raw SHA-256
local byte size
```

This proves committed-content equivalence while also recording the exact local bytes that participated in execution.

## Critical-asset binding

Bind the files that materially determine the run, for example:

```text
runtime adapter under qualification
Verification Kernel / Finish Gate when used
public semantic launcher/projection
procedure/runtime helper code
qualification driver
fixture / guardian / external checker
relevant config/lock files
```

The list must be derived from the actual execution path rather than from a permanently frozen hand-maintained list where practical.

## Installed runtime binding

Source provenance is incomplete if the physical run executes an installed/copied artifact that is not proven equivalent to reviewed source.

Required pattern when installation is involved:

```text
materialize expected source from exact head
 -> independently hash/identify expected installed artifacts
 -> compare installed files/tree
 -> launch only proven installed runtime
 -> record install/runtime identity in evidence
```

A repository `HEAD` cannot substitute for proof of an installed copy.

## Transitive dependency / runtime closure

If behavior can be changed by transitive runtime dependencies, provenance must bind the relevant complete closure, not only top-level lock/config files.

#118 strengthened Browser qualification by binding the exact-lock Node runtime tree and revalidating it after Browser actions.

General rule:

```text
committed lock/config proves intended dependency graph
installed closure proof proves the bytes actually available to runtime
```

Where closure cannot be completely enumerated, the qualification must explicitly narrow the claim rather than imply full dependency provenance.

## Provenance generation / freshness

Provenance evidence is not timeless.

If a consequence-bearing action can mutate source/install/runtime state, revalidate the relevant provenance after those actions and before authoritative Finish Gate completion.

Do not reuse pre-action provenance after an invalidating action without proving continuity/new generation.

Conceptually:

```text
prepare provenance generation G
 -> execute admitted actions
 -> revalidate source/install/runtime closure
 -> freeze authoritative final evidence
 -> independent Finish Gate
```

## Qualification script / checker provenance

The script that verifies source/runtime provenance and the external checker/Finish Gate cannot be outside the provenance claim when their bytes affect acceptance.

Bind or independently materialize/hash qualification drivers, fixtures and checkers as applicable.

A checker that can be silently replaced after prepare does not provide independent evidence.

## Process / fixture generation binding

Source bytes alone are insufficient when the qualification claim depends on one specific live fixture/runtime generation.

Physical evidence should bind relevant process/session generations, for example:

```text
owned process PID + generation/start identity
fixture identity / nonce
tunnel/runtime generation
source/install provenance generation
```

Reused PID/title/port alone is not always sufficient ownership proof.

## Atomic final evidence

Where an external Finish Gate consumes a final snapshot, produce one authoritative frozen evidence generation after required mutations/cleanup/provenance revalidation.

Avoid split-brain final evidence assembled from independently mutable files when one atomic/frozen snapshot is practical.

An interrupted/partial final-evidence write must not become authoritative.

## Current Browser / Windows reference scope

Accepted Stage 26.3B Windows/application and Browser L3 gates demonstrated this methodology at increasing strength.

The strongest recorded Browser repeat (#118) bound:

- exact frozen source head/worktree;
- installed semantic/runtime source equivalence;
- relevant runtime helpers;
- complete exact-lock Node dependency tree;
- post-action provenance revalidation;
- frozen final state/history;
- external Finish Gate;
- fixture/guardian cleanup.

This is scoped evidence for that route, not a claim that every future capability automatically inherits complete provenance coverage.

## Failure semantics

If required provenance cannot be proven:

```text
UNKNOWN / FAIL / NOT_DONE
```

as appropriate to the gate.

Never downgrade missing provenance to a warning merely because functional state appears correct.

## Maintenance / assurance

Mutation/adversarial provenance cases live in `MUTATION_ASSURANCE.md` (CAP-M6 family). Permanent source/runtime-output compromises live in `TECH_DEBT.md`.

A new capability/physical gate should reuse this methodology instead of inventing another unrelated source-binding protocol, while adapting the concrete closure to its actual execution path.

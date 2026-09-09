# Evidence Dependency Graph and Selective Requalification

Status: **POST-#149 RESEARCH DIRECTION ONLY — NO PRODUCTION AUTHORITY**

This note records a concrete post-#149 improvement identified while physically qualifying PR #149 on Windows.

The current conservative rule is intentionally simple: physical evidence is bound to the exact executable runtime/generation that was qualified. If release-critical runtime bytes change, prior physical evidence is treated as stale unless the repository can prove that the changed bytes are outside that evidence's trusted dependency set.

That rule is correct as a safety fallback, but it is too coarse as a permanent developer workflow. CAP should move toward **dependency-bound evidence + selective requalification** rather than "rerun every physical gate after any runtime change".

This note does not weaken PR #149 and must not be used to waive its current gates. Any production adoption requires fresh Stage Research after #149 is accepted.

---

## 1. Core invariant

Physical acceptance proves a specific executable artifact under specific authority/provenance assumptions.

```text
qualified executable inputs X
        -> physical gate G
        -> evidence E(X, G)
```

If an executable input on which `G` depends changes from `X` to `Y`, `E(X, G)` cannot automatically prove `Y`.

However, a new Git HEAD alone should not make unrelated evidence stale when all authoritative inputs used by that evidence are byte-identical.

Target rule:

```text
HEAD changed
    != automatically all evidence stale

trusted dependency changed
    -> dependent evidence stale

trusted dependency unchanged
    -> dependent evidence may remain CURRENT
```

The system must fail conservatively: if dependency coverage cannot be proven exactly, requalify.

---

## 2. Replace one coarse generation with dependency-aware fingerprints

Do not discard exact whole-runtime provenance. Keep a whole-runtime generation for archival identity, but additionally compute narrow, deterministic fingerprints for release-critical authority domains.

Illustrative domains:

```text
runtime_generation
send_authority_generation
capture_authority_generation
browser_lifecycle_generation
controller_generation
source_provenance_generation
result_parser_generation
```

Names and exact boundaries are not accepted by this document; Stage Research must derive them from real dependency edges.

A domain generation should be a canonical hash over the exact Git blobs/configuration that can affect that domain, not over filenames, timestamps, test labels or claimed scope.

Example:

```text
send_authority_generation = H(
  manifest/content-script registration,
  composer qualification,
  Temporary/non-personalized authority predicates,
  prompt equality,
  claim protocol,
  send-control selection,
  pre-click revalidation,
  execution-generation bootstrap inputs
)
```

---

## 3. Evidence dependency graph

Each physical/hosted gate should declare the authoritative input fingerprints it depends on.

Conceptual graph:

```text
source/runtime blobs
        |
        v
component/domain fingerprints
        |
        v
acceptance gates
        |
        v
accepted evidence records
        |
        v
release/Finish decision
```

For PR #149-style qualification, an initial candidate map is:

```text
A0  provenance/loading qualification
    -> source_provenance_generation
    -> manifest/loading inputs
    -> whole runtime archive identity

A   uninterrupted one-Send + result capture
    -> send_authority_generation
    -> capture_authority_generation
    -> controller_generation
    -> source_provenance_generation

B1  complete browser/MV3 loss before first claim
    -> browser_lifecycle_generation
    -> send_authority_generation
    -> controller launch/claim state generation
    -> source_provenance_generation

B2  complete browser/MV3 loss after claim/Send
    -> browser_lifecycle_generation
    -> send_authority_generation
    -> controller delivery/result state generation
    -> source_provenance_generation
```

This is a research seed, not an accepted dependency map. The real graph must be generated from production authority paths and executable tests.

---

## 4. Evidence record requirements

A reusable evidence record should bind at least:

```text
gate_id
scenario_version
qualified_head_sha
whole_runtime_generation
exact dependency fingerprint set
target environment identity where relevant
artifact/source attestation
result status
observed consequence counts / key state facts
qualification timestamp
```

The release gate should compare the evidence's dependency fingerprints against the current candidate, not merely compare `qualified_head_sha`.

If all dependency fingerprints remain identical, the evidence may remain CURRENT even if documentation, tests or unrelated provider runtime changed.

If one dependency differs, invalidate that gate and every downstream assertion that depends on it.

---

## 5. Transitive invalidation, not manual judgement

Selective requalification must be machine-computed from a checked-in dependency graph.

```text
changed Git blob
   -> changed domain fingerprint(s)
   -> stale directly dependent gate(s)
   -> stale downstream release evidence
```

Do not rely on PR prose such as "this change only affects capture" or reviewer judgement alone.

Conservative fallback:

```text
unknown dependency
ambiguous edge
unclassified executable input
    -> invalidate the broader parent domain / gate set
```

This prevents selective requalification from becoming a loophole for skipping physical tests.

---

## 6. Expected developer workflow

Target post-#149 workflow:

```text
change
  -> recompute dependency fingerprints
  -> calculate stale evidence set
  -> run hosted semantic/unit/security gates
  -> rerun only stale physical gates
  -> bind new/reused evidence to exact current candidate
  -> Finish Gate
```

Examples:

```text
README-only change
  -> no executable fingerprint changes
  -> A0/A/B1/B2 remain current

result-parser-only change with proven isolation
  -> capture/result domain changes
  -> rerun A (or narrower future capture gate)
  -> B1 may remain current if its dependencies are byte-identical

send-control qualification change
  -> send authority changes
  -> A + B1/B2 stale
  -> A0 may remain current if loading/provenance inputs are unchanged

background/claim/lifecycle change
  -> browser lifecycle / send-delivery domains change
  -> A + B1 + B2 stale

manifest/content-script/loading change
  -> provenance/loading changes
  -> A0 stale and dependent physical gates likely stale transitively
```

---

## 7. Prefer smaller orthogonal gates over one giant physical script

Where practical, split broad physical qualification into orthogonal contracts so evidence can be reused safely.

For example, future qualification could separate:

```text
P0 exact-source/loading provenance
P1 Temporary/non-personalized/no-plugin authority
P2 exactly-one Send authority
P3 correlated result capture
R1 pre-claim browser-loss recovery
R2 post-Send browser-loss recovery
```

This does not mean multiplying public tools or production state machines. It is an acceptance/evidence decomposition only.

A gate should be split only when its inputs and success criteria can be independently proven; otherwise keep the larger conservative gate.

---

## 8. Tests must prove dependency declarations

A checked-in dependency graph becomes release-critical authority and therefore needs adversarial tests.

Required classes include:

- changing every declared input invalidates the expected gate;
- changing an unrelated documentation/test blob does not invalidate physical evidence;
- introducing a new executable source without classification fails closed;
- renaming/moving executable sources cannot escape generation binding;
- generated/bundled/archived runtime bytes remain traceable to bound source inputs;
- dependency graph changes themselves require appropriate review/acceptance;
- transitive invalidation cannot be bypassed by retaining an old component hash.

A useful acceptance property is:

> For each physical gate, mutate one production input that can change the gate's behavior and prove the stale-set calculator includes that gate.

---

## 9. Relationship to review and CI

Selective physical requalification must not weaken semantic review or normal hosted CI.

```text
semantic review asks: is the current design/code correct?
CI asks: do executable automated contracts pass?
physical gates ask: does the real target environment satisfy release-critical behavior?
```

Reusing physical evidence is permitted only because its exact trusted inputs are proven unchanged, not because a reviewer believes a change is harmless.

A material contract/authority change can still require fresh Stage Research and fresh semantic review even if some physical evidence remains reusable.

---

## 10. Recommended post-#149 research task

After #149 merges, include this in Composition Stage Research:

**Evidence Dependency Graph + Selective Requalification**

Research/implement in this order:

1. inventory current physical gates and their real production dependencies;
2. derive a minimal checked-in dependency graph;
3. define deterministic component/domain fingerprints;
4. define evidence record schema and CURRENT/STALE calculation;
5. add fail-closed handling for unclassified executable inputs;
6. add adversarial dependency-mutation tests;
7. prove selective invalidation on at least two real historical CAP changes;
8. only then allow the Finish Gate to reuse old physical evidence across a changed HEAD.

Success criterion:

> CAP reruns every physical test whose trusted behavior inputs changed, but does not require manual requalification of gates whose exact dependency set is demonstrably byte-identical.

Until this is accepted, keep the current conservative exact-runtime requalification rule.
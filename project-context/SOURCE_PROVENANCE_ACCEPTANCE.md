# Source Provenance Acceptance Contract

Status: **AUTHORITATIVE PHYSICAL-ACCEPTANCE METHODOLOGY — common gate implemented in PR #114, acceptance pending**

## Purpose

Physical acceptance must prove not only that a named Git commit was checked out, but that the actual source bytes used by the qualification run corresponded to the intended exact head.

A check such as:

```text
git rev-parse HEAD == EXPECTED_HEAD
```

is necessary but insufficient because tracked files may be locally modified and untracked files may influence execution while `HEAD` remains unchanged.

For a project whose acceptance model is based on independently verifiable evidence, this was identified as a **P1 methodology defect**. PR #114 introduces the reusable implementation in `scripts/source-provenance-gate.py` and wires it into the Windows physical qualification path. The methodology becomes accepted for release-critical use only after that exact implementation passes hosted tests and target-Windows physical qualification.

---

## 1. SourceProvenanceGate

Every release-critical target-machine physical acceptance run must bind one `SourceProvenanceGate` result to its evidence.

Minimum required fields:

```text
expected_head
actual_head
working_tree_clean
tracked_diff_empty
untracked_empty
source_root
critical_asset_hashes
qualification_driver_hashes
relevant_lockfile_hashes
runtime/tool versions required by that gate
captured_at
```

Minimum pass conditions:

```text
actual_head == expected_head
working tree contains no tracked modifications
working tree contains no untracked files that can influence the run
critical source hashes match the files from expected_head
qualification scripts are themselves bound by hash
relevant dependency/lock configuration is bound by hash
```

The gate must fail closed rather than silently accepting an unverifiable checkout.

Current PR #114 implementation additionally records, for each bound project file:

```text
expected Git blob from EXPECTED_HEAD
local Git clean-filtered blob
local raw SHA-256
local byte size
```

This matters on Windows because Git may legitimately apply line-ending clean filters. The Git-blob comparison proves committed content after Git's configured clean transformation, while raw SHA-256 records the exact local bytes used by the run.

---

## 2. Clean working-tree rule

At minimum the qualification source root must satisfy the equivalent of:

```text
git status --porcelain=v1 --untracked-files=all
```

returning no entries. The common implementation also checks staged and unstaged diffs independently.

The implementation may use a detached worktree or another isolated checkout, but isolation alone is not proof. The actual run must record and verify cleanliness before executing release-critical qualification logic.

If the physical gate intentionally generates files inside the source checkout, those generated paths must be explicitly excluded by a reviewed rule or, preferably, written outside the source checkout. Broad wildcard exclusions are not acceptable substitutes for a clean source tree.

The PR #114 Windows harness writes provenance/result evidence outside the source checkout. It also performs a launcher-side clean-tree preflight **before** starting the Windows fixture, then invokes the reusable Python gate for the full hash binding.

---

## 3. Critical-asset hash binding

A physical acceptance should bind hashes for the files whose local bytes materially determine the result.

Examples:

```text
runtime adapter under qualification
shared Verification Kernel when used
public semantic launcher/projection when used
qualification driver script
fixture implementation
external Finish Gate/checker
relevant config/lock files
```

Do not require a manually maintained list of every repository file when Git already proves the committed tree. The critical-asset hash list is additional evidence that the exact local files actually invoked by the harness were the expected bytes.

Preferred evidence form:

```json
{
  "source_provenance": {
    "expected_head": "...",
    "actual_head": "...",
    "working_tree_clean": true,
    "tracked_diff_empty": true,
    "untracked_empty": true,
    "critical_assets": {
      "runtime/...": {
        "git_blob_expected": "...",
        "git_blob_local_clean_filtered": "...",
        "matches_expected_blob": true,
        "sha256": "..."
      }
    },
    "lockfiles": {
      "...": {
        "matches_expected_blob": true,
        "sha256": "..."
      }
    }
  }
}
```

Exact schema may evolve, but the proof obligations above must remain.

---

## 4. Relationship to exact-head acceptance

The project should use the phrase **exact-head physical acceptance** only when both are proven:

```text
commit identity
AND
source-byte provenance / clean-tree identity
```

A commit SHA without source cleanliness proves repository ancestry, not necessarily the complete executed byte state.

This rule applies to:

```text
Browser L3
Windows verifier qualification
Windows/application L3
file/artifact qualification
future Office adapters
future OpenAdapt procedure acceptance
future Local Execution Kernel acceptance
future cross-capability release gates
```

---

## 5. Existing accepted evidence

Previously accepted physical results are not automatically invalidated merely because this stronger methodology was defined later.

In particular, Browser L3 PR #113 has:

```text
functional result                         PASS
independent final-state evidence          PASS
mutation-history evidence                 PASS
source provenance under this new contract INCOMPLETE
```

The correct interpretation is **not** "PR #113 failed".

Instead, before Stage 26.3B is declared fully closed, repeat one representative Browser L3 run on accepted `main` under the new SourceProvenanceGate. This cheaply closes the proof gap without rewriting historical evidence.

Do not rewrite accepted history to claim the old gate proved cleanliness when it did not.

---

## 6. Physical qualification sequence

Preferred release-critical sequence:

```text
resolve live PR/final head
 -> freeze intended head
 -> fresh hosted checks
 -> prepare isolated target-machine source root
 -> SourceProvenanceGate PASS
 -> run physical capability/L3 qualification
 -> independent Finish Gate / checker where applicable
 -> bind result to same source-provenance evidence
 -> review no unresolved finding
 -> merge
```

If source provenance changes after the gate, the physical result is stale and must not be attributed to the new bytes.

---

## 7. Infrastructure failure vs semantic failure

Physical and hosted acceptance should distinguish failure classes.

Example:

```text
semantic failure
  target/action delivered but expected effect fails
  identity is wrong
  verifier returns FAIL/UNKNOWN for real state

infrastructure failure
  runner/browser process unavailable
  environment setup broken
  UI test framework times out before action delivery
  fixture never becomes interactable
```

Do not turn an infrastructure timeout into a semantic PASS by merely increasing a timeout.

For timing/settling failures such as a UI framework waiting for an element to become stable:

```text
repeat a bounded number of runs
capture visibility/enabled/geometry/stability evidence
compare runner/runtime versions
classify reproducible semantic-fixture defect vs environment/runner drift
then change settling/timeout behavior only with evidence
```

Uncharacterized infrastructure instability still blocks release-critical acceptance; it should not be mislabeled as a product semantic failure.

---

## 8. Source provenance for external dependencies

When a qualification uses pinned third-party code such as OpenAdapt or selected UFO-derived components, source provenance must additionally record:

```text
upstream repository
pinned commit/tag/version
license
installed/local artifact hash where practical
project adapter version/hash
compatibility-test result
```

An upstream version string alone is not enough if locally installed bytes may differ.

PR #114 applies this rule to the existing accepted Windows resolver dependency on OpenAdapt Flow: the project lockfile is source-bound by the common gate, and the physical Python driver additionally records the installed `openadapt-flow` version plus SHA-256 of the actual imported `openadapt_flow.backends.win_agent.server` source file. Physical acceptance requires the installed version to match the locked declared version.

---

## 9. Current implementation and promotion state

Common implementation introduced in PR #114:

```text
scripts/source-provenance-gate.py
```

Hosted regression coverage:

```text
tests/test_source_provenance_gate.py
  clean exact-head checkout -> PASS
  tracked modification      -> FAIL
  untracked file            -> FAIL
  evidence output inside source checkout -> rejected
```

The current Windows physical launcher also requires:

```text
SOURCE_PROVENANCE_GATE=PASS
WORKING_TREE_CLEAN=True
TRACKED_DIFF_EMPTY=True
UNTRACKED_EMPTY=True
```

before the overall Windows qualification may pass.

Until PR #114 itself passes fresh hosted checks and the target-Windows physical run on one final head, the implementation is **implemented/pending acceptance**, not accepted historical evidence.

---

## 10. Non-goals

This methodology does not require:

- rebuilding the repository from scratch before every unit test;
- hashing every OS file or every package in the machine;
- invalidating all historical physical evidence;
- treating a clean tree as proof of semantic correctness;
- replacing capability-specific independent Finish Gates.

Source provenance answers only:

> **what exact project/source material did this acceptance run execute?**

Capability verification and Finish Gate answer different questions and remain independently required.

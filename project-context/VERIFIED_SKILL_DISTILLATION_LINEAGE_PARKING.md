# Verified Skill Distillation + Skill Lineage — parked Stage 26.4 plan

Status: **PARKED — do not implement in PR #149**

This note exists so the AREX/DisCo ideas we want to adapt are not lost before the roadmap reaches Stage 26.4.

## Roadmap placement

Current intended order remains:

```text
bounded Agent Session / Delegation
 -> automatic reviewer migration
 -> broad real-application physical coverage gate
 -> bounded OpenAdapt integration spike
 -> 26.4 Human Demo -> verified candidate skill / skill lineage
```

Re-enter this note when starting the `verified candidate skill / skill lineage` part of Stage 26.4. If the roadmap changes before then, re-evaluate the trigger rather than treating this ordering as permanent.

## External reference

Primary reference candidate:

- repository: `VectorSpaceLab/AREX-Skill`
- inspected `main` baseline on 2026-09-06: `ac3fe1afa80fb9a09775ecfb2b6cc3ba850a2db6`
- CAP disposition: **REFERENCE_ONLY / ADAPT_MECHANIC** by default

Do not adopt the DisCo agent/runtime wholesale merely to get these ideas.

Before implementation, rerun current CAP `stage-research` + `source-code-research` against the then-current exact AREX ref. README/docs-level evidence is insufficient when public implementation exists. Inspect concrete Creator/Researcher routing, creation, verification, provenance, refresh, import/rollback, package/update and router implementation/tests.

## What CAP should take

### 1. Verified skill-distillation lifecycle

Adapt the lifecycle:

```text
source/task anchor
 -> scope capabilities
 -> ground in admissible evidence
 -> construct candidate skill graph
 -> verify/refine
 -> VERIFIED_CANDIDATE
 -> explicit install/approval
```

Candidate public entry for research:

```text
procedure_run: verified_skill_distill_v1
```

Prefer extending existing `procedure_run`. Do not add a seventh public semantic tool unless later evidence proves a genuinely new consequence class.

### 2. Skill source provenance

A repository-derived skill should be bound to an exact source baseline. Research the minimum CAP-owned record containing at least:

```text
skill_id
skill_version
source_kind
source_identity
source_commit_or_tag
source_digest / evidence digest where justified
evidence_set
verified_cases
unverified_boundaries
generated_from
supersedes
refresh_required_when
status
```

For GitHub sources record the exact commit/tag and concrete source/docs/tests/examples used. Record what was actually executed versus only inspected.

### 3. Verification gate for skills

Do not treat a plausible `SKILL.md` as verified.

Adapt these mechanics behind CAP-owned Verification Kernel / Finish Gate:

- assertion-backed usability cases;
- content/self-consistency review against source scope;
- representative safe native repo examples/tests/CLI/import checks when feasible;
- adversarial/troubleshooting cases where consequence-relevant;
- static checks for broken references, missing helpers, provenance, local-path/secret leakage and skill-package shape;
- explicit unresolved backend/hardware limits rather than converting them into PASS;
- final verified/not-verified result with residual gaps.

Generated tests/reports are evidence, not runtime operating instructions.

### 4. Separate runtime skill from verification artifacts

Keep the live skill compact:

```text
SKILL.md
references/
scripts/       # only helpers actually needed at runtime
```

Keep usability cases, evals, verification reports, source audits, human-review notes and publication/install evidence outside the runtime skill tree under the existing CAP evidence/project structure.

### 5. Refresh / staleness lifecycle

A verified skill is not timeless. Research a bounded state model such as:

```text
CANDIDATE
VERIFIED
STALE
REJECTED
```

Potential refresh triggers:

- upstream source commit/API/config/CLI changed materially;
- referenced files or native tests changed;
- runtime/package version crosses a recorded compatibility boundary;
- previously verified helper no longer passes;
- observed real-task failure contradicts skill guidance.

Refresh should preserve still-grounded guidance, update stale claims/provenance, rerun the applicable verification set, and only then restore `VERIFIED`.

### 6. Progressive routing — defer until scale requires it

AREX progressively routes area -> family -> repository -> sub-skill so large skill libraries do not fill model context.

CAP should borrow this only when the number of live skills makes flat discovery measurably costly or ambiguous. Do **not** build a large taxonomy/router framework for the current handful of project skills.

If/when scale justifies routing, requirements should include:

- progressive disclosure;
- smallest useful skill set;
- no forced match;
- explicit scope/role metadata;
- structured metadata as the source for generated router/index views rather than hand-maintained prose where scale justifies it.

## What CAP should NOT take by default

Do not silently adopt:

- DisCo/Pi coding-agent runtime as a second general planner;
- DisCo session/host authority in place of CAP Control Plane;
- its package manager as a new project-wide owner without a real CAP consumer;
- its 5,000+ ML skill library as an automatically trusted dependency;
- its Creator/Researcher role model as a replacement for CAP manager/worker/session boundaries;
- a large taxonomy/router before real skill-count pressure exists.

Ordinary ChatGPT remains CAP's only current general planning layer. Verification, consequence authority, WorkingState, Finish Gate and the accepted six-tool public surface remain CAP-owned.

## Intended CAP flow to research for 26.4

```text
GitHub repo / docs / paper / successful human-demonstrated procedure
        ↓
resolve exact source identity
        ↓
scope capability
        ↓
collect grounded evidence
        ↓
generate candidate skill
        ↓
SKILL.md + references/ + optional runtime scripts/
        ↓
provenance + lineage record
        ↓
usability/native/adversarial verification
        ↓
Verification Kernel
        ↓
independent Finish Gate
        ↓
VERIFIED_CANDIDATE
        ↓
human approval / bounded install
        ↓
live skill
```

Longer-term behavior to enable:

> Prefer an existing current verified skill. If none covers the task, propose a bounded distillation/refresh workflow instead of relearning the same repository from scratch every time.

## Reuse existing CAP mechanisms before inventing new ones

- `.agents/skills/*/SKILL.md` remains the current skill packaging convention unless Stage Research proves an extension is needed.
- `stage-research` and `source-code-research` already provide exact-ref/source-evidence discipline and should feed distillation rather than be duplicated.
- Verification Kernel / Finish Gate should own verification semantics where applicable.
- `procedure_run` is the preferred public entry surface for a bounded distillation/refresh procedure.
- accepted evidence/provenance patterns should be reused rather than creating a parallel trust system.

## When to do it

### Now

- Keep this plan parked.
- Do not move PR #149 HEAD for this work.
- Do not add this architecture to the current Agent Session acceptance slice.

### Re-entry point

Begin actual Stage Research when the roadmap reaches Stage 26.4 after the preceding accepted sequence remains satisfied:

1. bounded Agent Session / Delegation accepted;
2. automatic reviewer migration accepted;
3. broad real-application physical coverage gate accepted;
4. bounded OpenAdapt integration spike completed/decided;
5. then begin 26.4 Human Demo -> verified candidate skill / skill lineage.

## Questions Stage Research must answer before implementation

1. What exact artifact owns skill identity, provenance and lineage?
2. What makes a skill `VERIFIED` rather than only `CANDIDATE`?
3. Which checks are deterministic CAP verification versus model semantic review?
4. How is source drift detected without introducing an always-on update service prematurely?
5. What evidence invalidates a previously verified skill?
6. How does a real-task failure feed refresh/repair without allowing self-modifying unreviewed skills?
7. What install/overwrite authority is required?
8. How are runtime skill bytes separated from check-only evidence?
9. What is the minimal first consumer from the 26.4 Human Demo?
10. At what actual skill count/context cost does progressive routing become justified?
11. Which AREX mechanics are reusable independently of DisCo's own runtime/trust model?
12. What failure/crash/partial-install matrix is required if install/replacement becomes consequence-bearing?

## Initial acceptance target

Prefer one narrow end-to-end proof, not a general skill marketplace:

```text
one demonstrated/repository-backed capability
 -> one candidate skill
 -> exact source provenance
 -> assertion-backed verification
 -> at least one real/native check where feasible
 -> explicit residual gaps
 -> independent Finish Gate
 -> human-approved install
 -> fresh task uses the installed skill successfully
 -> provenance/lineage readback remains exact
```

Defer bulk auto-generation, 5,000-skill catalogs, automatic global routing and autonomous self-install until real consumers justify them.

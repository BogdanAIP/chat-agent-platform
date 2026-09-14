# Verified Skill Distillation + Skill Lineage — parked Stage 26.4 plan

Status: **PARKED — architecture/research input for PR #151; not part of the accepted #149 scope**

This note records the AREX/DisCo mechanics that are candidates for adaptation into Chat Agent Platform so the idea is preserved together with the broader composition-first architecture.

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

## Additional external reference — Microsoft Skill Recorder

Secondary reference candidate:

- repository: `microsoft/skill-recorder`
- inspected `main` baseline on 2026-09-14: `d22be1a66b250c663dde3bf202b04514ba82134c`
- license: MIT
- CAP disposition: **REFERENCE_ONLY / REUSE_CANDIDATE / ADAPT_MECHANIC** by default

Skill Recorder is materially relevant to the Stage 26.4 Human Demo -> verified candidate skill path because it does not merely record coordinates for later replay. Its current flow is:

```text
human demonstration
 -> local capture of screen/activity + optional narration
 -> Copilot analysis
 -> reconstructed intent + ordered steps
 -> reviewed analysis
 -> generated SKILL.md and/or Automation
```

The generated procedure is intended to generalize from the demonstrated run and prefers agent-native tools such as CLI/API-style tools over reproducing raw UI clicks when those tools are available.

This makes Skill Recorder a distinct reuse candidate from a pure demonstration-replay substrate:

```text
OpenAdapt candidate role:
capture -> compile/program graph -> replay/checkpoint mechanics

Skill Recorder candidate role:
capture -> infer intent/steps -> generalize -> skill/automation artifact
```

Do not assume either product owns the complete CAP path. Fresh Stage Research should compare whether CAP can reuse one or both layers behind CAP-owned provenance, verification, consequence authority and Finish Gate.

### CAP adaptation hypothesis

A desirable provider-neutral CAP flow to research is:

```text
human demonstrates one task
        ↓
qualified capture substrate
        ↓
intent / ordered-step reconstruction
        ↓
tool-generalized candidate procedure
        ↓
CAP skill packaging
        ↓
source/demo provenance + lineage
        ↓
CAP Verification Kernel
        ↓
independent Finish Gate
        ↓
VERIFIED_CANDIDATE
        ↓
human-approved install
```

The architectural value is the **demonstration -> generalized skill** transformation, not dependence on Copilot itself. CAP should investigate whether the mechanics can be reused, adapted or reimplemented behind a provider-neutral boundary so the resulting skill can later be executed by whatever qualified provider owns the required CLI/API/browser/desktop mechanics.

Do not silently make GitHub Copilot, Microsoft Scout or any Microsoft-hosted analysis service a mandatory CAP runtime dependency.

### Privacy / trust boundary note

At the inspected baseline, recording/storage/frame extraction and optional narration transcription happen locally. When the user explicitly chooses Analyze, event timeline data, window/document titles, URLs, clipboard previews, extracted screen images and narration text are sent to GitHub cloud for Copilot processing.

Therefore any CAP adoption must separately research:

- explicit user consent before remote analysis;
- secret/credential redaction or hard capture exclusions;
- whether a fully local or user-selected analysis provider is possible;
- provenance for which model/provider transformed a demonstration into a candidate skill;
- separation between capture evidence and installed runtime skill bytes;
- whether sensitive screenshots/clipboard evidence can be discarded after verification;
- offline/degraded behavior when the cloud analysis provider is unavailable.

### Stage Research questions added for Skill Recorder

Before implementation, inspect the exact source release/current source and answer:

1. Which capture, describer and builder components can be reused independently of Copilot-specific product wiring?
2. What is the precise generated `SKILL.md` contract and how much of the generalization logic lives in prompts versus deterministic code?
3. Can output be redirected into CAP's existing `.agents/skills/*/SKILL.md` packaging without adopting a second skill authority?
4. How does the builder decide to replace demonstrated UI actions with native CLI/API tools, and how is that mapping verified?
5. What evals currently measure describer and builder generalization, and which of them can become CAP evidence?
6. Can capture be composed with OpenAdapt, WinApp CLI, BrowserProvider or another qualified substrate rather than creating a second overlapping recorder stack?
7. Can remote analysis be made provider-selectable or local without forking most of the product?
8. What Windows support and capture limitations matter for CAP's actual Windows target matrix?
9. What failure mode occurs when the inferred generalized procedure is plausible but semantically wrong, and how should CAP force it to remain `CANDIDATE` until independent verification succeeds?
10. Which upstream components are useful as maintained reuse dependencies versus reference-only implementation ideas?

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

- Keep this plan parked inside PR #151 with the rest of the post-#149 architecture.
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

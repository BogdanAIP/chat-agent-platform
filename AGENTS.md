# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

## Mandatory session bootstrap — resolve repository skills before planning

Every fresh development invocation, and every materially changed task within an existing session, must resolve repository skills **before proposing an implementation plan or editing production code**.

1. Resolve live `main`, the current branch/PR and their exact heads.
2. Enumerate `.agents/skills/*/SKILL.md` from the current repository ref instead of relying on remembered skill names.
3. Read the frontmatter and trigger of each plausibly applicable skill and select every skill whose trigger matches the actual task.
4. Load the selected skill(s) before planning the implementation.
5. If `stage-research` applies, production implementation remains blocked until its Stage Research Brief ends with `PROCEED`, `NARROW`, or `DEFER`; only `PROCEED` or `NARROW` opens implementation, while `DEFER` keeps it blocked.
6. Never rely on remembered or cached skill text. Bind the decision to the skill path and the current source ref/head, so an updated skill is picked up automatically after merge/rebase.
7. Re-run this bootstrap when `main` advances, the working branch is rebased, a new roadmap stage/substage starts, or the task materially changes scope.
8. If implementation, tests or review introduce a materially new architecture primitive or materially change persistence, recovery, retry, concurrency, identity or authority semantics, treat the prior Stage Research Brief as invalid and re-enter the applicable research skill before continuing production implementation.

For release-critical work, fail closed if an applicable mandatory skill cannot be read or its required pre-implementation output is missing or has been invalidated by a later material architecture change.

A merge does **not** autonomously start the next stage or launch background work. The next development invocation reruns this bootstrap against the new repository state; that is the automatic stage-transition behavior. Do not create a post-merge daemon, generic workflow engine, runtime `SkillGate`, new public tool or Control Plane authority merely to perform repository-skill discovery.

## Read first

Resolve live GitHub state first, then read only the current operating set:

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ROADMAP.md`
4. `project-context/PROJECT_RISKS.md`
5. `project-context/ARCHITECTURE.md` only when the task changes or depends on architecture

Read `project-context/ARCHITECTURE_REUSE_BASELINE.md` when `stage-research` applies or when work may duplicate, replace, or cross a previously selected external-component/project-owned role. Read `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs and historical Stage docs only when the current task actually needs them.

Current code/tests, exact PR heads, CI and required physical evidence outrank prose. Never infer live repository state from a recorded SHA in documentation.

## Development method

### 1. Design the product model ahead

The project may define the long-horizon product shape in advance: Files, Browser, Windows/Desktop, Vision, Procedures/Skills, Agent Sessions/Delegation, Connectors, Scheduled Tasks and other capability classes under one deterministic Control Plane / verification boundary.

Long-horizon architecture should establish durable boundaries and invariants such as:

- discovery is not authorization;
- environmental content is data, not policy authority;
- action/message delivery is not effect success;
- transition PASS is not task DONE;
- evidence is not a grant;
- WorkingState is structured operational state, never private chain-of-thought;
- ordinary ChatGPT is the only current general planner unless a later accepted decision explicitly changes that.

### 2. Research each concrete stage immediately before implementation

For every new release-critical stage/substage, major subsystem, new capability family, materially new recovery/security/authority architecture, **or material release-critical change to persistence ordering/ownership, retry/reconciliation semantics, concurrency, identity/correlation, or consequence-bearing authority**, invoke the repository skill `.agents/skills/stage-research/SKILL.md` before production implementation begins.

The skill is the canonical stage-research gate. Its Stage Research Brief must end with `PROCEED`, `NARROW`, or `DEFER`. `PROCEED` and `NARROW` may open implementation; `DEFER` does not. Do not bypass the gate merely because an older ADR already contains an implementation design or because the change occurs inside an existing subsystem.

At minimum, stage research must:

1. inspect the current repository/runtime and actual failure/evidence history;
2. research current strong public approaches relevant to that exact stage;
3. identify every architecture primitive the proposed solution introduces or materially relies on and research the mature engineering domain that studies that primitive directly;
4. investigate known limitations, issue reports, postmortems and operational failure modes of those approaches and primitives;
5. separate evidence that the problem exists from evidence that the proposed mechanism is an appropriate solution;
6. compare materially distinct architecture approaches rather than variants of one favored design;
7. for persistence/recovery/side-effect/concurrency/authority changes, build a failure/crash matrix covering the consequence-bearing boundaries before code;
8. identify why failures happen, how others mitigated them, and how this project can avoid repeating them;
9. compare the research with `project-context/ARCHITECTURE_REUSE_BASELINE.md`, existing future ADRs and project constraints; for every affected prior role record `KEEP`, `REUSE_MORE`, `REFINE`, `REPLACE`, `DEFER`, or `REJECT` rather than silently redesigning it;
10. keep, revise or reject previously proposed implementation details;
11. define the smallest stage architecture that solves the current problem without weakening required guarantees;
12. define focused/adversarial/independent/physical acceptance evidence before implementation.

`ARCHITECTURE_REUSE_BASELINE.md` is the canonical prior-decision comparison baseline, not immutable implementation authority. It exists so new research explicitly checks whether custom code duplicates an already selected upstream mechanism and whether a new external component crosses a boundary intentionally kept project-owned. `REPLACE` or `REJECT` of a prior baseline role requires explicit evidence, and an accepted lineage change must update the baseline before or with merge.

A role-level lineage `DEFER` is not permission to continue past an unresolved requirement. It is valid only for a role explicitly outside the selected implementation scope; if the role is required for the current stage goal or release-critical guarantee, the Stage Research Brief must narrow that goal to exclude the role or return top-level `DEFER` and keep implementation blocked.

`NARROW` narrows implementation scope only; it does not reduce research depth for a release-critical mechanism.

If a materially new architecture primitive or materially different persistence/recovery/retry/concurrency/identity/authority design appears after the Stage Research Brief, the previous research decision is no longer sufficient implementation authority. Re-enter `stage-research`, research the newly relevant engineering domain/failure class, revise the alternatives and failure/crash matrix where applicable, and issue a fresh decision. Resume production implementation only if that fresh decision is `PROCEED` or `NARROW`; `DEFER` keeps implementation stopped. Merely editing the PR body to describe the new design does not satisfy this requirement.

Future ADRs are architectural hypotheses plus boundary constraints, not immutable implementation specifications. A future ADR must not force the project to implement stale fields, APIs, event families or abstractions when current evidence supports a simpler design.

Do not skip stage research merely because a future architecture document already exists.

Narrow bug fixes, dependency bumps, isolated regressions and documentation-only corrections do not require the full skill unless they materially alter architecture, authority or a release-critical guarantee.

## Complexity policy

Before adding a new framework, workflow, ADR, state type, gate, taxonomy or documentation owner, answer:

1. Is this a new product guarantee/capability, or infrastructure around an existing one?
2. Can the requirement be expressed through an existing mechanism?
3. What existing complexity will this replace, consolidate or make unnecessary?

Prefer extending an existing assurance/runtime mechanism over creating one mechanism per Stage/CAP/guarantee family.

Test observable invariants and real behavior where practical. Avoid source-text/order assertions when the same guarantee can be proven through execution or instrumentation.

Historical Stage/CAP/PR lineage belongs primarily in Git history and `EVIDENCE_INDEX.md`; the current architecture should be explained by the system's present form rather than the order in which it was built. `ARCHITECTURE_REUSE_BASELINE.md` is the narrow exception for selected component/project-owned role lineage because future research must know which prior reuse decision it is keeping or changing.

## Current semantic boundary

The accepted Chat-facing surface remains exactly six tools unless a separately reviewed/accepted change widens it:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal path:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical semantic projection
 -> deterministic Control Plane / focused capabilities
```

1MCP remains optional internal Extension Manager infrastructure, not normal-route authority.

## Computer-use / completion invariants

For mutating execution, preserve the state-first verified loop:

```text
observe
 -> bind ExpectedEffect / operation identity
 -> authorize one bounded action
 -> act
 -> fresh re-observation
 -> verify PASS | FAIL | UNKNOWN
 -> reconcile ambiguous outcome before retry
 -> bounded recovery / LoopGuard / budgets
 -> independent Finish Gate
```

Do not weaken:

- fail-closed behavior on stale/ambiguous/UNKNOWN evidence;
- independent final-state/history verification for consequence-bearing tasks;
- source/runtime provenance when qualification depends on exact executed bytes;
- separation of planner intent, deterministic authorization, effect verification and task completion.

## Merge policy

For material production/runtime/security/recovery/authority/acceptance changes, **independent semantic review is required** before merge. Material changes to the repository's own merge/review policy are also review-significant once this policy is accepted.

Primary review is a fresh ordinary ChatGPT context using `.agents/skills/code-review/SKILL.md`, bound to the exact `BASE_SHA..HEAD_SHA`. It is an assurance layer, not another implementation/planning workspace.

Use this order:

```text
stage-research skill when required by the change class
 -> implementation
 -> focused tests
 -> preliminary required hosted CI on the intended head
 -> freeze BASE_SHA + HEAD_SHA
 -> required fresh ordinary ChatGPT semantic review via code-review skill
 -> optional @codex review when available
 -> validate every reported finding as CONFIRMED / REJECTED / SUPERSEDED
 -> fix confirmed findings
 -> any material post-review change makes the prior review stale
 -> fresh required ChatGPT review on the new exact head
 -> optional fresh @codex review when available
 -> final exact-head CI / required physical acceptance
 -> verify reviewed BASE_SHA + HEAD_SHA still match the PR
 -> merge
```

The mandatory primary reviewer must run in a separate fresh ordinary-ChatGPT conversation/context and reconstruct evidence from the repository. Do not use ChatGPT Work, Workspace Agents, Codex automation or Codex Review as a substitute for this required review. A one-time ChatGPT Scheduled Task may launch the review only when it can truthfully satisfy the fresh ordinary-ChatGPT context contract in `code-review`; otherwise use a manually opened fresh ordinary-ChatGPT conversation.

Codex Review is an optional additional reviewer. Use it when quota is available because its independent findings remain valuable, but Codex quota exhaustion does not block merge when the required fresh ChatGPT review, finding validation and all other applicable gates pass. State Codex unavailability explicitly; never represent an unavailable Codex review as completed.

A reported finding is a review result, not automatically project truth. Validate it against code/tests/evidence before fixing. Do not merge with unresolved reported findings.

The review result is valid only for the exact reviewed identity. A material post-review change to runtime, security, recovery/retry, concurrency/identity, verification/acceptance semantics, acceptance tests/gates or merge/review policy invalidates the old review. A base change likewise requires a fresh exact-base review. Clearly non-material spelling/formatting-only deltas may preserve review validity only after explicit inspection; when uncertain, review again.

Do not auto-merge while active hardening/review changes are still being made. Final exact-head CI and any required physical gate run after the final material review/fix cycle.

Documentation-only PRs that do not materially alter process/security/acceptance/runtime semantics should not be forced through the independent semantic-review or physical gates. Process PRs that materially change merge/review semantics are review-significant, but the PR that first introduces this policy is adopted under the previously accepted merge policy; the new policy governs subsequent PRs after merge.

## PR/document discipline

Keep live documentation small and role-specific:

- `CURRENT_STATE.md` = current accepted boundary and immediate work;
- `ROADMAP.md` = release order;
- `PROJECT_RISKS.md` = ranked risks;
- `ARCHITECTURE_REUSE_BASELINE.md` = selected external-component/project-owned role lineage for Stage Research comparison, not runtime status;
- `EVIDENCE_INDEX.md` = exact accepted evidence/SHAs/locators;
- `TECH_DEBT.md` = existing compromises with close conditions;
- architecture docs = durable boundaries and current/future design hypotheses.

Do not duplicate exact SHA snapshots, active PR state or large physical evidence blocks across multiple live documents.

When a branch is logically complete, intended diff is reviewed, required checks/evidence pass on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.

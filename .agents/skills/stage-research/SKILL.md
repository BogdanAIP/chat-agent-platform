---
name: stage-research
description: Research and design gate for starting a new release-critical stage, substage, major subsystem, capability family, or materially new recovery/security/authority architecture. Use before implementation begins. Do not use for narrow bug fixes, dependency bumps, or documentation-only edits unless they materially change architecture or authority.
compatibility: Designed for Chat Agent Platform work with repository access and current web research.
metadata:
  version: "1.1"
  project: "chat-agent-platform"
---

# Stage Research

Use this skill before implementation of a new release-critical stage/substage, a major subsystem, a new capability family, or a materially new recovery/security/authority mechanism.

The repository-wide session bootstrap in `AGENTS.md` resolves applicable `.agents/skills/*/SKILL.md` before planning. Do not depend on chat memory or a previously read copy of this skill; use the current repository ref so merged skill changes are picked up automatically on the next development invocation.

The goal is not to produce a research document for its own sake. The goal is to make the next implementation decision from current evidence while preserving the long-horizon product model and avoiding both weak minimalism and unnecessary infrastructure.

## Trigger

Activate when work starts on one of these:

- a new roadmap stage or substage;
- a major new runtime subsystem;
- a new capability family or cross-capability abstraction;
- a material change to recovery, verification, security or authority boundaries;
- implementation of a future ADR that has not yet been validated against current code and current external practice.

Do not require this gate for a narrow bug fix, mechanical dependency update, isolated regression, or documentation-only correction unless the change materially alters architecture, authority, or a release-critical guarantee.

## Hard rules

Do not start production implementation merely because an older ADR already describes the subsystem.

A future ADR is an input: durable boundary constraints may remain authoritative, while implementation details are revisable hypotheses.

Before implementation, produce a Stage Research Brief with a decision of `PROCEED`, `NARROW`, or `DEFER`.

`NARROW` means a narrower **implementation scope**, not a lower research standard. A release-critical mechanism receives the same depth of mechanism/failure research whether it has one consumer or many.

A material architecture change after the Brief invalidates the previous research decision. Production implementation is blocked again until the changed mechanism and its adjacent engineering domain are researched and the Brief is revised.

## 1. Resolve current project truth

Before external research:

1. resolve live `main`, relevant open PRs and exact heads;
2. inspect the current implementation that the stage will extend;
3. read the minimal current owner documents (`CURRENT_STATE.md`, `ROADMAP.md`, `PROJECT_RISKS.md`, and architecture/security/evidence only as needed);
4. inspect relevant tests, accepted physical evidence, review findings and actual failure history;
5. identify existing mechanisms that may already solve part of the stage.

Do not infer current state from historical Stage prose or recorded SHAs in stale documents.

## 2. Define the exact stage question

State explicitly:

- user/product outcome the stage must enable;
- durable invariants that must not be weakened;
- concrete failure modes already observed in this project;
- scope that belongs to this stage;
- tempting adjacent work that is explicitly out of scope.

Keep the long-horizon product model in view: this project is not only a Browser agent. Files, Browser, Windows/Desktop, Vision, Procedures/Skills, Agent Sessions/Delegation, Connectors, Scheduled Tasks and future capability classes should remain able to fit one coherent Control Plane/trust model.

## 3. Research Scope Expansion Gate

Before choosing an architecture, list every **architecture primitive/mechanism** the proposed solution would introduce or materially rely on, even when it sounds implementation-local. Examples include write-ahead markers, journals/WAL, leases, idempotency keys, durable checkpoints, caches, locks, reconciliation loops, generation tokens, capability grants, retry ledgers, event logs and transactional outboxes.

For each primitive:

1. name the mature engineering domain that studies the mechanism directly;
2. identify the guarantees the mechanism is supposed to provide here;
3. identify its assumptions and known failure boundaries;
4. research primary/strong sources from that engineering domain, not only sources describing the original product problem;
5. record adjacent domains that become relevant because of the mechanism, such as filesystem durability, distributed-systems consistency, concurrency control, identity/ABA safety, transaction processing or controller reconciliation.

Do not infer solution validity from problem evidence. For example, evidence that retries can duplicate side effects does not by itself prove that a particular write-ahead protocol is correct.

If a new architecture primitive appears during implementation, testing or review and that primitive was not covered by the current Brief, stop production changes and rerun this gate before continuing.

## 4. Research current strong approaches

Research current public primary sources for the exact stage problem **and for each architecture primitive identified by the Scope Expansion Gate**. Prefer, in order:

1. current official documentation and source code of relevant systems;
2. recent papers / technical reports / benchmark analyses;
3. maintainers' design notes, release notes and engineering posts;
4. real issue trackers, discussions, postmortems and user reports for failure evidence.

For each serious approach, determine:

- what it does;
- why the authors chose it;
- what guarantee or failure mode it addresses;
- what assumptions it depends on;
- what maturity/evidence supports it.

Do not copy a pattern merely because a well-known system uses it.

## 5. Research failures, not only success stories

For every candidate approach and every proposed architecture primitive, actively search for problems encountered in practice.

Look for:

- documented limitations and unsupported cases;
- issue tracker reports and maintainer discussions;
- postmortems and regressions;
- flaky or timing-sensitive behavior;
- stale-state / TOCTOU / duplicate-effect failures;
- restart and crash-recovery problems;
- identity/correlation mistakes and ABA-style reuse;
- concurrent writer/resume races;
- state/context growth and persistence costs;
- latency, compute and operational costs;
- security/authority leakage;
- abstractions that became difficult to maintain or were later removed/simplified.

For each relevant problem record:

- symptom;
- root cause when known;
- consequence;
- workaround or fix used by others;
- whether the fix is proven or still incomplete;
- how this project can avoid repeating the problem before implementation.

Community reports are useful failure evidence but are not by themselves authoritative architecture guidance. Cross-check important claims where possible.

## 6. Separate problem evidence from solution evidence

The Brief must contain two distinct evidence blocks:

### Problem evidence
Evidence that the failure/limitation actually exists or is a credible analogous risk for this project.

### Solution evidence
Evidence that the **specific proposed mechanism** is appropriate for the required guarantee under our persistence, concurrency, restart, identity and authority assumptions.

A mechanism cannot become `must have now` merely because the problem is real. If direct solution evidence is weak, either research further, choose a better-supported mechanism, narrow the guarantee, or return `DEFER`.

## 7. Compare materially distinct approaches

For a release-critical new recovery/security/authority mechanism, compare at least **three materially distinct architecture approaches** when three credible alternatives exist. Do not satisfy this requirement with naming variants of the same design. If fewer than three credible approaches exist, explicitly justify why.

The comparison must contain at least:

- approach/mechanism;
- problem it solves;
- core state/authority owner;
- persistence and crash boundary;
- concurrency/identity model where relevant;
- strengths;
- known failure modes / operational problems;
- complexity and ongoing maintenance cost;
- evidence/maturity;
- fit with Chat Agent Platform.

Prefer understanding mechanisms over ranking products.

## 8. Map external lessons to this repository

For each important mechanism or failure case ask:

1. Do we already have this failure mode, or a credible analogous risk?
2. Has our own physical qualification/review history already exposed it?
3. Does an existing project mechanism already address it?
4. Can we avoid the known external problem structurally before adopting the mechanism?
5. Can the same guarantee be achieved more simply inside our current architecture?
6. Would adopting it create a new framework, workflow, state owner, gate, taxonomy or document that we then have to maintain?

Distinguish:

- **must have now** — required for correctness/security/release acceptance;
- **useful now** — worthwhile and justified by current evidence;
- **defer** — plausible future need without a current consumer or failure mode;
- **reject** — conflicts with project boundaries or adds more cost than guarantee.

## 9. Failure/Crash Matrix Gate

When the stage changes persistence, restart/recovery, side effects, concurrency or consequence-bearing authority, build a failure matrix **before production implementation**.

Cover every boundary that can change the answer to "did the effect happen and may we act again?". At minimum, when applicable, examine:

- before durable intent/state;
- after durable intent but before delivery;
- during delivery / partial external effect;
- after external effect but before durable outcome;
- after durable outcome but before receipt/node advancement;
- during checkpoint/journal replacement or persistence failure;
- restart/load/reconciliation;
- stale or ambiguous observation after restart;
- concurrent resume / duplicate worker / duplicate caller;
- identity replacement or ABA-style state reuse;
- compensation/rollback while an earlier outcome is unresolved.

For each cell record:

- authoritative durable state;
- possible physical state;
- what fresh evidence is required;
- whether retry is allowed, blocked or requires reconciliation;
- maximum additional physical effects permitted;
- invariant/test that proves the rule.

If any release-critical cell is answered with "unknown", the implementation decision cannot be `PROCEED` or `NARROW` yet.

## 10. Choose the minimum sufficient architecture

Use best practices to set the quality bar, but implement only the mechanisms needed for the current stage and long-horizon compatibility.

Avoid weak minimalism such as replacing a real recovery problem with an arbitrary retry counter.

Also avoid overengineering such as introducing registries, buses, plugin frameworks, services or persistence layers when a few typed data structures and deterministic functions provide the same guarantee.

Before adding any new abstraction answer:

- Which concrete current requirement needs it?
- Which second current or near-term consumer makes it genuinely common, if applicable?
- What existing complexity does it replace or consolidate?
- What is the simplest design that keeps the durable product boundary intact?

The "second consumer" question is evidence, not an absolute rule. A common product primitive may be justified earlier when the multi-capability product model itself clearly requires it; its detailed API should still stay minimal until real consumers constrain it.

## 11. Define failure shields before code

For every must-have mechanism, identify the failure it must prevent and the observable invariant that proves protection.

Prefer behavioral/instrumented verification over source-text/order assertions when practical.

Map important guarantees to existing assurance families where they already exist. Do not create a new test framework/workflow/document owner merely because a new guarantee ID is added.

## 12. Define the acceptance ladder

Choose only the evidence required for this stage:

- focused unit/state-machine tests;
- integration tests;
- adversarial/fault-injection tests;
- hosted CI/security checks;
- independent review;
- physical target-machine / ordinary-Chat acceptance only when the changed consequence boundary requires it.

State what would falsify the design and force reconsideration.

## 13. Produce the Stage Research Brief

Before production implementation, summarize:

### Stage goal
What concrete product/runtime outcome is being added.

### Current project baseline
Existing mechanisms, constraints and relevant observed failures.

### Architecture primitives and adjacent domains
Every proposed primitive/mechanism, the engineering domain that directly studies it, assumptions and relevant adjacent domains.

### Problem evidence
Why the problem/failure is real or credibly analogous here.

### Solution evidence
Why the proposed mechanism is appropriate for the required guarantee under this repository's assumptions.

### Best current approaches
The strongest materially distinct mechanisms and why they exist.

### Failure lessons
Problems others encountered, root causes, attempted fixes and how we plan to avoid them.

### Alternatives comparison
At least three materially distinct approaches when available, or an explicit justification for fewer.

### Failure/Crash Matrix
Required for persistence/recovery/side-effect/concurrency/authority changes; include all applicable boundaries from section 9.

### Fit to this architecture
What applies directly, what does not, and why.

### Architecture decision
- `PROCEED`, `NARROW`, or `DEFER`;
- must-have mechanisms now;
- mechanisms explicitly deferred/rejected;
- existing components to reuse/consolidate;
- durable invariants preserved.

### Verification plan
Focused, adversarial, independent-review and physical acceptance requirements.

### Complexity budget
New abstractions/workflows/docs being added and what existing complexity they replace. If the answer is "adds infrastructure but replaces nothing", justify why it is still necessary.

Do not create a standalone research Markdown file by default. Put the brief in the first implementation PR body or update an existing authoritative stage/architecture owner only when the result needs durable architectural persistence.

## 14. Design-change invalidation and re-entry

After the Brief, continuously compare actual implementation against the researched mechanism set.

The current Stage Research Brief becomes **invalid for implementation authority** when any of the following occurs:

- a new architecture primitive is introduced;
- persistence ownership/order changes materially;
- retry/reconciliation/identity/concurrency semantics change materially;
- a new consequence boundary or authority source is added;
- tests or review reveal a failure class not covered by the existing matrix;
- the chosen approach changes enough that its solution evidence no longer applies.

When invalidated:

1. stop production implementation at the smallest safe boundary;
2. update the architecture-primitive/domain map;
3. research the newly relevant domain/failure mode;
4. revise alternatives and the failure matrix as needed;
5. replace the old `PROCEED`/`NARROW`/`DEFER` decision with a fresh decision;
6. only then resume production implementation.

A PR-body edit that merely restates the new design without this re-entry work does not satisfy the gate.

## 15. Implementation handoff

Only after the current Stage Research Brief is complete and not invalidated:

1. implement the smallest coherent slice;
2. reuse existing runtime/assurance/CI mechanisms;
3. add the failure shields identified above;
4. run focused tests and required hosted checks;
5. obtain Codex Review / equivalent independent review for runtime/security/recovery/authority changes when available/required;
6. fix findings and repeat review after material changes when appropriate;
7. if a material architecture change occurs, return to section 14 before continuing;
8. run final exact-head CI and required physical acceptance;
9. merge only when the exact final head has the required evidence.

## Final quality check

Before declaring the research gate complete, verify all are true:

- research included current external approaches and current repository reality;
- every proposed architecture primitive was mapped to its directly relevant engineering domain;
- problem evidence and solution evidence are separate and both sufficient;
- failure reports/limitations were actively investigated, not omitted;
- materially distinct alternatives were compared when available;
- the required failure/crash matrix has no release-critical unknown cell;
- known external problems have an explicit avoidance/mitigation decision;
- best practices were not copied without explaining their purpose;
- the chosen design is not weaker than required for the guarantee;
- `NARROW` reduced implementation scope, not research depth;
- the chosen design does not introduce broad future infrastructure without current justification;
- future ADR details were allowed to change when current evidence justified it;
- no material architecture primitive/change appeared after the current Brief without re-entering research;
- acceptance criteria can actually falsify a bad implementation;
- the implementation can start from a concise decision rather than a new documentation bureaucracy.

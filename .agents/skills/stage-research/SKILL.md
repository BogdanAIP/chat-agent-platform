---
name: stage-research
description: Research and design gate for starting a new release-critical stage, substage, major subsystem, capability family, or materially new recovery/security/authority architecture. Use before implementation begins. Do not use for narrow bug fixes, dependency bumps, or documentation-only edits unless they materially change architecture or authority.
compatibility: Designed for Chat Agent Platform work with repository access and current web research.
metadata:
  version: "1.0"
  project: "chat-agent-platform"
---

# Stage Research

Use this skill before implementation of a new release-critical stage/substage, a major subsystem, a new capability family, or a materially new recovery/security/authority mechanism.

The goal is not to produce a research document for its own sake. The goal is to make the next implementation decision from current evidence while preserving the long-horizon product model and avoiding both weak minimalism and unnecessary infrastructure.

## Trigger

Activate when work starts on one of these:

- a new roadmap stage or substage;
- a major new runtime subsystem;
- a new capability family or cross-capability abstraction;
- a material change to recovery, verification, security or authority boundaries;
- implementation of a future ADR that has not yet been validated against current code and current external practice.

Do not require this gate for a narrow bug fix, mechanical dependency update, isolated regression, or documentation-only correction unless the change materially alters architecture, authority, or a release-critical guarantee.

## Hard rule

Do not start production implementation merely because an older ADR already describes the subsystem.

A future ADR is an input: durable boundary constraints may remain authoritative, while implementation details are revisable hypotheses.

Before implementation, produce a Stage Research Brief with a decision of `PROCEED`, `NARROW`, or `DEFER`.

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

## 3. Research current strong approaches

Research current public primary sources for the exact stage problem. Prefer, in order:

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

## 4. Research failures, not only success stories

For every candidate approach, actively search for problems encountered in practice.

Look for:

- documented limitations and unsupported cases;
- issue tracker reports and maintainer discussions;
- postmortems and regressions;
- flaky or timing-sensitive behavior;
- stale-state / TOCTOU / duplicate-effect failures;
- restart and crash-recovery problems;
- identity/correlation mistakes;
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

## 5. Compare approaches

Build a compact comparison containing at least:

- approach/mechanism;
- problem it solves;
- strengths;
- known failure modes / operational problems;
- complexity and ongoing maintenance cost;
- evidence/maturity;
- fit with Chat Agent Platform.

Prefer understanding mechanisms over ranking products.

## 6. Map external lessons to this repository

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

## 7. Choose the minimum sufficient architecture

Use best practices to set the quality bar, but implement only the mechanisms needed for the current stage and long-horizon compatibility.

Avoid weak minimalism such as replacing a real recovery problem with an arbitrary retry counter.

Also avoid overengineering such as introducing registries, buses, plugin frameworks, services or persistence layers when a few typed data structures and deterministic functions provide the same guarantee.

Before adding any new abstraction answer:

- Which concrete current requirement needs it?
- Which second current or near-term consumer makes it genuinely common, if applicable?
- What existing complexity does it replace or consolidate?
- What is the simplest design that keeps the durable product boundary intact?

The "second consumer" question is evidence, not an absolute rule. A common product primitive may be justified earlier when the multi-capability product model itself clearly requires it; its detailed API should still stay minimal until real consumers constrain it.

## 8. Define failure shields before code

For every must-have mechanism, identify the failure it must prevent and the observable invariant that proves protection.

Prefer behavioral/instrumented verification over source-text/order assertions when practical.

Map important guarantees to existing assurance families where they already exist. Do not create a new test framework/workflow/document owner merely because a new guarantee ID is added.

## 9. Define the acceptance ladder

Choose only the evidence required for this stage:

- focused unit/state-machine tests;
- integration tests;
- adversarial/fault-injection tests;
- hosted CI/security checks;
- independent review;
- physical target-machine / ordinary-Chat acceptance only when the changed consequence boundary requires it.

State what would falsify the design and force reconsideration.

## 10. Produce the Stage Research Brief

Before production implementation, summarize:

### Stage goal
What concrete product/runtime outcome is being added.

### Current project baseline
Existing mechanisms, constraints and relevant observed failures.

### Best current approaches
The strongest relevant mechanisms and why they exist.

### Failure lessons
Problems others encountered, root causes, attempted fixes and how we plan to avoid them.

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

## 11. Implementation handoff

Only after the Stage Research Brief is complete:

1. implement the smallest coherent slice;
2. reuse existing runtime/assurance/CI mechanisms;
3. add the failure shields identified above;
4. run focused tests and required hosted checks;
5. obtain Codex Review / equivalent independent review for runtime/security/recovery/authority changes when available/required;
6. fix findings and repeat review after material changes when appropriate;
7. run final exact-head CI and required physical acceptance;
8. merge only when the exact final head has the required evidence.

## Final quality check

Before declaring the research gate complete, verify all are true:

- research included current external approaches and current repository reality;
- failure reports/limitations were actively investigated, not omitted;
- known external problems have an explicit avoidance/mitigation decision;
- best practices were not copied without explaining their purpose;
- the chosen design is not weaker than required for the guarantee;
- the chosen design does not introduce broad future infrastructure without current justification;
- future ADR details were allowed to change when current evidence justified it;
- acceptance criteria can actually falsify a bad implementation;
- the implementation can start from a concise decision rather than a new documentation bureaucracy.

# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

## Read first

Resolve live GitHub state first, then read only the current operating set:

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ROADMAP.md`
4. `project-context/PROJECT_RISKS.md`
5. `project-context/ARCHITECTURE.md` only when the task changes or depends on architecture

Read `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs and historical Stage docs only when the current task actually needs them.

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

Before implementing a new release-critical subsystem or stage:

1. inspect the current repository/runtime and the actual failure history;
2. research current public approaches relevant to that exact stage;
3. compare the research with existing future ADRs and project constraints;
4. keep, revise or reject previously proposed implementation details;
5. define the smallest stage architecture that solves the current problem;
6. implement a minimal slice with the required tests and acceptance evidence.

Future ADRs are architectural hypotheses plus boundary constraints, not immutable implementation specifications. A future ADR must not force the project to implement stale fields, APIs, event families or abstractions when current evidence supports a simpler design.

Do not skip stage research merely because a future architecture document already exists.

## Complexity policy

Before adding a new framework, workflow, ADR, state type, gate, taxonomy or documentation owner, answer:

1. Is this a new product guarantee/capability, or infrastructure around an existing one?
2. Can the requirement be expressed through an existing mechanism?
3. What existing complexity will this replace, consolidate or make unnecessary?

Prefer extending an existing assurance/runtime mechanism over creating one mechanism per Stage/CAP/guarantee family.

Test observable invariants and real behavior where practical. Avoid source-text/order assertions when the same guarantee can be proven through execution or instrumentation.

Historical Stage/CAP/PR lineage belongs primarily in Git history and `EVIDENCE_INDEX.md`; the current architecture should be explained by the system's present form rather than the order in which it was built.

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

For runtime/security/recovery/authority changes, use this order:

```text
implementation
 -> focused tests
 -> required hosted CI on the exact head
 -> Codex Review / independent review when available and required by the change class
 -> fix findings
 -> repeat independent review after material fixes when appropriate
 -> final exact-head CI / required physical acceptance
 -> merge
```

Do not auto-merge while active hardening/review changes are still being made.

If Codex Review is unavailable, state that explicitly. Do not represent independent review as completed. Merge only when the repository's documented acceptance policy permits proceeding without it.

Documentation-only/process PRs should not be forced through physical gates unless they alter acceptance/runtime behavior.

## PR/document discipline

Keep live documentation small and role-specific:

- `CURRENT_STATE.md` = current accepted boundary and immediate work;
- `ROADMAP.md` = release order;
- `PROJECT_RISKS.md` = ranked risks;
- `EVIDENCE_INDEX.md` = exact accepted evidence/SHAs/locators;
- `TECH_DEBT.md` = existing compromises with close conditions;
- architecture docs = durable boundaries and current/future design hypotheses.

Do not duplicate exact SHA snapshots, active PR state or large physical evidence blocks across multiple live documents.

When a branch is logically complete, intended diff is reviewed, required checks/evidence pass on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.
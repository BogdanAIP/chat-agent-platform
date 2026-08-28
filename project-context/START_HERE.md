# Start Here — authoritative continuation guide

Use this file after resolving live GitHub state. Do not treat recorded prose as a substitute for live `main`, open PRs, exact heads, hosted checks or required physical evidence.

Before planning implementation, follow the mandatory session bootstrap in `AGENTS.md`: enumerate `.agents/skills/*/SKILL.md` from the current repository ref, resolve applicable skills, and load them before planning. This check is repeated after `main` advances or the task moves into a new stage/substage, so merged skill updates are picked up from current repository bytes rather than chat memory.

## Minimal read set

For ordinary continuation, read:

1. `CURRENT_STATE.md`
2. `ROADMAP.md`
3. `PROJECT_RISKS.md`
4. `ARCHITECTURE.md` only when the current task changes or depends on architecture

Read `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs and historical Stage documents only when the current task needs them.

The repository should not require a fresh agent to reconstruct the whole build history before continuing current work.

## Current boundary

Stage 26.3B is accepted/closed for its recorded representative scope. The current release-critical direction is Stage 26.3C: project-owned WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport.

Exact accepted heads and machine-local evidence locators belong in `EVIDENCE_INDEX.md`, not here.

The accepted Chat-facing surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical semantic projection
 -> deterministic Control Plane / focused capabilities
```

Ordinary ChatGPT is the only current general planner/intelligence. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions.

## Product model vs stage implementation

The project intentionally designs the **general product model** ahead: Files, Browser, Windows/Desktop, Vision, Procedures/Skills, Agent Sessions/Delegation, Connectors, Scheduled Tasks and other capability classes should fit one coherent product and trust model.

That does **not** mean future detailed APIs are implementation commitments.

When starting a new release-critical stage/substage, major subsystem, new capability family or materially new recovery/security/authority design, use `.agents/skills/stage-research/SKILL.md` before production implementation. The skill must produce a Stage Research Brief with `PROCEED`, `NARROW`, or `DEFER`.

The research gate explicitly includes both **best practices and failure lessons**: investigate what strong systems do, why they do it, what failure modes they address, what problems/limitations they encounter in practice, root causes and mitigations, and how this project can avoid repeating those failures.

Before implementing each concrete stage or subsystem:

```text
current repo/runtime audit
 -> stage-research skill
 -> current best practices + failure reports / postmortems / limitations
 -> compare with existing ADRs and constraints
 -> revise/reject stale future implementation details
 -> choose the minimum sufficient stage architecture
 -> implement minimal coherent slice
 -> adversarial/acceptance tests
 -> independent review
 -> exact-head acceptance
```

Future ADRs are design hypotheses plus durable boundary constraints. They are inputs to the stage research, not substitutes for it.

Do not implement a future `CapabilityRegistry`, `TypedEventBus`, `PolicyHooks`, Session API, Connector model or other broad abstraction merely because it is already described in a future architecture document. Introduce only the parts current evidence and current consumers require while preserving the long-horizon product boundaries.

## Complexity rule

When adding a framework, workflow, gate, ADR, state type or documentation owner, ask:

```text
Is this a new capability/guarantee?
Can an existing mechanism express it?
What old complexity will this replace or consolidate?
```

Avoid one new infrastructure layer per Stage/CAP/guarantee family. Historical Stage/PR lineage belongs primarily in Git history and `EVIDENCE_INDEX.md`.

Prefer behavioral/instrumented tests of invariants over source-text/order assertions when practical.

## Computer-use invariant

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery/reconciliation + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Mutating outcomes must distinguish safe retry from ambiguous delivery. `OUTCOME_UNKNOWN` is reconciled from fresh authoritative state before retry. Repeated physical attempts are bounded; identical blind retries are not an acceptable recovery strategy.

WorkingState stores structured operational state, never private chain-of-thought.

## Current Browser scope

The accepted Browser L3 path uses real target-Windows runtime/effects through isolated headless Playwright/Chrome. It does not by itself prove control of an already-open visible desktop Chrome session. Any visible/attached-browser claim requires its own acceptance definition and evidence.

## Future architecture

Track M / Agent Sessions, ADR-036 Browser Harness expansion and ADR-037 CapabilityRegistry/Event/Hook substrate remain future architecture. Read their dedicated documents only when the current task touches those areas.

Their durable authority boundaries remain useful; their detailed implementation shapes may be revised after focused stage research.

## Merge rule

For runtime/security/recovery/authority changes:

```text
stage-research skill when applicable
 -> implementation
 -> focused tests
 -> required hosted CI on exact head
 -> Codex Review / independent review when available and required
 -> fixes
 -> repeat review after material fixes when appropriate
 -> final exact-head CI / required physical acceptance
 -> merge
```

Do not auto-merge while active hardening/review changes are still being made. If independent review is unavailable, record that fact rather than representing the review as completed.

`AGENTS.md` owns the repository-wide development method. `CURRENT_STATE.md` owns the present accepted boundary. `ROADMAP.md` owns release order.
# Decisions

Historical ADR detail remains in Git history. This file lists decisions that govern current development.

A decision marked **PROVISIONAL** is the accepted architecture direction but is not product-accepted until its stated implementation/evidence gate passes.

## ADR-010 — Off-the-shelf MCP bridge — ACCEPTED

Use standard MCP and mature reachability/runtime components. Prefer official/vendor, mature OSS, mature generic adapter, then the smallest project-owned focused adapter for a measured gap.

## ADR-011 — OpenAI Secure MCP Tunnel is primary ChatGPT reachability — ACCEPTED

Accepted by real ordinary-Chat E2E. Historical custom/public ingress experiments are not the normal path.

## ADR-012 — Superseded universal core removed — ACCEPTED

The old universal agent/gateway platform is historical only. Recover specific pieces only for a later measured gap.

## ADR-013 — 1MCP is replaceable internal infrastructure — ACCEPTED

1MCP remains useful for diagnostics/adaptive lifecycle/aggregation. Stage 24.1 removed it from the normal semantic critical path because direct stdio was simpler/faster with equivalent tested behavior.

## ADR-014 — Privileged capabilities require scoped acceptance — ACCEPTED

Security controls scope/consequence/lifetime; it must not become blanket capability paralysis.

## ADR-015 — Thin Windows bootstrap/manager is integration code — ACCEPTED

Bootstrap/controller/tray may install, configure, start/stop and report health. It is not the general planner, procedure Control Plane, generic gateway/registry/vault or arbitrary authorization platform.

## ADR-016 — Generic adaptive meta-tool is not the ordinary-Chat surface — ACCEPTED NEGATIVE DECISION

Do not promote generic `tool_schema` / `tool_invoke` / arbitrary backend dispatch as the Chat-facing product contract.

## ADR-017 — AVAILABLE -> ACTIVE -> AUTHORIZED lifecycle — ACCEPTED

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Backend availability, process activation and action authorization are distinct.

## ADR-018 — Small concrete semantic Chat-facing surface — ACCEPTED

Current public tool names are:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Five is a current proven contract, not an eternal limit. Never preserve it by hiding unrelated consequences behind misleading schemas.

## ADR-019 — One authoritative Windows manager owner — ACCEPTED

Installed/source copies coordinate one authoritative runtime owner. Ambiguous/unowned shared runtime state fails closed.

## ADR-020 — Local specialist inference is a capability backend, not a planner — ACCEPTED

Accepted target vision uses llama.cpp + LFM2.5-VL-450M F16. Local models may perform bounded perception/extraction/grounding/classification, but model output is non-authorizing evidence. Heavy inference is task-driven/on-demand/unloadable.

## ADR-021 — Direct semantic stdio tunnel binding — ACCEPTED

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> secure launcher
 -> direct stdio semantic-projection
```

`semantic-projection` remains deterministic and does not become planner/lifecycle/workflow state.

## ADR-022 — Semantic-first same-session local vision — ACCEPTED

Structure/accessibility first. Reviewed visual fallback only after specific miss classes; VLM proposal is followed by deterministic authorization/freshness and one action or ABSTAIN.

## ADR-023 — Procedural memory + deterministic progression, not a second planner — PROVISIONAL

OpenAdapt Flow/Capture provide the qualified procedural substrate. The project boundary is now:

```text
successful trajectory / demonstration
 -> ProgramGraph / versioned candidate procedure
 -> ChatGPT decides applicability / goal / parameters
 -> deterministic local Control Plane loads selected procedure
 -> current state resolves one permitted transition
 -> capability authorization
 -> bounded action
 -> postcondition verification
 -> checkpoint / advance
 -> repeat while state remains known
 -> ABSTAIN/escalate when new strategy is needed
```

Rules:

- ordinary ChatGPT remains the only **current general planner/interpreter**;
- a procedure may drive multiple predeclared transitions without ChatGPT micromanaging every low-level step;
- procedure/model output never grants action authority;
- current state outranks remembered procedure;
- blind absolute-coordinate replay is never authority/primary identity;
- one success/demo creates at most a project CANDIDATE;
- completion requires verifier/effect evidence;
- private chain-of-thought is never persisted;
- raw desktop capture retention requires explicit privacy policy.

This ADR supersedes the older interpretation that procedures are only passive advice to ChatGPT.

## ADR-024 — Desktop capability and public-contract expansion are separate — ACCEPTED DIRECTION

The Windows desktop capability has now progressed through accepted Stage 26.2A-D. A public desktop/procedure tool surface still requires a separate ADR and ordinary-Chat acceptance. Do not overload `web_interact` or add opaque workflow dispatch merely to keep five tool names.

## ADR-025 — Reuse qualified OpenAdapt procedural core before replacements — ACCEPTED

Pinned target-tested sources:

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Adopt Flow `Workflow`/`ProgramGraph`; adapt lifecycle/versioning/trust mechanics; do not reimplement generic recorder/compiler/store without a measured blocker.

## ADR-026 — Windows agent/F16 qualification boundary — SUPERSEDED BY ACCEPTED 26.2A-D

The earlier A/B/provisional boundary has been resolved by target evidence:

- hardened typed executor accepted;
- production runtime promoted;
- exact-window DesktopState accepted;
- native F16 Grounder accepted proposal-only;
- deterministic structure-first Windows visual routing accepted for the bounded controlled-fixture contract.

Broad real-application acceptance remains Stage 26.2E rather than ADR-026.

## ADR-027 — Deterministic local execution Control Plane under ChatGPT — PROVISIONAL / AUTHORITATIVE DIRECTION

The project will implement a local deterministic execution Control Plane rather than make ChatGPT micromanage every low-level procedural transition.

Responsibilities:

```text
TaskState
selected procedure/ProgramGraph version
current node / permitted transitions
current evidence + provenance
capability policy / authorization
checkpoints / rollback metadata
verifier/postconditions
bounded retries/recovery
resource/action/time budgets
escalation reasons
```

Boundary:

- it does not infer arbitrary user goals;
- it does not invent an open-ended strategy;
- it may advance only known transitions that match current state and pass authorization + verification;
- novel/ambiguous/stale/incompatible state escalates to ChatGPT;
- it is separate from `semantic-projection` and Windows manager lifecycle;
- no model/planner/procedure may bypass it.

Implementation gate: Stage 26.3 Verified Procedure Runtime after accepted Stage 26.2E real-app E2E.

Canonical document: `CONTROL_PLANE.md`.

## ADR-028 — Future local general planner is retained as optional Track P — ACCEPTED LONG-TERM DIRECTION

A local general planner is **not banned forever** and should not be deleted from future architecture discussions.

It is intentionally deferred until real verified procedure-state data and measured need exist. Candidate triggers include offline operation, material planning round-trip latency, multi-machine/highly parallel workloads, deployment/privacy constraints or demonstrated local-model parity.

Research order:

```text
P0 shadow/proposal-only planner
 -> benchmark against ordinary ChatGPT manager
 -> no authorization/actuation

P1 bounded subtask planner
 -> explicitly scoped workloads
 -> deterministic Control Plane remains authoritative

P2 optional local general planner
 -> only after parity/safety/resource evidence
 -> never silently replaces ChatGPT default
```

Even a future local planner cannot grant itself capability authority and must remain above the same deterministic Control Plane/verifier boundary.

Track P is not a Stage 27/28 release prerequisite.

## ADR-029 — One planner does not mean one round trip per action — ACCEPTED ARCHITECTURAL CLARIFICATION

`ordinary ChatGPT is the only current general planner` does **not** mean ChatGPT must be invoked after every deterministic action.

A selected verified procedure may execute locally through repeated:

```text
observe -> match permitted transition -> authorize -> act -> verify -> checkpoint
```

until an escalation condition occurs. This is the mechanism for long-horizon autonomy without introducing a second current general planner.

# Decisions

Historical ADR detail remains in Git history. This file lists decisions that govern current development.

A decision marked **PROVISIONAL** is the accepted architecture direction but is not product-accepted until its stated implementation/evidence gate passes.

## ADR-010 — Off-the-shelf MCP bridge — ACCEPTED

Use standard MCP and mature reachability/runtime components. Prefer official/vendor, mature OSS, mature generic adapter, then the smallest project-owned focused adapter for a measured gap.

## ADR-011 — OpenAI Secure MCP Tunnel is primary ChatGPT reachability — ACCEPTED

Accepted by real ordinary-Chat E2E. Historical custom/public ingress experiments are not the normal path.

## ADR-012 — Superseded universal core removed — ACCEPTED

The old universal agent/gateway platform is historical only. Recover specific pieces only for a later measured gap.

## ADR-013 — 1MCP is replaceable optional internal infrastructure — ACCEPTED

1MCP is not part of the normal semantic critical path. Stage 24.1 removed it from that path because direct stdio was simpler/faster with equivalent tested behavior.

Retain 1MCP as an optional internal component for extension discovery/aggregation, backend lifecycle, diagnostics and adaptive experiments. Failure or absence of 1MCP must not prevent install/start/health of the normal six-tool semantic route.

The persistent OpenAI tunnel anchor is product state and must not be owned by a `local-1mcp` profile. The neutral source of truth is `state/tunnel.json`; a legacy `local-1mcp.yaml` may be read only as a bounded migration fallback for an existing accepted `tunnel_*` id.

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

Current public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Six is the current canonical contract, not an eternal maximum. Never preserve a tool count by hiding unrelated consequences behind misleading schemas. New capability classes require a truthful public-contract decision or remain behind existing truthful project-owned semantics.

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
 -> direct stdio canonical six-tool semantic projection
```

`semantic-projection` remains deterministic and does not become planner/lifecycle/workflow state. Normal semantic install/start/smoke acceptance must not require 1MCP.

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

The Windows desktop capability has now progressed through accepted Stage 26.2A-D. A truthful public desktop surface still requires a separate ADR and ordinary-Chat acceptance. Do not overload `web_interact` or add opaque workflow dispatch merely to preserve the current six tool names.

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

## ADR-030 — Self-healing transport supervisor with a persistent tunnel anchor — PROVISIONAL

The normal direct semantic transport should gain a lightweight user-context supervisor that continuously reconciles the user's explicit desired transport state and restores recoverable platform-owned runtime failures.

The supervisor belongs to the Windows lifecycle/diagnostics boundary, not the Stage 26.3 procedure Control Plane and not the planner boundary.

Required principles:

- keep the existing accepted `tunnel_*` id as the persistent anchor;
- store that anchor in neutral platform state rather than an extension-specific profile;
- restart/reconnect replaceable local `tunnel-client` / semantic runtime around that anchor;
- represent local MCP health, local tunnel health, OpenAI control-plane health and last-known ChatGPT route health as distinct evidence;
- use failure-specific recovery rather than blind restart loops;
- recover local/process/network/transient-service failures with bounded fast retries followed by indefinite low-rate re-probing while desired state remains `running`;
- fail closed on authentication, permission or conclusive remote-resource loss;
- do not claim that remote control-plane health proves a current ChatGPT app route;
- do not automatically create/delete/rotate tunnel resources as normal recovery;
- do not require or persist a long-lived `OPENAI_ADMIN_KEY` in the supervisor by default;
- preserve DPAPI `CurrentUser` secret storage and semantic-child credential scrubbing;
- keep tray lifetime independent from supervisor lifetime;
- prefer stable official `tunnel-client` lifecycle/recovery features when a reviewed published release provides them instead of duplicating upstream behavior.

The existing unmerged `chat/tunnel-reliability-e2e-health` branch is prototype evidence only and is not accepted by this ADR.

Implementation/acceptance contract: `TRANSPORT_SUPERVISOR.md`.

## ADR-031 — 1MCP is the optional internal Extension Manager — ACCEPTED DIRECTION

Future third-party MCP backends may be attached behind an internal Extension Manager implemented with 1MCP or a qualified replacement.

Target boundary:

```text
ordinary ChatGPT
        |
        v
project-owned canonical semantic surface
        |
        +----> deterministic Control Plane / project-owned capabilities
        |
        `----> internal Extension Manager
                    |
                   1MCP
                    |
              third-party MCP backends
```

Rules:

- 1MCP is optional and replaceable;
- normal six-tool semantic install/start/health does not depend on 1MCP or `npx` preflight;
- 1MCP may own discovery, aggregation, enable/disable, lazy lifecycle, health and restart of extension backends;
- a third-party MCP is not automatically trusted or Chat-facing merely because 1MCP can load it;
- raw backend tool catalogs are not exported directly to ordinary ChatGPT;
- project-owned semantic adapters/facades remain small, typed, truthful, scope-preserving and non-planning;
- Control Plane/capability policy remains authoritative for consequences and authorization;
- extension failure must be isolated from the baseline six-tool route unless the current task explicitly depends on that extension;
- extension versions, licenses, supply pins, scopes and acceptance evidence remain mandatory before promotion.

This ADR turns the old `adaptive`/aggregation role into an explicit long-term extension boundary rather than an alternative ordinary-Chat product surface.

## ADR-032 — State-first hybrid computer-use control loop — PROVISIONAL / AUTHORITATIVE DIRECTION

The future Browser/Windows computer-use architecture will generalize the already accepted structure-first capability work into one project-owned control-loop contract:

```text
semantic/native state first
 -> selective visual evidence only when structural evidence is insufficient
 -> capability-aware bounded action
 -> fresh post-action re-observation
 -> explicit transition verification
 -> typed bounded recovery / LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Rules:

- pixels are selective evidence, not the default source of truth when reliable DOM/AX/UIA/app state exists;
- every mutating transition defines current-state preconditions, an expected effect/postcondition, one bounded action, re-observation scope and `PASS | FAIL | UNKNOWN` verification;
- delivery never implies success;
- planner self-assessment may produce only `candidate_done`; a separate fresh-evidence Finish Gate produces `DONE`;
- WorkingState stores user-visible/structured constraints, facts+provenance+freshness, subgoal progress, evidence refs, expected/observed deltas and recovery/budget state — never hidden chain-of-thought;
- recovery is typed and budgeted; identical state/action fingerprints without new evidence/progress must not loop indefinitely;
- capability routing is based on reviewed preconditions/evidence, not merely on tool/backend availability;
- grounding proposals should carry target identity/source/frame binding/confidence/ambiguity when relevant, not coordinates alone;
- external benchmark mechanisms are evidence inputs, not automatic production architecture or release gates.

Implementation mapping:

```text
26.3B Verification Kernel + independent Finish Gate
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 demonstration -> verified candidate skill
 -> 26.5 hybrid computer-use integration
```

A future Windows/computer-use public Chat-facing surface still requires the separate ADR/schema/security/ordinary-Chat physical acceptance required by ADR-024. ADR-032 does not authorize new public tool names by itself.

Canonical detail: `COMPUTER_USE_ARCHITECTURE.md`.

## ADR-033 — Environmental content is data, not authority — ACCEPTED SECURITY INVARIANT

Content observed from web pages/DOM, application UI, email/messages, files/documents, screenshots/OCR, and third-party tool/MCP outputs is **untrusted environmental data** with respect to user intent, capability policy and safety authority.

Rules:

- environmental text cannot grant itself a higher instruction priority, broaden permission scope, alter Control Plane policy or authorize a consequence merely because the planner/model can read it;
- provenance/trust classification must be preserved when facts move between applications/capabilities;
- task-success verification and safety/policy verification are separate dimensions;
- a task can be capability-successful but safety-failed, and evaluation must preserve that distinction;
- safety/policy gates prefer deterministic/native predicates where available; model judgment may assist ambiguous classification but never grants execution authority;
- third-party extension output remains subject to the same rule and does not gain trust from 1MCP availability.

Implementation is staged through 26.3B safety/completion evidence, 26.3C WorkingState provenance, and later computer-use safety evaluation. This invariant is immediately binding on new designs even before all corresponding runtime machinery exists.

Canonical detail: `COMPUTER_USE_ARCHITECTURE.md` and `SECURITY_POLICY.md`.

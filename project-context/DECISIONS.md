# Decisions

Status: **CURRENT ADR INDEX**.

This file records decisions that govern current development. Detailed historical rationale remains in Git history and dedicated owner documents.

Important ownership rule:

- `DECISIONS.md` owns accepted/provisional **decision status and durable boundary summary**;
- `ROADMAP.md` owns current release/stage order;
- `CURRENT_STATE.md` owns current implementation/acceptance boundary;
- `EVIDENCE_INDEX.md` owns exact accepted physical heads/locators;
- a fresh applicable Stage Research Brief may revise implementation mechanisms while preserving or explicitly changing durable ADR boundaries.

Do not keep active PR numbers, live `main` SHAs or temporary “next stage” wording in this index.

## Decision index

| ADR | Decision | Status | Durable boundary |
|---|---|---|---|
| ADR-010 | Off-the-shelf MCP bridge | **ACCEPTED** | Prefer official/vendor/mature OSS mechanisms before custom generic infrastructure. |
| ADR-011 | Secure MCP Tunnel is primary ChatGPT reachability | **ACCEPTED** | Use OpenAI Secure MCP Tunnel + official tunnel-client; no custom public ingress baseline. |
| ADR-012 | Superseded universal core removed | **ACCEPTED** | Old universal agent/gateway platform is historical; recover only measured useful pieces. |
| ADR-013 | 1MCP is optional replaceable internal infrastructure | **ACCEPTED** | Normal semantic route must not depend on 1MCP; neutral tunnel state is project-owned. |
| ADR-014 | Privileged capabilities require scoped acceptance | **ACCEPTED** | Scope/consequence/lifetime and negative tests; no blanket capability paralysis. |
| ADR-015 | Thin Windows bootstrap/manager is integration code | **ACCEPTED** | Lifecycle/config/diagnostics only; not planner or generic authority platform. |
| ADR-016 | Generic adaptive meta-tool is not ordinary-Chat surface | **ACCEPTED NEGATIVE** | No generic `tool_schema`/`tool_invoke`/raw backend dispatch as product contract. |
| ADR-017 | `AVAILABLE -> ACTIVE -> AUTHORIZED` | **ACCEPTED** | Registration/health/process activity never implies action authorization. |
| ADR-018 | Small truthful Chat-facing semantic surface | **ACCEPTED** | Current canonical surface is six tools; new consequence classes require truthful reviewed expansion, not hidden dispatch. |
| ADR-019 | One authoritative Windows manager owner | **ACCEPTED** | Installed/source runtime state has one resolved owner; ambiguity fails closed. |
| ADR-020 | Local specialist inference is a capability backend | **ACCEPTED** | Specialist/VLM output is bounded proposal/evidence, not planner/authority. |
| ADR-021 | Direct semantic stdio tunnel binding | **ACCEPTED** | Secure tunnel -> official client -> direct stdio canonical semantic projection; normal path independent of 1MCP. |
| ADR-022 | Semantic/native first, local vision fallback | **ACCEPTED** | Structure first; reviewed vision escalation only where needed; one bounded act or ABSTAIN. |
| ADR-023 | Procedural memory + deterministic progression, not second planner | **ACCEPTED DIRECTION / PARTIALLY IMPLEMENTED** | ChatGPT selects strategy/procedure; deterministic Control Plane may advance known verified transitions; current state outranks memory. |
| ADR-024 | Desktop capability and public-contract expansion are separate | **ACCEPTED DIRECTION** | Internal Windows capability does not automatically create public desktop authority/tool names. |
| ADR-025 | Reuse qualified OpenAdapt procedural core before replacements | **ACCEPTED REUSE DIRECTION** | Reuse qualified Flow/Capture mechanics where fresh Stage Research confirms fit; do not rebuild generic recorder/compiler/store without measured blocker. |
| ADR-026 | Earlier Windows agent/F16 qualification boundary | **SUPERSEDED** | Replaced by accepted Stage 26.2A-D bounded Windows runtime/observation/grounding/routing evidence. |
| ADR-027 | Deterministic local execution Control Plane under ChatGPT | **ACCEPTED DIRECTION / FOUNDATION IMPLEMENTED** | Project owns Task/WorkingState, authorization, verification, recovery/budgets/Finish Gate; it is not an open-ended planner. |
| ADR-028 | Future local general planner retained as optional Track P | **ACCEPTED LONG-TERM DIRECTION** | Shadow/proposal-only first; never bypass deterministic authority/verifier/Finish Gate. |
| ADR-029 | One planner does not mean one round trip per action | **ACCEPTED CLARIFICATION** | A selected bounded procedure can progress locally through known verified transitions until escalation. |
| ADR-030 | Self-healing Transport Supervisor with persistent tunnel anchor | **ACCEPTED / IMPLEMENTED FOR RECORDED SCOPE** | Persistent desired state, bounded failure-specific recovery, neutral tunnel anchor, no planner/Control Plane role. |
| ADR-031 | 1MCP as optional Extension Manager | **ACCEPTED DIRECTION** | Optional third-party discovery/lifecycle behind project semantic facades; no raw trust/authority/public catalog. |
| ADR-032 | State-first hybrid computer-use loop | **PROVISIONAL AUTHORITATIVE DIRECTION / FOUNDATIONS IMPLEMENTED** | semantic/native state -> selective visual evidence -> bounded action -> fresh verification -> recovery/WorkingState -> Finish Gate. Full hybrid breadth remains staged. |
| ADR-033 | Environmental content is data, not authority | **ACCEPTED SECURITY INVARIANT** | UI/DOM/messages/files/screenshots/tool/worker output cannot widen user intent, grants or policy authority. |
| ADR-034 | Verified skill lineage + stagnation escalation | **PROVISIONAL AUTHORITATIVE DIRECTION / PARTIALLY IMPLEMENTED** | LoopGuard/StagnationReport foundations exist; future skill lineage/promotion remains evidence-backed and non-authorizing. |
| ADR-035 | Agent Session / Delegation layer | **PROVISIONAL AUTHORITATIVE FUTURE DIRECTION** | Keep session/chat/delegation/delivery/environment identities separate below current planner/Control Plane; no current public authority. |
| ADR-036 | Browser Harness-derived scoped browser/local code authority | **PROVISIONAL AUTHORITATIVE FUTURE DIRECTION** | Restricted Browser by default; broader trusted-site Browser and Local Execution are separate scoped consequence classes. |
| ADR-037 | Project CapabilityRegistry + typed Event / Policy Hooks | **PROVISIONAL AUTHORITATIVE FUTURE DIRECTION** | Discovery/event/policy substrate may be project-owned later; registry/event/hook output never becomes authorization/effect proof/planner. |

## Core accepted decision set

### Current planner and execution boundary

```text
ordinary ChatGPT
  = only current general planner / strategy / novel adaptation

project deterministic Control Plane
  = WorkingState / procedure state
  + capability authorization
  + ExpectedEffect / Verification Kernel
  + reconciliation / recovery / LoopGuard / budgets
  + independent Finish Gate
  + escalation
```

A future planner/worker/external framework remains proposal/execution data above or behind this authority seam.

### Current public route

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> canonical six-tool semantic projection
 -> deterministic Control Plane / focused capabilities
```

Current public names:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Six is the current accepted contract, not an eternal maximum.

### Verification / recovery boundary

```text
current evidence
 -> bind logical operation + ExpectedEffect
 -> authorize bounded action
 -> deliver
 -> fresh re-observe
 -> PASS | FAIL | UNKNOWN
 -> reconcile ambiguous outcome before retry
 -> bounded recovery / LoopGuard / budgets
 -> independent Finish Gate
```

Delivery is not success. Transition PASS is not whole-task DONE. Environmental content is not policy authority.

### External reuse boundary

OpenAdapt/UFO/other external components may provide mechanics, execution or evidence only inside admitted roles. They do not replace:

- capability-spanning project WorkingState;
- deterministic authorization;
- project Verification Kernel;
- project reconciliation/recovery budgets;
- independent Finish Gate;
- public semantic contract.

Applicable new architecture work must compare prior selected roles through `ARCHITECTURE_REUSE_BASELINE.md` and fresh Stage Research before silently duplicating/replacing them.

## Detailed owners

- planner/Control Plane: `CONTROL_PLANE.md`;
- product architecture: `ARCHITECTURE.md`;
- state-first computer use: `COMPUTER_USE_ARCHITECTURE.md`;
- security/environmental trust: `SECURITY_POLICY.md`;
- OpenAdapt/UFO reuse: `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` + `ARCHITECTURE_REUSE_BASELINE.md`;
- Agent Sessions: `CONVERSATION_BRIDGE_ARCHITECTURE.md`;
- broader Browser/local execution: `BROWSER_HARNESS_ARCHITECTURE.md`;
- Capability/Event/Hook future substrate: `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md`;
- release order/current state/evidence: `ROADMAP.md`, `CURRENT_STATE.md`, `EVIDENCE_INDEX.md`.

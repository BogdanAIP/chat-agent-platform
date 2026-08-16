# Decisions

Historical ADRs for superseded architectures remain in Git history. Only decisions listed here are active. A decision marked **PROVISIONAL** is the current direction but must not be reported as accepted until its acceptance gate passes.

## ADR-010 — Off-the-shelf MCP bridge — ACCEPTED

```text
ordinary ChatGPT Chat -> standard MCP -> mature reachability -> mature local MCP runtime -> replaceable modules
```

ChatGPT is the intelligence/orchestration layer. Infrastructure selection order is official/vendor, mature OSS, mature generic adapter, then the smallest project-owned missing adapter.

## ADR-011 — OpenAI Secure MCP Tunnel is primary ChatGPT reachability — ACCEPTED

Accepted by real E2E on 2026-08-10. Public Funnel/Yandex/custom ingress is not required for normal operation.

## ADR-012 — Superseded universal core removed from active tree — ACCEPTED

The old Rust/Python universal platform, relay/gateway and media platform core are historical only. Recover exact pieces only for a later measured gap. Historical source: `a446397d99276856c614bc49526cab422c7e74bd`.

## ADR-013 — 1MCP is replaceable infrastructure — ACCEPTED

`@1mcp/agent@0.34.4` is the accepted direct Windows baseline. 1MCP is not product identity. A different/newer line may be evaluated for measured compatibility/lifecycle requirements without making multiple gateways permanent dependencies.

## ADR-014 — Privileged capabilities require scoped acceptance — ACCEPTED

Filesystem, shell, browser, application control, credentials and devices require scoped configuration and negative tests before promotion. Security reviews capability risk; it does not mandate permanent isolation of every pair of tools regardless of task.

## ADR-015 — Thin Windows bootstrap/manager is integration code — ACCEPTED

Bootstrap/controller/tray may install, configure, start/stop, report health and coordinate accepted components. They must not become a planner, workflow engine, generic MCP gateway, registry, vault or authorization platform. Runtime secrets remain local and use DPAPI; tunnel profiles are created with the official CLI.

## ADR-016 — Generic adaptive meta-tool contract is not the ordinary-Chat product surface — ACCEPTED AS A NEGATIVE DECISION

### Evidence

The adaptive 1MCP runtime itself passes local/remote lifecycle acceptance through exact `@1mcp/agent@0.35.0-beta.3` plus the hash-guarded compatibility package. Filesystem and Playwright can enable, appear through lazy discovery, execute a real operation, disable and clean up in one MCP session while the top-level generic surface stays fixed.

The real ordinary-Chat test then exposed the exact eight generic/lifecycle actions. Read-only list/status/discovery calls reached the bridge, but lifecycle actions plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

The exact OpenAI admission cause was not isolated. Therefore do not claim that a specific annotation alone caused the failure.

### Decision

Do not promote the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` plus lifecycle surface as the normal ordinary-Chat product contract.

The generic dispatcher is also structurally difficult to describe truthfully at one static tool boundary because the nested operation determines the real schema and consequences. Do not relabel it read-only/non-destructive merely to bypass product review.

Keep the adaptive implementation as useful local/CI lifecycle infrastructure and a diagnostic experiment. Revisit generic dynamic invocation only if a future standard/product mechanism exposes downstream operation semantics truthfully and passes ordinary-Chat acceptance.

## ADR-017 — Task-driven capability lifecycle and authorization — PROVISIONAL

Use separate states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

The platform should not keep every backend process running. Sequential tasks should normally activate backends sequentially. Workflows that genuinely require multiple capabilities may keep multiple backends active together.

Real ordinary-Chat Filesystem + Browser typed use has now passed on a synthetic scoped workspace, so permanent mutual exclusion is not a product requirement.

Authorization should prioritize scoped roots/resources, reversible workspaces, backups/git and consequence-based confirmation over prompting for every low-risk action. OpenAI app permission mode is an additional product control, not the only safety boundary.

Promotion to ACCEPTED requires the scalable typed capability mechanism and task-driven lifecycle to pass together on the real product path.

## ADR-018 — Concrete typed Chat-facing capability surface — PROVISIONAL

### Evidence

A freshly scanned direct Playwright surface passed ordinary-Chat `browser_navigate`.

A combined local runtime exposed 14 Filesystem + 20 Playwright actions. The Chat-facing app effectively surfaced 20 actions, excluding later browser actions such as `browser_navigate`/`browser_click`.

After reducing Filesystem to four typed actions, the local runtime exposed 24 total actions and a refreshed/new ordinary Chat successfully used typed `list_allowed_directories`, `read_text_file`, `write_file`, `browser_navigate`, `browser_find` and `browser_click` in one conversation.

Official OpenAI documentation says ChatGPT MCP apps use a frozen reviewed tool snapshot; later MCP tool-definition changes are not automatically enabled. 1MCP tags/presets/filtering can narrow local runtime exposure but do not independently make an already-scanned ordinary-Chat app dynamically acquire new typed actions. OpenAI Tool Search solves large tool surfaces in the API/Agents SDK, but it is not currently documented as available to this ordinary-Chat custom-MCP-app path.

### Decision under acceptance

Preserve concrete typed schemas and truthful tool semantics as the Chat-facing contract. Solve scaling by projecting a small stable semantic typed surface onto the larger approved local capability catalog rather than publishing hundreds of tools or hiding all operations behind opaque generic invocation.

The observed ~20-action behavior is **not** an official OpenAI limit and must not be hard-coded as a universal constant. The implementation should measure/fail safely and remain adaptable if product limits change.

A project-owned capability projection/facade is allowed only if it is the smallest measured compatibility boundary and does not become a planner, workflow engine or generic replacement MCP platform. Each exposed operation must have a truthful fixed schema and consequence class; do not recreate `tool_invoke` under another name.

Promotion requires real ordinary-Chat acceptance across more than one backend class without one Chat app per backend or routine manual Refresh for each operation.

## ADR-019 — One authoritative Windows manager owner — ACCEPTED

### Evidence

The target machine exposed a stale installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` listening on `127.0.0.1:3050` while the source checkout reported its known profiles stopped. New source startup could therefore observe the stale runtime health endpoint.

The implementation adds shared `manager-owner.json` state, cross-copy status delegation/stop/takeover behavior and fail-closed handling when the fixed MCP port is occupied without a trustworthy owner.

Target Windows acceptance on 2026-08-14 proved installed start, source observation, installed -> source takeover, source observation from the installed copy, source -> installed takeover and foreign-owner Stop/cleanup with exactly one `3050` listener at each running state. A separate occupied-port test proved an unrelated `3050` listener is rejected rather than accepted as platform readiness.

Commit `923d2f9...` fixed the diagnostic string exposed by that negative test. Functional head `ffcc2e407...` then added a real Windows CI test that binds a foreign listener and verifies the public manager's non-zero fail-closed path. All CI/profile/security workflows pass on that exact functional head.

### Decision

Installed and source manager copies are not independent platform instances. They coordinate one authoritative owner for the fixed local MCP/tunnel runtime through shared LocalAppData state. Status follows the recorded owner, takeover stops the previous owner first, and an unowned occupied port fails closed.

The foreign-owner `Toggle` branch remains regression-covered but was not separately repeated as a dedicated target-machine user action. That does not reopen the measured split-brain defect; if Toggle behavior changes later, test that specific path before claiming a new Toggle implementation accepted.

## ADR-020 — Local specialist inference is a capability backend, not a second brain — PROVISIONAL

### Decision under acceptance

Local models may be used for bounded specialist inference such as screen/image/document understanding, OCR, grounding, comparison, extraction or classification while ordinary ChatGPT remains the planner/orchestrator.

Prefer a mature replaceable local model-runtime manager over embedding one inference stack into platform core. LM Studio/`llmster` is the first runtime-manager candidate because its current documented surface includes local model discovery, memory estimation before load, GPU-offload control, JIT loading, TTL and auto-eviction.

`LiquidAI/LFM2.5-VL-3B`, officially released 2026-08-12, is the first preferred `local-vision` model candidate. Liquid AI publishes screen/UI, OCR/document/chart, grounding and multi-image capabilities plus GGUF/llama.cpp and ONNX support.

Neither LM Studio nor LFM2.5-VL-3B is product-accepted until target Windows hardware/runtime benchmarking passes. The platform must keep runtime/model selection replaceable and hardware/evidence driven.

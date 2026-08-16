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

`@1mcp/agent@0.34.4` is the accepted direct Windows baseline from Stage 24. 1MCP is not product identity. A different/newer line or a narrower direct transport may be evaluated for measured compatibility/lifecycle requirements without making multiple gateways permanent dependencies.

Stage 24 ordinary-Chat acceptance proves that 1MCP works in the accepted semantic baseline. Any later removal of 1MCP from the semantic critical path is an architecture simplification decision, not evidence that the accepted 1MCP path was broken.

## ADR-014 — Privileged capabilities require scoped acceptance — ACCEPTED

Filesystem, shell, browser, application control, credentials and devices require scoped configuration and negative tests before promotion. Security reviews capability risk; it does not mandate permanent isolation of every pair of tools regardless of task.

## ADR-015 — Thin Windows bootstrap/manager is integration code — ACCEPTED

Bootstrap/controller/tray may install, configure, start/stop, report health and coordinate accepted components. They must not become a planner, workflow engine, generic MCP gateway, registry, vault or authorization platform. Runtime secrets remain local and use DPAPI; tunnel profiles are created with the official CLI.

## ADR-016 — Generic adaptive meta-tool contract is not the ordinary-Chat product surface — ACCEPTED AS A NEGATIVE DECISION

### Evidence

The adaptive 1MCP runtime passes local/remote lifecycle acceptance through exact `@1mcp/agent@0.35.0-beta.3` plus the hash-guarded compatibility package. Filesystem and Playwright can enable, appear through lazy discovery, execute a real operation, disable and clean up in one MCP session while the top-level generic surface stays fixed.

The real ordinary-Chat test exposed the exact eight generic/lifecycle actions. Read-only list/status/discovery calls reached the bridge, but lifecycle actions plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

The exact OpenAI admission cause was not isolated. Therefore do not claim that a specific annotation alone caused the failure.

### Decision

Do not promote the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` plus lifecycle surface as the normal ordinary-Chat product contract.

Keep the adaptive implementation as useful local/CI lifecycle infrastructure and a diagnostic experiment. Revisit generic dynamic invocation only if a future standard/product mechanism exposes downstream operation semantics truthfully and passes ordinary-Chat acceptance.

## ADR-017 — Task-driven capability lifecycle and authorization — PROVISIONAL

Use separate states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

The platform should not keep every backend process running. Sequential tasks should normally activate backends sequentially. Workflows that genuinely require multiple capabilities may keep multiple backends active together.

Real ordinary-Chat Filesystem + Browser typed use has passed on a synthetic scoped workspace, so permanent mutual exclusion is not a product requirement.

Authorization should prioritize scoped roots/resources, reversible workspaces, backups/git and consequence-based confirmation over prompting for every low-risk action. OpenAI app permission mode is an additional product control, not the only safety boundary.

This lifecycle model remains provisional for broader future catalogs even though the Stage 24 semantic path itself passed product acceptance.

## ADR-018 — Concrete typed semantic Chat-facing capability surface — ACCEPTED

### Evidence

A freshly scanned direct Playwright surface passed ordinary-Chat `browser_navigate`.

A combined local runtime exposed 14 Filesystem + 20 Playwright actions. The Chat-facing app effectively surfaced 20 actions, excluding later browser actions such as `browser_navigate`/`browser_click`.

After reducing Filesystem to four typed actions, the local runtime exposed 24 total actions and a refreshed/new ordinary Chat successfully used typed file and browser actions in one conversation.

Stage 24 then implemented a fixed five-tool semantic projection:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

On 2026-08-16 a real ordinary-Chat session through the normal Secure MCP Tunnel path used those semantic actions to read `SEMANTIC_FINAL_INPUT_20260816`, navigate from `example.com` through the actual observed `Learn more` link to `Example Domains`, write `result.txt`, and independently read back the exact two-line result. No raw backend tools or generic `tool_invoke` were used.

PR #66 final head `87a8701b938a128901646d096e13142700cc109a` passed the full final CI/security/acceptance suite and was squash-merged to `main` as `175d36236f80a1f99f091d4f031a1c6255f3652b`.

### Decision

Preserve concrete typed schemas and truthful tool semantics as the Chat-facing product contract. Scale by projecting a small stable semantic typed surface onto approved local capabilities rather than publishing hundreds of tools or hiding operations behind opaque generic invocation.

The observed ~20-action behavior is measured evidence, **not** an official universal limit and must not be hard-coded as one.

The project-owned semantic projection is allowed because it is a small deterministic compatibility boundary. It must not choose user goals, plan workflows, hide heterogeneous risk behind a generic schema or become a project-owned general MCP gateway.

## ADR-019 — One authoritative Windows manager owner — ACCEPTED

### Evidence

The target machine exposed a stale installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` listening on `127.0.0.1:3050` while the source checkout reported its known profiles stopped. New source startup could therefore observe stale runtime health.

The implementation added shared `manager-owner.json` state, cross-copy status delegation/stop/takeover behavior and fail-closed handling when the fixed MCP port is occupied without a trustworthy owner.

Target Windows acceptance proved installed start, source observation, installed -> source takeover, source observation from the installed copy, source -> installed takeover and foreign-owner Stop/cleanup with exactly one `3050` listener at each running state. A separate occupied-port test proved an unrelated `3050` listener is rejected rather than accepted as platform readiness. Automated Windows CI covers the negative path.

### Decision

Installed and source manager copies are not independent platform instances. They coordinate one authoritative owner for the accepted Stage 24 local MCP/tunnel runtime through shared LocalAppData state. Status follows the recorded owner, takeover stops the previous owner first, and an unowned occupied port fails closed.

A later direct semantic transport may reduce the semantic profile's need for port `3050`, but it must not weaken the single-owner/fail-closed guarantees for profiles that continue to use it.

## ADR-020 — Local specialist inference is a capability backend, not a second brain — PROVISIONAL

Local models may be used for bounded specialist inference such as screen/image/document understanding, OCR, grounding, comparison, extraction or classification while ordinary ChatGPT remains the planner/orchestrator.

Prefer a mature replaceable local model-runtime manager over embedding one inference stack into platform core. LM Studio/`llmster` is the first runtime-manager candidate. `LiquidAI/LFM2.5-VL-3B` is the first preferred `local-vision` model candidate.

Neither runtime nor model is product-accepted until target Windows hardware/runtime benchmarking passes. The platform must keep runtime/model selection replaceable and evidence driven.

## ADR-021 — Direct semantic stdio tunnel binding — PROVISIONAL

### Motivation

The accepted Stage 24 semantic request path is:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> HTTP 1MCP
  -> stdio semantic-projection
  -> Filesystem / Playwright MCP
```

The semantic projection already owns the fixed five-tool Chat-facing boundary and directly manages its exact downstream MCP clients. Therefore 1MCP may be an unnecessary intermediate hop for this one product path even though it remains useful infrastructure elsewhere.

### Candidate

Evaluate:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> stdio semantic-projection
  -> Filesystem / Playwright MCP
```

Do not remove 1MCP from the repository. Candidate B removes it only from the semantic critical path if measured acceptance proves equivalence or improvement.

### Required evidence

Before promotion, Candidate B must pass:

1. Windows CI through the official tunnel-client stdio main binding, including modern protocol negotiation and exact five-tool inventory;
2. real Filesystem + Playwright calls and negative cases through that transport;
3. target-machine startup/operation/cleanup acceptance;
4. public-manager lifecycle/status integration without weakening accepted ownership/fail-closed behavior;
5. real ordinary-Chat refresh showing the same exact five semantic tools;
6. the same accepted ordinary-Chat read -> browser -> write -> independent read workflow;
7. A/B comparison showing no material reliability/diagnostic regression.

Until those gates pass, the Stage 24 1MCP semantic path remains the accepted baseline.

### Boundary

The direct transport experiment must not turn `semantic-projection` into a generic gateway, registry, lifecycle platform or planner. 1MCP remains available for adaptive experiments, aggregation, inspection and catalog/lifecycle cases where its feature set provides measured value.

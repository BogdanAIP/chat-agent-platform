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

Stage 24 ordinary-Chat acceptance proves that 1MCP works in the accepted semantic baseline. Stage 24.1 later removed 1MCP from the normal semantic critical path because direct stdio proved materially simpler/faster with equivalent acceptance, not because the Stage 24 path was broken.

1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments, aggregation/inspection and future catalog work where its features add measured value.

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

Stage 24.1 repeated the same five-tool ordinary-Chat workflow through the direct stdio transport with the same results. Transport therefore remains an implementation detail beneath this accepted semantic contract.

### Decision

Preserve concrete typed schemas and truthful tool semantics as the Chat-facing product contract. Scale by projecting a small stable semantic typed surface onto approved local capabilities rather than publishing hundreds of tools or hiding operations behind opaque generic invocation.

The observed ~20-action behavior is measured evidence, **not** an official universal limit and must not be hard-coded as one.

The project-owned semantic projection is allowed because it is a small deterministic compatibility boundary. It must not choose user goals, plan workflows, hide heterogeneous risk behind a generic schema or become a project-owned general MCP gateway.

## ADR-019 — One authoritative Windows manager owner — ACCEPTED

### Evidence

The target machine exposed a stale installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` listening on `127.0.0.1:3050` while the source checkout reported its known profiles stopped. New source startup could therefore observe stale runtime health.

The implementation added shared `manager-owner.json` state, cross-copy status delegation/stop/takeover behavior and fail-closed handling when the fixed MCP port is occupied without a trustworthy owner.

Target Windows acceptance proved installed start, source observation, installed -> source takeover, source observation from the installed copy, source -> installed takeover and foreign-owner Stop/cleanup with exactly one `3050` listener at each running 1MCP-backed state. A separate occupied-port test proved an unrelated `3050` listener is rejected rather than accepted as platform readiness. Automated Windows CI covers the negative path.

Stage 24.1 extended the same single-owner/fail-closed scope to the direct semantic `tunnel-client` process. Direct semantic lifecycle and crash recovery proved exactly one owned process, clean stopped status after forced process death, normal-Start recovery and duplicate-free idempotent repeated Start.

### Decision

Installed and source manager copies are not independent platform instances. They coordinate one authoritative owner through shared LocalAppData state. Status follows the recorded owner, takeover stops the previous owner first, and an unowned shared runtime fails closed.

Port `3050` remains part of ownership/fail-closed detection for profiles that use 1MCP. The promoted direct `semantic` profile does not require a `3050` listener and is identified/owned through its exact tunnel-client command/health state instead.

## ADR-020 — Local specialist inference is a capability backend, not a second brain — PROVISIONAL

Local models may be used for bounded specialist inference such as screen/image/document understanding, OCR, grounding, comparison, extraction or classification while ordinary ChatGPT remains the planner/orchestrator.

Prefer a mature replaceable local model-runtime manager over embedding one inference stack into platform core. LM Studio/`llmster` is the first runtime-manager candidate because current official LM Studio tooling provides headless Windows operation, model discovery/load/unload, memory estimation before load, GPU-offload/context controls, TTL/JIT eviction and OpenAI-compatible image chat.

`LiquidAI/LFM2.5-VL-3B` is an official Liquid AI model released on 2026-08-12. Direct official release evidence is recorded from Liquid AI's release blog and model documentation plus the official Hugging Face model repository and WebGPU demo.

Stage 25 distinguishes model quality preference from current-hardware test order:

- preferred quality candidate: `LiquidAI/LFM2.5-VL-3B`;
- middle current-generation comparison: `LiquidAI/LFM2.5-VL-1.6B`;
- first target-laptop runtime candidate: `LiquidAI/LFM2.5-VL-450M-GGUF` Q4 because the machine has 7.68 GB RAM and Intel Iris Xe.

Neither runtime nor model is product-accepted until target Windows hardware/runtime benchmarking passes. The platform must keep runtime/model selection replaceable and evidence driven.

## ADR-021 — Direct semantic stdio tunnel binding — ACCEPTED AND RELEASE-COMPLETE

### Baseline and candidate

Stage 24 accepted:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> HTTP 1MCP
  -> stdio semantic-projection
  -> Filesystem / Playwright MCP
```

Stage 24.1 evaluated:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> stdio semantic-projection
  -> Filesystem / Playwright MCP
```

This evaluation was an architecture simplification exercise, not evidence that 1MCP failed.

### Acceptance evidence

Candidate B passed all architecture/acceptance gates:

1. Windows CI through official tunnel-client stdio binding with modern MCP negotiation and the exact five-tool inventory;
2. real scoped Filesystem + Playwright operations and negative cases;
3. target-machine direct-tunnel startup/operation/cleanup;
4. first-class public-manager lifecycle, single-owner/fail-closed handling, crash recovery and duplicate-free repeated Start;
5. existing `Chat Local Bridge Test` refreshed to the same exact five semantic actions;
6. real ordinary-Chat `read -> browser observe/interact -> write -> independent read` workflow;
7. target-machine A/B lifecycle comparison;
8. normal public `semantic` promotion smoke;
9. all exact promotion-head and post-merge `main` workflows green;
10. stable LocalAppData installation updated from merged `main` with SHA256 equality for manager/direct-controller/semantic-projection and `STAGE24_1_PERSISTENT_INSTALL=PASS`.

Both transports completed 3/3 healthy A/B cycles. Average target-machine timings were:

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| initial Start | 123685 ms | 5007 ms |
| repeated/idempotent Start | 84119 ms | 4876 ms |
| Stop | 23252 ms | 1043 ms |
| port 3050 listeners while running | 1 | 0 |

The direct path was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample, while preserving the tested reliability/diagnostic behavior.

### Decision

Direct stdio binding is the normal public `semantic` transport.

Stage 24.1 was squash-merged to `main` as `df1d5e232b739b62e72ad81e5d82fd01be53e884` and its stable installed bundle passed final target acceptance.

`semantic-direct` may remain temporarily as a compatibility/diagnostic alias during cleanup. The legacy 1MCP-backed semantic path remains internal diagnostic/reference evidence and should not be deleted solely because it is no longer the normal public route.

Retain 1MCP as replaceable internal infrastructure for adaptive lifecycle experiments, aggregation/inspection, diagnostics and future catalog/lifecycle cases where its features add measured value.

The direct transport does not expand the semantic projection's responsibilities. `semantic-projection` remains the deterministic fixed typed boundary and must not become a generic gateway, registry, lifecycle platform or planner.

## ADR-022 — Stage 25 local-vision integration uses a replaceable runtime/model boundary — PROVISIONAL

### Decision direction

Do not couple the public Chat-facing contract to LM Studio commands, a Liquid AI model identifier, or one inference format.

Use a focused deterministic local-vision adapter with a small semantic operation surface. The adapter owns runtime/model compatibility and lifecycle mechanics; Chat owns user-goal reasoning.

The adapter may use reviewed policy to estimate memory, load an accepted local model, set benchmarked context/GPU/TTL options, execute bounded multimodal inference and unload/evict the model. It must not become a planner or dynamically download/choose arbitrary internet models during a user call.

### Acceptance gate

ADR-022 becomes accepted only after a target Windows runtime/model path passes:

- headless lifecycle and machine-readable status;
- pre-load memory estimate and measured peak RAM/VRAM;
- representative UI/screenshot, OCR/document, chart/graph, comparison and frame/image quality tests;
- cold-load, TTFT, throughput and unload/recovery measurements;
- deterministic negative cases;
- a small reviewed typed Chat-facing vision capability;
- one real ordinary-Chat E2E through that capability.

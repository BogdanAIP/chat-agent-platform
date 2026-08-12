# Decisions

Historical ADRs for the superseded Rust/Yandex architecture remain in Git history. Only current architecture decisions are active here.

## ADR-010 — Off-the-shelf MCP bridge

The product is a generic bridge:

```text
ordinary ChatGPT Chat -> standard MCP -> mature reachability -> mature local MCP runtime -> replaceable modules
```

ChatGPT is the intelligence/orchestration layer. The project does not implement a second agent runtime.

Infrastructure selection order is official/vendor implementation, mature OSS, mature generic adapter, then the smallest project-owned missing adapter.

## ADR-011 — OpenAI Secure MCP Tunnel is the primary ChatGPT reachability path

Accepted by a real end-to-end call on 2026-08-10:

```text
ChatGPT -> OpenAI Secure MCP Tunnel -> official tunnel-client -> 1MCP -> sequential_thinking -> ChatGPT
```

Therefore public Funnel/Yandex/custom `/gpt` paths are not required for normal ChatGPT operation.

## ADR-012 — Remove the superseded universal core from the active tree

Stage 22 removes the custom Rust/Python universal platform, relay/gateway stack and media-specific platform code instead of keeping dead code as mandatory baggage.

Rationale:

- official tunnel-client replaces custom reachability/control-plane work;
- 1MCP replaces custom aggregation/process bridging;
- standard MCP modules replace a universal capability registry;
- old domain code is not product-defining and can be recovered from Git history only if Stage 23 proves it is needed.

The pre-cleanup source remains available at commit `a446397d99276856c614bc49526cab422c7e74bd`.

## ADR-013 — 1MCP is current default, not a permanent lock-in

`@1mcp/agent@0.34.4` is the first accepted Windows runtime. Replace it only for a measured requirement such as isolation, auth/governance or protocol compatibility; do not carry multiple gateways by default.

## ADR-014 — Privileged modules require a separate security gate

The accepted reference profile contains only Sequential Thinking. Filesystem, shell, browser, app control, credentials and devices are not enabled until least-privilege exposure and negative tests are accepted.

## ADR-015 — A thin Windows bootstrap/manager is integration code, not a second platform

A small Windows lifecycle layer is justified because ordinary users need a reliable way to install the official tunnel client, keep local configuration/secrets outside Git, select an explicit task profile, and see whether the bridge is actually ready.

Boundary:

- bootstrap may verify prerequisites, install a reviewed official `tunnel-client` release, call the official CLI to create the tunnel profile, install the thin local script/config bundle, request the runtime key, and perform diagnostics;
- controller may coordinate start/stop/status/profile selection and local settings;
- tray is UI only and consumes controller status rather than independently reimplementing process/health rules;
- manager must not become a planner, workflow engine, generic policy service, cloud backend, MCP gateway implementation or authorization server;
- the installed manager lives under `%LOCALAPPDATA%\ChatAgentPlatform\app` so normal use does not depend on a Git checkout;
- runtime secrets stay outside the app bundle and use Windows DPAPI `CurrentUser`;
- tunnel profile generation uses the official `tunnel-client init` surface rather than project-owned YAML generation;
- the bootstrap pins a reviewed tunnel-client version/checksum rather than silently following `latest` during installation.

This moves the thin lifecycle manager into Stage 24 because the operational need is now measured, while preserving the original product boundary.

# Stage 22 — Legacy Reduction

## Decision method

Every subsystem from the pre-cleanup tree was classified by one question: does it provide a capability still required by the accepted ChatGPT → Secure MCP Tunnel → 1MCP architecture that is not already supplied by a mature component?

## Removed from the active tree

### Generic platform/runtime — REMOVE

- Rust `agent-platform.exe` universal core;
- Project Binding/capability registry/policy/artifact/job/secret/confirmation framework as mandatory runtime;
- Python v0.1 behavioral oracle and Rust/Python parity machinery;
- custom relay request/response contracts.

Reason: the bridge no longer needs a project-owned universal execution platform. Standard MCP modules are the unit of capability.

### Transport/cloud — REMOVE

- custom `/gpt` loopback ingress;
- outbound polling relay lifecycle;
- Rust `relay-server`;
- Yandex Function/API Gateway templates and deployment scripts;
- GPT Action OpenAPI templates;
- Stage 4 transport tests/workflows;
- Tailscale `8443` pilot lifecycle scripts.

Reason: accepted OpenAI Secure MCP Tunnel + official `tunnel-client` replaces the primary ChatGPT reachability path, and 1MCP supplies the local MCP endpoint.

### Old product-specific core — ARCHIVE IN GIT, EXTRACT ONLY IF NEEDED

- FFmpeg/media operations;
- REAPER render integration;
- EBU R128/mastering workflows;
- Matchering/reference mastering integration;
- media/mastering project skills and stage documents.

Reason: these are possible modules, not bridge core. Stage 23 must first look for acceptable ready-made MCP servers. If one is genuinely missing, recover only the useful implementation from pre-cleanup commit `a446397d99276856c614bc49526cab422c7e74bd` and wrap/extract it as one independent MCP module.

### Release machinery — REMOVE

- release packaging for `agent-platform.exe`;
- Cargo/SBOM/license workflows specific to the deleted Rust product;
- obsolete release metadata tests.

Reason: publishing the superseded universal binary would give users the wrong product shape.

## Retained

- MIT license and security reporting policy;
- GitHub secret-history scanning;
- CodeQL for the remaining GitHub Actions surface;
- a Windows CI check that proves the pinned 1MCP + Sequential Thinking reference runtime;
- minimal 1MCP config and start/status/stop scripts;
- current architecture, security, acceptance and roadmap documents.

## Recovery guarantee

Deletion from `main` is not destruction. The full legacy implementation and its tests remain immutable in Git history at `a446397d99276856c614bc49526cab422c7e74bd` and earlier PRs.

## Result

The active repository now represents the product that actually passed acceptance instead of continuing to maintain a second, superseded product in parallel.

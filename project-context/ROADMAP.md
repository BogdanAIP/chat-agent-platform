# Roadmap v1.5 — Chat-to-Local Bridge

## Goal

Build the smallest reliable bridge that lets **ordinary ChatGPT Chat** use replaceable capabilities on the user's local computer through standard MCP.

Do not build a second agent runtime. Prefer mature maintained MCP runtimes, gateways, tunnels and servers. Project-owned code is justified only for convenience/configuration or for a local program that lacks an acceptable MCP adapter.

Source of truth:

- `project-context/BRIDGE_ARCHITECTURE.md`
- `project-context/ARCHITECTURE.md`
- `project-context/CONNECTOR_ARCHITECTURE.md`
- `project-context/CURRENT_STATE.md`

## Phase A — Prove a zero-custom-core bridge

### A1 — Public localhost reachability — done

Evidence from 2026-08-10:

- Tailscale Funnel exposes a stable public HTTPS origin for the Windows laptop;
- a direct request reached the local process;
- `local_ping` returned `status=success`, `pong=true`, `executed_locally=true`.

This proves reachability only. It does not yet prove native ChatGPT MCP.

### A2 — Off-the-shelf MCP runtime pilot — prepared

Selected first candidate: **1MCP**.

Prepared assets:

- pinned 1MCP runtime `@1mcp/agent@0.34.4`;
- pinned official `@modelcontextprotocol/server-sequential-thinking@2026.7.4`;
- loopback runtime `127.0.0.1:3050`;
- separate Tailscale Funnel listener on HTTPS `8443`;
- expected public endpoint `https://id182019.tailc0abda.ts.net:8443/mcp`;
- start/stop scripts that do not modify the existing `443` route.

### A3 — Native ChatGPT MCP round trip — next manual gate

From ordinary ChatGPT Chat:

1. create a **new** development MCP connection for the pilot; do not modify the working Yandex connection;
2. use `https://id182019.tailc0abda.ts.net:8443/mcp`;
3. scan tools;
4. verify `sequential_thinking` is discovered;
5. invoke it from Chat;
6. receive the result;
7. stop the unauthenticated pilot listener.

If this passes, the project has proved that the central runtime/transport does not need custom Rust code.

If it fails, identify whether the failure is:

- ChatGPT account/plan/developer-mode policy;
- 1MCP protocol compatibility;
- MCP authentication expectations;
- HTTPS/Funnel behavior.

Do not implement a custom MCP server before testing mature alternatives for the identified failure mode.

## Phase B — Select the permanent bridge runtime

### B1 — Accept 1MCP if A3 passes

Adopt 1MCP as the default local runtime while keeping it replaceable.

### B2 — Fallback evaluation only if needed

- **ToolHive** — stronger isolation, auth, audit/rate limiting, registry/governance and protocol translation.
- **agentgateway** — protocol/security edge when routing/auth/version translation is the actual gap.
- **Docker MCP Toolkit** — only when Docker Desktop is an accepted baseline dependency.

No bake-off is required if the narrowest candidate already satisfies the real ChatGPT test.

## Phase C — Secure privileged local access

Before any filesystem/program-control module is exposed publicly:

1. choose an authentication method supported by the selected runtime and the actual ChatGPT MCP surface;
2. restrict exposed servers and tools;
3. test unauthorized public requests;
4. verify ChatGPT permission/confirmation behavior;
5. document start/stop/recovery behavior;
6. only then enable privileged modules.

The tunnel itself is never treated as authorization.

## Phase D — Modular local capabilities

Capabilities are installed independently.

For every requested local program/service:

```text
official MCP exists?
  yes -> use it
  no  -> mature OSS MCP exists?
           yes -> use it
           no  -> generic adapter/API/CLI bridge exists?
                    yes -> use it
                    no  -> implement one small project-owned adapter
```

Examples such as files, Git, browser, REAPER, FFmpeg, Origin, Blender, CAD, local models and hardware must remain replaceable modules.

Adding or removing one module must not require a bridge-core release.

## Phase E — Convenience product layer

Only after the direct bridge works and module management is understood, consider a thin Windows configurator that can:

- install/detect the chosen runtime;
- add/remove/update MCP modules;
- group modules into profiles;
- start/stop the bridge and reachability profile;
- show health and the ChatGPT connection URL;
- manage secrets through the selected runtime/OS facilities;
- export diagnostics.

This layer must not become an autonomous agent or workflow engine.

## Phase F — Legacy reduction

The repository already contains substantial custom Rust infrastructure from the previous architecture:

- universal `agent-platform.exe` runtime;
- Project Binding/policy/capability machinery;
- Secret/Artifact/Job/Confirmation stores;
- custom `/gpt` ingress;
- polling relay/Yandex transport;
- media-specific adapters and workflows.

Do not delete it before Phase A3.

After direct off-the-shelf MCP acceptance, classify each component:

- **remove** — mature ecosystem component replaces it;
- **extract** — useful as one optional MCP adapter/module;
- **retain** — only when a concrete bridge requirement cannot be met otherwise;
- **archive/reference** — valuable historical acceptance evidence but not shipped runtime.

The reduction should lower installation complexity, background processes, code maintenance and security surface.

## Historical implementation inventory

The previous Stages 0–20 remain evidence of work already completed, not the v1.5 development plan. In particular:

- Hosted Chat -> local execution was proved through the legacy Yandex path;
- Rust local execution, policy, jobs, artifacts, FFmpeg, REAPER and mastering work exist;
- CI/supply-chain hardening exists;
- first versioned public release has not yet been published.

No historical implementation is automatically a permanent dependency.

## Definition of Done

The bridge is successful when:

1. ordinary ChatGPT Chat is the intelligence/orchestration surface;
2. ChatGPT reaches one standard MCP endpoint on the laptop through a mature reachability layer;
3. local capabilities can be added, removed or replaced as MCP modules without changing the bridge core;
4. Work, Codex and OpenAI API model billing are optional, not required for normal operation;
5. privileged local access is authenticated and permission-bounded;
6. the permanent project-owned runtime surface is smaller than the ecosystem components it coordinates.

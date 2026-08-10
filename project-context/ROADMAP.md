# Roadmap v1.6 — Chat-to-Local Bridge

## Goal

Build the smallest reliable bridge that lets **ordinary ChatGPT Chat** use replaceable capabilities on the user's local computer through standard MCP.

Do not build a second agent runtime. Prefer mature maintained MCP runtimes, gateways, tunnels and servers. Project-owned code is justified only for convenience/configuration or for a local program that lacks an acceptable MCP adapter.

## Phase A — Prove a zero-custom-core bridge

### A1 — Hosted Chat -> local Windows — done

Historical evidence already proved ChatGPT could reach the local Windows machine through the legacy Yandex path.

### A2 — Off-the-shelf local MCP runtime — done

Accepted local runtime candidate: **1MCP**.

Accepted test components:

- `@1mcp/agent@0.34.4`;
- official `@modelcontextprotocol/server-sequential-thinking@2026.7.4`;
- local Streamable HTTP endpoint `http://127.0.0.1:3050/mcp`.

The reference server was intentionally harmless and exposed no filesystem, shell, browser, credentials or local application control.

### A3 / Stage 21 — Native ChatGPT MCP round trip — done

Accepted on 2026-08-10 through the official **OpenAI Secure MCP Tunnel**.

Observed end-to-end path:

```text
ordinary ChatGPT Chat
  -> development MCP app `Chat Local Bridge Test`
  -> OpenAI Secure MCP Tunnel
  -> official `openai/tunnel-client`
  -> http://127.0.0.1:3050/mcp
  -> 1MCP
  -> sequential_thinking
  -> result returned to the same ChatGPT conversation
```

Returned tool result included:

```json
{
  "thoughtNumber": 1,
  "totalThoughts": 1,
  "nextThoughtNeeded": false,
  "branches": [],
  "thoughtHistoryLength": 1
}
```

This proves that the bridge core does **not** require a project-owned MCP transport, public ingress or autonomous agent runtime.

Tailscale Funnel `8443` is no longer the primary ChatGPT transport. It remains optional/fallback evidence only. The pre-existing HTTPS `443`/Yandex path remains untouched until a separate cleanup decision.

## Phase B — Permanent bridge stack — accepted baseline

Default baseline:

```text
ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> replaceable local MCP runtime (currently 1MCP)
  -> replaceable MCP modules/adapters
  -> local programs/files/devices
```

1MCP is accepted as the current default local runtime because it passed the real ChatGPT round trip. It remains replaceable.

Fallbacks are evaluated only for a measured gap:

- **ToolHive** — stronger isolation/governance/security/runtime management;
- **agentgateway** — protocol/auth/routing edge;
- **Docker MCP Toolkit** — only when Docker Desktop is an accepted baseline dependency.

Do not carry all candidates permanently.

## Phase C / Stage 22 — Legacy subsystem classification — next

Classify every existing custom subsystem as exactly one of:

- **remove** — mature ecosystem component replaces it;
- **extract** — useful as an optional MCP adapter/module;
- **retain** — concrete measured requirement remains;
- **archive/reference** — historical evidence only.

Priority inventory:

- `agent-platform.exe` universal runtime;
- custom `/gpt` ingress;
- polling relay/Yandex transport;
- Project Binding/policy/confirmation layers;
- Secret/Artifact/Job stores;
- FFmpeg/REAPER/media workflows;
- Python behavioral oracle.

Do not delete by sunk-cost reaction or wholesale rewrite. Reduce only from evidence.

## Phase D / Stage 23 — Module catalog

For each requested local capability:

```text
official MCP exists?
  yes -> use it
  no  -> mature OSS MCP exists?
           yes -> use it
           no  -> generic adapter/API/CLI bridge exists?
                    yes -> use it
                    no  -> implement one small project-owned adapter
```

Programs such as files, Git, browser, REAPER, FFmpeg, Origin, Blender, CAD, local models and hardware remain independent modules.

## Phase E / Stage 24 — Privilege and auth model

Before privileged modules are enabled:

1. keep tunnel runtime credentials outside git;
2. use the minimum OpenAI tunnel permission set (`Tunnels Read + Use`) for the runtime key;
3. define which local MCP modules/tools are exposed per profile;
4. verify ChatGPT permission behavior;
5. add negative tests for unauthorized/unintended access where applicable;
6. document rotation/recovery/stop behavior.

Secure MCP Tunnel is transport and control-plane access, not a replacement for least-privilege tool design.

## Phase F / Stage 25 — Optional Windows bridge manager

Only after Stage 22-24, consider a thin Windows layer that can:

- detect/install the supported tunnel client and local MCP runtime;
- add/remove/update MCP modules;
- manage profiles;
- start/stop/status the local bridge;
- show health/ready state;
- keep secrets outside repository files;
- export diagnostics.

It must not become a second planner, agent or workflow engine.

## Definition of Done

The product direction is successful when:

1. ordinary ChatGPT Chat remains the intelligence/orchestration surface;
2. ChatGPT reaches the laptop through a mature supported MCP transport;
3. local capabilities are replaceable MCP modules;
4. Work, Codex and model API billing are optional rather than required for normal interaction;
5. privileged capabilities are bounded by explicit security profiles;
6. project-owned infrastructure is smaller than the mature components it coordinates.

# Development Principles

## 1. Chat is the agent

Do not add a second planner, workflow brain or autonomous coordinator behind ChatGPT. Local components expose capabilities; ChatGPT decides when to use them.

## 2. Off-the-shelf first

For transport, MCP runtime, discovery, lifecycle and common integrations, use maintained ecosystem components before writing project code.

For a local capability use this order:

```text
official/vendor MCP
  -> mature OSS MCP
  -> mature generic API/CLI adapter
  -> smallest project-owned MCP adapter
```

## 3. Evidence before architecture

A component becomes part of the supported stack only after a real install/start/health/call test on the target Windows environment. Documentation claims are not acceptance evidence by themselves.

## 4. Thin project-owned surface

Allowed project code should normally be one of:

- lifecycle/configuration convenience;
- compatibility tests;
- a focused adapter for one program/device with no acceptable MCP server.

Do not rebuild generic tunnels, gateways, registries, vaults, databases, job systems or policy engines without a measured gap.

## 5. Replaceability

Removing one module must not require changing the bridge protocol or ChatGPT app. Runtime and tunnel choices are implementation details, not domain APIs.

## 6. Security follows capability risk

Harmless read-only reference tools may be used for connectivity tests. Filesystem, shell, browser, app control and secrets require least-privilege configuration and negative tests before acceptance.

## 7. No sunk-cost architecture

Git history is the archive. Old code is not kept in the active tree merely because it took time to build. Recover only the exact part that later proves useful.

## 8. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce paid servers or model API usage as mandatory dependencies when ordinary ChatGPT plus the local bridge already satisfies the goal.

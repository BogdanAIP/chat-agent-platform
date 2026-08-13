# Development Principles

## 1. Chat is the agent

Do not add a second planner, workflow brain or autonomous coordinator behind ChatGPT. Local components expose capabilities; ordinary ChatGPT decides how to combine them.

## 2. Off-the-shelf first

For transport, MCP runtime, discovery, lifecycle and common integrations, use maintained ecosystem components before writing project code.

```text
official/vendor MCP
  -> mature OSS MCP
  -> mature generic/local API or CLI adapter
  -> smallest project-owned focused adapter
```

Do not write a custom gateway/broker until a concrete upstream gap is demonstrated.

## 3. Evidence before architecture

A component becomes supported only after the applicable real install/start/health/tool-call acceptance. A target design or documentation claim is not acceptance evidence.

When CI and docs disagree, investigate the code/logs; do not rewrite evidence to fit the intended architecture.

## 4. Thin project-owned surface

Allowed project code should normally be lifecycle/configuration convenience, compatibility/acceptance tests, or a focused adapter for one missing program/device boundary.

Do not rebuild generic tunnels, MCP gateways, registries, vaults, databases, job systems or policy engines without a measured requirement.

## 5. Stable capability boundary

Adding/removing a backend should not require changing the bridge protocol or normally creating another ChatGPT app/plugin. Runtime/tunnel/module choices remain replaceable implementation details.

## 6. Task-driven lifecycle

Do not run the whole backend catalog permanently. Register capabilities separately from process activation. Start what the task needs, reuse active backends across dependent stages, and stop idle backends.

Parallel backend execution is allowed when the task requires it; sequential execution is a resource-saving default, not a universal prohibition.

## 7. Security enables controlled capability

Use least privilege and negative tests, but do not turn security into capability paralysis.

Think in terms of:

```text
AVAILABLE
ACTIVE
AUTHORIZED
```

Avoid broad always-on access. Scope sensitive operations and keep dangerous administrative mutation tools out of ordinary Chat. Legitimate multi-tool workflows may receive the combined capability they need.

## 8. No sunk-cost architecture

Git history is the archive. Old code stays out of the active tree unless later evidence proves a specific piece useful.

## 9. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce paid model APIs or SaaS as mandatory dependencies when ordinary ChatGPT + local bridge satisfies the requirement.

## 10. Acceptance ownership and continuation discipline

Keep `START_HERE.md` and `CURRENT_STATE.md` synchronized with functional reality at architecture-changing points.

Codex should perform all locally accessible acceptance itself when its environment and permissions allow it, including Windows, CLI, process lifecycle, local applications, MCP backends and local integration tests. Do not ask the user to perform routine local tests that the development agent can execute directly.

Reserve user participation for gates that specifically require the real ordinary ChatGPT UI/custom-app path or another irreducible user-only action. For such a gate, provide one precise test and wait for the actual result. Do not substitute a mock, local MCP client or narrower integration test for a claimed ordinary-Chat E2E pass.

Do not claim a local-machine or ordinary-Chat test unless that exact path actually ran. After a user-run ordinary-Chat acceptance, record the evidence and continue development.

Use isolated branches/worktrees for independent parallel agents and integrate only reviewed/tested results.

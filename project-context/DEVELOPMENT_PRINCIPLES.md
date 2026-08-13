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

## 10. Continuation discipline

Keep `START_HERE.md` and `CURRENT_STATE.md` synchronized with functional reality at architecture-changing points. Do not claim a user-machine or ordinary-Chat test unless it actually ran. Use isolated branches/worktrees for independent parallel agents and integrate only reviewed/tested results.

# Development Principles

## 1. Chat is the agent

Do not add a second planner, workflow brain or autonomous coordinator behind ChatGPT. Local components expose capabilities; ordinary ChatGPT decides how to combine them.

Specialized local models are allowed only as bounded capability backends for tasks such as vision/OCR/grounding/extraction/classification. They must not silently become a second planner. Chat is the brain; specialist models are tools.

## 2. Off-the-shelf first

For transport, MCP runtime, discovery, lifecycle, local model serving and common integrations, use maintained ecosystem components before writing project code.

```text
official/vendor MCP or runtime
  -> mature OSS MCP/runtime
  -> mature generic/local API or CLI adapter
  -> smallest project-owned focused adapter
```

Do not write a custom gateway/broker/model runtime until a concrete upstream gap is demonstrated.

## 3. Evidence before architecture

A component becomes supported only after the applicable real install/start/health/tool-call acceptance. A target design or documentation claim is not acceptance evidence.

When CI and docs disagree, investigate the code/logs; do not rewrite evidence to fit the intended architecture.

Distinguish local/runtime failure from Chat product admission/safety failure. A tool blocked before MCP is not evidence that the backend itself failed.

## 4. Thin project-owned surface

Allowed project code should normally be lifecycle/configuration convenience, compatibility/acceptance tests, or a focused typed adapter for one missing program/device/model boundary.

Do not rebuild generic tunnels, MCP gateways, registries, vaults, databases, job systems, policy engines or general model-serving stacks without a measured requirement.

## 5. Stable typed capability boundary

Adding/removing a backend should not require changing the bridge protocol or normally creating another ChatGPT app/plugin. Runtime/tunnel/module/model choices remain replaceable implementation details.

Preserve concrete typed schemas and truthful tool semantics at the Chat-facing boundary. Do not hide heterogeneous operations behind an opaque generic dispatcher solely to reduce the visible tool count.

Real Stage 24 evidence showed effective action-snapshot truncation around 20 actions in the tested app. Treat this as a measured compatibility constraint, not an official universal constant. The scaling mechanism must remain adaptable if Chat product behavior changes.

## 6. Task-driven lifecycle

Do not run the whole backend catalog permanently. Register capabilities separately from process activation. Start what the task needs, reuse active backends across dependent stages, and stop idle backends.

Parallel backend execution is allowed when the task requires it; sequential execution is a resource-saving default, not a universal prohibition.

Model runtimes follow the same principle: load/JIT the selected specialist model when needed and unload/evict it when idle unless a measured workflow benefits from residence.

## 7. Security enables controlled capability

Use least privilege and negative tests, but do not turn security into capability paralysis.

Think in terms of:

```text
AVAILABLE
ACTIVE
AUTHORIZED
```

Avoid broad always-on access. Scope sensitive operations and keep dangerous administrative mutation tools out of ordinary Chat. Legitimate multi-tool workflows may receive the combined capability they need.

Prefer containment and reversibility — explicit roots, disposable/synthetic workspaces, backups, git, rollback and tool allowlists — over asking the user to approve every low-risk action. Reserve confirmation for genuinely consequential or hard-to-reverse effects.

Do not assume that Chat app permission mode is the only safety layer. OpenAI safety may still block a composite workflow even when the same typed calls pass separately.

## 8. No sunk-cost architecture

Git history is the archive. Old code stays out of the active tree unless later evidence proves a specific piece useful.

## 9. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce paid model APIs or SaaS as mandatory dependencies when ordinary ChatGPT + local bridge satisfies the requirement.

A local runtime manager such as LM Studio may be evaluated because it avoids bespoke model-serving code and paid inference APIs, but it remains replaceable infrastructure rather than a mandatory product identity.

## 10. Hardware-aware local model selection

Do not hard-code a local model/quantization based on guesswork. Prefer runtime-provided capability discovery and resource estimation before load. Choose the highest-quality tested variant that fits measured RAM/VRAM/latency guardrails on the actual machine.

Keep fallback models/runtimes available where useful. A machine upgrade should normally change selection results, not require architecture changes.

## 11. Acceptance ownership and continuation discipline

Keep `START_HERE.md` and `CURRENT_STATE.md` synchronized with functional reality at architecture-changing points.

Codex should perform all locally accessible acceptance itself when its environment and permissions allow it, including Windows, CLI, process lifecycle, local applications, MCP backends, local inference runtimes and local integration tests. Do not ask the user to perform routine local tests that the development agent can execute directly.

Reserve user participation for gates that specifically require the real ordinary ChatGPT UI/custom-app path or another irreducible user-only action. For such a gate, provide one precise test and wait for the actual result. Do not substitute a mock, local MCP client or narrower integration test for a claimed ordinary-Chat E2E pass.

Do not claim a local-machine or ordinary-Chat test unless that exact path actually ran. After a user-run ordinary-Chat acceptance, record the evidence and continue development.

Use isolated branches/worktrees for independent parallel agents and integrate only reviewed/tested results.

Preserve local uncommitted work before syncing remote documentation/code. Reconcile overlapping documentation intentionally rather than discarding the user's local diff.

# Development Principles

## 1. Chat is the agent

Do not add a second planner, workflow brain or autonomous coordinator behind ChatGPT. Local components expose capabilities, bounded perception or non-agentic procedural memory; ordinary ChatGPT decides how to combine them.

Specialized local models are tools for vision/OCR/grounding/extraction/classification. Stored workflows are guidance/evidence. Neither may silently become a second planner.

## 2. Off-the-shelf first

For transport, MCP runtime, discovery, lifecycle, model serving and common integrations, use maintained ecosystem components before writing project code.

```text
official/vendor MCP or runtime
  -> mature OSS MCP/runtime
  -> mature generic/local API or CLI adapter
  -> smallest project-owned focused adapter
```

Do not write a custom generic gateway/broker/model runtime/workflow platform until a concrete upstream gap is demonstrated.

Stage 26 may use upstream implementations such as `Tencent/UI-Mate` as technical references without importing their whole agent/model architecture.

## 3. Evidence before architecture

A component becomes supported only after applicable real install/start/health/tool-call/task acceptance. Documentation/design is not acceptance evidence.

When CI/docs disagree, investigate code/logs. Distinguish local/runtime failure from Chat product admission/safety failure.

For procedural memory, distinguish:

- one successful trajectory;
- a compiled candidate skill;
- a verified/promoted reusable skill.

Do not collapse those into one claim.

## 4. Thin project-owned surface

Allowed project code should normally be lifecycle/configuration convenience, compatibility/acceptance tests, focused adapters, or the smallest procedural-memory schemas/state/verifiers needed for the product boundary.

Do not rebuild generic tunnels, MCP gateways, registries, vaults, databases, job systems, policy engines, autonomous agent runtimes or general model-serving stacks without a measured requirement.

## 5. Stable truthful typed capability boundary

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Adding/removing a backend should not normally require another ChatGPT app/plugin. Preserve concrete schemas and truthful semantics; do not hide heterogeneous operations behind opaque generic dispatch.

The current count of five is a proven contract, not a permanent dogma. After Windows desktop surface exists, explicitly decide whether new truthful public capability names are required. Never overload existing tools with unrelated behavior solely to preserve the count.

## 6. Task-driven lifecycle and task-driven capability selection

Do not run the whole backend catalog permanently. Start what the task needs, reuse active backends across dependent stages, and stop idle heavyweight components.

Do not preselect a fixed future list of local programs merely because they were previously discussed. Select concrete integrations/benchmarks from real user tasks and evidence when the relevant capability stage is reached.

## 7. Security enables controlled capability

Use least privilege and negative tests, but do not turn security into capability paralysis.

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedural skill trust:

```text
CANDIDATE -> VERIFIED -> PROMOTED
```

These are separate. A trusted workflow is not blanket authorization for its actions.

Prefer scoped roots/resources, reversible workspaces, backups/git/rollback and tool allowlists. Reserve confirmation for genuinely consequential or hard-to-reverse effects where practical.

## 8. Current state beats memory

Procedural memory must never become blind replay.

Execution priority:

```text
current observed state
  > completion criteria / current subtask goal
  > prior successful milestones
  > historical low-level action sequence
```

When remembered procedure conflicts with live state, adapt or ABSTAIN.

Compiled skills must not contain actionable replay coordinates as the solution.

## 9. Completion is verified, not merely asserted

ChatGPT may propose that a subtask is complete, but workflow state advances only after applicable verification:

```text
PASS -> advance
FAIL -> remain
UNKNOWN -> observe / ABSTAIN / user input
```

Prefer deterministic/native verification where available; bounded vision may supply evidence but does not self-authorize completion.

## 10. Procedural memory has a privacy boundary

Do not persist private chain-of-thought.

Store only structured/user-visible intent summaries, actions, observations/results and explicit verification evidence needed for procedural reuse/debugging.

Before long-term arbitrary human-demo storage, define screenshot/text retention, redaction, secret filtering, deletion and versioning policies.

One successful run creates at most a candidate skill. Do not auto-promote based on invented confidence scores.

## 11. No sunk-cost architecture

Git history is the archive. Old code/design docs stay out of the active decision path unless later evidence proves a specific piece useful.

Historical Stage 25 candidate/model docs do not override accepted Stage 25.2 reality. Active continuation docs must state clearly when older files are research/history.

## 12. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce paid model APIs or extra SaaS as mandatory dependencies when ordinary ChatGPT + local bridge satisfies the requirement.

A large local CUA model is not justified merely because an upstream procedural-memory reference uses one; ChatGPT already supplies the planning/intelligence layer.

## 13. Hardware-aware local models

Do not hard-code a model/quantization based on guesswork. Use measured RAM/VRAM/latency and accepted target evidence.

Current accepted local-vision target path is llama.cpp + LFM2.5-VL-450M F16. Future model changes require evidence, not architecture churn.

## 14. Windows desktop surface is a separate capability boundary

Do not blur browser Playwright acceptance into general desktop control.

Stage 26.3 must separately establish:

- native/deterministic UI observation where possible;
- screen capture where needed;
- bounded vision fallback;
- reviewed keyboard/mouse action;
- window/focus/freshness integrity;
- post-action verification and ABSTAIN.

True arbitrary human “show me once” capture belongs at or after this boundary.

## 15. Acceptance ownership and continuation discipline

Keep `START_HERE.md`, `CURRENT_STATE.md`, the active stage contract, `ROADMAP.md` and relevant ADRs synchronized at architecture-changing points.

Codex/automation should perform all locally accessible acceptance when environment/permissions allow it. Reserve user participation for gates that specifically require the real ordinary ChatGPT UI/custom-app path or another irreducible user-only action.

Never claim a local-machine or ordinary-Chat test unless that exact path actually ran. Preserve local uncommitted work before syncing remote code/docs. Use isolated branches/worktrees for independent work.

## 16. Context transfer is a product-development requirement

A fresh ChatGPT/Codex session should be able to determine:

- current merged `main`;
- what is actually accepted;
- the active stage and exact next gate;
- historical files that must not override current design;
- residual risks;
- whether user-machine/ordinary-Chat evidence is required.

When a stage closes, audit entry-point docs instead of only adding another historical handoff file.

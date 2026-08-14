# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/DECISIONS.md`
5. `project-context/ROADMAP.md`
6. `project-context/DEVELOPMENT_PRINCIPLES.md`

For module work also read `project-context/MODULE_SELECTION_POLICY.md` and `project-context/MODULE_CATALOG.md`.

## Source-of-truth order

When documents disagree, use this order:

1. current code, tests and current CI/log evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. accepted ADRs in `DECISIONS.md` and `ARCHITECTURE.md`;
4. `ROADMAP.md`;
5. `README.md` and historical PR text.

Do not revive an older design merely because it is still mentioned in Git history or an old PR description.

## Product boundary

- ordinary ChatGPT Chat is the primary intelligence/planning/orchestration layer;
- local components expose capabilities through standard MCP or the smallest focused local adapter around a strong local API/CLI;
- do not add a second planner, autonomous workflow brain or general-purpose agent runtime behind ChatGPT;
- specialized local inference is allowed as a replaceable capability backend when it performs bounded perception/extraction/classification work rather than taking over planning. A local vision model is an example: Chat remains the brain, the local model is an eye;
- prefer official/vendor MCP, then mature OSS MCP, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not build a project-owned tunnel, generic MCP gateway, registry, vault, job system or policy platform while an accepted ecosystem component covers the boundary.

## Current direction

Stage 24 no longer treats the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` contract as the expected ordinary-Chat product surface. The adaptive runtime remains useful diagnostic/CI infrastructure, but the real Chat gate admitted typed backend actions and blocked the generic/lifecycle path before MCP execution.

Real ordinary-Chat evidence now proves that concrete typed Filesystem and Playwright actions can work through one `Chat Local Bridge Test` app in the same conversation, including scoped reads/writes plus browser navigation/find/click. A separate experiment also showed an effective Chat-facing snapshot truncation around 20 actions in the tested app; this is measured behavior, not an official OpenAI limit.

The Stage 24 scaling problem is therefore: preserve concrete typed schemas and truthful action semantics while making a large local capability catalog usable without one ChatGPT app per backend or hundreds of simultaneously published tools. Do not solve this by relabeling an opaque generic dispatcher as harmless.

Direct `files-readonly` and `browser-isolated` profiles remain deterministic diagnostics/reference paths during convergence.

## Safety without capability paralysis

Use the model `AVAILABLE -> ACTIVE -> AUTHORIZED`:

- a backend may be registered without running;
- start only the backend(s) needed for the current task;
- multiple backends may run together when the task genuinely requires it;
- scope local roots, credentials and destructive operations at the strongest practical boundary;
- prefer rollback, backups, git and contained workspaces over a confirmation dialog for every low-risk action;
- reserve explicit confirmation for genuinely consequential or hard-to-reverse effects rather than creating approval fatigue;
- OpenAI app permissions are not the only safety layer: real testing showed that a composite workflow can be blocked by OpenAI safety even when the same typed actions pass individually under full app access.

## Local specialist inference direction

After Stage 24, evaluate LM Studio/`llmster` as a replaceable local model-runtime manager rather than embedding one model/runtime into platform core. The runtime should support capability/model discovery, memory estimation before load, hardware-aware variant choice, load/JIT/TTL/unload behavior and a stable typed `local-vision` boundary.

`LiquidAI/LFM2.5-VL-3B` is the first preferred vision candidate because Liquid AI officially released it on 2026-08-12 with screen/UI understanding, OCR/document/chart understanding, grounding, multi-image input and day-one GGUF/llama.cpp plus ONNX support. It is a candidate, not yet product-accepted on the target Windows machine.

Do not hard-code the platform to LFM2.5-VL-3B or LM Studio. Model/runtime selection remains replaceable and evidence-driven.

## Development workflow

- inspect the actual repository/PR/CI state before editing;
- use stage branches and isolated worktrees for parallel agents;
- parallelize only independent work; do not let agents concurrently edit the same files in one working tree;
- `main` is the integration line for accepted stages, not a shared scratch branch;
- do not force-push or rewrite `main` history;
- Codex should perform local-machine acceptance itself whenever its environment and permissions allow it, including Windows, CLI, process lifecycle, local applications, MCP backends and local integration tests;
- do not ask the user to perform a local test that Codex can perform itself;
- ordinary ChatGPT UI/custom-app acceptance is a separate gate: when a test specifically requires the real ordinary-Chat user path, provide one precise user test and wait for the actual result instead of spending agentic work on reproducing that UI path;
- never substitute a mock, local MCP client or Codex-only browser test for a claimed ordinary-Chat E2E pass;
- after the user reports the ordinary-Chat result, record the evidence in project context and continue development;
- when local working-tree documentation differs from remote docs, preserve the local diff before pulling/rebasing and reconcile it intentionally rather than discarding it.

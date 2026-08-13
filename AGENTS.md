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

- ordinary ChatGPT Chat is the intelligence/planning layer;
- local components expose capabilities through standard MCP;
- do not add a second planner, autonomous workflow brain or model-runtime dependency behind ChatGPT;
- prefer official/vendor MCP, then mature OSS, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not build a project-owned tunnel, generic MCP gateway, registry, vault, job system or policy platform while an accepted ecosystem component covers the boundary.

## Current direction

Stage 24 is evaluating one stable Chat-facing 1MCP surface with Lazy Loading and task-driven backend lifecycle. The goal is to add future local capabilities without creating a new ChatGPT app/plugin or requiring a Refresh for every backend.

The adaptive path is **not accepted yet**. Direct `files-readonly` and `browser-isolated` profiles remain working diagnostic/reference paths until adaptive acceptance and real ordinary-Chat validation pass.

Do not create a separate ChatGPT app/plugin for every capability as the default architecture.

## Safety without capability paralysis

Use the model `AVAILABLE -> ACTIVE -> AUTHORIZED`:

- a backend may be registered without running;
- start only the backend(s) needed for the current task;
- multiple backends may run together when the task genuinely requires it;
- scope sensitive operations and keep dangerous administrative tools out of the Chat-facing surface;
- avoid an always-on broad local-files + open-web baseline, but do not turn that into a blanket ban on legitimate multi-tool workflows.

## Development workflow

- inspect the actual repository/PR/CI state before editing;
- use stage branches and isolated worktrees for parallel agents;
- parallelize only independent work; do not let agents concurrently edit the same files in one working tree;
- `main` is the integration line for accepted stages, not a shared scratch branch;
- do not force-push or rewrite `main` history;
- do not claim a real Windows or ordinary-Chat acceptance test unless it actually ran on the target user surface;
- if a final gate requires the user's machine or ChatGPT UI, provide one precise test and wait for the result.

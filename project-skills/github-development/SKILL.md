---
name: github-development
description: Prepare, verify, and hand off Chat Agent Platform repository changes for Git and GitHub while preserving project binding, local work, test evidence, reviewability, and guarded boundaries. Use for branch, commit, pull request, CI, release, issue, review, or GitHub handoff requests involving this repository, including local preparation when GitHub access is unavailable.
---

# GitHub Development

Prepare locally first. Network access is an execution capability, not a prerequisite
for code quality.

## Workflow

1. Resolve the explicit repository and read `CURRENT_STATE`, `CONSTRAINTS`, and the
   relevant roadmap stage.
2. Inspect `git status`; preserve unrelated user changes.
3. Make one cohesive change and run its real validation path.
4. Use `project-context/HANDOFF_TEMPLATE.md` as a source template; do not overwrite
   it. Put the completed handoff in the task/PR description or a dedicated report.
5. Before a commit, require configured Git author identity; never invent it.
6. Before push/PR, verify the target remote/repository and available GitHub surface.
7. Report the exact local verification and any unavailable external step.

## Guardrails

- Never force-push, rewrite shared history, merge main, or modify secrets implicitly.
- Treat merge, release, secret changes, and destructive branch operations as guarded.
- Do not claim CI/PR success from local tests.
- Keep Cargo.lock and contract fixtures with the change that depends on them.
- Prefer a small reviewable diff over a mixed refactor/feature/migration change.
- Use `scripts/verify.ps1`; do not require pytest because the Python oracle uses unittest.

# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

## Read first

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/START_HERE.md`
3. `project-context/CURRENT_STATE.md`
4. `project-context/ROADMAP.md`
5. `project-context/ARCHITECTURE.md`
6. `project-context/MODULE_CATALOG.md`
7. `project-context/KNOWN_ISSUES.md`
8. active stage document, currently `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md` while Stage 26.2E is open
9. older accepted qualification docs only as historical evidence when needed

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`;
3. `ROADMAP.md`, `ARCHITECTURE.md`, `MODULE_CATALOG.md`, `KNOWN_ISSUES.md`;
4. active/accepted stage documents;
5. `DECISIONS.md` and `DEVELOPMENT_PRINCIPLES.md`;
6. historical research/handoffs/older revisions.

Always resolve live `main` and relevant PR heads before branching/editing. Never treat a documentation SHA as permanently current.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

## Public semantic contract

Current Chat-facing tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Normal path:

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure.

## Non-negotiable product boundary

- ordinary ChatGPT is the only general planner/intelligence;
- local components may provide deterministic observation/execution, bounded specialist perception, verification and non-agentic procedural memory;
- no second local planner/Agent Control Plane/autonomous workflow brain;
- no generic hidden `tool_invoke`, shell/Python executor or unbounded workflow dispatcher;
- current observed state outranks remembered procedure;
- observation is not authorization;
- procedure/model proposal is not authorization;
- action delivery is not completion evidence;
- stale/ambiguous/UNKNOWN evidence causes zero mutation;
- prefer mature upstream, then the smallest focused project adapter for a measured gap;
- do not duplicate qualified OpenAdapt mechanisms without a demonstrated blocker.

## Accepted browser foundation

Stage 25.2 remains semantic/native first. Local LFM2.5-VL-450M F16 is proposal-only and remains behind deterministic target/freshness authorization.

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
CPU 8 threads
ctx 2048
```

## Accepted Windows foundation

### Stage 26.1A / 26.1B

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
Capture qualification head = 7a9daa9329d81994833c22b4ca2e321927527dcc
```

### Stage 26.1C–26.1E — accepted and merged #83/#84/#85

Typed executor accepted; warm desktop-wide UIA blocker measured; exact-window UIA accepted. Controlled Stage 26.1E evidence: 97 scoped resolutions, zero Desktop fallback/binding failures/ambiguities/false/unrelated-window actions, about 3.324 s p50 / 3.720 s p95.

### Stage 26.2A — production Windows runtime — accepted / merged #87

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA.

### Stage 26.2B — DesktopState — accepted / merged #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is evidence only. Observation fingerprints are not executor authorization.

### Stage 26.2C — native Desktop Grounder — accepted / merged #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Grounder returns proposal/ABSTAIN only. The physical ordinal-label behavior is narrowly handled; no general fuzzy matching.

### Stage 26.2D — structure-first Windows vision routing — accepted / merged #90

Integration `main` after merge:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical run proved one real guarded visual-fallback click after fresh frame/evidence/native foreground-hit-test authorization, with correct no-promotion/role-conflict/wrong-window refusals and no Desktop fallback/binding failures/ambiguities. This remains controlled WinForms evidence.

## Current critical path

```text
Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 release work
```

While Stage 26.2E is active, the qualification branch is `chat/stage26-2e-vscode-real-app-e2e`. It uses an isolated VS Code profile and one disposable TEMP file, one guarded keyboard mutation, independent file SHA verification and rollback. Read the active stage document before changing this contract.

Do not replace Stage 26.3 with a local generic planner. Verified Procedure Runtime is bounded support for ordinary ChatGPT, not a new agent brain.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable review/acceptance checks are satisfied, merge it without waiting for a separate merge command.

Do not auto-merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

## Development workflow

- inspect live repository/PR/CI state before editing;
- branch from the exact intended base;
- preserve physically tested runtime heads and evidence;
- distinguish docs-only descendants from physically tested code heads;
- keep `main` as integration line, not scratch;
- never rewrite/force-push `main`;
- use the user only for irreducible target-machine or ordinary-Chat UI gates;
- never claim a target path passed unless that exact path ran;
- do not weaken fail-closed behavior to improve hit rate;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- track browser network isolation, Windows root/junction containment, credential isolation and release-grade artifact reproducibility as cross-cutting requirements.
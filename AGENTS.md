# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/DECISIONS.md`
6. `project-context/ROADMAP.md`
7. `project-context/KNOWN_ISSUES.md`
8. `project-context/DEVELOPMENT_PRINCIPLES.md`

Stage 25/25.1 research and handoff documents remain useful historical evidence, but they are no longer the active continuation contract. In particular, `ACTIVE_VISUAL_GROUNDING.md`, `LOCAL_SPECIALIST_INFERENCE.md`, `STAGE25_TARGET_BENCHMARKS.md`, `STAGE25_CHAT_HANDOFF_2026-08-17.md` and `STAGE25_1_VISION_INTEGRATION.md` must not override the merged Stage 25.2 state or Stage 26 plan.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. the active stage contract `STAGE26_PROCEDURAL_MEMORY.md`;
4. `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`;
5. `DEVELOPMENT_PRINCIPLES.md` and current capability contracts;
6. historical research/handoff documents and older README revisions.

Do not revive an older design merely because it remains in Git history.

## Current accepted line

Current `main` after Stage 25.2:

`2a410476ef849fd6d9c172703a004b1befcbcfb1` — `Stage 25.2: semantic-first internal vision escalation (#77)`.

Public semantic tools remain exactly:

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

## Product boundary

- ordinary ChatGPT Chat is the primary and only planning/intelligence layer;
- local components expose deterministic capabilities, bounded specialist perception, or non-agentic procedural memory;
- never add a second planner, autonomous workflow brain, generic local agent runtime, or hidden `tool_invoke` equivalent behind ChatGPT;
- a stored workflow is guidance/evidence, not a planner and not authorization;
- current observed state outranks remembered procedure;
- prefer official/vendor MCP/runtime, then mature OSS, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not build a project-owned generic tunnel/gateway/registry/vault/job/policy platform while accepted ecosystem components cover those boundaries.

## Stage 25.2 accepted behavior

`web_interact(click)` is semantic-first. Vision is allowed only after a reviewed zero-exact-candidate semantic miss for the promoted text-labeled button path. Disabled/non-button exact matches and unresolved semantic ambiguity ABSTAIN without starting VLM. Planner `target`/free-form `instruction` cannot redirect visual authorization away from `targetText`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Final real target result: 2 semantic HIT, 1 real-F16 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors, `semantic_cases_started_vlm=0`, `acceptance_pass=true`, runtime stopped afterward and Chrome remained running.

## Active Stage 26 direction

The next stage is Procedural Memory / Demo2Workflow, based on an upstream technical analysis of `Tencent/UI-Mate` pinned in `STAGE26_PROCEDURAL_MEMORY.md`.

Do not turn this into a second GUI agent. Implement a small local substrate for trajectory recording, workflow compilation, skill storage/versioning, retrieval evidence, workflow progress and completion verification while ChatGPT remains the planner.

Specific local programs/capabilities are selected later from actual tasks and evidence; do not hard-code a future application list into architecture.

**Windows desktop surface is an explicit planned Stage 26.x item and must not be forgotten.** Only after that surface exists should the project decide, via a separate ADR and ordinary-Chat acceptance, whether the public contract needs new tool names or can preserve the same small-semantic-surface philosophy.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- create stage branches from exact current `main`;
- keep `main` as integration line, not scratch;
- do not force-push/rewrite `main`;
- update authoritative documentation whenever accepted architecture/runtime/security evidence changes;
- distinguish deterministic CI from real target-machine and ordinary-Chat acceptance;
- use the user only for irreducible target-machine or Chat UI gates;
- never claim a target/ordinary-Chat result unless that exact path ran;
- preserve/reconcile local uncommitted work rather than discarding it;
- do not weaken fail-closed behavior merely to increase benchmark hit rate;
- never persist private chain-of-thought into procedural memory; keep only structured/user-visible intent, actions, observations and verification evidence;
- do not describe browser filters or loopback PID checks as stronger isolation/authentication than actually proved.

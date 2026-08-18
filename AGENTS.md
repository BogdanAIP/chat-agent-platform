# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md`
4. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
5. `project-context/ARCHITECTURE.md`
6. `project-context/DECISIONS.md`
7. `project-context/ROADMAP.md`
8. `project-context/KNOWN_ISSUES.md`
9. `project-context/DEVELOPMENT_PRINCIPLES.md`

Stage 25/25.1 research and handoff documents remain useful historical evidence, but they are no longer the active continuation contract. Do not revive an older design merely because it remains in Git history.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. `STAGE26_1A_OPENADAPT_QUALIFICATION.md` and `STAGE26_PROCEDURAL_MEMORY.md`;
4. `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`;
5. `DEVELOPMENT_PRINCIPLES.md` and current capability contracts;
6. historical research/handoff documents and older README revisions.

## Resolve live repository state first

Do not hard-code a documentation merge SHA as “current main”. Before any new work, resolve live `main` from GitHub and record it in the branch/PR/handoff evidence.

Stable milestones:

- Stage 25.2 runtime/code baseline: `2a410476ef849fd6d9c172703a004b1befcbcfb1` — PR #77;
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` — PR #78;
- Stage 26.1A target-tested qualification code: `f8e8f606db845821b8fa24c09f9032015fb0e79e` — PR #80 branch before docs-only descendants.

Live `main` may be newer than any of these.

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
- prefer official/vendor runtime, then mature OSS, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not duplicate accepted upstream mechanisms without a demonstrated integration/security/product blocker.

## Stage 25.2 accepted behavior

`web_interact(click)` is semantic-first. Vision is allowed only after a reviewed zero-exact-candidate semantic miss for the promoted text-labeled button path. Disabled/non-button exact matches and unresolved semantic ambiguity ABSTAIN without starting VLM. Planner `target`/free-form `instruction` cannot redirect visual authorization away from `targetText`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Final real target result: 2 semantic HIT, 1 real-F16 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors, `semantic_cases_started_vlm=0`, `acceptance_pass=true`, runtime stopped afterward and Chrome remained running.

## Active Stage 26 direction

Stage 26 is Procedural Memory / Demo2Workflow, but the implementation plan changed after a broader upstream qualification.

### Stage 26.0 — DONE

`Tencent/UI-Mate` remains a workflow-guidance reference: rich demonstration evidence -> compact current-subtask guidance while live state stays authoritative. Do not adopt UI-Mate as a second planner/agent.

### Stage 26.1A — OpenAdapt core qualification — TARGET PASS

Pinned and target-tested:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`

Target result: exact package commits verified, `PHASE_B_PASS=True`, `PHASE_C_TUTORIAL_PASS=True`, no probe/error, Chrome 15->15, `TEST_EXIT_CODE=0`.

Decisions:

- Flow compiler + `Workflow`/`ProgramGraph`: **ADOPT** behind project boundaries;
- `SkillLibrary` + learning/teach lifecycle: **ADAPT**, because project trust remains candidate-first;
- Capture: qualify on real bounded Windows before adoption; do **not** build a project recorder first;
- Windows backend/agent: security A/B still required;
- local F16: prototype through OpenAdapt's proposal-only `Grounder` seam after capture qualification;
- OpenAdapt Desktop: Stage 27 distribution/cockpit reference only for now.

No OpenAdapt code is integrated into production `semantic-projection` or the installed product path yet.

### Next — Stage 26.1B real Windows Capture qualification

Use a harmless bounded fixture. Prove window scope, click/type/key/scroll capture, UIA evidence where available, conversion/compile/replay or bounded refusal, zero false/unrelated-window actions, local raw-artifact containment and clean cleanup.

Specific local programs/capabilities are selected later from actual tasks and evidence; do not hard-code a future application list.

### After capture — Stage 26.1C executor A/B + F16 seam

Compare OpenAdapt typed Windows agent against a narrower actuator boundary. The pinned server's legacy `/execute_windows` route is disabled by default; product configuration must prove it cannot be enabled/reached. Then test the accepted LFM2.5-VL F16 through the narrow Grounder protocol.

### Stage 26.2 — ChatGPT procedural integration

Integrate only accepted upstream components behind the ChatGPT-only planner boundary. Retrieval/procedure selection is non-authorizing; current state outranks history; verifier/effect evidence controls completion; bootstrap procedures follow project candidate policy.

### Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

**Windows desktop surface remains an explicit required stage and must not be forgotten.** Productize whichever Windows observation/actuation/verification combination wins qualification.

Only after that surface exists should the project decide, via a separate ADR and ordinary-Chat acceptance, whether the public contract needs new tool names or can preserve the same small-semantic-surface philosophy.

## Development workflow

- resolve live `main` before branching/editing;
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
- never persist private chain-of-thought into procedural memory;
- treat raw capture as sensitive local data until retention/redaction/encryption policy is accepted;
- do not describe browser filters, loopback PID checks or typed Windows routes as stronger isolation/authentication than actually proved.

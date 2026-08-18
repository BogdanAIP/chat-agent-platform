# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## Current accepted integration line

Current accepted `main`:

`2a410476ef849fd6d9c172703a004b1befcbcfb1` — `Stage 25.2: semantic-first internal vision escalation (#77)`.

The ordinary-Chat path is:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

The current public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. ChatGPT remains the only planner/intelligence.

## Accepted foundation through Stage 25.2

- Stage 24: five-tool semantic surface and Windows lifecycle accepted.
- Stage 24.1: direct semantic tunnel selected as normal path.
- Stage 25: LFM2.5-VL-450M F16 local grounding baseline accepted on the target laptop; present-target accuracy remains 3/5 because repeated-row/tiny are deliberately unpromoted.
- Stage 25.1: same-session screenshot -> grounding -> freshness -> coordinate action/ABSTAIN foundation accepted and merged.
- Stage 25.2: first public semantic-first internal vision escalation accepted and merged in PR #77.

Stage 25.2 final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Final target evidence with normal Chrome workload open:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

### Stage 25.2 routing invariant

```text
fresh accessibility snapshot
  -> exact enabled button: semantic click; VLM stays stopped
  -> same-name buttons with exactly one enabled + disabled alternatives: semantic click
  -> disabled/non-button/ambiguous exact semantic evidence: ABSTAIN; VLM stays stopped
  -> zero exact candidates:
       same Playwright page/session screenshot
       -> reviewed F16 text-labeled visual grounder
       -> deterministic authorization
       -> freshness proof
       -> one coordinate click OR ABSTAIN
```

`targetText` is the authorization anchor. Planner `target`, free-form `instruction` and planner-supplied `kind` cannot redirect visual authorization.

## Active development priority — Stage 26 Procedural Memory / Demo2Workflow

Read `project-context/STAGE26_PROCEDURAL_MEMORY.md` before implementation work.

Stage 26 is based on a technical review of official `Tencent/UI-Mate` pinned to upstream commit `d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`.

Core direction:

```text
successful trajectory
  -> raw structured evidence
  -> Demo Compiler
  -> coordinate-free versioned candidate skill
  -> compact current-subtask guidance
  -> current observed state stays authoritative
  -> completion verifier
  -> evidence-based promotion / stale / disable
```

A workflow is procedural memory, not a second planner and not action authorization. ChatGPT still chooses how to solve the user's task.

Do not store private chain-of-thought. Procedural traces may store structured/user-visible intent summaries, semantic actions, observations, result classifications and verification evidence only.

## Stage 26 order

1. **26.0 — upstream analysis and contract:** documentation/design; current step.
2. **26.1 — procedural data foundation:** raw trajectory schema, redaction/retention, compiled skill schema, versioned skill store, validators. No public tool change.
3. **26.2 — Demo Compiler + verifier + self-demo dogfood:** compile successful existing Chat/semantic trajectories; prove coordinate-free current-state-first reuse including a changed/variant case.
4. **26.3 — Windows desktop surface:** explicit required stage. Native/semantic observation first, screen/vision where needed, reviewed keyboard/mouse execution, fail closed.
5. **26.4 — human demonstration capture + transferable skill acceptance:** only after desktop observation/actuation can capture real arbitrary user demonstrations honestly.
6. **26.5 — public contract decision:** only after desktop surface exists, decide explicitly whether new public tool names are needed or whether the existing small-semantic-surface philosophy can continue with a few coarse truthful actions.

Specific local programs/capabilities are selected later from actual tasks and evidence. Do not precommit the roadmap to a fixed application list.

## Public contract rule during Stage 26 foundation

Until the explicit post-desktop decision:

- current accepted public tool names remain the same five;
- procedural-memory components stay internal/non-agentic unless a truthful Chat-facing boundary is separately designed and accepted;
- do not hide workflow CRUD/execution behind misleading existing tool semantics;
- do not add a generic opaque workflow dispatcher as a renamed `tool_invoke`.

## After Stage 26

Stage 27 is distribution/maintenance hardening: stable install artifact, locked Python/model artifacts, installer/update/repair/doctor/uninstall, key rotation, upgrade/rollback and restart recovery.

Stage 28 is the clean-user product E2E + first stable release gate.

## Residual risks that remain explicit

- repeated-row/tiny/icon-only automatic visual promotion is incomplete;
- screenshot and coordinate click remain a narrow non-atomic TOCTOU boundary;
- PID-bound loopback is not cryptographic endpoint authentication;
- DNS/rebinding/redirect browser isolation is incomplete;
- Python/model packaging is not release-grade;
- deprecated transitive `glob@10.5.0` remains a dependency follow-up;
- procedural-memory runtime/skill lifecycle is not implemented yet;
- Windows desktop surface and arbitrary human demo capture are not implemented yet;
- no stable release exists yet.

## Non-negotiable product boundary

- ordinary ChatGPT remains the planner/intelligence;
- local models are bounded perception/extraction backends, never a second planner;
- remembered procedures are bounded guidance/evidence, never a second planner;
- prefer semantic/native structure over vision whenever deterministic structure exists;
- visual grounding must fail closed;
- keep the public tool surface small and truthful;
- preserve single-owner/fail-closed lifecycle guarantees;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. this file and `CURRENT_STATE.md`;
3. `STAGE26_PROCEDURAL_MEMORY.md`;
4. `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`;
5. `DEVELOPMENT_PRINCIPLES.md` and current capability contracts;
6. Stage 25/25.1 research, dated handoffs and older README revisions.

Stage 25.1 documents remain useful for low-level same-session/vision history but are not the active continuation guide.

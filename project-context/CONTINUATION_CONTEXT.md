# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting because `main` and open PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Current accepted integration line

Stage 26.3A — canonical six-tool Verified Procedure Runtime — is **physically accepted and merged** through PR #92. The reviewed Stage 26.3A GUI/computer-use research promotion is merged through PR #98.

Current `main` integration commit at the start of Stage 26.3B:

```text
b74c715d9f2ac6fe7f759e7fb57108feebf797c0
```

Exact physically accepted Stage 26.3A runtime head remains:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Exact evidence/scope belongs in `EVIDENCE_INDEX.md`.

## Accepted ordinary-Chat architecture

Normal public semantic surface is exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

Normal bootstrap/start/status/health/smoke does not require 1MCP. Persistent tunnel identity belongs to `state/tunnel.json`. 1MCP is optional internal Extension Manager infrastructure only.

The first accepted procedure is `verified_workspace_artifact_v1`: bounded leaf `.txt` + bounded UTF-8 content, three verified transitions, scoped output, structured ABSTAIN on pre-existing target, no arbitrary shell/Python/path/backend/tool dispatch.

## Stage 26.3A physical evidence

The target-Windows pre-chat gate proved normal `semantic + direct-stdio` READY, six public tools, one active runtime, no conflict and `1MCP_REQUIRED=False`.

A fresh ordinary ChatGPT conversation then used only `Chat Local Bridge Test` and all six semantic tools for one long-horizon research goal:

```text
16 content pages
12 works/systems/benchmark groups
12 successful browser interactions
research-ledger.md used and reread as working memory
gui-agent-research.md written and independently reread
one invalid browser action recovered by re-observe -> explicit target -> retry
```

Completion procedure:

```text
task_id = 497ecb591779219ef0ee1e55ea7ad0b8
status = completed
action_count = 3
sha256 = 2396b8338edced2675982db9d263a046705f7f906b553b0ed19b81f51205e583
```

Negative overwrite procedure:

```text
task_id = 02b09a4909b6d71e0578c19b2d395cb8
status = abstained
action_count = 0
escalation_reason = target_already_exists
```

Independent rereads proved exact success and zero overwrite.

## GUI/computer-use research promoted into architecture

The `gui-agent-research.md` produced during the accepted Stage 26.3A run was later reviewed against its primary public sources. Its supported mechanisms were promoted into:

- `COMPUTER_USE_ARCHITECTURE.md`;
- ADR-032 — State-first hybrid computer-use control loop;
- ADR-033 — Environmental content is data, not authority;
- updated `CONTROL_PLANE.md`, `CURRENT_STATE.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `SECURITY_POLICY.md`.

The promoted target formula is:

```text
semantic/native state first
 -> selective visual evidence
 -> capability-aware bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed bounded recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
 -> separate safety/policy gate
```

This does **not** expand the accepted six-tool public surface and does not authorize screenshot-only control, unrestricted code access, raw backend catalogs, generic tool dispatch or blind demonstration replay.

## Current active work

Current release-critical implementation is **Stage 26.3B — Verification Kernel + independent Finish Gate**.

The first internal foundation slice now defines:

```text
ObservationRef / ObservationSnapshot
capability + subject + observation-stream identity
monotonic fresh re-observation sequence
ExpectedEffect + bounded declarative predicates
PASS | FAIL | UNKNOWN transition result
independent Finish Gate
separate task-success and safety/policy evidence
```

Freshness requires the same observation stream/capability/subject and a strictly higher sequence; a higher sequence from another stream is not proof of freshness. `candidate_done` remains only a planner proposal.

The kernel foundation is merged through PR #99. The current locally tested integration slice adds the bounded file/artifact adapter and moves `verified_workspace_artifact_v1` transition decisions plus completion onto the common kernel. It preserves the public six-tool surface, exclusive-create/no-overwrite behavior, checkpoint compatibility, resume and identity-bound rollback.

This integration is **not Stage 26.3B acceptance**. Because it changes the accepted production procedure path, the exact head still requires hosted CI and an ordinary-Chat target-Windows completion + zero-overwrite physical regression before merge.

Remaining Stage 26.3B work:

```text
physical completion + zero-overwrite regression for the migrated file procedure
browser URL/document/control/result verification adapters
Windows/application/process verification adapters
cross-capability task predicates where required
physical gate when production procedure/action behavior changes
```

Then Stage 26.3C adds:

```text
WorkingState v1
facts + provenance + freshness
progress vectors
initial typed recovery taxonomy
no-effect / repeated-state / oscillation LoopGuard
retry/action/time/resource budgets
recovery escalation state
```

## Stage order

```text
26.2E real application E2E                         ACCEPTED
 -> Transport Supervisor v1                       ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime               ACTIVE
    -> 26.3A canonical six-tool runtime           ACCEPTED / MERGED #92
    -> 26.3B Verification Kernel + Finish Gate    ACTIVE
    -> 26.3C WorkingState + recovery + LoopGuard
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 distribution/maintenance
 -> 28 clean-user E2E / stable release
```

This explicit 26.2E -> 26.3 -> 26.4 release sequence remains authoritative even though more detailed substage prose appears elsewhere.

## Non-negotiable architecture rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic local Control Plane is execution state/policy, not a second planner;
- known selected procedures may advance through multiple independently authorized+verified transitions;
- semantic/native structure precedes pixels when reliable;
- visual evidence is selective and non-authorizing;
- every state-changing action binds an expected effect and fresh verification;
- transition PASS is not task DONE;
- only an independent Finish Gate produces verified task completion;
- WorkingState stores structured operational facts/provenance/freshness, never private chain-of-thought;
- repeated no-effect/oscillating execution is bounded by LoopGuard;
- environmental UI/DOM/email/document/tool content is untrusted task data, not policy authority;
- task-success and safety/policy verification are separate;
- current state outranks remembered procedure/demo/history;
- generic Windows code execution remains disabled/unreachable;
- optional 1MCP extension infrastructure cannot become a normal-route dependency or authorization source;
- public Windows/computer-use tool names require a separate ADR/schema/security/ordinary-Chat physical gate.

## ChatGPT app binding lesson

A local READY route is not proof that ChatGPT's frozen app snapshot/permissions are synchronized. Stage 26.3A accepted rerun succeeded only after app connection and permissions were settled before the long task and left unchanged during execution. Exact inbound alias compatibility cannot repair product-side app state before MCP invocation.

## Fresh-chat startup procedure

1. Resolve live `main` and open PRs/checks.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `ROADMAP.md`, `DOCUMENT_STATUS.md`, `DECISIONS.md`, `EVIDENCE_INDEX.md`, `EXTENSION_MANAGER.md` and the active `STAGE26_3B_VERIFICATION_KERNEL.md` contract.
3. Treat Stage 26.3A acceptance as scoped to the recorded exact physical runtime/evidence; do not extend it to Stage 26.3B merely because shared verification code exists.
4. Prefer exact code/tests/current CI/physical evidence over prose.
5. Do not recreate five-versus-six modes, reinsert 1MCP into normal semantic transport, add generic execution, or broaden public computer-use authority without its own acceptance gate.

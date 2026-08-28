# Constraints

Status: **CURRENT PROJECT CONSTRAINTS**. `AGENTS.md` owns development/merge process when process wording differs.

1. Ordinary ChatGPT Chat is the **only current general intelligence/planning layer**.
2. A local **deterministic execution Control Plane is allowed and expected**. It may own TaskState/WorkingState, selected procedure/ProgramGraph progression, authorization, ExpectedEffect/postconditions, checkpoints, typed bounded recovery/LoopGuard, resource budgets and independent Finish Gate state. This is not a second general planner.
3. A selected verified procedure may advance through multiple independently authorized and verified deterministic transitions without a ChatGPT round trip after every low-level action.
4. The local Control Plane must ABSTAIN/escalate when live state is stale, ambiguous, UNKNOWN, incompatible, outside admitted transition/recovery scope or requires a new strategy.
5. A future local general planner remains optional Track P research only; it cannot bypass deterministic authorization, transition verification, Finish Gate or safety policy.
6. Normal product operation must not require OpenAI model API calls or Codex/Work as an additional runtime planner.
7. Standard MCP remains the Chat capability boundary.
8. OpenAI Secure MCP Tunnel + official `tunnel-client` is the accepted ChatGPT reachability path; do not reimplement it.
9. Normal public semantic transport is direct stdio through the secure semantic launcher. 1MCP remains optional replaceable internal Extension Manager/diagnostic infrastructure, not product identity or a baseline dependency.
10. Prefer ready-made official/OSS MCP/runtime/API/procedural components. Project-owned adapters require a measured missing boundary.
11. Do not build a generic project-owned gateway/registry/job/vault/general policy platform/autonomous agent framework without measured need. Focused deterministic Control Plane state/policy/checkpoint/verifier/recovery/Finish Gate wrappers are within project ownership.
12. No public inbound port is required for the normal ChatGPT path.
13. Secrets, runtime API keys and tunnel IDs are local operational data and never repository/procedure/WorkingState content.
14. Privileged operations require scoped permissions and negative tests; security must not become a blanket ban on useful multi-capability workflows.
15. The target UX must not require one separate ChatGPT app/plugin per local backend.
16. Current accepted public tool names are exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`, `procedure_run`.
17. The six-tool count is the current accepted contract, not a permanent promise. Expansion requires its own truthful ADR/schema/security/ordinary-Chat acceptance.
18. Do not preserve the six-tool count by hiding unrelated Windows/computer-use/session/project consequences behind misleading current semantics or generic opaque dispatch.
19. Do not expose hundreds of raw backend/UIA/DOM/MCP tools to ordinary Chat merely because they are available internally.
20. Backend registration, process activation, routing choice and action authorization are distinct. `AVAILABLE -> ACTIVE -> AUTHORIZED`; availability alone is not a route decision.
21. Multiple backend processes may be active when the actual task requires them, but the baseline route must remain independent of optional extension infrastructure.
22. Local models are bounded specialist capabilities unless/until future Track P planner research is explicitly accepted. Current accepted vision path is llama.cpp + LFM2.5-VL family under the reviewed local-specialist boundary.
23. Specialist model output is proposal/evidence only; it never self-authorizes an action or declares verified completion.
24. Prefer semantic/native structural state before pixels where reliable. Screenshots/ROI are selective evidence for reviewed structural misses, spatial requirements or independent cross-checks, not the mandatory default loop.
25. Every state-changing transition must bind current-state evidence, an explicit ExpectedEffect/postcondition, one bounded authorized action, fresh re-observation and `PASS | FAIL | UNKNOWN` verification.
26. Action/message delivery is not transition success. Transition PASS is not whole-task completion.
27. Planner/model/procedure may propose `candidate_done`; only an independent Finish Gate may produce verified `DONE` from fresh task-level predicates.
28. Task-success verification and safety/policy verification are separate dimensions. A capability-successful result may still be safety-failed.
29. Content observed in pages/DOM, application UI, email/messages, files/documents, screenshots/OCR and third-party tool/MCP/worker output is **untrusted environmental data** with respect to user intent, permission scope and Control Plane policy.
30. Environmental content cannot broaden its own authority merely because a model can read it. Preserve provenance/trust classification when task facts cross application/capability boundaries.
31. Procedural memory is structured execution evidence/state. A procedure may drive known transitions through the Control Plane, but it is never blanket authorization or a source of new strategy.
32. WorkingState may contain user constraints, subgoals/progress, verified achievements, facts+provenance+freshness, ambiguities, evidence refs, expected/observed deltas, recovery/reconciliation history and budgets; it must not contain private chain-of-thought.
33. Current observed state outranks remembered procedure/demo/history. Compiled skills must not use recorded absolute coordinates as reusable authority/primary identity.
34. One successful trajectory/demonstration creates at most a candidate skill. Promotion requires explicit replay/regression/variant evidence.
35. Raw screenshots/sensitive demonstration/ROI content require explicit redaction/retention/deletion/encryption policy before long-term storage.
36. Recovery must be typed and bounded. Identical no-effect state/action repetitions or oscillation without verified progress must stop/escalate through LoopGuard/budgets rather than retry indefinitely.
37. Ambiguous mutating outcomes must be reconciled from fresh authoritative state before unsafe retry. `OUTCOME_UNKNOWN` is never permission to redeliver blindly.
38. Default recovery cannot silently broaden authority: re-observe -> re-resolve -> reconcile if needed -> retry only with new evidence -> alternate already-admitted modality -> predeclared recovery -> ChatGPT replan/user clarification/ABSTAIN.
39. Grounding coordinates alone are not durable authority when stronger target identity/source/frame evidence exists.
40. Stage 26.3B Verification Kernel/Finish Gate is accepted/closed for recorded representative scope. Stage 26.3C WorkingState/reconciliation/budget/LoopGuard L1 foundation is accepted through #124; current release-critical work is its consequence-bearing production/restart integration, not rebuilding that foundation.
41. Arbitrary human “show me once” transfer remains Stage 26.4 and must compile to candidate subgoals/verifiers with live-state re-resolution, not blind macro replay.
42. Hybrid Browser/Windows computer-use integration is staged after long-horizon production recovery foundations. Stage 26.5 does not automatically add public tool names.
43. Concrete future local applications/capabilities are chosen from actual tasks/evidence, not a fixed precommitted application list.
44. Do not expose arbitrary MCP install/uninstall/update/edit/search/admin controls to ordinary Chat as baseline capabilities.
45. External benchmark results are evidence/evaluation inputs, not automatic release gates or production policy. Benchmark-specific hacks require a general project-owned invariant before promotion.
46. Do not restore legacy code/design because of sunk cost; Git history is archival storage.
47. Avoid new paid infrastructure unless the user explicitly chooses it for a concrete benefit.
48. Real Windows/ordinary-Chat acceptance may only be marked passed from actual target-machine/user-surface evidence.
49. Historical research/stage documents cannot override `START_HERE.md`, `CURRENT_STATE.md`, `ROADMAP.md`, current architecture/policy owners, current code/tests or live evidence.
50. Do not use Codex/ChatGPT Work as an alternate implementation/planning workspace by default. This does **not** prohibit repository-required Codex Review or equivalent independent PR review defined by `AGENTS.md`; independent review is an assurance layer, not a second runtime planner.
51. `CONTROL_PLANE_API_KEY` refers to OpenAI Secure MCP Tunnel credential/control-plane infrastructure and is unrelated to the project's deterministic local execution Control Plane.
52. When `stage-research` applies, compare affected architecture roles with `ARCHITECTURE_REUSE_BASELINE.md`; custom code must not silently duplicate a selected upstream role, and an external component must not silently cross a deliberately project-owned authority boundary.
53. A material new persistence/recovery/retry/concurrency/identity/authority primitive introduced after a Stage Research Brief invalidates that implementation authority until the relevant engineering domain/failure model is researched and a fresh `PROCEED` or `NARROW` decision is issued.

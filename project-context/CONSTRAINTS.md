# Constraints

1. Ordinary ChatGPT Chat is the **only current general intelligence/planning layer**.
2. A local **deterministic execution Control Plane is allowed and expected**. It may own TaskState, selected procedure/ProgramGraph progression, authorization, checkpoints, verifier/postconditions, bounded retry/recovery and resource budgets. This is not a second general planner.
3. A selected verified procedure may advance through multiple independently authorized and verified deterministic transitions without a ChatGPT round trip after every low-level action.
4. The local Control Plane must ABSTAIN/escalate when live state is stale, ambiguous, UNKNOWN, incompatible, outside the selected procedure or requires a new strategy.
5. A future local general planner remains an optional research direction only; it is not part of the current release-critical path and cannot bypass the deterministic Control Plane.
6. Normal product operation must not require OpenAI model API calls or Codex/Work as an additional planner.
7. Standard MCP remains the Chat capability boundary.
8. OpenAI Secure MCP Tunnel + official `tunnel-client` is the accepted ChatGPT reachability path; do not reimplement it.
9. Normal public semantic transport is direct stdio through the secure semantic launcher. 1MCP remains replaceable internal/diagnostic infrastructure, not product identity.
10. Prefer ready-made official/OSS MCP/runtime/API/procedural components. Project-owned adapters require a measured missing boundary.
11. Do not build a generic project-owned gateway/registry/job/vault/general policy platform/autonomous agent framework without measured need. Focused deterministic Control Plane state/policy/checkpoint/verifier wrappers are explicitly within project ownership.
12. No public inbound port is required for the normal ChatGPT path.
13. Secrets, runtime API keys and tunnel IDs are local operational data and never repository/procedural content.
14. Privileged operations require scoped permissions and negative tests; security must not become a blanket ban on useful multi-capability workflows.
15. The target UX must not require one separate ChatGPT app/plugin per local backend.
16. Current accepted public tool names are exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`.
17. The five-tool count is a current accepted contract, not a permanent promise. Expansion requires its own ADR/schema/ordinary-Chat acceptance.
18. Do not preserve the five-tool count by hiding unrelated workflow/desktop operations behind misleading current semantics or a generic opaque dispatcher.
19. Backend registration and backend process activation are separate. Do not run the entire catalog permanently.
20. Multiple backend processes may be active when the actual task requires them.
21. Local models are bounded specialist capabilities unless and until a future Track P planner is explicitly researched/accepted. Current accepted vision path is llama.cpp + LFM2.5-VL-450M F16.
22. Specialist model output is proposal/evidence only; it never self-authorizes an action.
23. Procedural memory is structured execution evidence/state. A procedure may drive known transitions through the deterministic Control Plane, but it is never blanket authorization or a source of new strategy.
24. Current observed state outranks remembered procedure. Compiled skills must not use recorded absolute coordinates as reusable authority/primary identity.
25. One successful trajectory creates at most a candidate skill. Promotion requires explicit replay/regression/variant evidence.
26. Procedural memory and Control Plane task state must not persist private chain-of-thought. Store structured/user-visible intent summaries, observations, actions/receipts and verification only.
27. Raw screenshots/sensitive demonstration content require explicit redaction/retention/deletion/encryption policy before long-term storage.
28. A model/Chat/planner completion assertion does not advance procedure state by itself; applicable completion verification is required.
29. The Windows desktop capability foundation is already accepted through Stage 26.2D. Stage 26.2E is the first real-application gate; Stage 26.3 is Verified Procedure Runtime / deterministic Control Plane integration.
30. Arbitrary human “show me once” transfer remains Stage 26.4 after procedure-runtime foundations and must be candidate-first, not blind replay.
31. Concrete future local applications/capabilities are chosen from actual tasks/evidence, not a fixed precommitted application list.
32. Do not expose arbitrary MCP install/uninstall/update/edit/search/admin controls to ordinary Chat as baseline capabilities.
33. Do not restore legacy code/design because of sunk cost; Git history is archival storage.
34. Avoid new paid infrastructure unless the user explicitly chooses it for a concrete benefit.
35. Real Windows/ordinary-Chat acceptance may only be marked passed from actual target-machine/user-surface evidence.
36. Historical research/stage documents cannot override `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md`, active stage contracts or current code/tests.
37. Under the current development operating constraint, use ordinary ChatGPT + GitHub + project local/connected tools; do not use Codex or ChatGPT Work unless explicitly re-enabled.
38. The term `CONTROL_PLANE_API_KEY` refers to OpenAI Secure MCP Tunnel credential/control-plane infrastructure and is unrelated to the project's deterministic local execution Control Plane.

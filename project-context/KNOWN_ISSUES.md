# Known Issues

Only unresolved issues for the current architecture are listed here. Historical Stage 25 candidate/runtime problems that were superseded by accepted Stage 25.2 evidence are not active blockers.

1. **Present-target visual capability is intentionally limited.** Stage 25 baseline remains 3/5 present-target HIT because repeated-row and tiny-indicator classes are deliberately blocked. Stage 25.2 public escalation is narrow; repeated-row/tiny/icon-only classes are not automatically promoted.

2. **Freshness verification is not atomic with coordinate click.** The viewport is re-captured and must satisfy deterministic freshness checks before coordinate action, but screenshot and click remain separate MCP calls. A narrow TOCTOU window remains.

3. **Loopback vision endpoint ownership is PID-checked but not cryptographically authenticated.** A same-user race around process/port reuse remains theoretically possible after ownership verification.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains available. DNS resolution/rebinding and redirect policy remain residual work.

5. **Vision Python/model dependency reproducibility is not release-grade.** Stable distribution still needs an explicit artifact/hash/update policy for Python/runtime/model assets.

6. **Pinned semantic npm graph includes deprecated transitive `glob@10.5.0`.** Keep this as a dedicated dependency follow-up with the full locked acceptance matrix.

7. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP remains internal diagnostic/lifecycle infrastructure; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product surface.

8. **Large typed action surfaces can be truncated in the tested Chat app.** Keep the Chat-facing surface small and truthful; measured historical behavior is not a universal hard-coded limit.

9. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Stage 26 foundation should avoid public schema changes until a truthful boundary is needed and accepted.

10. **OpenAI safety can block composite workflows independently of app permission mode.** Treat a pre-MCP product block separately from local backend failure.

11. **Authorization policy is not yet accepted for future Windows desktop/consequential capability classes.** Stage 25.2 browser-click authorization must not be generalized automatically to desktop actions.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** These remain Stage 27 distribution/maintenance work.

13. **Procedural memory is design-active, not implemented/product-accepted.** Raw trajectory schema, redaction/retention, Demo Compiler, versioned skill store, trust lifecycle, retrieval evidence and completion verifier still need implementation and acceptance.

14. **A successful trajectory is not yet a trusted reusable skill.** Stage 26 must prove candidate -> verified -> promoted/stale/disabled lifecycle and prevent one lucky success from auto-promotion.

15. **Human demonstration privacy/retention is unresolved.** Long-term raw screenshot/text storage could contain secrets or personal data. Redaction and retention policy must exist before arbitrary demonstrations are persisted.

16. **Private reasoning must not enter procedural memory.** The recorder/compiler must store structured/user-visible intent summaries and operational evidence only, not private chain-of-thought.

17. **Completion verification is not implemented yet.** A model/Chat `subtask_complete` claim must not advance a workflow pointer without applicable verifier evidence.

18. **Windows desktop surface is not implemented yet.** Native/deterministic UI observation, screen capture, bounded vision and reviewed keyboard/mouse actuation need their own scoped acceptance before arbitrary local desktop workflows can be claimed.

19. **Arbitrary human “show me once” recording is not available yet.** The current browser semantic path can observe controlled Chat/tool actions, not general user interaction across Windows. True human demonstration capture belongs at/after the Windows desktop surface.

20. **The post-desktop public contract is intentionally undecided.** Current accepted public tool names remain five. After Windows desktop surface exists, a separate ADR and ordinary-Chat acceptance must decide whether new truthful tool names are required or the same small-semantic philosophy can continue. Do not overload existing tools or add a generic opaque dispatcher merely to avoid this decision.

21. **Concrete future local programs/capabilities are intentionally not preselected.** They should be chosen from actual user tasks and evidence when desktop/capability benchmarking begins.

22. **Repository metadata may still contain historical wording.** Current code and authoritative `project-context` docs override stale descriptive metadata.

23. **No first stable release exists.** Browser semantic→vision is accepted, but Procedural Memory, Windows desktop capability, distribution/maintenance hardening and clean-user product E2E remain incomplete.

## Closed / superseded findings

- Stage 25.1 PR #74 was squash-merged after full review and real target acceptance.
- Stage 25.2 PR #77 was squash-merged to `main` as `2a410476ef849fd6d9c172703a004b1befcbcfb1`.
- Final Stage 25.2 target-tested production-code HEAD `41ef3f4032ae9169d940b3a04e5bdfe75170ca85` passed the public semantic→real-F16 gate: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors, `semantic_cases_started_vlm=0`, `acceptance_pass=true`, `TEST_EXIT_CODE=0`.
- Final Stage 25.2 cleanup is proved: runtime stopped, Chrome remained running, minimum observed free physical RAM was 1.04 GB and no safety stop occurred.
- Semantic click authorization requires an enabled button; disabled/non-button exact matches ABSTAIN without VLM.
- Planner-controlled visual redirection is closed at the router boundary: `targetText` is the authorization anchor; planner `target`, free-form `instruction` and planner-supplied `kind` do not choose another visual target.
- Semantic ambiguity and generic semantic click errors do not trigger vision.
- Safe ABSTAIN is a no-action result rather than a backend error.
- Installed semantic bootstrap/source drift, lockfile application, prepared-target expiry/cap, descendant stdio/buffering, junction containment, credential scrub, CodeQL coverage and literal private-network blocking remain regression-tested foundations.
- Earlier Stage 25 runtime/model candidate rankings are historical research; accepted target path is the measured llama.cpp + LFM2.5-VL-450M F16 configuration above.

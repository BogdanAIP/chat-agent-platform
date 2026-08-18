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

13. **Procedural-memory upstream core is qualified but not integrated into the product path.** OpenAdapt Flow/Capture passed exact-source install/import and model-free tutorial verification on the target Windows machine, but no OpenAdapt dependency is yet part of production `semantic-projection` or installed runtime.

14. **The first compiled procedure must not silently become product-trusted.** Upstream `SkillLibrary.create_skill()` marks bootstrap v1 active; Chat Agent Platform keeps a stricter candidate-first product policy. A thin policy adapter still needs implementation/acceptance before integration.

15. **Human demonstration privacy/retention is unresolved.** Raw desktop capture may contain everything visible or typed. Long-lived storage/sync is not accepted until deletion, encryption and redaction policy is defined and tested.

16. **Private reasoning must not enter procedural memory.** Store structured/user-visible intent summaries and operational evidence only, never private chain-of-thought.

17. **OpenAdapt Capture has not yet passed the real bounded Windows capture gate.** Package install/symbol checks passed, but Stage 26.1B still must prove window-scoped recording, action classes, UIA evidence, conversion/compile/replay or bounded refusal, zero unrelated-window actions and clean local artifact containment.

18. **Windows executor authority boundary is not accepted yet.** The pinned OpenAdapt server has bounded typed `/input`, `/input/guarded`, `/uia/find` and `/uia/act` routes and disables legacy `/execute_windows` by default. The project still must compare this agent boundary with a narrower actuator and prove generic exec is disabled/unreachable in product configuration.

19. **F16 -> OpenAdapt Grounder adapter is not implemented yet.** The seam looks compatible and proposal-only, but it needs a real adapter test proving local/on-demand lifecycle, no screenshot egress, and preservation of identity/risk/freshness/effect gates.

20. **Windows desktop surface is not product-accepted yet.** Native/deterministic UI observation, screen capture, bounded vision and reviewed keyboard/mouse actuation need their own scoped acceptance before arbitrary local desktop workflows can be claimed.

21. **Arbitrary human “show me once” transfer is not accepted yet.** Capture and compiler candidates exist upstream, but Stage 26.4 still must prove real demonstration -> compiled procedure -> project trust gate -> variant-task reuse with current-state priority.

22. **The post-desktop public contract is intentionally undecided.** Current accepted public tool names remain five. After Windows desktop surface exists, a separate ADR and ordinary-Chat acceptance must decide whether new truthful tool names are required or the same small-semantic philosophy can continue. Do not overload existing tools or add a generic opaque dispatcher merely to avoid this decision.

23. **Concrete future local programs/capabilities are intentionally not preselected.** Choose them from actual user tasks and evidence when desktop/capability benchmarking begins.

24. **OpenAdapt Desktop is not the qualified runtime baseline.** Its pinned packaging lane embeds a different Flow version from the target-qualified Flow 1.31.0. Reuse its Tauri/sidecar/installer ideas only after Stage 27 compatibility review.

25. **Python/OpenAdapt packaging is not release-grade.** Qualification used isolated Python 3.12 because Flow 1.31.0 currently declares Python `<3.13`. Stage 27 must own exact Python/upstream artifact/hash/update policy instead of relying on user global environments.

26. **Repository metadata may still contain historical wording.** Current code and authoritative `project-context` docs override stale descriptive metadata.

27. **No first stable release exists.** Browser semantic→vision is accepted, but Procedural Memory integration, Windows desktop capability, distribution/maintenance hardening and clean-user product E2E remain incomplete.

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
- The assumption that Stage 26 must first build its own recorder/compiler/skill store from scratch is superseded. Pinned OpenAdapt Flow/Capture passed exact-source qualification on Windows; reuse/adapt qualified upstream mechanisms before writing replacements.
- An early Stage 26.1A target failure caused by missing `requests` was a qualification-harness defect: the probe imported `WindowsBackend` while installing Flow only with `[browser]`. The pinned package correctly declares `requests` in `[windows]`; after installing `[browser,windows]` the exact target rerun passed.

# Known Issues

Only unresolved issues for the current architecture are listed here. Closed/superseded qualification findings are kept at the end for historical clarity.

1. **Present-target browser visual capability remains intentionally limited.** Stage 25 baseline still blocks repeated-row/tiny classes rather than promoting unsafe clicks.

2. **Browser screenshot -> coordinate action is not atomic.** Freshness is rechecked before click, but capture and action remain separate calls with a narrow TOCTOU window.

3. **Loopback vision endpoint ownership is PID-checked, not cryptographically authenticated.** A same-user process/port race remains theoretically possible.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Literal private/link-local/metadata targets are blocked while DNS rebinding/redirect/private-network isolation remains residual work.

5. **Python/model/OpenAdapt dependency reproducibility is not release-grade.** Stable distribution needs exact artifact/hash/update policy rather than user-global environments.

6. **Pinned semantic npm graph includes deprecated transitive `glob@10.5.0`.** Keep as a dependency follow-up with the full locked acceptance matrix.

7. **Generic adaptive Chat-facing actions are not product-accepted.** 1MCP remains internal; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product contract.

8. **Large exported action surfaces can be truncated in the tested Chat app.** Keep the public surface small and truthful; historical truncation is not a universal numeric hard limit.

9. **Exported Chat action definitions require explicit Refresh/review.** Do not change the public contract casually during Windows integration.

10. **OpenAI product safety may block a composite workflow before MCP invocation.** Distinguish pre-MCP product blocks from local backend failures.

11. **Authorization policy is not accepted for arbitrary Windows consequence classes.** Stage 26.2D proves one bounded structure-first visual route, not universal desktop authority.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** Stage 27 work remains.

13. **OpenAdapt procedural substrate is target-qualified but not integrated into the normal product path.** Flow/Capture mechanics are accepted upstream candidates; verified procedure runtime starts only after real-app E2E.

14. **First compiled procedure must not silently become product-trusted.** Project policy remains candidate-first even if an upstream bootstrap version is active internally.

15. **Human demonstration privacy/retention is unresolved.** Raw desktop capture may expose visible/typed sensitive data. Long-lived sync/storage is not accepted until deletion, encryption and redaction policy is defined and tested.

16. **Private reasoning must never enter procedural memory.** Store structured/user-visible goals, observed state, transitions, receipts and verification only.

17. **The 97/97 Stage 26.1E fixture result is not global Windows accuracy.** It proves one controlled role+name path. Multiple real applications, custom controls and weaker accessibility providers need separate evidence.

18. **`AutomationId` lacks dedicated accepted physical coverage across real applications.** Add explicit coverage before claiming broad structural-resolution reliability.

19. **No real-application Windows E2E has passed yet.** Stage 26.2D physically proved a real guarded visual click on a WinForms fixture, but fixture evidence is not equivalent to VS Code/OriginPro/Reaper/custom real-app evidence. Stage 26.2E is active.

20. **Arbitrary human “show me once” transfer is not accepted.** Capture/compiler candidates exist, but candidate trust, verifier-controlled replay and changed-task reuse require product evidence.

21. **Public desktop/procedure contract is intentionally undecided.** Current five tools remain accepted. Use a dedicated ADR after desktop evidence; do not overload `web_interact` or add a generic workflow dispatcher.

22. **The first real application is a qualification choice, not an architectural dependency.** Stage 26.2E currently uses isolated VS Code because it offers a medium-complexity real app plus a strongly disposable artifact/profile boundary.

23. **OpenAdapt Desktop is not the qualified runtime baseline.** Its packaging ideas may be useful in Stage 27, but compatibility must be checked against the exact qualified Flow line.

24. **Specialized tiny reasoning is intentionally not committed to the release path.** TRM/STARM/FPRM or another model is only justified after real verified procedure-state data and measured need.

25. **Multi-chat orchestration is a separate parallel layer.** It is not part of Windows executor safety or a Stage 27/28 prerequisite. Codex/Work remain disabled under the current operating constraint.

26. **No first stable release exists.** Real-app E2E, verified procedural reuse, distribution hardening and clean-user release gates remain incomplete.

27. **Stage 26.2E VS Code UIA focus shape is not yet physically known on the target machine.** The qualification intentionally accepts only a narrow enabled/visible focused editor-like control. If target VS Code exposes a different role/name/focus pattern, the first physical run must fail before mutation and preserve diagnostics; broaden only from observed evidence.

28. **Stage 26.2E guarded-input evidence covers one harmless text mutation only.** It is not permission for arbitrary editing, file operations or application commands.

## Closed / superseded findings

- Stage 25.1 and Stage 25.2 browser semantic/vision foundations are merged and accepted; historical candidate-runtime comparisons no longer define the active path.
- The assumption that Stage 26 must build its own recorder/compiler/skill store from scratch is superseded by exact OpenAdapt Flow/Capture qualification.
- Stage 26.1B OpenAdapt Capture real bounded Windows qualification passed at `7a9daa9329d81994833c22b4ca2e321927527dcc`.
- Stage 26.1C bounded Windows executor authority qualification passed at `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.
- Stage 26.1D measured the ~184 s warm UIA cycle and isolated desktop-wide traversal as the dominant blocker.
- Stage 26.1E replaced accepted desktop-wide resolution with bounded exact-window UIA and passed 97 scoped resolutions with zero desktop fallback/binding failures/ambiguities/false/unrelated-window actions.
- The old issue that the accepted executor/resolver were only qualification assets is closed by Stage 26.2A production runtime (#87).
- The old issue that no canonical DesktopState existed is closed by Stage 26.2B (#88).
- The old issue that no native Desktop F16 Grounder existed is closed by Stage 26.2C (#89).
- The old issue that deterministic Windows UIA -> vision routing was not accepted is closed for the bounded controlled-fixture contract by Stage 26.2D (#90). Broad real-application accuracy remains issue #19.
- The old stacked/unmerged #83/#84/#85 landing issue is closed; the stack was safely rebased/landed with accepted trees preserved.
- The proposal to create a local generic Agent Control Plane/Planner after Stage 26.2D is superseded: it conflicts with the product boundary. Ordinary ChatGPT remains the only general planner; the release path is real-app E2E then Verified Procedure Runtime.